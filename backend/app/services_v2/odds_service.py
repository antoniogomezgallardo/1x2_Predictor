from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..domain.entities.match import Match
from ..services.api_football_client import APIFootballClient


class OddsService:
    def __init__(self, db: Session):
        self.db = db
        self.api_client = APIFootballClient()
    
    async def update_odds_for_matches(self, match_ids: List[int]) -> Dict[str, Any]:
        """Update odds for specific matches"""
        results = {
            "updated": [],
            "failed": [],
            "total_processed": len(match_ids)
        }
        
        for match_id in match_ids:
            try:
                success = await self._update_single_match_odds(match_id)
                if success:
                    results["updated"].append(match_id)
                else:
                    results["failed"].append({"match_id": match_id, "reason": "Match not found"})
            except Exception as e:
                results["failed"].append({"match_id": match_id, "reason": str(e)})
        
        self.db.commit()
        return results
    
    async def update_odds_for_fixture(self, fixture_api_id: int) -> Optional[Match]:
        """Update odds for a match by its API fixture ID"""
        match = self.db.query(Match).filter_by(api_id=fixture_api_id).first()
        if not match:
            return None
        
        success = await self._update_single_match_odds(match.id)
        if success:
            self.db.commit()
            return match
        return None
    
    async def get_best_odds_comparison(self, match_id: int) -> Dict[str, Any]:
        """Get the best odds comparison for a match"""
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match:
            return {}
        
        # Get odds from multiple bookmakers if available
        odds_data = await self.api_client.get_odds(match.api_id)
        
        if not odds_data:
            return {
                "match_id": match_id,
                "current_odds": {
                    "home": match.home_odds,
                    "draw": match.draw_odds,
                    "away": match.away_odds
                },
                "bookmakers": []
            }
        
        bookmakers_odds = self._extract_all_bookmakers_odds(odds_data)
        
        return {
            "match_id": match_id,
            "fixture_id": match.api_id,
            "current_odds": {
                "home": match.home_odds,
                "draw": match.draw_odds,
                "away": match.away_odds
            },
            "bookmakers": bookmakers_odds,
            "best_odds": self._find_best_odds(bookmakers_odds)
        }
    
    def calculate_implied_probabilities(self, odds: Dict[str, float]) -> Dict[str, float]:
        """Calculate implied probabilities from odds"""
        probabilities = {}
        
        for outcome, odd in odds.items():
            if odd and odd > 0:
                probabilities[outcome] = 1 / odd
        
        # Calculate overround (bookmaker margin)
        total_prob = sum(probabilities.values())
        
        # Normalize probabilities (remove overround)
        if total_prob > 0:
            normalized_probs = {
                outcome: prob / total_prob 
                for outcome, prob in probabilities.items()
            }
            
            return {
                "raw_probabilities": probabilities,
                "normalized_probabilities": normalized_probs,
                "overround": total_prob - 1.0,
                "bookmaker_margin": ((total_prob - 1.0) / total_prob) * 100
            }
        
        return {"raw_probabilities": probabilities}
    
    def calculate_value_bets(self, predicted_probs: Dict[str, float], market_odds: Dict[str, float]) -> List[Dict[str, Any]]:
        """Calculate value betting opportunities"""
        value_bets = []
        
        for outcome in ["home", "draw", "away"]:
            if outcome in predicted_probs and outcome in market_odds:
                predicted_prob = predicted_probs[outcome]
                market_odd = market_odds[outcome]
                
                if market_odd > 0:
                    implied_prob = 1 / market_odd
                    
                    # Calculate expected value
                    expected_value = (predicted_prob * market_odd) - 1
                    
                    # Calculate Kelly criterion (optimal bet size)
                    kelly_fraction = (predicted_prob * market_odd - 1) / (market_odd - 1)
                    
                    if expected_value > 0:  # Positive expected value
                        value_bets.append({
                            "outcome": outcome,
                            "predicted_probability": predicted_prob,
                            "market_odds": market_odd,
                            "implied_probability": implied_prob,
                            "expected_value": expected_value,
                            "value_percentage": (expected_value / 1) * 100,
                            "kelly_fraction": max(0, kelly_fraction),
                            "confidence": "high" if expected_value > 0.1 else "moderate"
                        })
        
        # Sort by expected value
        value_bets.sort(key=lambda x: x["expected_value"], reverse=True)
        
        return value_bets
    
    def get_odds_movement_analysis(self, match_id: int) -> Dict[str, Any]:
        """Analyze odds movement (placeholder for future implementation)"""
        # This would require storing historical odds data
        # For now, return current odds structure
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match:
            return {}
        
        return {
            "match_id": match_id,
            "current_odds": {
                "home": match.home_odds,
                "draw": match.draw_odds,
                "away": match.away_odds
            },
            "movement_analysis": "Historical odds tracking not yet implemented",
            "recommendation": "Monitor odds closer to match time for better value"
        }
    
    async def _update_single_match_odds(self, match_id: int) -> bool:
        """Update odds for a single match"""
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match:
            return False
        
        odds_data = await self.api_client.get_odds(match.api_id)
        
        if not odds_data:
            return False
        
        # Extract and update odds
        odds = self._extract_match_winner_odds(odds_data)
        if odds:
            match.home_odds = odds.get("home")
            match.draw_odds = odds.get("draw")
            match.away_odds = odds.get("away")
            return True
        
        return False
    
    def _extract_match_winner_odds(self, odds_data: list) -> Optional[Dict[str, float]]:
        """Extract Match Winner odds from API response"""
        if not odds_data:
            return None
        
        bookmakers = odds_data[0].get("bookmakers", [])
        if not bookmakers:
            return None
        
        # Use first bookmaker's odds (usually the primary one)
        bets = bookmakers[0].get("bets", [])
        for bet in bets:
            if bet.get("name") == "Match Winner":
                values = bet.get("values", [])
                odds = {}
                
                for value in values:
                    if value.get("value") == "Home":
                        odds["home"] = float(value.get("odd", 0))
                    elif value.get("value") == "Draw":
                        odds["draw"] = float(value.get("odd", 0))
                    elif value.get("value") == "Away":
                        odds["away"] = float(value.get("odd", 0))
                
                return odds if odds else None
        
        return None
    
    def _extract_all_bookmakers_odds(self, odds_data: list) -> List[Dict[str, Any]]:
        """Extract odds from all available bookmakers"""
        all_odds = []
        
        if not odds_data:
            return all_odds
        
        bookmakers = odds_data[0].get("bookmakers", [])
        
        for bookmaker in bookmakers:
            bookmaker_name = bookmaker.get("name", "Unknown")
            bets = bookmaker.get("bets", [])
            
            for bet in bets:
                if bet.get("name") == "Match Winner":
                    values = bet.get("values", [])
                    odds = {"bookmaker": bookmaker_name}
                    
                    for value in values:
                        if value.get("value") == "Home":
                            odds["home"] = float(value.get("odd", 0))
                        elif value.get("value") == "Draw":
                            odds["draw"] = float(value.get("odd", 0))
                        elif value.get("value") == "Away":
                            odds["away"] = float(value.get("odd", 0))
                    
                    if "home" in odds and "draw" in odds and "away" in odds:
                        all_odds.append(odds)
        
        return all_odds
    
    def _find_best_odds(self, bookmakers_odds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find the best odds for each outcome across all bookmakers"""
        if not bookmakers_odds:
            return {}
        
        best_odds = {"home": 0, "draw": 0, "away": 0}
        best_bookmakers = {"home": "", "draw": "", "away": ""}
        
        for bookmaker_data in bookmakers_odds:
            bookmaker = bookmaker_data.get("bookmaker", "")
            
            for outcome in ["home", "draw", "away"]:
                if outcome in bookmaker_data:
                    current_odd = bookmaker_data[outcome]
                    if current_odd > best_odds[outcome]:
                        best_odds[outcome] = current_odd
                        best_bookmakers[outcome] = bookmaker
        
        return {
            "odds": best_odds,
            "bookmakers": best_bookmakers
        }