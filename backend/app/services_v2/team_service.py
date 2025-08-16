from sqlalchemy.orm import Session
from typing import List, Optional
from ..domain.entities.team import Team
from ..services.api_football_client import APIFootballClient
from ..config.settings import settings


class TeamService:
    def __init__(self, db: Session):
        self.db = db
        self.api_client = APIFootballClient()
    
    async def update_teams(self, season: int) -> None:
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
                    self._update_team(existing_team, team_info, venue_info)
                else:
                    # Create new team
                    new_team = self._create_team(team_info, venue_info, league_id)
                    self.db.add(new_team)
        
        self.db.commit()
    
    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Get team by internal ID"""
        return self.db.query(Team).filter(Team.id == team_id).first()
    
    def get_team_by_api_id(self, api_id: int) -> Optional[Team]:
        """Get team by API ID"""
        return self.db.query(Team).filter(Team.api_id == api_id).first()
    
    def get_teams_by_league(self, league_id: int) -> List[Team]:
        """Get all teams from a specific league"""
        return self.db.query(Team).filter(Team.league_id == league_id).all()
    
    def get_all_teams(self) -> List[Team]:
        """Get all teams"""
        return self.db.query(Team).all()
    
    def _update_team(self, team: Team, team_info: dict, venue_info: dict) -> None:
        """Update existing team with new data"""
        team.name = team_info.get("name")
        team.short_name = team_info.get("code")
        team.logo = team_info.get("logo")
        team.founded = team_info.get("founded")
        team.venue_name = venue_info.get("name")
        team.venue_capacity = venue_info.get("capacity")
    
    def _create_team(self, team_info: dict, venue_info: dict, league_id: int) -> Team:
        """Create new team entity"""
        return Team(
            api_id=team_info.get("id"),
            name=team_info.get("name"),
            short_name=team_info.get("code"),
            logo=team_info.get("logo"),
            league_id=league_id,
            founded=team_info.get("founded"),
            venue_name=venue_info.get("name"),
            venue_capacity=venue_info.get("capacity")
        )