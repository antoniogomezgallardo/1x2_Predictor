from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from ..domain.entities.team import Team
from ..domain.entities.statistics import TeamStatistics
from ..services.api_football_client import APIFootballClient


class StatisticsService:
    def __init__(self, db: Session):
        self.db = db
        self.api_client = APIFootballClient()
    
    async def update_team_statistics(self, season: int) -> None:
        """Update team statistics for all teams"""
        teams = self.db.query(Team).all()
        
        for team in teams:
            stats_data = await self.api_client.get_team_statistics(
                team.api_id, team.league_id, season
            )
            
            if not stats_data:
                continue
            
            await self._process_team_statistics(team, stats_data, season)
        
        self.db.commit()
    
    async def update_single_team_statistics(self, team_id: int, season: int) -> Optional[TeamStatistics]:
        """Update statistics for a single team"""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return None
        
        stats_data = await self.api_client.get_team_statistics(
            team.api_id, team.league_id, season
        )
        
        if not stats_data:
            return None
        
        statistics = await self._process_team_statistics(team, stats_data, season)
        self.db.commit()
        return statistics
    
    def get_team_statistics(self, team_id: int, season: int) -> Optional[TeamStatistics]:
        """Get team statistics for a specific season"""
        return self.db.query(TeamStatistics).filter(
            TeamStatistics.team_id == team_id,
            TeamStatistics.season == season
        ).first()
    
    def get_league_statistics(self, league_id: int, season: int) -> List[TeamStatistics]:
        """Get all team statistics for a league and season"""
        return self.db.query(TeamStatistics).filter(
            TeamStatistics.league_id == league_id,
            TeamStatistics.season == season
        ).order_by(TeamStatistics.points.desc()).all()
    
    def get_team_statistics_history(self, team_id: int) -> List[TeamStatistics]:
        """Get historical statistics for a team across all seasons"""
        return self.db.query(TeamStatistics).filter(
            TeamStatistics.team_id == team_id
        ).order_by(TeamStatistics.season.desc()).all()
    
    def compare_teams_statistics(self, team1_id: int, team2_id: int, season: int) -> dict:
        """Compare statistics between two teams for a season"""
        team1_stats = self.get_team_statistics(team1_id, season)
        team2_stats = self.get_team_statistics(team2_id, season)
        
        if not team1_stats or not team2_stats:
            return {}
        
        return {
            "team1": {
                "team_id": team1_id,
                "matches_played": team1_stats.matches_played,
                "wins": team1_stats.wins,
                "draws": team1_stats.draws,
                "losses": team1_stats.losses,
                "goals_for": team1_stats.goals_for,
                "goals_against": team1_stats.goals_against,
                "points": team1_stats.points,
                "goal_difference": team1_stats.goals_for - team1_stats.goals_against,
                "win_percentage": (team1_stats.wins / max(team1_stats.matches_played, 1)) * 100
            },
            "team2": {
                "team_id": team2_id,
                "matches_played": team2_stats.matches_played,
                "wins": team2_stats.wins,
                "draws": team2_stats.draws,
                "losses": team2_stats.losses,
                "goals_for": team2_stats.goals_for,
                "goals_against": team2_stats.goals_against,
                "points": team2_stats.points,
                "goal_difference": team2_stats.goals_for - team2_stats.goals_against,
                "win_percentage": (team2_stats.wins / max(team2_stats.matches_played, 1)) * 100
            }
        }
    
    def calculate_form_metrics(self, team_id: int, season: int) -> dict:
        """Calculate additional form metrics for a team"""
        stats = self.get_team_statistics(team_id, season)
        if not stats:
            return {}
        
        total_matches = max(stats.matches_played, 1)
        
        return {
            "win_percentage": (stats.wins / total_matches) * 100,
            "draw_percentage": (stats.draws / total_matches) * 100,
            "loss_percentage": (stats.losses / total_matches) * 100,
            "goals_per_match": stats.goals_for / total_matches,
            "goals_conceded_per_match": stats.goals_against / total_matches,
            "points_per_match": stats.points / total_matches,
            "goal_difference": stats.goals_for - stats.goals_against,
            "home_win_percentage": (stats.home_wins / max(stats.matches_played // 2, 1)) * 100,
            "away_win_percentage": (stats.away_wins / max(stats.matches_played // 2, 1)) * 100
        }
    
    async def _process_team_statistics(self, team: Team, stats_data: dict, season: int) -> TeamStatistics:
        """Process team statistics data from API"""
        # Check if statistics exist
        existing_stats = self.db.query(TeamStatistics).filter_by(
            team_id=team.id,
            season=season,
            league_id=team.league_id
        ).first()
        
        fixtures = stats_data.get("fixtures", {})
        goals = stats_data.get("goals", {})
        
        stats_values = self._extract_statistics_values(fixtures, goals)
        
        if existing_stats:
            # Update existing statistics
            for key, value in stats_values.items():
                setattr(existing_stats, key, value)
            existing_stats.updated_at = datetime.utcnow()
            return existing_stats
        else:
            # Create new statistics
            new_stats = TeamStatistics(
                team_id=team.id,
                season=season,
                league_id=team.league_id,
                **stats_values
            )
            self.db.add(new_stats)
            return new_stats
    
    def _extract_statistics_values(self, fixtures: dict, goals: dict) -> dict:
        """Extract and calculate statistics values from API data"""
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
        
        return stats_values