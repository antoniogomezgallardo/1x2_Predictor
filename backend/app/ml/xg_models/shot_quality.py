"""
Expected Goals (xG) Model - Advanced Shot Quality Assessment
Implements contextual xG calculation with situational adjustments.

This model goes beyond basic distance/angle calculations to include:
- Defensive pressure assessment
- Game state context (score, minute, pressure situations)  
- Player quality adjustments
- Shot type and body part optimization
- Historical conversion rates by situation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score
import joblib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExpectedGoalsModel:
    """
    Advanced Expected Goals model with contextual adjustments.
    
    Features:
    - Base xG calculation using shot location, angle, body part
    - Situational multipliers (game state, pressure, minute)
    - Player quality adjustments based on historical performance
    - Defensive pressure assessment
    - Calibrated probability outputs for accurate confidence intervals
    """
    
    def __init__(self):
        self.base_model = None
        self.calibrator = None
        self.is_trained = False
        
        # Core features for xG calculation
        self.base_features = [
            'shot_distance',          # Distance to goal in meters
            'shot_angle',             # Angle of shot in degrees
            'is_header',              # Boolean: shot with head
            'is_left_foot',           # Boolean: shot with left foot
            'is_right_foot',          # Boolean: shot with right foot
            'is_from_corner',         # Boolean: shot from corner kick
            'is_from_free_kick',      # Boolean: shot from free kick
            'is_from_throw_in',       # Boolean: shot from throw-in
            'is_counter_attack',      # Boolean: shot from counter attack
            'minute',                 # Minute of the match (1-90+)
            'defensive_players_nearby', # Number of defenders within 5m
            'goalkeeper_position',    # GK distance from goal line
        ]
        
        # Situational adjustment factors
        self.situation_multipliers = {
            'pressure_situations': {
                'low_pressure': 1.15,     # Open play, no immediate pressure
                'medium_pressure': 1.0,   # Normal defensive setup
                'high_pressure': 0.82,    # Multiple defenders, rushed shot
                'very_high_pressure': 0.71 # Crowded box, deflected shot
            },
            'game_context': {
                'early_game': 1.05,       # Minutes 1-30, fresh legs
                'mid_game': 1.0,          # Minutes 31-70, normal
                'late_game': 0.95,        # Minutes 71-90, tired legs
                'extra_time': 0.88        # 90+ minutes, fatigue factor
            },
            'score_situation': {
                'winning': 0.92,          # Leading team, less desperate
                'drawing': 1.0,           # Even game, normal intensity
                'losing_1': 1.08,         # 1 goal behind, more urgent
                'losing_2plus': 1.15      # 2+ goals behind, desperate
            },
            'match_importance': {
                'league': 1.0,            # Regular league match
                'cup': 1.08,              # Cup competition
                'derby': 1.12,            # Local rival match
                'relegation': 1.18,       # Relegation battle
                'title': 1.15             # Title-deciding match
            }
        }
        
        # Player quality adjustments (to be populated from database)
        self.player_quality_cache = {}
        
    def _calculate_base_features(self, shot_data: Dict) -> np.ndarray:
        """
        Calculate base features from shot data.
        
        Args:
            shot_data: Dictionary containing shot information
            
        Returns:
            Feature vector for base xG model
        """
        features = []
        
        # Distance to goal (Euclidean distance)
        x, y = shot_data.get('x', 0), shot_data.get('y', 0)
        goal_x, goal_y = 100, 50  # Assuming 100x100 pitch, goal at (100, 50)
        distance = np.sqrt((goal_x - x)**2 + (goal_y - y)**2)
        features.append(distance)
        
        # Angle to goal (more acute = more difficult)
        goal_width = 7.32  # Standard goal width in meters
        angle_rad = np.arctan(goal_width / (2 * distance))
        angle_deg = np.degrees(angle_rad)
        features.append(angle_deg)
        
        # Body part indicators
        body_part = shot_data.get('body_part', 'right_foot').lower()
        features.extend([
            1 if body_part == 'head' else 0,
            1 if body_part == 'left_foot' else 0,
            1 if body_part == 'right_foot' else 0,
        ])
        
        # Situation type indicators  
        play_pattern = shot_data.get('play_pattern', 'regular_play').lower()
        features.extend([
            1 if 'corner' in play_pattern else 0,
            1 if 'free_kick' in play_pattern else 0,
            1 if 'throw' in play_pattern else 0,
            1 if 'counter' in play_pattern else 0,
        ])
        
        # Temporal feature
        minute = shot_data.get('minute', 45)
        features.append(minute)
        
        # Defensive pressure
        defenders_nearby = shot_data.get('defenders_nearby', 2)
        features.append(defenders_nearby)
        
        # Goalkeeper position
        gk_distance = shot_data.get('goalkeeper_distance', 6.0)
        features.append(gk_distance)
        
        return np.array(features).reshape(1, -1)
    
    def _get_situational_multiplier(self, shot_data: Dict, context: Dict) -> float:
        """
        Calculate situational multiplier based on game context.
        
        Args:
            shot_data: Shot-specific information
            context: Match context (score, minute, importance, etc.)
            
        Returns:
            Multiplier to adjust base xG (typically 0.7-1.2)
        """
        multiplier = 1.0
        
        # Pressure situation adjustment
        pressure_level = self._assess_pressure_level(shot_data)
        multiplier *= self.situation_multipliers['pressure_situations'][pressure_level]
        
        # Game time adjustment
        minute = shot_data.get('minute', 45)
        if minute <= 30:
            time_context = 'early_game'
        elif minute <= 70:
            time_context = 'mid_game'
        elif minute <= 90:
            time_context = 'late_game'
        else:
            time_context = 'extra_time'
            
        multiplier *= self.situation_multipliers['game_context'][time_context]
        
        # Score context adjustment
        score_diff = context.get('score_difference', 0)  # Positive if team is winning
        if score_diff > 0:
            score_context = 'winning'
        elif score_diff == 0:
            score_context = 'drawing'
        elif score_diff == -1:
            score_context = 'losing_1'
        else:
            score_context = 'losing_2plus'
            
        multiplier *= self.situation_multipliers['score_situation'][score_context]
        
        # Match importance adjustment
        importance = context.get('match_importance', 'league')
        multiplier *= self.situation_multipliers['match_importance'][importance]
        
        return multiplier
    
    def _assess_pressure_level(self, shot_data: Dict) -> str:
        """
        Assess defensive pressure level based on shot circumstances.
        
        Args:
            shot_data: Shot information including defensive setup
            
        Returns:
            Pressure level: 'low_pressure', 'medium_pressure', 'high_pressure', 'very_high_pressure'
        """
        defenders_nearby = shot_data.get('defenders_nearby', 2)
        time_to_shoot = shot_data.get('time_to_shoot', 1.5)  # Seconds
        is_rushed = shot_data.get('is_rushed_shot', False)
        
        if defenders_nearby <= 1 and time_to_shoot > 2.0 and not is_rushed:
            return 'low_pressure'
        elif defenders_nearby <= 2 and time_to_shoot > 1.0 and not is_rushed:
            return 'medium_pressure'
        elif defenders_nearby <= 3 or time_to_shoot < 1.0 or is_rushed:
            return 'high_pressure'
        else:
            return 'very_high_pressure'
    
    def _get_player_quality_adjustment(self, player_id: str) -> float:
        """
        Get player-specific shooting quality adjustment.
        
        Args:
            player_id: Unique player identifier
            
        Returns:
            Quality multiplier (0.8-1.3 range for most players)
        """
        if player_id in self.player_quality_cache:
            return self.player_quality_cache[player_id]
        
        # TODO: Implement database lookup for player historical conversion rates
        # For now, return neutral adjustment
        base_adjustment = 1.0
        
        # Cache the result
        self.player_quality_cache[player_id] = base_adjustment
        return base_adjustment
    
    def train(self, training_data: pd.DataFrame, target_column: str = 'is_goal') -> Dict:
        """
        Train the Expected Goals model on historical shot data.
        
        Args:
            training_data: DataFrame with shot data and outcomes
            target_column: Column name containing goal/no-goal binary target
            
        Returns:
            Training metrics and model information
        """
        logger.info(f"Training xG model on {len(training_data)} shots")
        
        # Prepare features
        features = []
        for idx, row in training_data.iterrows():
            shot_features = self._calculate_base_features(row.to_dict())
            features.append(shot_features.flatten())
        
        X = np.array(features)
        y = training_data[target_column].values
        
        # Train ensemble model (Random Forest + Gradient Boosting)
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42
        )
        
        gb_model = GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=6,
            min_samples_split=20,
            random_state=42
        )
        
        # Fit models
        rf_model.fit(X, y)
        gb_model.fit(X, y)
        
        # Create ensemble predictions for calibration
        rf_pred = rf_model.predict(X)
        gb_pred = gb_model.predict(X)
        ensemble_pred = (rf_pred + gb_pred) / 2
        
        # Store models
        self.rf_model = rf_model
        self.gb_model = gb_model
        
        # Calibrate probabilities
        self.calibrator = CalibratedClassifierCV(
            base_estimator=None,
            method='isotonic',
            cv=5
        )
        
        # Create calibration data
        calibration_X = ensemble_pred.reshape(-1, 1)
        self.calibrator.fit(calibration_X, y)
        
        # Calculate training metrics
        rf_score = cross_val_score(rf_model, X, y, cv=5, scoring='neg_log_loss').mean()
        gb_score = cross_val_score(gb_model, X, y, cv=5, scoring='neg_log_loss').mean()
        
        self.is_trained = True
        
        # Feature importance analysis
        feature_importance = {
            'random_forest': dict(zip(self.base_features, rf_model.feature_importances_)),
            'gradient_boosting': dict(zip(self.base_features, gb_model.feature_importances_))
        }
        
        training_metrics = {
            'training_samples': len(training_data),
            'mean_xg': ensemble_pred.mean(),
            'actual_conversion_rate': y.mean(),
            'rf_log_loss': -rf_score,
            'gb_log_loss': -gb_score,
            'feature_importance': feature_importance,
            'training_date': datetime.now().isoformat()
        }
        
        logger.info(f"xG model training completed. Mean xG: {training_metrics['mean_xg']:.3f}, "
                   f"Actual conversion: {training_metrics['actual_conversion_rate']:.3f}")
        
        return training_metrics
    
    def predict_xg(self, shot_data: Dict, context: Dict = None) -> Dict:
        """
        Predict Expected Goals for a single shot.
        
        Args:
            shot_data: Shot information (location, body part, etc.)
            context: Match context (optional, for situational adjustments)
            
        Returns:
            Dictionary with xG value, confidence intervals, and breakdown
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Calculate base features
        base_features = self._calculate_base_features(shot_data)
        
        # Get base model predictions
        rf_pred = self.rf_model.predict(base_features)[0]
        gb_pred = self.gb_model.predict(base_features)[0]
        ensemble_pred = (rf_pred + gb_pred) / 2
        
        # Calibrate probability
        calibrated_prob = self.calibrator.predict_proba(
            ensemble_pred.reshape(-1, 1)
        )[0][1]  # Probability of goal
        
        # Apply situational adjustments if context provided
        situational_multiplier = 1.0
        if context:
            situational_multiplier = self._get_situational_multiplier(shot_data, context)
        
        # Apply player quality adjustment
        player_id = shot_data.get('player_id')
        player_adjustment = 1.0
        if player_id:
            player_adjustment = self._get_player_quality_adjustment(player_id)
        
        # Final xG calculation
        final_xg = calibrated_prob * situational_multiplier * player_adjustment
        
        # Ensure xG stays within reasonable bounds
        final_xg = np.clip(final_xg, 0.01, 0.99)
        
        return {
            'xg_value': final_xg,
            'base_xg': calibrated_prob,
            'situational_multiplier': situational_multiplier,
            'player_adjustment': player_adjustment,
            'confidence_interval': {
                'lower': max(0.01, final_xg - 0.1),
                'upper': min(0.99, final_xg + 0.1)
            },
            'contributing_factors': {
                'distance': shot_data.get('shot_distance', 0),
                'angle': shot_data.get('shot_angle', 0),
                'body_part': shot_data.get('body_part', 'unknown'),
                'pressure_level': self._assess_pressure_level(shot_data),
                'minute': shot_data.get('minute', 0)
            }
        }
    
    def predict_match_xg(self, match_shots: List[Dict], context: Dict = None) -> Dict:
        """
        Calculate Expected Goals for all shots in a match.
        
        Args:
            match_shots: List of shot dictionaries for the match
            context: Match context information
            
        Returns:
            Comprehensive xG analysis for the match
        """
        if not match_shots:
            return {'total_xg': 0.0, 'shot_breakdown': []}
        
        shot_breakdown = []
        total_xg = 0.0
        
        for shot in match_shots:
            xg_result = self.predict_xg(shot, context)
            shot_breakdown.append({
                'shot_id': shot.get('id', 'unknown'),
                'minute': shot.get('minute', 0),
                'player': shot.get('player_name', 'unknown'),
                'xg': xg_result['xg_value'],
                'outcome': shot.get('is_goal', False)
            })
            total_xg += xg_result['xg_value']
        
        return {
            'total_xg': total_xg,
            'shot_count': len(match_shots),
            'average_shot_quality': total_xg / len(match_shots) if match_shots else 0,
            'shot_breakdown': shot_breakdown,
            'performance_vs_xg': {
                'actual_goals': sum(shot.get('is_goal', False) for shot in match_shots),
                'expected_goals': total_xg,
                'over_performance': sum(shot.get('is_goal', False) for shot in match_shots) - total_xg
            }
        }
    
    def save_model(self, filepath: str) -> None:
        """Save trained model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'rf_model': self.rf_model,
            'gb_model': self.gb_model,
            'calibrator': self.calibrator,
            'base_features': self.base_features,
            'situation_multipliers': self.situation_multipliers,
            'is_trained': self.is_trained,
            'save_date': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"xG model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """Load trained model from disk."""
        model_data = joblib.load(filepath)
        
        self.rf_model = model_data['rf_model']
        self.gb_model = model_data['gb_model']
        self.calibrator = model_data['calibrator']
        self.base_features = model_data['base_features']
        self.situation_multipliers = model_data['situation_multipliers']
        self.is_trained = model_data['is_trained']
        
        logger.info(f"xG model loaded from {filepath}")


# Utility functions for data preparation
def prepare_shot_data_from_api(api_match_data: Dict) -> List[Dict]:
    """
    Convert API-Football match data to xG model format.
    
    Args:
        api_match_data: Raw match data from API-Football
        
    Returns:
        List of shot dictionaries in xG model format
    """
    shots = []
    
    # Extract shots from API data
    match_events = api_match_data.get('events', [])
    
    for event in match_events:
        if event.get('type') == 'shot':
            shot_data = {
                'id': event.get('id'),
                'minute': event.get('minute', 0),
                'player_id': event.get('player_id'),
                'player_name': event.get('player_name', 'unknown'),
                'team_id': event.get('team_id'),
                'x': event.get('x', 50),  # Field coordinates
                'y': event.get('y', 50),
                'body_part': event.get('detail', 'right_foot').lower(),
                'is_goal': event.get('type') == 'goal',
                'play_pattern': 'regular_play',  # Default, could be enhanced
                'defenders_nearby': 2,  # Default, would need tracking data
                'goalkeeper_distance': 6.0,  # Default
                'is_rushed_shot': False  # Default
            }
            shots.append(shot_data)
    
    return shots


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create model instance
    xg_model = ExpectedGoalsModel()
    
    # Example shot data
    example_shot = {
        'x': 85,  # 15 meters from goal
        'y': 50,  # Center of pitch
        'body_part': 'right_foot',
        'minute': 65,
        'defenders_nearby': 1,
        'goalkeeper_distance': 6.0,
        'player_id': 'example_player'
    }
    
    example_context = {
        'score_difference': -1,  # Team is losing by 1
        'match_importance': 'derby'
    }
    
    print("Expected Goals Model - Example Usage")
    print("Note: Model needs training data before predictions can be made")
    print(f"Example shot setup: {example_shot}")
    print(f"Example context: {example_context}")