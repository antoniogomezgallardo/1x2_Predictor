"""
Expected Threat (xT) Model - Possession Value and Ball Progression Assessment
Quantifies the threat level of ball possession at different field positions.

This model evaluates:
- Field position value (how threatening is possession at each location)
- Ball progression value (increase/decrease in threat from actions)
- Action effectiveness (passes, dribbles, carries that advance play)
- Defensive disruption (how actions break down opposition structure)
- Zone transitions and their impact on goal probability
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy.spatial.distance import cdist
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExpectedThreatModel:
    """
    Expected Threat model for evaluating possession value and ball progression.
    
    Calculates the probability of scoring a goal from different field positions
    and actions, providing a continuous measure of attacking threat.
    """
    
    def __init__(self):
        self.position_threat_map = None
        self.action_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Field dimensions (standard football pitch)
        self.field_length = 100
        self.field_width = 64
        self.grid_size = 4  # 4x4 meter grid cells
        
        # Initialize threat grid
        self.grid_rows = self.field_width // self.grid_size
        self.grid_cols = self.field_length // self.grid_size
        self.threat_grid = np.zeros((self.grid_rows, self.grid_cols))
        
        # Action types and their base values
        self.action_types = {
            'pass': {'success_bonus': 0.02, 'failure_penalty': -0.01},
            'dribble': {'success_bonus': 0.05, 'failure_penalty': -0.03},
            'carry': {'success_bonus': 0.03, 'failure_penalty': -0.01},
            'cross': {'success_bonus': 0.08, 'failure_penalty': -0.02},
            'shot': {'success_bonus': 0.5, 'failure_penalty': -0.1},
            'key_pass': {'success_bonus': 0.12, 'failure_penalty': -0.02}
        }
        
        # Zone definitions for strategic analysis
        self.zones = {
            'defensive_third': {'x_min': 0, 'x_max': 33.33},
            'middle_third': {'x_min': 33.33, 'x_max': 66.66},
            'attacking_third': {'x_min': 66.66, 'x_max': 100},
            'left_wing': {'y_min': 0, 'y_max': 21.33},
            'center': {'y_min': 21.33, 'y_max': 42.66},
            'right_wing': {'y_min': 42.66, 'y_max': 64}
        }
    
    def _position_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """
        Convert field coordinates to grid indices.
        
        Args:
            x, y: Field coordinates (0-100, 0-64)
            
        Returns:
            Grid indices (row, col)
        """
        col = int(np.clip(x / self.grid_size, 0, self.grid_cols - 1))
        row = int(np.clip(y / self.grid_size, 0, self.grid_rows - 1))
        return row, col
    
    def _grid_to_position(self, row: int, col: int) -> Tuple[float, float]:
        """
        Convert grid indices back to field coordinates.
        
        Args:
            row, col: Grid indices
            
        Returns:
            Field coordinates (x, y)
        """
        x = (col + 0.5) * self.grid_size
        y = (row + 0.5) * self.grid_size
        return x, y
    
    def _calculate_base_threat_values(self) -> np.ndarray:
        """
        Calculate base threat values for each grid position.
        
        Based on historical goal probability from each field position.
        Higher values closer to goal, with adjustments for angle.
        
        Returns:
            Threat value grid
        """
        threat_grid = np.zeros((self.grid_rows, self.grid_cols))
        
        # Goal position
        goal_x = 100
        goal_y = 32  # Center of goal
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x, y = self._grid_to_position(row, col)
                
                # Distance to goal
                distance_to_goal = np.sqrt((goal_x - x)**2 + (goal_y - y)**2)
                
                # Angle to goal (better angles = higher threat)
                goal_width = 7.32  # Standard goal width
                if distance_to_goal > 0:
                    angle_rad = np.arctan(goal_width / distance_to_goal)
                    angle_factor = angle_rad / np.pi * 2  # Normalize
                else:
                    angle_factor = 1.0
                
                # Base threat calculation (exponential decay with distance)
                base_threat = np.exp(-distance_to_goal / 25.0) * angle_factor
                
                # Penalty area bonus
                if x >= 83 and 37 <= y <= 63:  # In penalty area
                    base_threat *= 2.5
                elif x >= 75:  # Near penalty area
                    base_threat *= 1.5
                
                # Central corridor bonus
                if 25 <= y <= 39:  # Central area
                    base_threat *= 1.3
                
                # Wide area penalty (harder to score from wings)
                if y <= 10 or y >= 54:
                    base_threat *= 0.7
                
                threat_grid[row, col] = base_threat
        
        # Normalize to 0-1 range
        if threat_grid.max() > 0:
            threat_grid = threat_grid / threat_grid.max()
        
        return threat_grid
    
    def train_position_model(self, possession_data: pd.DataFrame) -> Dict:
        """
        Train the position-based threat model using historical possession data.
        
        Args:
            possession_data: DataFrame with possession events and outcomes
            
        Returns:
            Training metrics
        """
        logger.info("Training Expected Threat position model")
        
        # Start with base threat values
        self.threat_grid = self._calculate_base_threat_values()
        
        # Adjust based on historical data
        if len(possession_data) > 0:
            self._update_threat_grid_from_data(possession_data)
        
        # Mark as trained
        self.is_trained = True
        
        training_metrics = {
            'base_model': 'distance_angle_based',
            'data_samples': len(possession_data),
            'max_threat_value': float(self.threat_grid.max()),
            'min_threat_value': float(self.threat_grid.min()),
            'training_date': datetime.now().isoformat()
        }
        
        logger.info(f"Position threat model trained. Max threat: {training_metrics['max_threat_value']:.4f}")
        
        return training_metrics
    
    def _update_threat_grid_from_data(self, possession_data: pd.DataFrame) -> None:
        """
        Update threat grid values based on actual goal outcomes.
        
        Args:
            possession_data: Historical possession events with outcomes
        """
        # Group possessions by grid position
        grid_outcomes = {}
        
        for _, row in possession_data.iterrows():
            x, y = row.get('x', 50), row.get('y', 32)
            grid_row, grid_col = self._position_to_grid(x, y)
            grid_key = (grid_row, grid_col)
            
            if grid_key not in grid_outcomes:
                grid_outcomes[grid_key] = {'possessions': 0, 'goals': 0}
            
            grid_outcomes[grid_key]['possessions'] += 1
            if row.get('resulted_in_goal', False):
                grid_outcomes[grid_key]['goals'] += 1
        
        # Update grid with empirical probabilities
        for (row, col), outcomes in grid_outcomes.items():
            if outcomes['possessions'] >= 10:  # Minimum sample size
                empirical_threat = outcomes['goals'] / outcomes['possessions']
                # Blend with base model (70% empirical, 30% base)
                self.threat_grid[row, col] = (
                    0.7 * empirical_threat + 0.3 * self.threat_grid[row, col]
                )
    
    def get_position_threat(self, x: float, y: float) -> float:
        """
        Get threat value for a specific field position.
        
        Args:
            x, y: Field coordinates
            
        Returns:
            Threat value (0-1)
        """
        if not self.is_trained:
            # Return basic distance-based estimate
            goal_distance = np.sqrt((100 - x)**2 + (32 - y)**2)
            return max(0, 1 - goal_distance / 100)
        
        row, col = self._position_to_grid(x, y)
        return self.threat_grid[row, col]
    
    def calculate_action_threat(self, action_data: Dict) -> Dict:
        """
        Calculate threat change from a specific action.
        
        Args:
            action_data: Action information (start/end positions, type, outcome)
            
        Returns:
            Threat analysis dictionary
        """
        start_x = action_data.get('start_x', 50)
        start_y = action_data.get('start_y', 32)
        end_x = action_data.get('end_x', start_x)
        end_y = action_data.get('end_y', start_y)
        
        # Get threat values
        start_threat = self.get_position_threat(start_x, start_y)
        end_threat = self.get_position_threat(end_x, end_y)
        
        # Basic threat change
        threat_change = end_threat - start_threat
        
        # Action-specific adjustments
        action_type = action_data.get('action_type', 'pass').lower()
        action_success = action_data.get('successful', True)
        
        # Apply action bonuses/penalties
        if action_type in self.action_types:
            if action_success:
                threat_change += self.action_types[action_type]['success_bonus']
            else:
                threat_change += self.action_types[action_type]['failure_penalty']
        
        # Distance bonus (longer successful actions = more valuable)
        if action_success:
            action_distance = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
            if action_distance > 20:  # Long action
                threat_change *= 1.2
        
        # Zone progression bonus
        zone_progression = self._calculate_zone_progression(start_x, start_y, end_x, end_y)
        threat_change += zone_progression * 0.03
        
        return {
            'start_threat': start_threat,
            'end_threat': end_threat,
            'threat_change': threat_change,
            'action_type': action_type,
            'successful': action_success,
            'zone_progression': zone_progression,
            'threat_rating': self._rate_threat_change(threat_change)
        }
    
    def _calculate_zone_progression(self, start_x: float, start_y: float, 
                                  end_x: float, end_y: float) -> int:
        """
        Calculate number of zones progressed toward goal.
        
        Returns:
            Number of zones progressed (can be negative for regression)
        """
        start_zone = self._get_field_zone(start_x)
        end_zone = self._get_field_zone(end_x)
        
        zone_order = ['defensive_third', 'middle_third', 'attacking_third']
        
        try:
            start_idx = zone_order.index(start_zone)
            end_idx = zone_order.index(end_zone)
            return end_idx - start_idx
        except ValueError:
            return 0
    
    def _get_field_zone(self, x: float) -> str:
        """Get the field zone for an x coordinate."""
        if x <= 33.33:
            return 'defensive_third'
        elif x <= 66.66:
            return 'middle_third'
        else:
            return 'attacking_third'
    
    def _rate_threat_change(self, threat_change: float) -> str:
        """Rate the quality of threat change."""
        if threat_change >= 0.1:
            return 'Excellent'
        elif threat_change >= 0.05:
            return 'Good'
        elif threat_change >= 0.01:
            return 'Moderate'
        elif threat_change >= -0.01:
            return 'Neutral'
        else:
            return 'Poor'
    
    def analyze_possession_sequence(self, sequence: List[Dict]) -> Dict:
        """
        Analyze a complete possession sequence for threat progression.
        
        Args:
            sequence: List of actions in chronological order
            
        Returns:
            Comprehensive sequence analysis
        """
        if not sequence:
            return {'total_threat_change': 0.0, 'actions': []}
        
        action_analyses = []
        total_threat_change = 0.0
        sequence_start_threat = 0.0
        sequence_end_threat = 0.0
        
        for i, action in enumerate(sequence):
            action_result = self.calculate_action_threat(action)
            action_analyses.append(action_result)
            total_threat_change += action_result['threat_change']
            
            if i == 0:
                sequence_start_threat = action_result['start_threat']
            if i == len(sequence) - 1:
                sequence_end_threat = action_result['end_threat']
        
        # Sequence-level metrics
        sequence_length = len(sequence)
        avg_threat_per_action = total_threat_change / sequence_length if sequence_length > 0 else 0
        
        # Progression analysis
        forward_passes = sum(1 for a in action_analyses if a['zone_progression'] > 0)
        backward_passes = sum(1 for a in action_analyses if a['zone_progression'] < 0)
        
        return {
            'total_threat_change': total_threat_change,
            'sequence_start_threat': sequence_start_threat,
            'sequence_end_threat': sequence_end_threat,
            'net_threat_improvement': sequence_end_threat - sequence_start_threat,
            'sequence_length': sequence_length,
            'avg_threat_per_action': avg_threat_per_action,
            'actions': action_analyses,
            'progression_stats': {
                'forward_passes': forward_passes,
                'backward_passes': backward_passes,
                'progression_ratio': forward_passes / sequence_length if sequence_length > 0 else 0
            },
            'sequence_quality': self._rate_sequence_quality(total_threat_change, sequence_length)
        }
    
    def _rate_sequence_quality(self, total_threat: float, length: int) -> str:
        """Rate overall possession sequence quality."""
        if length == 0:
            return 'No Data'
        
        avg_threat = total_threat / length
        
        if avg_threat >= 0.03:
            return 'Excellent'
        elif avg_threat >= 0.015:
            return 'Good'
        elif avg_threat >= 0.005:
            return 'Average'
        elif avg_threat >= -0.005:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def get_team_threat_profile(self, team_actions: List[Dict]) -> Dict:
        """
        Generate comprehensive threat profile for a team.
        
        Args:
            team_actions: All actions by the team in a match/period
            
        Returns:
            Team threat analysis
        """
        if not team_actions:
            return {'total_threat_generated': 0.0}
        
        total_threat = 0.0
        zone_threat = {'defensive_third': 0.0, 'middle_third': 0.0, 'attacking_third': 0.0}
        action_type_threat = {}
        
        # Analyze each action
        for action in team_actions:
            threat_result = self.calculate_action_threat(action)
            threat_change = threat_result['threat_change']
            total_threat += threat_change
            
            # Zone-based analysis
            start_zone = self._get_field_zone(action.get('start_x', 50))
            zone_threat[start_zone] += threat_change
            
            # Action type analysis
            action_type = action.get('action_type', 'pass')
            if action_type not in action_type_threat:
                action_type_threat[action_type] = 0.0
            action_type_threat[action_type] += threat_change
        
        return {
            'total_threat_generated': total_threat,
            'actions_analyzed': len(team_actions),
            'avg_threat_per_action': total_threat / len(team_actions),
            'zone_breakdown': zone_threat,
            'action_type_breakdown': action_type_threat,
            'threat_efficiency': total_threat / len(team_actions) if team_actions else 0,
            'team_threat_rating': self._rate_team_threat(total_threat, len(team_actions))
        }
    
    def _rate_team_threat(self, total_threat: float, action_count: int) -> str:
        """Rate team's overall threat generation."""
        if action_count == 0:
            return 'No Data'
        
        threat_per_action = total_threat / action_count
        
        if threat_per_action >= 0.02:
            return 'Excellent'
        elif threat_per_action >= 0.01:
            return 'Good'
        elif threat_per_action >= 0.005:
            return 'Average'
        elif threat_per_action >= 0:
            return 'Below Average'
        else:
            return 'Poor'
    
    def visualize_threat_grid(self) -> np.ndarray:
        """
        Return the threat grid for visualization purposes.
        
        Returns:
            Threat grid array (can be used with matplotlib/seaborn)
        """
        return self.threat_grid.copy()
    
    def save_model(self, filepath: str) -> None:
        """Save the threat model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'threat_grid': self.threat_grid,
            'action_types': self.action_types,
            'zones': self.zones,
            'field_length': self.field_length,
            'field_width': self.field_width,
            'grid_size': self.grid_size,
            'is_trained': self.is_trained,
            'save_date': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Expected Threat model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """Load threat model from disk."""
        model_data = joblib.load(filepath)
        
        self.threat_grid = model_data['threat_grid']
        self.action_types = model_data['action_types']
        self.zones = model_data['zones']
        self.field_length = model_data['field_length']
        self.field_width = model_data['field_width']
        self.grid_size = model_data['grid_size']
        self.is_trained = model_data['is_trained']
        
        # Recalculate grid dimensions
        self.grid_rows = self.field_width // self.grid_size
        self.grid_cols = self.field_length // self.grid_size
        
        logger.info(f"Expected Threat model loaded from {filepath}")


# Utility functions
def prepare_possession_data_from_api(api_match_data: Dict) -> List[Dict]:
    """
    Convert API match data to possession events for threat analysis.
    
    Args:
        api_match_data: Raw match data from API
        
    Returns:
        List of possession event dictionaries
    """
    events = []
    
    match_events = api_match_data.get('events', [])
    
    for event in match_events:
        if event.get('type') in ['pass', 'dribble', 'carry', 'shot']:
            event_data = {
                'id': event.get('id'),
                'minute': event.get('minute', 0),
                'team_id': event.get('team_id'),
                'player_id': event.get('player_id'),
                'action_type': event.get('type', 'pass'),
                'start_x': event.get('start_x', 50),
                'start_y': event.get('start_y', 32),
                'end_x': event.get('end_x', 50),
                'end_y': event.get('end_y', 32),
                'successful': event.get('successful', True),
                'resulted_in_goal': False  # Would need to link to subsequent goals
            }
            events.append(event_data)
    
    return events


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create threat model
    threat_model = ExpectedThreatModel()
    
    # Train with empty data (uses base model)
    training_metrics = threat_model.train_position_model(pd.DataFrame())
    
    # Example action
    example_action = {
        'start_x': 60,
        'start_y': 30,
        'end_x': 80,
        'end_y': 35,
        'action_type': 'pass',
        'successful': True
    }
    
    # Calculate threat
    threat_result = threat_model.calculate_action_threat(example_action)
    
    print("Expected Threat Model - Example")
    print(f"Training metrics: {training_metrics}")
    print(f"Example action threat: {threat_result}")
    print(f"Threat grid shape: {threat_model.threat_grid.shape}")
    print(f"Max threat position: {threat_model.threat_grid.max():.4f}")