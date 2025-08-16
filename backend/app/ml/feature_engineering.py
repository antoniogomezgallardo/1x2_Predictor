import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from ..database.models import TeamStatistics, Match


class FeatureEngineer:
    def __init__(self):
        self.feature_names = []
    
    def extract_features(self, match_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for a single match"""
        features = {}
        
        # Basic team statistics features
        home_stats = match_data.get("home_stats")
        away_stats = match_data.get("away_stats")
        
        if home_stats and away_stats:
            features.update(self._team_performance_features(home_stats, away_stats))
            features.update(self._goal_statistics_features(home_stats, away_stats))
            features.update(self._home_away_advantage_features(home_stats, away_stats))
        
        # Head-to-head features
        h2h_data = match_data.get("h2h_data", [])
        features.update(self._head_to_head_features(h2h_data, match_data))
        
        # Form features
        home_form = match_data.get("home_form", [])
        away_form = match_data.get("away_form", [])
        features.update(self._form_features(home_form, away_form))
        
        # League position features
        if home_stats and away_stats:
            features.update(self._position_features(home_stats, away_stats))
        
        # Store feature names for later use
        self.feature_names = list(features.keys())
        
        return features
    
    def _team_performance_features(self, home_stats: TeamStatistics, 
                                 away_stats: TeamStatistics) -> Dict[str, float]:
        """Extract team performance-based features"""
        features = {}
        
        # Win percentages
        home_matches = home_stats.matches_played or 1
        away_matches = away_stats.matches_played or 1
        
        features["home_win_pct"] = home_stats.wins / home_matches
        features["away_win_pct"] = away_stats.wins / away_matches
        features["home_draw_pct"] = home_stats.draws / home_matches
        features["away_draw_pct"] = away_stats.draws / away_matches
        
        # Points per game
        features["home_ppg"] = home_stats.points / home_matches
        features["away_ppg"] = away_stats.points / away_matches
        features["ppg_difference"] = features["home_ppg"] - features["away_ppg"]
        
        # Performance differential
        features["win_pct_diff"] = features["home_win_pct"] - features["away_win_pct"]
        
        return features
    
    def _goal_statistics_features(self, home_stats: TeamStatistics, 
                                away_stats: TeamStatistics) -> Dict[str, float]:
        """Extract goal-related features"""
        features = {}
        
        home_matches = home_stats.matches_played or 1
        away_matches = away_stats.matches_played or 1
        
        # Goals per game
        features["home_goals_per_game"] = home_stats.goals_for / home_matches
        features["away_goals_per_game"] = away_stats.goals_for / away_matches
        features["home_goals_against_per_game"] = home_stats.goals_against / home_matches
        features["away_goals_against_per_game"] = away_stats.goals_against / away_matches
        
        # Goal difference
        features["home_goal_diff"] = home_stats.goals_for - home_stats.goals_against
        features["away_goal_diff"] = away_stats.goals_for - away_stats.goals_against
        features["goal_diff_difference"] = features["home_goal_diff"] - features["away_goal_diff"]
        
        # Attack vs Defense matchup
        features["attack_vs_defense"] = features["home_goals_per_game"] - features["away_goals_against_per_game"]
        features["defense_vs_attack"] = features["away_goals_per_game"] - features["home_goals_against_per_game"]
        
        return features
    
    def _home_away_advantage_features(self, home_stats: TeamStatistics, 
                                    away_stats: TeamStatistics) -> Dict[str, float]:
        """Extract home/away specific performance features"""
        features = {}
        
        # Home team home performance
        home_home_matches = (home_stats.home_wins + home_stats.home_draws + home_stats.home_losses) or 1
        features["home_team_home_win_pct"] = home_stats.home_wins / home_home_matches
        features["home_team_home_draw_pct"] = home_stats.home_draws / home_home_matches
        
        # Away team away performance
        away_away_matches = (away_stats.away_wins + away_stats.away_draws + away_stats.away_losses) or 1
        features["away_team_away_win_pct"] = away_stats.away_wins / away_away_matches
        features["away_team_away_draw_pct"] = away_stats.away_draws / away_away_matches
        
        # Home advantage
        features["home_advantage"] = features["home_team_home_win_pct"] - features["away_team_away_win_pct"]
        
        return features
    
    def _head_to_head_features(self, h2h_data: List[Dict], 
                             match_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract head-to-head historical features"""
        features = {
            "h2h_home_wins": 0.0,
            "h2h_draws": 0.0,
            "h2h_away_wins": 0.0,
            "h2h_home_goals_avg": 0.0,
            "h2h_away_goals_avg": 0.0,
            "h2h_total_matches": 0.0
        }
        
        if not h2h_data:
            return features
        
        home_team_id = match_data.get("home_team", {}).get("api_id")
        away_team_id = match_data.get("away_team", {}).get("api_id")
        
        home_wins = 0
        draws = 0
        away_wins = 0
        home_goals_total = 0
        away_goals_total = 0
        total_matches = len(h2h_data)
        
        for match in h2h_data:
            teams = match.get("teams", {})
            goals = match.get("goals", {})
            
            if not goals.get("home") or not goals.get("away"):
                continue
            
            # Determine which team was home in this historical match
            if teams.get("home", {}).get("id") == home_team_id:
                # Current home team was home in historical match
                home_goals_total += goals["home"]
                away_goals_total += goals["away"]
                
                if goals["home"] > goals["away"]:
                    home_wins += 1
                elif goals["home"] < goals["away"]:
                    away_wins += 1
                else:
                    draws += 1
            else:
                # Current home team was away in historical match
                home_goals_total += goals["away"]
                away_goals_total += goals["home"]
                
                if goals["away"] > goals["home"]:
                    home_wins += 1
                elif goals["away"] < goals["home"]:
                    away_wins += 1
                else:
                    draws += 1
        
        if total_matches > 0:
            features["h2h_home_wins"] = home_wins / total_matches
            features["h2h_draws"] = draws / total_matches
            features["h2h_away_wins"] = away_wins / total_matches
            features["h2h_home_goals_avg"] = home_goals_total / total_matches
            features["h2h_away_goals_avg"] = away_goals_total / total_matches
            features["h2h_total_matches"] = total_matches
        
        return features
    
    def _form_features(self, home_form: List[Dict], away_form: List[Dict]) -> Dict[str, float]:
        """Extract recent form features"""
        features = {
            "home_form_points": 0.0,
            "away_form_points": 0.0,
            "home_form_goals_for": 0.0,
            "away_form_goals_for": 0.0,
            "home_form_goals_against": 0.0,
            "away_form_goals_against": 0.0,
            "form_difference": 0.0
        }
        
        # Analyze last 5 matches for home team
        home_points = 0
        home_goals_for = 0
        home_goals_against = 0
        
        for match in home_form[-5:]:  # Last 5 matches
            goals = match.get("goals", {})
            teams = match.get("teams", {})
            
            if not goals.get("home") or not goals.get("away"):
                continue
            
            # Determine if team was home or away
            home_team_api_id = teams.get("home", {}).get("id")
            
            # This logic needs the actual team API ID to work correctly
            # For now, we'll use a simplified approach
            if goals["home"] > goals["away"]:
                home_points += 3
            elif goals["home"] == goals["away"]:
                home_points += 1
            
            home_goals_for += goals.get("home", 0)
            home_goals_against += goals.get("away", 0)
        
        # Similar for away team
        away_points = 0
        away_goals_for = 0
        away_goals_against = 0
        
        for match in away_form[-5:]:
            goals = match.get("goals", {})
            
            if not goals.get("home") or not goals.get("away"):
                continue
            
            if goals["away"] > goals["home"]:
                away_points += 3
            elif goals["away"] == goals["home"]:
                away_points += 1
            
            away_goals_for += goals.get("away", 0)
            away_goals_against += goals.get("home", 0)
        
        features["home_form_points"] = home_points
        features["away_form_points"] = away_points
        features["home_form_goals_for"] = home_goals_for
        features["away_form_goals_for"] = away_goals_for
        features["home_form_goals_against"] = home_goals_against
        features["away_form_goals_against"] = away_goals_against
        features["form_difference"] = home_points - away_points
        
        return features
    
    def _position_features(self, home_stats: TeamStatistics, 
                          away_stats: TeamStatistics) -> Dict[str, float]:
        """Extract league position-based features"""
        features = {}
        
        # Position difference (lower is better)
        home_pos = home_stats.position or 20
        away_pos = away_stats.position or 20
        
        features["home_position"] = home_pos
        features["away_position"] = away_pos
        features["position_difference"] = away_pos - home_pos  # Positive if home team is higher
        
        # Position categories
        features["home_top_half"] = 1.0 if home_pos <= 10 else 0.0
        features["away_top_half"] = 1.0 if away_pos <= 10 else 0.0
        features["home_top_six"] = 1.0 if home_pos <= 6 else 0.0
        features["away_top_six"] = 1.0 if away_pos <= 6 else 0.0
        features["home_relegation_zone"] = 1.0 if home_pos >= 18 else 0.0
        features["away_relegation_zone"] = 1.0 if away_pos >= 18 else 0.0
        
        return features
    
    def create_feature_matrix(self, matches_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
        """Create feature matrix for multiple matches"""
        features_list = []
        
        for match_data in matches_data:
            features = self.extract_features(match_data)
            features_list.append(features)
        
        if not features_list:
            return np.array([]), []
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(features_list)
        
        # Fill any missing values with 0
        df = df.fillna(0)
        
        return df.values, df.columns.tolist()
    
    def get_feature_importance_names(self) -> List[str]:
        """Get list of feature names for importance analysis"""
        return self.feature_names