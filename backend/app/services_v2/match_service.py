from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from ..domain.entities.match import Match
from ..domain.entities.team import Team
from ..services.api_football_client import APIFootballClient
from ..config.settings import settings


class MatchService:
    def __init__(self, db: Session):
        self.db = db
        self.api_client = APIFootballClient()
    
    async def update_matches(self, season: int, from_date: str = None, to_date: str = None) -> None:
        """Update matches from both leagues"""
        leagues = [settings.la_liga_id, settings.segunda_division_id]
        
        for league_id in leagues:
            fixtures_data = await self.api_client.get_fixtures_by_league(
                league_id, season, from_date, to_date
            )
            
            for fixture_data in fixtures_data:
                await self._process_fixture(fixture_data, league_id, season)
        
        self.db.commit()
    
    async def update_odds(self, match_ids: List[int]) -> None:
        """Update odds for specific matches"""
        for match_id in match_ids:
            match = self.db.query(Match).filter_by(id=match_id).first()
            if not match:
                continue
            
            odds_data = await self.api_client.get_odds(match.api_id)
            
            if odds_data:
                self._update_match_odds(match, odds_data)
        
        self.db.commit()
    
    def get_match_by_id(self, match_id: int) -> Optional[Match]:
        """Get match by internal ID"""
        return self.db.query(Match).filter(Match.id == match_id).first()
    
    def get_match_by_api_id(self, api_id: int) -> Optional[Match]:
        """Get match by API ID"""
        return self.db.query(Match).filter(Match.api_id == api_id).first()
    
    def get_matches_by_season(self, season: int) -> List[Match]:
        """Get all matches from a specific season"""
        return self.db.query(Match).filter(Match.season == season).all()
    
    def get_matches_by_teams(self, home_team_id: int, away_team_id: int) -> List[Match]:
        """Get head-to-head matches between two teams"""
        return self.db.query(Match).filter(
            ((Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id)) |
            ((Match.home_team_id == away_team_id) & (Match.away_team_id == home_team_id))
        ).all()
    
    def get_team_matches(self, team_id: int, season: int = None) -> List[Match]:
        """Get all matches for a specific team"""
        query = self.db.query(Match).filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        )
        
        if season:
            query = query.filter(Match.season == season)
        
        return query.all()
    
    async def _process_fixture(self, fixture_data: dict, league_id: int, season: int) -> None:
        """Process individual fixture data"""
        fixture = fixture_data.get("fixture", {})
        teams = fixture_data.get("teams", {})
        goals = fixture_data.get("goals", {})
        
        # Get team IDs from database
        home_team = self.db.query(Team).filter_by(
            api_id=teams.get("home", {}).get("id")
        ).first()
        away_team = self.db.query(Team).filter_by(
            api_id=teams.get("away", {}).get("id")
        ).first()
        
        if not home_team or not away_team:
            return
        
        # Check if match exists
        existing_match = self.db.query(Match).filter_by(
            api_id=fixture.get("id")
        ).first()
        
        # Determine result
        result = self._calculate_result(goals)
        
        if existing_match:
            # Update existing match
            self._update_match(existing_match, fixture, goals, result)
        else:
            # Create new match
            new_match = self._create_match(
                fixture, fixture_data, home_team, away_team, 
                league_id, season, goals, result
            )
            self.db.add(new_match)
    
    def _calculate_result(self, goals: dict) -> Optional[str]:
        """Calculate match result (1, X, 2)"""
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        
        if home_goals is not None and away_goals is not None:
            if home_goals > away_goals:
                return "1"
            elif home_goals < away_goals:
                return "2"
            else:
                return "X"
        return None
    
    def _update_match(self, match: Match, fixture: dict, goals: dict, result: str) -> None:
        """Update existing match with new data"""
        match.status = fixture.get("status", {}).get("short")
        match.home_goals = goals.get("home")
        match.away_goals = goals.get("away")
        match.result = result
    
    def _create_match(self, fixture: dict, fixture_data: dict, home_team: Team, 
                     away_team: Team, league_id: int, season: int, goals: dict, result: str) -> Match:
        """Create new match entity"""
        match_date = datetime.fromisoformat(
            fixture.get("date").replace("Z", "+00:00")
        )
        
        return Match(
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
    
    def _update_match_odds(self, match: Match, odds_data: list) -> None:
        """Update match odds from API data"""
        if not odds_data:
            return
            
        bookmakers = odds_data[0].get("bookmakers", [])
        if not bookmakers:
            return
            
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