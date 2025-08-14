"""
Advanced Football Metrics Calculator
Implements cutting-edge football analytics metrics including PPDA, packing rates,
passing networks, and other advanced performance indicators.

Metrics implemented:
- PPDA (Passes per Defensive Action)
- Packing Rate (players eliminated per action)
- Passing Networks (network analysis of team play)
- Progressive Distance (advancement toward goal)
- Defensive Intensity (pressing metrics)
- Ball Recovery Rate and locations
- Counter-pressing efficiency
- Line-breaking passes
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from scipy.spatial.distance import cdist
from scipy.stats import entropy
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AdvancedTeamMetrics:
    """Container for advanced team metrics"""
    team_name: str
    match_id: str
    
    # Defensive metrics
    ppda: float
    ppda_defensive_third: float
    defensive_actions_per_minute: float
    
    # Pressing metrics
    pressing_intensity: float
    counter_pressing_success_rate: float
    high_press_triggers: int
    
    # Possession metrics
    packing_rate: float
    progressive_distance: float
    line_breaking_passes: int
    
    # Network metrics
    passing_network_density: float
    passing_network_centralization: float
    key_passers_influence: float
    
    # Transition metrics
    ball_recovery_rate: float
    transition_success_rate: float
    fast_breaks: int


class AdvancedMetricsCalculator:
    """
    Calculator for advanced football metrics using event data
    """
    
    def __init__(self):
        # Field dimensions (standardized)
        self.field_length = 100
        self.field_width = 64
        
        # Zone definitions
        self.zones = {
            'defensive_third': (0, 33.33),
            'middle_third': (33.33, 66.67),
            'attacking_third': (66.67, 100)
        }
        
        # Defensive action types
        self.defensive_actions = [
            'tackle', 'interception', 'block', 'clearance', 
            'foul', 'aerial_duel_won', 'ball_recovery'
        ]
        
        # Progressive action thresholds
        self.progressive_thresholds = {
            'min_distance': 10,  # Minimum meters to be progressive
            'attacking_half_threshold': 10,  # Reduced threshold in attacking half
            'final_third_threshold': 5   # Even lower in final third
        }
    
    def calculate_ppda(self, team_events: List[Dict], opposition_events: List[Dict]) -> Dict[str, float]:
        """
        Calculate Passes per Defensive Action (PPDA)
        
        PPDA = Opposition passes / (Team defensive actions)
        Lower PPDA = more aggressive pressing
        
        Args:
            team_events: Events by the team (defensive actions)
            opposition_events: Events by the opposition (passes)
            
        Returns:
            Dictionary with PPDA metrics
        """
        # Count opposition passes
        opposition_passes = len([e for e in opposition_events 
                               if e.get('type') == 'pass' and e.get('successful', True)])
        
        # Count team defensive actions
        team_def_actions = len([e for e in team_events 
                              if e.get('type') in self.defensive_actions])
        
        # Overall PPDA
        overall_ppda = opposition_passes / team_def_actions if team_def_actions > 0 else float('inf')
        
        # PPDA by zone
        def_third_actions = len([e for e in team_events 
                               if (e.get('type') in self.defensive_actions and 
                                   self._get_zone(e.get('x', 50)) == 'defensive_third')])
        
        def_third_opp_passes = len([e for e in opposition_events 
                                  if (e.get('type') == 'pass' and e.get('successful', True) and
                                      self._get_zone(e.get('x', 50)) == 'attacking_third')])  # Opposition's attacking third
        
        defensive_third_ppda = def_third_opp_passes / def_third_actions if def_third_actions > 0 else float('inf')
        
        return {
            'overall_ppda': overall_ppda,
            'defensive_third_ppda': defensive_third_ppda,
            'defensive_actions': team_def_actions,
            'opposition_passes': opposition_passes,
            'pressing_intensity_rating': self._rate_pressing_intensity(overall_ppda)
        }
    
    def calculate_packing_rate(self, pass_events: List[Dict], all_events: List[Dict]) -> Dict[str, float]:
        """
        Calculate packing rate - how many opposition players are eliminated per action
        
        Packing = eliminating opponents from play through passes/dribbles
        
        Args:
            pass_events: Pass events with start/end locations
            all_events: All events for opponent position estimation
            
        Returns:
            Dictionary with packing metrics
        """
        total_packing = 0.0
        successful_actions = 0
        
        for pass_event in pass_events:
            if not pass_event.get('successful', True):
                continue
                
            start_x = pass_event.get('start_x', 50)
            start_y = pass_event.get('start_y', 32)
            end_x = pass_event.get('end_x', 50)
            end_y = pass_event.get('end_y', 32)
            
            # Estimate opponents eliminated
            opponents_packed = self._calculate_opponents_packed(
                (start_x, start_y), (end_x, end_y), all_events, pass_event.get('minute', 0)
            )
            
            total_packing += opponents_packed
            successful_actions += 1
        
        packing_rate = total_packing / successful_actions if successful_actions > 0 else 0.0
        
        return {
            'packing_rate': packing_rate,
            'total_opponents_packed': total_packing,
            'successful_actions': successful_actions,
            'packing_efficiency': self._rate_packing_efficiency(packing_rate)
        }
    
    def _calculate_opponents_packed(self, start_pos: Tuple[float, float], 
                                  end_pos: Tuple[float, float], 
                                  all_events: List[Dict], minute: int) -> float:
        """
        Estimate how many opponents were eliminated by this action
        
        This is simplified - actual packing requires tracking data
        We estimate based on pass direction and typical formations
        """
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        # Calculate pass vector
        pass_distance = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        if pass_distance < 5:  # Short pass, minimal packing
            return 0.1
        
        # Estimate based on pass characteristics
        packing_estimate = 0.0
        
        # Forward passes in attacking areas pack more players
        if end_x > start_x and start_x > 50:  # Forward pass in attacking half
            packing_estimate += 0.8
        
        # Long passes typically pack more players
        if pass_distance > 25:
            packing_estimate += 0.6
        
        # Central passes pack more than wide passes
        if 25 <= start_y <= 39 and 25 <= end_y <= 39:  # Central corridor
            packing_estimate += 0.4
        
        # Through balls pack more (would need pass type classification)
        # For now, estimate based on rapid advancement
        if (end_x - start_x) > 15:  # Significant forward progression
            packing_estimate += 0.5
        
        return min(packing_estimate, 3.0)  # Max 3 players packed per action
    
    def calculate_passing_network(self, pass_events: List[Dict], player_positions: Dict[str, Tuple[float, float]] = None) -> Dict:
        """
        Calculate passing network metrics using network analysis
        
        Args:
            pass_events: Pass events with passer/receiver information
            player_positions: Average positions (if available)
            
        Returns:
            Network analysis results
        """
        # Build passing network graph
        G = nx.DiGraph()
        
        # Add edges (passes between players)
        for pass_event in pass_events:
            if not pass_event.get('successful', True):
                continue
                
            passer = pass_event.get('passer')
            receiver = pass_event.get('receiver')
            
            if passer and receiver and passer != receiver:
                if G.has_edge(passer, receiver):
                    G[passer][receiver]['weight'] += 1
                else:
                    G.add_edge(passer, receiver, weight=1)
        
        if len(G.nodes()) == 0:
            return {'network_density': 0.0, 'centralization': 0.0}
        
        # Calculate network metrics
        try:
            # Network density (0-1, higher = more connections)
            density = nx.density(G)
            
            # Centralization (0-1, higher = more centralized through key players)
            centrality = nx.degree_centrality(G)
            max_centrality = max(centrality.values()) if centrality else 0
            centralization = max_centrality
            
            # Key player influence (based on betweenness centrality)
            betweenness = nx.betweenness_centrality(G)
            key_influence = max(betweenness.values()) if betweenness else 0
            
            # Network efficiency
            try:
                efficiency = nx.global_efficiency(G)
            except:
                efficiency = 0.0
            
            return {
                'network_density': density,
                'centralization': centralization,
                'key_player_influence': key_influence,
                'network_efficiency': efficiency,
                'total_connections': len(G.edges()),
                'total_players': len(G.nodes()),
                'most_connected_player': max(centrality.items(), key=lambda x: x[1])[0] if centrality else None
            }
            
        except Exception as e:
            logger.warning(f"Error calculating network metrics: {e}")
            return {'network_density': 0.0, 'centralization': 0.0}
    
    def calculate_progressive_metrics(self, events: List[Dict]) -> Dict[str, float]:
        """
        Calculate progressive passing and carrying metrics
        
        Args:
            events: All team events (passes, carries, dribbles)
            
        Returns:
            Progressive metrics dictionary
        """
        progressive_actions = 0
        total_progressive_distance = 0.0
        line_breaking_passes = 0
        total_actions = 0
        
        for event in events:
            if event.get('type') not in ['pass', 'carry', 'dribble']:
                continue
                
            if not event.get('successful', True):
                continue
                
            start_x = event.get('start_x', 50)
            end_x = event.get('end_x', start_x)
            
            # Calculate forward progression
            progression = end_x - start_x
            
            # Determine if action is progressive
            is_progressive = self._is_progressive_action(start_x, progression)
            
            if is_progressive:
                progressive_actions += 1
                total_progressive_distance += progression
                
                # Check if it's line-breaking (significant vertical progression)
                start_y = event.get('start_y', 32)
                end_y = event.get('end_y', start_y)
                
                if abs(end_y - start_y) > 10 and progression > 15:
                    line_breaking_passes += 1
            
            total_actions += 1
        
        return {
            'progressive_actions': progressive_actions,
            'progressive_percentage': progressive_actions / total_actions if total_actions > 0 else 0.0,
            'avg_progressive_distance': total_progressive_distance / progressive_actions if progressive_actions > 0 else 0.0,
            'line_breaking_passes': line_breaking_passes,
            'total_progressive_distance': total_progressive_distance
        }
    
    def calculate_defensive_intensity(self, defensive_events: List[Dict], match_duration: int = 90) -> Dict[str, float]:
        """
        Calculate defensive intensity and pressing metrics
        
        Args:
            defensive_events: Defensive actions events
            match_duration: Match duration in minutes
            
        Returns:
            Defensive intensity metrics
        """
        total_def_actions = len(defensive_events)
        
        # Actions per minute
        actions_per_minute = total_def_actions / match_duration
        
        # High press actions (defensive actions in opponent's half)
        high_press_actions = len([e for e in defensive_events 
                                if e.get('x', 50) > 50])
        
        # Counter-pressing (defensive actions within 5 seconds of possession loss)
        counter_press_actions = self._calculate_counter_pressing(defensive_events)
        
        # Defensive third intensity
        def_third_actions = len([e for e in defensive_events 
                               if self._get_zone(e.get('x', 50)) == 'defensive_third'])
        
        return {
            'defensive_actions_per_minute': actions_per_minute,
            'high_press_percentage': high_press_actions / total_def_actions if total_def_actions > 0 else 0.0,
            'counter_press_actions': counter_press_actions,
            'defensive_third_intensity': def_third_actions / match_duration,
            'total_defensive_actions': total_def_actions,
            'intensity_rating': self._rate_defensive_intensity(actions_per_minute)
        }
    
    def calculate_transition_metrics(self, all_events: List[Dict]) -> Dict[str, float]:
        """
        Calculate transition (attacking/defensive) metrics
        
        Args:
            all_events: All match events
            
        Returns:
            Transition metrics
        """
        ball_recoveries = 0
        successful_transitions = 0
        fast_breaks = 0
        
        # Sort events by time
        sorted_events = sorted(all_events, key=lambda x: (x.get('minute', 0), x.get('second', 0)))
        
        for i, event in enumerate(sorted_events[:-1]):
            # Look for ball recovery followed by quick attack
            if event.get('type') in self.defensive_actions:
                ball_recoveries += 1
                
                # Check next few events for quick transition
                next_events = sorted_events[i+1:i+6]  # Next 5 events
                
                for next_event in next_events:
                    if next_event.get('team') == event.get('team'):
                        # Same team kept possession - successful recovery
                        if next_event.get('type') in ['pass', 'carry', 'dribble']:
                            # Check if it led to attacking action
                            if next_event.get('x', 50) > event.get('x', 50):  # Forward movement
                                successful_transitions += 1
                                
                                # Fast break if rapid progression
                                start_x = event.get('x', 50)
                                attack_x = next_event.get('x', 50)
                                if attack_x - start_x > 30:  # Significant field progression
                                    fast_breaks += 1
                        break
        
        return {
            'ball_recoveries': ball_recoveries,
            'successful_transitions': successful_transitions,
            'transition_success_rate': successful_transitions / ball_recoveries if ball_recoveries > 0 else 0.0,
            'fast_breaks': fast_breaks,
            'fast_break_rate': fast_breaks / ball_recoveries if ball_recoveries > 0 else 0.0
        }
    
    def calculate_comprehensive_team_metrics(self, team_events: List[Dict], 
                                           opposition_events: List[Dict],
                                           match_duration: int = 90) -> AdvancedTeamMetrics:
        """
        Calculate comprehensive advanced metrics for a team
        
        Args:
            team_events: All events by the team
            opposition_events: All events by opposition
            match_duration: Match duration in minutes
            
        Returns:
            AdvancedTeamMetrics object with all calculated metrics
        """
        team_name = team_events[0].get('team', 'Unknown') if team_events else 'Unknown'
        match_id = team_events[0].get('match_id', 'Unknown') if team_events else 'Unknown'
        
        # Calculate individual metric categories
        ppda_metrics = self.calculate_ppda(team_events, opposition_events)
        packing_metrics = self.calculate_packing_rate(
            [e for e in team_events if e.get('type') == 'pass'], 
            team_events + opposition_events
        )
        network_metrics = self.calculate_passing_network(
            [e for e in team_events if e.get('type') == 'pass']
        )
        progressive_metrics = self.calculate_progressive_metrics(team_events)
        defensive_metrics = self.calculate_defensive_intensity(
            [e for e in team_events if e.get('type') in self.defensive_actions],
            match_duration
        )
        transition_metrics = self.calculate_transition_metrics(team_events)
        
        return AdvancedTeamMetrics(
            team_name=team_name,
            match_id=match_id,
            
            # Defensive metrics
            ppda=ppda_metrics.get('overall_ppda', 0.0),
            ppda_defensive_third=ppda_metrics.get('defensive_third_ppda', 0.0),
            defensive_actions_per_minute=defensive_metrics.get('defensive_actions_per_minute', 0.0),
            
            # Pressing metrics  
            pressing_intensity=defensive_metrics.get('high_press_percentage', 0.0),
            counter_pressing_success_rate=0.0,  # Would need more detailed calculation
            high_press_triggers=int(defensive_metrics.get('total_defensive_actions', 0) * 
                                  defensive_metrics.get('high_press_percentage', 0.0)),
            
            # Possession metrics
            packing_rate=packing_metrics.get('packing_rate', 0.0),
            progressive_distance=progressive_metrics.get('total_progressive_distance', 0.0),
            line_breaking_passes=progressive_metrics.get('line_breaking_passes', 0),
            
            # Network metrics
            passing_network_density=network_metrics.get('network_density', 0.0),
            passing_network_centralization=network_metrics.get('centralization', 0.0),
            key_passers_influence=network_metrics.get('key_player_influence', 0.0),
            
            # Transition metrics
            ball_recovery_rate=transition_metrics.get('ball_recoveries', 0) / match_duration,
            transition_success_rate=transition_metrics.get('transition_success_rate', 0.0),
            fast_breaks=transition_metrics.get('fast_breaks', 0)
        )
    
    # Helper methods
    def _get_zone(self, x: float) -> str:
        """Get field zone for x coordinate"""
        for zone_name, (min_x, max_x) in self.zones.items():
            if min_x <= x <= max_x:
                return zone_name
        return 'unknown'
    
    def _is_progressive_action(self, start_x: float, progression: float) -> bool:
        """Determine if an action is progressive"""
        if start_x >= 66.67:  # Final third
            return progression >= self.progressive_thresholds['final_third_threshold']
        elif start_x >= 50:  # Attacking half
            return progression >= self.progressive_thresholds['attacking_half_threshold']
        else:
            return progression >= self.progressive_thresholds['min_distance']
    
    def _calculate_counter_pressing(self, defensive_events: List[Dict]) -> int:
        """Calculate counter-pressing actions (simplified)"""
        # This would need temporal analysis of possession changes
        # For now, estimate based on high-press defensive actions
        return len([e for e in defensive_events 
                   if e.get('x', 50) > 60 and e.get('type') in ['tackle', 'interception']])
    
    def _rate_pressing_intensity(self, ppda: float) -> str:
        """Rate pressing intensity based on PPDA"""
        if ppda <= 8:
            return 'Very High'
        elif ppda <= 12:
            return 'High'
        elif ppda <= 16:
            return 'Medium'
        elif ppda <= 20:
            return 'Low'
        else:
            return 'Very Low'
    
    def _rate_packing_efficiency(self, packing_rate: float) -> str:
        """Rate packing efficiency"""
        if packing_rate >= 0.8:
            return 'Excellent'
        elif packing_rate >= 0.5:
            return 'Good'
        elif packing_rate >= 0.3:
            return 'Average'
        else:
            return 'Poor'
    
    def _rate_defensive_intensity(self, actions_per_minute: float) -> str:
        """Rate defensive intensity"""
        if actions_per_minute >= 2.5:
            return 'Very High'
        elif actions_per_minute >= 2.0:
            return 'High'
        elif actions_per_minute >= 1.5:
            return 'Medium'
        else:
            return 'Low'


# Utility functions for data preparation
def prepare_events_for_metrics(api_events: List[Dict], team_name: str) -> List[Dict]:
    """
    Prepare event data for metrics calculation
    
    Args:
        api_events: Raw API events
        team_name: Team name to filter for
        
    Returns:
        Processed events list
    """
    processed_events = []
    
    for event in api_events:
        if event.get('team_name') != team_name:
            continue
            
        processed_event = {
            'match_id': event.get('match_id'),
            'team': team_name,
            'type': event.get('type', '').lower(),
            'minute': event.get('minute', 0),
            'second': event.get('second', 0),
            'x': event.get('x', 50),
            'y': event.get('y', 32),
            'start_x': event.get('start_x', event.get('x', 50)),
            'start_y': event.get('start_y', event.get('y', 32)),
            'end_x': event.get('end_x', event.get('x', 50)),
            'end_y': event.get('end_y', event.get('y', 32)),
            'successful': event.get('successful', True),
            'passer': event.get('player_name') if event.get('type') == 'pass' else None,
            'receiver': event.get('pass_recipient') if event.get('type') == 'pass' else None
        }
        
        processed_events.append(processed_event)
    
    return processed_events


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    calculator = AdvancedMetricsCalculator()
    
    # Example events (simplified)
    example_team_events = [
        {'type': 'pass', 'start_x': 30, 'start_y': 32, 'end_x': 45, 'end_y': 35, 'successful': True, 'team': 'Team A', 'match_id': 'test'},
        {'type': 'tackle', 'x': 55, 'y': 30, 'team': 'Team A', 'match_id': 'test'},
        {'type': 'pass', 'start_x': 55, 'start_y': 30, 'end_x': 75, 'end_y': 32, 'successful': True, 'team': 'Team A', 'match_id': 'test'}
    ]
    
    example_opposition_events = [
        {'type': 'pass', 'successful': True, 'team': 'Team B'},
        {'type': 'pass', 'successful': True, 'team': 'Team B'},
        {'type': 'pass', 'successful': False, 'team': 'Team B'}
    ]
    
    # Calculate metrics
    metrics = calculator.calculate_comprehensive_team_metrics(
        example_team_events, 
        example_opposition_events
    )
    
    print("Advanced Metrics Calculator - Example Results")
    print(f"Team: {metrics.team_name}")
    print(f"PPDA: {metrics.ppda:.2f}")
    print(f"Packing Rate: {metrics.packing_rate:.2f}")
    print(f"Network Density: {metrics.passing_network_density:.2f}")
    print(f"Progressive Distance: {metrics.progressive_distance:.1f}m")
    print(f"Line Breaking Passes: {metrics.line_breaking_passes}")
    
    print("\nAdvanced metrics calculator ready for use!")