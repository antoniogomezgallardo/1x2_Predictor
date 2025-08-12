import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import asyncio
from ..config.settings import settings


class APIFootballClient:
    def __init__(self):
        self.base_url = f"https://{settings.api_football_host}"
        self.headers = {
            "X-RapidAPI-Key": settings.api_football_key,
            "X-RapidAPI-Host": settings.api_football_host
        }
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to API-Football"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params or {}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_teams_by_league(self, league_id: int, season: int) -> List[Dict[str, Any]]:
        """Get all teams in a specific league and season"""
        params = {
            "league": league_id,
            "season": season
        }
        data = await self._make_request("teams", params)
        return data.get("response", [])
    
    async def get_fixtures_by_league(self, league_id: int, season: int, 
                                   from_date: Optional[str] = None,
                                   to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get fixtures for a specific league and season"""
        params = {
            "league": league_id,
            "season": season
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
            
        data = await self._make_request("fixtures", params)
        return data.get("response", [])
    
    async def get_current_round(self, league_id: int, season: int) -> str:
        """Get current round/gameweek for a league"""
        params = {
            "league": league_id,
            "season": season,
            "current": "true"
        }
        data = await self._make_request("fixtures/rounds", params)
        rounds = data.get("response", [])
        return rounds[0] if rounds else ""
    
    async def get_team_statistics(self, team_id: int, league_id: int, season: int) -> Dict[str, Any]:
        """Get detailed statistics for a team in a specific league/season"""
        params = {
            "team": team_id,
            "league": league_id,
            "season": season
        }
        data = await self._make_request("teams/statistics", params)
        return data.get("response", {})
    
    async def get_head_to_head(self, team1_id: int, team2_id: int, last: int = 10) -> List[Dict[str, Any]]:
        """Get head-to-head matches between two teams"""
        params = {
            "h2h": f"{team1_id}-{team2_id}",
            "last": last
        }
        data = await self._make_request("fixtures/headtohead", params)
        return data.get("response", [])
    
    async def get_team_form(self, team_id: int, league_id: int, season: int, last: int = 5) -> List[Dict[str, Any]]:
        """Get recent form for a team"""
        params = {
            "team": team_id,
            "league": league_id,
            "season": season,
            "last": last
        }
        data = await self._make_request("fixtures", params)
        return data.get("response", [])
    
    async def get_odds(self, fixture_id: int, bookmaker_id: int = 8) -> Dict[str, Any]:
        """Get odds for a specific fixture (bookmaker_id=8 for bet365)"""
        params = {
            "fixture": fixture_id,
            "bookmaker": bookmaker_id
        }
        data = await self._make_request("odds", params)
        return data.get("response", [])
    
    async def get_standings(self, league_id: int, season: int) -> List[Dict[str, Any]]:
        """Get current league standings"""
        params = {
            "league": league_id,
            "season": season
        }
        data = await self._make_request("standings", params)
        return data.get("response", [])
    
    async def get_injuries(self, team_id: int) -> List[Dict[str, Any]]:
        """Get current injuries for a team"""
        params = {
            "team": team_id
        }
        data = await self._make_request("injuries", params)
        return data.get("response", [])
    
    async def get_quiniela_matches(self, season: int, week_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get matches for Spanish Quiniela (15 matches from La Liga and Segunda División)
        If week_number is provided, get specific week, otherwise get current week
        """
        # Get current or specific round
        if week_number is None:
            la_liga_round = await self.get_current_round(settings.la_liga_id, season)
            segunda_round = await self.get_current_round(settings.segunda_division_id, season)
        else:
            la_liga_round = f"Regular Season - {week_number}"
            segunda_round = f"Regular Season - {week_number}"
        
        # Get fixtures from both leagues
        la_liga_fixtures = await self.get_fixtures_by_league(
            settings.la_liga_id, season
        )
        segunda_fixtures = await self.get_fixtures_by_league(
            settings.segunda_division_id, season
        )
        
        # Filter by round and combine
        quiniela_matches = []
        
        # Add La Liga matches (usually 10 matches)
        for fixture in la_liga_fixtures:
            if fixture.get("league", {}).get("round") == la_liga_round:
                quiniela_matches.append(fixture)
        
        # Add Segunda División matches (usually 5 matches to complete 15)
        segunda_count = 15 - len(quiniela_matches)
        segunda_added = 0
        
        for fixture in segunda_fixtures:
            if (fixture.get("league", {}).get("round") == segunda_round and 
                segunda_added < segunda_count):
                quiniela_matches.append(fixture)
                segunda_added += 1
        
        return quiniela_matches[:15]  # Ensure exactly 15 matches