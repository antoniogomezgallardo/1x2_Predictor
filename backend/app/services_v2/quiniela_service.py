from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..domain.entities.team import Team
from ..domain.entities.statistics import TeamStatistics
from ..services.api_football_client import APIFootballClient


class QuinielaService:
    def __init__(self, db: Session):
        self.db = db
        self.api_client = APIFootballClient()
    
    async def get_quiniela_data(self, season: int, week_number: int = None) -> List[Dict[str, Any]]:
        """Get comprehensive data for quiniela predictions"""
        matches = await self.api_client.get_quiniela_matches(season, week_number)
        
        quiniela_data = []
        for match_data in matches:
            match_info = await self._process_quiniela_match(match_data, season)
            if match_info:
                quiniela_data.append(match_info)
        
        return quiniela_data
    
    async def get_enhanced_match_data(self, home_team_id: int, away_team_id: int, season: int) -> Dict[str, Any]:
        """Get enhanced data for a specific match"""
        home_team = self.db.query(Team).filter(Team.id == home_team_id).first()
        away_team = self.db.query(Team).filter(Team.id == away_team_id).first()
        
        if not home_team or not away_team:
            return {}
        
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
        
        return {
            "home_team": {
                "id": home_team.id,
                "name": home_team.name,
                "api_id": home_team.api_id,
                "statistics": home_stats,
                "form": home_form
            },
            "away_team": {
                "id": away_team.id,
                "name": away_team.name,
                "api_id": away_team.api_id,
                "statistics": away_stats,
                "form": away_form
            },
            "head_to_head": h2h_data
        }
    
    def calculate_match_probabilities(self, home_stats: TeamStatistics, away_stats: TeamStatistics) -> Dict[str, float]:
        """Calculate basic match outcome probabilities based on team statistics"""
        if not home_stats or not away_stats:
            return {"home_win": 0.33, "draw": 0.33, "away_win": 0.33}
        
        # Calculate strength metrics
        home_strength = self._calculate_team_strength(home_stats, is_home=True)
        away_strength = self._calculate_team_strength(away_stats, is_home=False)
        
        # Basic probability calculation (simplified)
        total_strength = home_strength + away_strength
        
        if total_strength == 0:
            return {"home_win": 0.33, "draw": 0.33, "away_win": 0.33}
        
        home_prob = (home_strength / total_strength) * 0.7 + 0.15  # Home advantage
        away_prob = (away_strength / total_strength) * 0.7 + 0.15
        draw_prob = 1.0 - home_prob - away_prob
        
        # Normalize to ensure sum = 1
        total = home_prob + draw_prob + away_prob
        
        return {
            "home_win": home_prob / total,
            "draw": draw_prob / total,
            "away_win": away_prob / total
        }
    
    def generate_betting_recommendation(self, probabilities: Dict[str, float], odds: Dict[str, float] = None) -> Dict[str, Any]:
        """Generate betting recommendation based on probabilities and odds"""
        if not odds:
            odds = {"home": 2.5, "draw": 3.0, "away": 2.8}  # Default odds
        
        recommendations = []
        
        # Calculate value bets
        for outcome, prob in probabilities.items():
            if outcome == "home_win" and "home" in odds:
                implied_prob = 1 / odds["home"]
                if prob > implied_prob * 1.1:  # 10% margin for value
                    recommendations.append({
                        "outcome": "1",
                        "confidence": prob,
                        "odds": odds["home"],
                        "value": (prob - implied_prob) / implied_prob,
                        "recommendation": "strong" if prob > implied_prob * 1.2 else "moderate"
                    })
            elif outcome == "draw" and "draw" in odds:
                implied_prob = 1 / odds["draw"]
                if prob > implied_prob * 1.1:
                    recommendations.append({
                        "outcome": "X",
                        "confidence": prob,
                        "odds": odds["draw"],
                        "value": (prob - implied_prob) / implied_prob,
                        "recommendation": "strong" if prob > implied_prob * 1.2 else "moderate"
                    })
            elif outcome == "away_win" and "away" in odds:
                implied_prob = 1 / odds["away"]
                if prob > implied_prob * 1.1:
                    recommendations.append({
                        "outcome": "2",
                        "confidence": prob,
                        "odds": odds["away"],
                        "value": (prob - implied_prob) / implied_prob,
                        "recommendation": "strong" if prob > implied_prob * 1.2 else "moderate"
                    })
        
        # Sort by value
        recommendations.sort(key=lambda x: x["value"], reverse=True)
        
        return {
            "recommendations": recommendations,
            "best_bet": recommendations[0] if recommendations else None,
            "probabilities": probabilities
        }
    
    async def _process_quiniela_match(self, match_data: dict, season: int) -> Optional[Dict[str, Any]]:
        """Process individual quiniela match data"""
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
            return None
        
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
        
        return {
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
    
    def _calculate_team_strength(self, stats: TeamStatistics, is_home: bool = False) -> float:
        """Calculate team strength metric based on statistics"""
        if not stats or stats.matches_played == 0:
            return 0.0
        
        # Basic strength calculation
        win_rate = stats.wins / stats.matches_played
        goal_diff = (stats.goals_for - stats.goals_against) / stats.matches_played
        points_per_game = stats.points / stats.matches_played
        
        # Home/away specific metrics
        if is_home:
            home_matches = max(stats.matches_played // 2, 1)
            home_win_rate = stats.home_wins / home_matches if home_matches > 0 else 0
            strength = (win_rate * 0.4 + home_win_rate * 0.3 + goal_diff * 0.2 + points_per_game * 0.1)
        else:
            away_matches = max(stats.matches_played // 2, 1)
            away_win_rate = stats.away_wins / away_matches if away_matches > 0 else 0
            strength = (win_rate * 0.4 + away_win_rate * 0.3 + goal_diff * 0.2 + points_per_game * 0.1)
        
        return max(0.0, strength)