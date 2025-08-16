# Backwards compatibility file for DataExtractor
# This file provides a wrapper that maintains the old interface while using the new services

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..services_v2.team_service import TeamService
from ..services_v2.match_service import MatchService
from ..services_v2.statistics_service import StatisticsService
from ..services_v2.quiniela_service import QuinielaService
from ..services_v2.odds_service import OddsService


class DataExtractor:
    """
    Backwards compatibility wrapper for the old DataExtractor class.
    This delegates to the new specialized services.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.team_service = TeamService(db)
        self.match_service = MatchService(db)
        self.statistics_service = StatisticsService(db)
        self.quiniela_service = QuinielaService(db)
        self.odds_service = OddsService(db)
    
    async def update_teams(self, season: int):
        """Update teams for both La Liga and Segunda División"""
        return await self.team_service.update_teams(season)
    
    async def update_matches(self, season: int, from_date: str = None, to_date: str = None):
        """Update matches from both leagues"""
        return await self.match_service.update_matches(season, from_date, to_date)
    
    async def update_team_statistics(self, season: int):
        """Update team statistics for all teams"""
        return await self.statistics_service.update_team_statistics(season)
    
    async def update_odds(self, match_ids: List[int]):
        """Update odds for specific matches"""
        return await self.odds_service.update_odds_for_matches(match_ids)
    
    async def get_quiniela_data(self, season: int, week_number: int = None) -> List[Dict[str, Any]]:
        """Get comprehensive data for quiniela predictions"""
        return await self.quiniela_service.get_quiniela_data(season, week_number)