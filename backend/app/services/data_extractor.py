from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
from ..database.models import Team, Match, TeamStatistics, Base
from .api_football_client import APIFootballClient
from ..config.settings import settings


class DataExtractor:
    def __init__(self, db: Session):
        self.db = db
        self.api_client = APIFootballClient()
    
    async def update_teams(self, season: int):
        """Update teams for both La Liga and Segunda División"""
        leagues = [settings.la_liga_id, settings.segunda_division_id]
        
        for league_id in leagues:
            teams_data = await self.api_client.get_teams_by_league(league_id, season)
            
            for team_data in teams_data:
                team_info = team_data.get("team", {})
                venue_info = team_data.get("venue", {})
                
                # Check if team exists
                existing_team = self.db.query(Team).filter_by(api_id=team_info.get("id")).first()
                
                if existing_team:
                    # Update existing team
                    existing_team.name = team_info.get("name")
                    existing_team.short_name = team_info.get("code")
                    existing_team.logo = team_info.get("logo")
                    existing_team.founded = team_info.get("founded")
                    existing_team.venue_name = venue_info.get("name")
                    existing_team.venue_capacity = venue_info.get("capacity")
                else:
                    # Create new team
                    new_team = Team(
                        api_id=team_info.get("id"),
                        name=team_info.get("name"),
                        short_name=team_info.get("code"),
                        logo=team_info.get("logo"),
                        league_id=league_id,
                        founded=team_info.get("founded"),
                        venue_name=venue_info.get("name"),
                        venue_capacity=venue_info.get("capacity")
                    )
                    self.db.add(new_team)
        
        self.db.commit()
    
    async def update_matches(self, season: int, from_date: str = None, to_date: str = None):
        """Update matches from both leagues"""
        leagues = [settings.la_liga_id, settings.segunda_division_id]
        
        for league_id in leagues:
            fixtures_data = await self.api_client.get_fixtures_by_league(
                league_id, season, from_date, to_date
            )
            
            for fixture_data in fixtures_data:
                fixture = fixture_data.get("fixture", {})
                teams = fixture_data.get("teams", {})
                goals = fixture_data.get("goals", {})
                score = fixture_data.get("score", {})
                
                # Get team IDs from database
                home_team = self.db.query(Team).filter_by(
                    api_id=teams.get("home", {}).get("id")
                ).first()
                away_team = self.db.query(Team).filter_by(
                    api_id=teams.get("away", {}).get("id")
                ).first()
                
                if not home_team or not away_team:
                    continue
                
                # Check if match exists
                existing_match = self.db.query(Match).filter_by(
                    api_id=fixture.get("id")
                ).first()
                
                # Determine result
                result = None
                if goals.get("home") is not None and goals.get("away") is not None:
                    if goals["home"] > goals["away"]:
                        result = "1"
                    elif goals["home"] < goals["away"]:
                        result = "2"
                    else:
                        result = "X"
                
                if existing_match:
                    # Update existing match
                    existing_match.status = fixture.get("status", {}).get("short")
                    existing_match.home_goals = goals.get("home")
                    existing_match.away_goals = goals.get("away")
                    existing_match.result = result
                else:
                    # Create new match
                    match_date = datetime.fromisoformat(
                        fixture.get("date").replace("Z", "+00:00")
                    )
                    
                    new_match = Match(
                        api_id=fixture.get("id"),
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        league_id=league_id,
                        season=season,
                        round=fixture_data.get("league", {}).get("round"),
                        match_date=match_date,
                        status=fixture.get("status", {}).get("short"),
                        home_goals=goals.get("home"),
                        away_goals=goals.get("away"),
                        result=result
                    )
                    self.db.add(new_match)
        
        self.db.commit()
    
    async def update_team_statistics(self, season: int):
        """Update team statistics for all teams"""
        teams = self.db.query(Team).all()
        
        for team in teams:
            stats_data = await self.api_client.get_team_statistics(
                team.api_id, team.league_id, season
            )
            
            if not stats_data:
                continue
            
            # Check if statistics exist
            existing_stats = self.db.query(TeamStatistics).filter_by(
                team_id=team.id,
                season=season,
                league_id=team.league_id
            ).first()
            
            fixtures = stats_data.get("fixtures", {})
            goals = stats_data.get("goals", {})
            
            stats_values = {
                "matches_played": fixtures.get("played", {}).get("total", 0),
                "wins": fixtures.get("wins", {}).get("total", 0),
                "draws": fixtures.get("draws", {}).get("total", 0),
                "losses": fixtures.get("loses", {}).get("total", 0),
                "goals_for": goals.get("for", {}).get("total", {}).get("total", 0),
                "goals_against": goals.get("against", {}).get("total", {}).get("total", 0),
                "home_wins": fixtures.get("wins", {}).get("home", 0),
                "home_draws": fixtures.get("draws", {}).get("home", 0),
                "home_losses": fixtures.get("loses", {}).get("home", 0),
                "away_wins": fixtures.get("wins", {}).get("away", 0),
                "away_draws": fixtures.get("draws", {}).get("away", 0),
                "away_losses": fixtures.get("loses", {}).get("away", 0),
            }
            
            # Calculate points
            stats_values["points"] = (stats_values["wins"] * 3 + stats_values["draws"])
            
            if existing_stats:
                # Update existing statistics
                for key, value in stats_values.items():
                    setattr(existing_stats, key, value)
                existing_stats.updated_at = datetime.utcnow()
            else:
                # Create new statistics
                new_stats = TeamStatistics(
                    team_id=team.id,
                    season=season,
                    league_id=team.league_id,
                    **stats_values
                )
                self.db.add(new_stats)
        
        self.db.commit()
    
    async def update_odds(self, match_ids: List[int]):
        """Update odds for specific matches"""
        for match_id in match_ids:
            match = self.db.query(Match).filter_by(id=match_id).first()
            if not match:
                continue
            
            odds_data = await self.api_client.get_odds(match.api_id)
            
            if odds_data:
                bookmakers = odds_data[0].get("bookmakers", [])
                if bookmakers:
                    bets = bookmakers[0].get("bets", [])
                    for bet in bets:
                        if bet.get("name") == "Match Winner":
                            values = bet.get("values", [])
                            for value in values:
                                if value.get("value") == "Home":
                                    match.home_odds = float(value.get("odd", 0))
                                elif value.get("value") == "Draw":
                                    match.draw_odds = float(value.get("odd", 0))
                                elif value.get("value") == "Away":
                                    match.away_odds = float(value.get("odd", 0))
        
        self.db.commit()
    
    async def get_quiniela_data(self, season: int, week_number: int = None) -> List[Dict[str, Any]]:
        """Get comprehensive data for quiniela predictions"""
        matches = await self.api_client.get_quiniela_matches(season, week_number)
        
        quiniela_data = []
        for match_data in matches:
            fixture = match_data.get("fixture", {})
            teams = match_data.get("teams", {})
            
            # Get teams from database
            home_team = self.db.query(Team).filter_by(
                api_id=teams.get("home", {}).get("id")
            ).first()
            away_team = self.db.query(Team).filter_by(
                api_id=teams.get("away", {}).get("id")
            ).first()
            
            if not home_team or not away_team:
                continue
            
            # Get team statistics
            home_stats = self.db.query(TeamStatistics).filter_by(
                team_id=home_team.id,
                season=season
            ).first()
            away_stats = self.db.query(TeamStatistics).filter_by(
                team_id=away_team.id,
                season=season
            ).first()
            
            # Get head-to-head data
            h2h_data = await self.api_client.get_head_to_head(
                home_team.api_id, away_team.api_id
            )
            
            # Get recent form
            home_form = await self.api_client.get_team_form(
                home_team.api_id, home_team.league_id, season
            )
            away_form = await self.api_client.get_team_form(
                away_team.api_id, away_team.league_id, season
            )
            
            match_info = {
                "fixture_id": fixture.get("id"),
                "match_date": fixture.get("date"),
                "home_team": {
                    "id": home_team.id,
                    "name": home_team.name,
                    "api_id": home_team.api_id
                },
                "away_team": {
                    "id": away_team.id,
                    "name": away_team.name,
                    "api_id": away_team.api_id
                },
                "home_stats": home_stats,
                "away_stats": away_stats,
                "h2h_data": h2h_data,
                "home_form": home_form,
                "away_form": away_form
            }
            
            quiniela_data.append(match_info)
        
        return quiniela_data