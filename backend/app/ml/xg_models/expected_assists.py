"""
Expected Assists (xA) Model - Pass Quality and Chance Creation Assessment
Evaluates the quality and likelihood of assists based on pass characteristics.

Features:
- Pass location, angle, and distance analysis
- Receiver position quality assessment  
- Defensive pressure on passer and receiver
- Pass type classification (through ball, cross, cutback, etc.)
- Temporal context (game state, urgency)
- Player quality adjustments for both passer and receiver
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


class ExpectedAssistsModel:
    """
    Advanced Expected Assists model evaluating chance creation quality.
    
    Analyzes passes that lead to shots and determines the probability
    that a similar pass will result in an assist (goal from the shot).
    """
    
    def __init__(self):
        self.base_model = None
        self.calibrator = None
        self.is_trained = False
        
        # Core features for xA calculation
        self.base_features = [
            'pass_distance',              # Distance of the pass in meters
            'pass_angle_to_goal',         # Angle from passer to goal
            'receiver_distance_to_goal',  # Distance from receiver to goal
            'receiver_angle_to_goal',     # Angle from receiver to goal
            'pass_speed',                 # Speed of the pass (if available)
            'is_through_ball',            # Boolean: through ball type
            'is_cross',                   # Boolean: cross from wide area
            'is_cutback',                 # Boolean: cutback pass
            'is_key_pass',                # Boolean: key pass classification
            'defenders_between',          # Defenders between passer and receiver
            'time_to_next_touch',         # Time receiver has before pressure
            'pass_accuracy_pressure',     # Difficulty of pass under pressure
            'receiver_space',             # Space available to receiver (m²)
            'pass_minute',                # When in match pass occurred
        ]
        
        # Pass type multipliers for assist probability
        self.pass_type_multipliers = {
            'through_ball': 1.35,         # High-value penetrating passes
            'cross': 1.15,                # Crosses from wide positions  
            'cutback': 1.28,              # Dangerous cutback passes
            'key_pass': 1.20,             # General key passes
            'regular_pass': 1.0,          # Standard passes
            'back_pass': 0.45,            # Backwards/safe passes
            'switch_play': 0.85           # Long switches (lower immediate threat)
        }
        
        # Receiver position quality zones
        self.position_quality_zones = {
            'central_box': 2.1,           # Central penalty area
            'left_box': 1.8,              # Left side penalty area
            'right_box': 1.8,             # Right side penalty area
            'edge_box': 1.3,              # Edge of penalty area
            'central_attacking': 1.1,     # Central attacking third
            'wide_attacking': 0.9,        # Wide attacking positions
            'midfield': 0.6,              # Midfield areas
            'defensive': 0.2              # Defensive areas
        }
        
        # Game context adjustments
        self.context_multipliers = {
            'score_context': {
                'winning': 0.90,          # Less urgency when leading
                'drawing': 1.0,           # Normal intensity
                'losing_1': 1.12,         # More direct play when behind
                'losing_2plus': 1.25      # Desperate attacking
            },
            'time_context': {
                'early': 1.02,            # Fresh, patient play
                'middle': 1.0,            # Standard play
                'late': 1.08,             # Increased urgency
                'very_late': 1.18         # Final minutes desperation
            }
        }
    
    def _calculate_base_features(self, pass_data: Dict) -> np.ndarray:
        """
        Calculate base features from pass data.
        
        Args:
            pass_data: Dictionary containing pass information
            
        Returns:
            Feature vector for base xA model
        """
        features = []
        
        # Pass geometry calculations
        pass_start_x = pass_data.get('start_x', 50)
        pass_start_y = pass_data.get('start_y', 50)
        pass_end_x = pass_data.get('end_x', 70)
        pass_end_y = pass_data.get('end_y', 50)
        
        # Pass distance
        pass_distance = np.sqrt((pass_end_x - pass_start_x)**2 + (pass_end_y - pass_start_y)**2)
        features.append(pass_distance)
        
        # Angle from passer to goal
        goal_x, goal_y = 100, 50  # Goal position
        passer_goal_angle = np.degrees(np.arctan2(goal_y - pass_start_y, goal_x - pass_start_x))
        features.append(abs(passer_goal_angle))
        
        # Distance from receiver to goal
        receiver_goal_distance = np.sqrt((goal_x - pass_end_x)**2 + (goal_y - pass_end_y)**2)
        features.append(receiver_goal_distance)
        
        # Angle from receiver to goal
        receiver_goal_angle = np.degrees(np.arctan2(goal_y - pass_end_y, goal_x - pass_end_x))
        features.append(abs(receiver_goal_angle))
        
        # Pass speed (estimated from distance and time if available)
        pass_duration = pass_data.get('pass_duration', 1.0)  # Default 1 second
        pass_speed = pass_distance / pass_duration
        features.append(pass_speed)
        
        # Pass type indicators
        pass_type = pass_data.get('pass_type', 'regular_pass').lower()
        features.extend([
            1 if 'through' in pass_type else 0,
            1 if 'cross' in pass_type else 0,
            1 if 'cutback' in pass_type else 0,
            1 if 'key' in pass_type else 0,
        ])
        
        # Defensive pressure indicators
        defenders_between = pass_data.get('defenders_between', 1)
        features.append(defenders_between)
        
        # Time pressure on receiver
        time_to_pressure = pass_data.get('time_to_pressure', 2.0)  # Seconds
        features.append(time_to_pressure)
        
        # Pass difficulty under pressure
        passer_pressure = pass_data.get('passer_under_pressure', False)
        pass_accuracy_pressure = 0.8 if passer_pressure else 1.0
        features.append(pass_accuracy_pressure)
        
        # Receiver space (estimated from defensive density)
        receiver_space = self._estimate_receiver_space(pass_data)
        features.append(receiver_space)
        
        # Temporal feature
        minute = pass_data.get('minute', 45)
        features.append(minute)
        
        return np.array(features).reshape(1, -1)
    
    def _estimate_receiver_space(self, pass_data: Dict) -> float:
        """
        Estimate space available to receiver based on defensive setup.
        
        Args:
            pass_data: Pass information including defensive positions
            
        Returns:
            Estimated space in square meters
        """
        base_space = 25.0  # Default space estimate
        
        # Reduce space based on nearby defenders
        nearby_defenders = pass_data.get('defenders_near_receiver', 1)
        space_reduction = nearby_defenders * 3.5  # Each defender reduces space
        
        # Account for position on field (more crowded in central areas)
        receiver_x = pass_data.get('end_x', 70)
        if 40 <= receiver_x <= 60:  # Central areas
            space_reduction += 2.0
        
        available_space = max(5.0, base_space - space_reduction)
        return available_space
    
    def _get_pass_type_multiplier(self, pass_data: Dict) -> float:
        """
        Get multiplier based on pass type quality.
        
        Args:
            pass_data: Pass information
            
        Returns:
            Multiplier for pass type (typically 0.5-2.0)
        """
        pass_type = pass_data.get('pass_type', 'regular_pass').lower()
        
        # Determine pass type category
        if 'through' in pass_type:
            return self.pass_type_multipliers['through_ball']
        elif 'cross' in pass_type:
            return self.pass_type_multipliers['cross']
        elif 'cutback' in pass_type:
            return self.pass_type_multipliers['cutback']
        elif 'key' in pass_type:
            return self.pass_type_multipliers['key_pass']
        elif 'back' in pass_type:
            return self.pass_type_multipliers['back_pass']
        elif 'switch' in pass_type:
            return self.pass_type_multipliers['switch_play']
        else:
            return self.pass_type_multipliers['regular_pass']
    
    def _get_position_quality_multiplier(self, pass_data: Dict) -> float:
        """
        Get multiplier based on receiver position quality.
        
        Args:
            pass_data: Pass information including receiver position
            
        Returns:
            Position quality multiplier
        """
        receiver_x = pass_data.get('end_x', 70)
        receiver_y = pass_data.get('end_y', 50)
        
        # Define penalty area boundaries (approximate)
        penalty_left, penalty_right = 83, 100
        penalty_top, penalty_bottom = 37, 63
        
        # Determine position zone
        if penalty_left <= receiver_x <= penalty_right:
            if penalty_top <= receiver_y <= penalty_bottom:
                # Inside penalty area
                if 44 <= receiver_y <= 56:  # Central area
                    return self.position_quality_zones['central_box']
                elif receiver_y < 44:
                    return self.position_quality_zones['left_box']
                else:
                    return self.position_quality_zones['right_box']
            else:
                return self.position_quality_zones['edge_box']
        elif receiver_x >= 65:  # Attacking third
            if 30 <= receiver_y <= 70:  # Central area
                return self.position_quality_zones['central_attacking']
            else:
                return self.position_quality_zones['wide_attacking']
        elif receiver_x >= 35:  # Midfield
            return self.position_quality_zones['midfield']
        else:  # Defensive areas
            return self.position_quality_zones['defensive']
    
    def _get_context_multiplier(self, pass_data: Dict, match_context: Dict) -> float:
        """
        Calculate context-based multipliers for assist probability.
        
        Args:
            pass_data: Pass information
            match_context: Match state information
            
        Returns:
            Context multiplier
        """
        multiplier = 1.0
        
        # Score context
        score_diff = match_context.get('score_difference', 0)
        if score_diff > 0:
            score_context = 'winning'
        elif score_diff == 0:
            score_context = 'drawing'
        elif score_diff == -1:
            score_context = 'losing_1'
        else:
            score_context = 'losing_2plus'
            
        multiplier *= self.context_multipliers['score_context'][score_context]
        
        # Time context
        minute = pass_data.get('minute', 45)
        if minute < 30:
            time_context = 'early'
        elif minute < 70:
            time_context = 'middle'
        elif minute < 85:
            time_context = 'late'
        else:
            time_context = 'very_late'
            
        multiplier *= self.context_multipliers['time_context'][time_context]
        
        return multiplier
    
    def train(self, training_data: pd.DataFrame, target_column: str = 'resulted_in_assist') -> Dict:
        """
        Train the Expected Assists model on historical pass data.
        
        Args:
            training_data: DataFrame with pass data and assist outcomes
            target_column: Column indicating if pass resulted in assist
            
        Returns:
            Training metrics and model information
        """
        logger.info(f"Training xA model on {len(training_data)} passes")
        
        # Prepare features
        features = []
        for idx, row in training_data.iterrows():
            pass_features = self._calculate_base_features(row.to_dict())
            features.append(pass_features.flatten())
        
        X = np.array(features)
        y = training_data[target_column].values
        
        # Train ensemble model
        rf_model = RandomForestRegressor(
            n_estimators=250,
            max_depth=12,
            min_samples_split=15,
            min_samples_leaf=8,
            random_state=42
        )
        
        gb_model = GradientBoostingRegressor(
            n_estimators=180,
            learning_rate=0.08,
            max_depth=8,
            min_samples_split=15,
            random_state=42
        )
        
        # Fit models
        rf_model.fit(X, y)
        gb_model.fit(X, y)
        
        # Store models
        self.rf_model = rf_model
        self.gb_model = gb_model
        
        # Create calibration
        rf_pred = rf_model.predict(X)
        gb_pred = gb_model.predict(X)
        ensemble_pred = (rf_pred + gb_pred) / 2
        
        self.calibrator = CalibratedClassifierCV(method='isotonic', cv=5)
        calibration_X = ensemble_pred.reshape(-1, 1)
        self.calibrator.fit(calibration_X, y)
        
        self.is_trained = True
        
        # Calculate metrics
        rf_score = cross_val_score(rf_model, X, y, cv=5, scoring='neg_mean_squared_error').mean()
        gb_score = cross_val_score(gb_model, X, y, cv=5, scoring='neg_mean_squared_error').mean()
        
        training_metrics = {
            'training_samples': len(training_data),
            'mean_xa': ensemble_pred.mean(),
            'actual_assist_rate': y.mean(),
            'rf_mse': -rf_score,
            'gb_mse': -gb_score,
            'feature_importance': {
                'random_forest': dict(zip(self.base_features, rf_model.feature_importances_)),
                'gradient_boosting': dict(zip(self.base_features, gb_model.feature_importances_))
            },
            'training_date': datetime.now().isoformat()
        }
        
        logger.info(f"xA model training completed. Mean xA: {training_metrics['mean_xa']:.4f}")
        
        return training_metrics
    
    def predict_xa(self, pass_data: Dict, match_context: Dict = None) -> Dict:
        """
        Predict Expected Assists for a single pass.
        
        Args:
            pass_data: Pass information
            match_context: Match context (optional)
            
        Returns:
            Dictionary with xA value and breakdown
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Calculate base features
        base_features = self._calculate_base_features(pass_data)
        
        # Get base model predictions
        rf_pred = self.rf_model.predict(base_features)[0]
        gb_pred = self.gb_model.predict(base_features)[0]
        ensemble_pred = (rf_pred + gb_pred) / 2
        
        # Calibrate probability
        calibrated_prob = self.calibrator.predict_proba(
            ensemble_pred.reshape(-1, 1)
        )[0][1]  # Probability of assist
        
        # Apply pass type multiplier
        pass_type_mult = self._get_pass_type_multiplier(pass_data)
        
        # Apply position quality multiplier
        position_mult = self._get_position_quality_multiplier(pass_data)
        
        # Apply context multiplier if available
        context_mult = 1.0
        if match_context:
            context_mult = self._get_context_multiplier(pass_data, match_context)
        
        # Final xA calculation
        final_xa = calibrated_prob * pass_type_mult * position_mult * context_mult
        
        # Ensure reasonable bounds
        final_xa = np.clip(final_xa, 0.001, 0.8)  # Assists are rarer than goals
        
        return {
            'xa_value': final_xa,
            'base_xa': calibrated_prob,
            'pass_type_multiplier': pass_type_mult,
            'position_multiplier': position_mult,
            'context_multiplier': context_mult,
            'pass_quality': self._assess_pass_quality(pass_data),
            'receiver_position_quality': self._assess_receiver_position(pass_data),
            'contributing_factors': {
                'pass_distance': pass_data.get('pass_distance', 0),
                'receiver_distance_to_goal': pass_data.get('receiver_distance_to_goal', 0),
                'pass_type': pass_data.get('pass_type', 'unknown'),
                'defenders_between': pass_data.get('defenders_between', 0),
                'minute': pass_data.get('minute', 0)
            }
        }
    
    def _assess_pass_quality(self, pass_data: Dict) -> str:
        """Assess overall pass quality rating."""
        pass_type_mult = self._get_pass_type_multiplier(pass_data)
        
        if pass_type_mult >= 1.3:
            return 'Excellent'
        elif pass_type_mult >= 1.15:
            return 'Good'
        elif pass_type_mult >= 0.9:
            return 'Average'
        else:
            return 'Poor'
    
    def _assess_receiver_position(self, pass_data: Dict) -> str:
        """Assess receiver position quality."""
        position_mult = self._get_position_quality_multiplier(pass_data)
        
        if position_mult >= 1.8:
            return 'Excellent (Box)'
        elif position_mult >= 1.3:
            return 'Very Good (Edge of Box)'
        elif position_mult >= 1.0:
            return 'Good (Attacking Third)'
        elif position_mult >= 0.6:
            return 'Average (Midfield)'
        else:
            return 'Poor (Defensive)'
    
    def predict_match_xa(self, match_passes: List[Dict], match_context: Dict = None) -> Dict:
        """
        Calculate Expected Assists for all key passes in a match.
        
        Args:
            match_passes: List of pass dictionaries
            match_context: Match context information
            
        Returns:
            Comprehensive xA analysis for the match
        """
        if not match_passes:
            return {'total_xa': 0.0, 'pass_breakdown': []}
        
        pass_breakdown = []
        total_xa = 0.0
        
        for pass_info in match_passes:
            xa_result = self.predict_xa(pass_info, match_context)
            pass_breakdown.append({
                'pass_id': pass_info.get('id', 'unknown'),
                'minute': pass_info.get('minute', 0),
                'passer': pass_info.get('passer_name', 'unknown'),
                'receiver': pass_info.get('receiver_name', 'unknown'),
                'xa': xa_result['xa_value'],
                'resulted_in_assist': pass_info.get('resulted_in_assist', False),
                'pass_quality': xa_result['pass_quality']
            })
            total_xa += xa_result['xa_value']
        
        return {
            'total_xa': total_xa,
            'key_pass_count': len(match_passes),
            'average_pass_quality': total_xa / len(match_passes) if match_passes else 0,
            'pass_breakdown': pass_breakdown,
            'creativity_metrics': {
                'actual_assists': sum(p.get('resulted_in_assist', False) for p in match_passes),
                'expected_assists': total_xa,
                'over_performance': sum(p.get('resulted_in_assist', False) for p in match_passes) - total_xa,
                'chance_creation_rate': len(match_passes) / 90  # Per 90 minutes
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
            'pass_type_multipliers': self.pass_type_multipliers,
            'position_quality_zones': self.position_quality_zones,
            'context_multipliers': self.context_multipliers,
            'is_trained': self.is_trained,
            'save_date': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"xA model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """Load trained model from disk."""
        model_data = joblib.load(filepath)
        
        self.rf_model = model_data['rf_model']
        self.gb_model = model_data['gb_model']  
        self.calibrator = model_data['calibrator']
        self.base_features = model_data['base_features']
        self.pass_type_multipliers = model_data['pass_type_multipliers']
        self.position_quality_zones = model_data['position_quality_zones']
        self.context_multipliers = model_data['context_multipliers']
        self.is_trained = model_data['is_trained']
        
        logger.info(f"xA model loaded from {filepath}")


# Utility function for pass data preparation
def prepare_pass_data_from_api(api_match_data: Dict) -> List[Dict]:
    """
    Convert API match data to xA model format.
    
    Args:
        api_match_data: Raw match data from API
        
    Returns:
        List of pass dictionaries in xA model format
    """
    passes = []
    
    # Extract passing events that led to shots
    match_events = api_match_data.get('events', [])
    
    # Find shot events first
    shot_events = [e for e in match_events if e.get('type') in ['shot', 'goal']]
    
    # For each shot, look for the preceding pass (assist candidate)
    for shot in shot_events:
        shot_minute = shot.get('minute', 0)
        shot_team = shot.get('team_id')
        
        # Look for passes in the 10 seconds before the shot
        for event in match_events:
            if (event.get('type') == 'pass' and 
                event.get('team_id') == shot_team and
                event.get('minute', 0) <= shot_minute and
                event.get('minute', 0) >= shot_minute - 1):  # Within 1 minute
                
                pass_data = {
                    'id': event.get('id'),
                    'minute': event.get('minute', 0),
                    'passer_name': event.get('player_name', 'unknown'),
                    'passer_id': event.get('player_id'),
                    'start_x': event.get('start_x', 50),
                    'start_y': event.get('start_y', 50),
                    'end_x': event.get('end_x', 70),
                    'end_y': event.get('end_y', 50),
                    'pass_type': event.get('detail', 'regular_pass'),
                    'resulted_in_assist': shot.get('type') == 'goal',
                    'led_to_shot': True,
                    'defenders_between': 1,  # Default estimate
                    'passer_under_pressure': False,  # Default
                    'pass_duration': 1.0  # Default
                }
                passes.append(pass_data)
                break  # Only one assist per goal
    
    return passes


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    xa_model = ExpectedAssistsModel()
    
    example_pass = {
        'start_x': 70,
        'start_y': 40,
        'end_x': 90,
        'end_y': 52,
        'pass_type': 'through_ball',
        'minute': 75,
        'defenders_between': 2,
        'passer_under_pressure': True
    }
    
    print("Expected Assists Model - Example Usage")
    print(f"Example pass: {example_pass}")
    print("Note: Model needs training data before predictions can be made")