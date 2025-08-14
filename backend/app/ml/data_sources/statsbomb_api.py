"""
StatsBomb API Integration - Event-Level Football Data
Integrates with StatsBomb's open data and API for detailed match analysis.

Features:
- Event-level data (passes, shots, carries, etc.)
- Player tracking and positioning data
- Advanced metrics calculation from events
- Free competition data access
- Shot and pass location mapping
- Defensive action analysis
"""

import requests
import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass
import asyncio
import aiohttp
from pathlib import Path
import time

logger = logging.getLogger(__name__)


@dataclass
class StatsBombEvent:
    """Single event from StatsBomb data"""
    id: str
    index: int
    period: int
    timestamp: str
    minute: int
    second: int
    type: str
    possession: int
    possession_team: str
    play_pattern: str
    team: str
    player: Optional[str]
    position: Optional[str]
    location: Optional[Tuple[float, float]]
    duration: Optional[float]
    under_pressure: bool = False
    off_camera: bool = False


@dataclass
class StatsBombMatch:
    """Match information from StatsBomb"""
    match_id: int
    match_date: str
    kick_off: str
    competition: str
    season: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    match_status: str
    home_managers: List[str]
    away_managers: List[str]
    stadium: Optional[str] = None
    referee: Optional[str] = None


class StatsBombCollector:
    """
    Collects detailed event data from StatsBomb
    """
    
    def __init__(self, use_local_data: bool = True):
        """
        Initialize StatsBomb collector
        
        Args:
            use_local_data: Whether to use StatsBomb's free open data
        """
        self.base_url = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
        self.api_base_url = "https://api.statsbomb.com/v1"  # For paid API
        self.use_local_data = use_local_data
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Football-Predictor/1.0',
            'Accept': 'application/json'
        })
        
        # Cache for frequently accessed data
        self.competitions_cache = None
        self.seasons_cache = {}
        
        # Free competitions available in open data
        self.free_competitions = {
            'FIFA World Cup': 43,
            'UEFA Euro': 55, 
            'La Liga': 11,
            'Premier League': 9,
            'FA WSL': 37,
            'NWSL': 49
        }
        
        # Field dimensions (StatsBomb uses 120x80 field)
        self.field_length = 120
        self.field_width = 80
    
    def get_competitions(self) -> List[Dict]:
        """
        Get available competitions
        
        Returns:
            List of competition dictionaries
        """
        if self.competitions_cache:
            return self.competitions_cache
        
        try:
            url = f"{self.base_url}/competitions.json"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            competitions = response.json()
            self.competitions_cache = competitions
            
            logger.info(f"Found {len(competitions)} competitions")
            return competitions
            
        except Exception as e:
            logger.error(f"Error fetching competitions: {e}")
            return []
    
    def get_matches(self, competition_id: int, season_id: int) -> List[StatsBombMatch]:
        """
        Get matches for a competition and season
        
        Args:
            competition_id: StatsBomb competition ID
            season_id: StatsBomb season ID
            
        Returns:
            List of StatsBombMatch objects
        """
        try:
            url = f"{self.base_url}/matches/{competition_id}/{season_id}.json"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            matches_data = response.json()
            matches = []
            
            for match_data in matches_data:
                match = StatsBombMatch(
                    match_id=match_data['match_id'],
                    match_date=match_data['match_date'],
                    kick_off=match_data.get('kick_off', ''),
                    competition=match_data.get('competition', {}).get('competition_name', ''),
                    season=match_data.get('season', {}).get('season_name', ''),
                    home_team=match_data.get('home_team', {}).get('home_team_name', ''),
                    away_team=match_data.get('away_team', {}).get('away_team_name', ''),
                    home_score=match_data.get('home_score', 0),
                    away_score=match_data.get('away_score', 0),
                    match_status=match_data.get('match_status', ''),
                    home_managers=[m.get('name', '') for m in match_data.get('home_team', {}).get('managers', [])],
                    away_managers=[m.get('name', '') for m in match_data.get('away_team', {}).get('managers', [])],
                    stadium=match_data.get('stadium', {}).get('name') if match_data.get('stadium') else None,
                    referee=match_data.get('referee', {}).get('name') if match_data.get('referee') else None
                )
                matches.append(match)
            
            logger.info(f"Found {len(matches)} matches for competition {competition_id}, season {season_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            return []
    
    def get_events(self, match_id: int) -> List[StatsBombEvent]:
        """
        Get all events for a specific match
        
        Args:
            match_id: StatsBomb match ID
            
        Returns:
            List of StatsBombEvent objects
        """
        try:
            url = f"{self.base_url}/events/{match_id}.json"
            response = self.session.get(url, timeout=60)  # Events can be large
            response.raise_for_status()
            
            events_data = response.json()
            events = []
            
            for event_data in events_data:
                # Parse location if available
                location = None
                if event_data.get('location'):
                    location = (event_data['location'][0], event_data['location'][1])
                
                event = StatsBombEvent(
                    id=event_data['id'],
                    index=event_data.get('index', 0),
                    period=event_data.get('period', 1),
                    timestamp=event_data.get('timestamp', ''),
                    minute=event_data.get('minute', 0),
                    second=event_data.get('second', 0),
                    type=event_data.get('type', {}).get('name', 'Unknown'),
                    possession=event_data.get('possession', 0),
                    possession_team=event_data.get('possession_team', {}).get('name', ''),
                    play_pattern=event_data.get('play_pattern', {}).get('name', ''),
                    team=event_data.get('team', {}).get('name', ''),
                    player=event_data.get('player', {}).get('name') if event_data.get('player') else None,
                    position=event_data.get('position', {}).get('name') if event_data.get('position') else None,
                    location=location,
                    duration=event_data.get('duration'),
                    under_pressure=event_data.get('under_pressure', False),
                    off_camera=event_data.get('off_camera', False)
                )
                events.append(event)
            
            logger.info(f"Loaded {len(events)} events for match {match_id}")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching events for match {match_id}: {e}")
            return []
    
    def get_shot_events(self, match_id: int) -> List[Dict]:
        """
        Extract shot events with detailed information
        
        Args:
            match_id: Match ID
            
        Returns:
            List of shot event dictionaries
        """
        events = self.get_events(match_id)
        shots = []
        
        for event in events:
            if event.type == 'Shot':
                # Get the raw event data for detailed shot info
                url = f"{self.base_url}/events/{match_id}.json"
                try:
                    response = self.session.get(url, timeout=30)
                    events_data = response.json()
                    
                    # Find the matching event
                    shot_data = next((e for e in events_data if e['id'] == event.id), None)
                    if shot_data and 'shot' in shot_data:
                        shot_details = shot_data['shot']
                        
                        shot_info = {
                            'id': event.id,
                            'match_id': match_id,
                            'minute': event.minute,
                            'second': event.second,
                            'team': event.team,
                            'player': event.player,
                            'position': event.position,
                            'location': event.location,
                            'under_pressure': event.under_pressure,
                            
                            # Shot-specific details
                            'statsbomb_xg': shot_details.get('statsbomb_xg', 0.0),
                            'end_location': shot_details.get('end_location', []),
                            'outcome': shot_details.get('outcome', {}).get('name', 'Unknown'),
                            'technique': shot_details.get('technique', {}).get('name', 'Unknown'),
                            'body_part': shot_details.get('body_part', {}).get('name', 'Unknown'),
                            'type': shot_details.get('type', {}).get('name', 'Open Play'),
                            'first_time': shot_details.get('first_time', False),
                            'deflected': shot_details.get('deflected', False),
                            'aerial_won': shot_details.get('aerial_won', False)
                        }
                        
                        shots.append(shot_info)
                        
                except Exception as e:
                    logger.warning(f"Error getting shot details for event {event.id}: {e}")
                    continue
        
        logger.info(f"Extracted {len(shots)} shots from match {match_id}")
        return shots
    
    def get_pass_events(self, match_id: int) -> List[Dict]:
        """
        Extract pass events with detailed information
        
        Args:
            match_id: Match ID
            
        Returns:
            List of pass event dictionaries
        """
        events = self.get_events(match_id)
        passes = []
        
        for event in events:
            if event.type == 'Pass':
                # Get detailed pass information
                url = f"{self.base_url}/events/{match_id}.json"
                try:
                    response = self.session.get(url, timeout=30)
                    events_data = response.json()
                    
                    # Find matching event
                    pass_data = next((e for e in events_data if e['id'] == event.id), None)
                    if pass_data and 'pass' in pass_data:
                        pass_details = pass_data['pass']
                        
                        pass_info = {
                            'id': event.id,
                            'match_id': match_id,
                            'minute': event.minute,
                            'second': event.second,
                            'team': event.team,
                            'player': event.player,
                            'position': event.position,
                            'start_location': event.location,
                            'under_pressure': event.under_pressure,
                            
                            # Pass-specific details
                            'end_location': pass_details.get('end_location', []),
                            'length': pass_details.get('length', 0.0),
                            'angle': pass_details.get('angle', 0.0),
                            'height': pass_details.get('height', {}).get('name', 'Ground Pass'),
                            'body_part': pass_details.get('body_part', {}).get('name', 'Right Foot'),
                            'type': pass_details.get('type', {}).get('name', 'Short'),
                            'outcome': pass_details.get('outcome', {}).get('name', 'Complete'),
                            'cross': pass_details.get('cross', False),
                            'switch': pass_details.get('switch', False),
                            'shot_assist': pass_details.get('shot_assist', False),
                            'goal_assist': pass_details.get('goal_assist', False),
                            'key_pass': 'key_pass_id' in pass_details
                        }
                        
                        passes.append(pass_info)
                        
                except Exception as e:
                    logger.warning(f"Error getting pass details for event {event.id}: {e}")
                    continue
        
        logger.info(f"Extracted {len(passes)} passes from match {match_id}")
        return passes
    
    def calculate_advanced_metrics(self, match_id: int) -> Dict:
        """
        Calculate advanced metrics from StatsBomb event data
        
        Args:
            match_id: Match ID
            
        Returns:
            Dictionary with advanced metrics
        """
        events = self.get_events(match_id)
        
        if not events:
            return {}
        
        # Get team names
        teams = list(set(e.team for e in events if e.team))
        if len(teams) != 2:
            logger.warning(f"Expected 2 teams, found {len(teams)} in match {match_id}")
            return {}
        
        home_team, away_team = teams[0], teams[1]
        
        # Initialize metrics
        metrics = {
            'match_id': match_id,
            'home_team': home_team,
            'away_team': away_team,
            'metrics': {}
        }
        
        # Calculate PPDA (Passes per Defensive Action)
        ppda = self._calculate_ppda(events, home_team, away_team)
        metrics['metrics']['ppda'] = ppda
        
        # Calculate field tilt (possession in attacking third)
        field_tilt = self._calculate_field_tilt(events, home_team, away_team)
        metrics['metrics']['field_tilt'] = field_tilt
        
        # Calculate passing accuracy by zone
        passing_accuracy = self._calculate_passing_accuracy_by_zone(events, home_team, away_team)
        metrics['metrics']['passing_accuracy'] = passing_accuracy
        
        # Calculate progressive actions
        progressive_actions = self._calculate_progressive_actions(events, home_team, away_team)
        metrics['metrics']['progressive_actions'] = progressive_actions
        
        return metrics
    
    def _calculate_ppda(self, events: List[StatsBombEvent], home_team: str, away_team: str) -> Dict:
        """
        Calculate Passes per Defensive Action (PPDA)
        
        PPDA = Opponent passes / (Team tackles + interceptions + fouls)
        """
        defensive_actions = ['Duel', 'Interception', 'Foul Committed', 'Block']
        
        home_passes = sum(1 for e in events if e.team == home_team and e.type == 'Pass')
        away_passes = sum(1 for e in events if e.team == away_team and e.type == 'Pass')
        
        home_def_actions = sum(1 for e in events if e.team == home_team and e.type in defensive_actions)
        away_def_actions = sum(1 for e in events if e.team == away_team and e.type in defensive_actions)
        
        home_ppda = away_passes / home_def_actions if home_def_actions > 0 else float('inf')
        away_ppda = home_passes / away_def_actions if away_def_actions > 0 else float('inf')
        
        return {
            home_team: home_ppda,
            away_team: away_ppda
        }
    
    def _calculate_field_tilt(self, events: List[StatsBombEvent], home_team: str, away_team: str) -> Dict:
        """
        Calculate field tilt (possession in attacking third)
        """
        attacking_third_threshold = 80  # StatsBomb field is 120 long
        
        home_attacking_actions = 0
        away_attacking_actions = 0
        home_total_actions = 0
        away_total_actions = 0
        
        for event in events:
            if event.location and event.type in ['Pass', 'Carry', 'Dribble']:
                x_coord = event.location[0]
                
                if event.team == home_team:
                    home_total_actions += 1
                    if x_coord >= attacking_third_threshold:
                        home_attacking_actions += 1
                elif event.team == away_team:
                    away_total_actions += 1
                    if x_coord <= (120 - attacking_third_threshold):  # Away team attacks in opposite direction
                        away_attacking_actions += 1
        
        home_tilt = home_attacking_actions / home_total_actions if home_total_actions > 0 else 0
        away_tilt = away_attacking_actions / away_total_actions if away_total_actions > 0 else 0
        
        return {
            home_team: home_tilt,
            away_team: away_tilt
        }
    
    def _calculate_passing_accuracy_by_zone(self, events: List[StatsBombEvent], 
                                          home_team: str, away_team: str) -> Dict:
        """
        Calculate passing accuracy by field zone
        """
        zones = {
            'defensive': (0, 40),
            'middle': (40, 80),
            'attacking': (80, 120)
        }
        
        accuracy = {
            home_team: {},
            away_team: {}
        }
        
        for team in [home_team, away_team]:
            for zone_name, (min_x, max_x) in zones.items():
                passes_in_zone = []
                
                for event in events:
                    if (event.team == team and event.type == 'Pass' and 
                        event.location and min_x <= event.location[0] <= max_x):
                        
                        # Determine if pass was successful
                        # In StatsBomb, incomplete passes have 'outcome' field
                        successful = not hasattr(event, 'outcome') or event.outcome != 'Incomplete'
                        passes_in_zone.append(successful)
                
                if passes_in_zone:
                    accuracy[team][zone_name] = sum(passes_in_zone) / len(passes_in_zone)
                else:
                    accuracy[team][zone_name] = 0.0
        
        return accuracy
    
    def _calculate_progressive_actions(self, events: List[StatsBombEvent], 
                                     home_team: str, away_team: str) -> Dict:
        """
        Calculate progressive passes and carries
        """
        progressive = {
            home_team: {'passes': 0, 'carries': 0},
            away_team: {'passes': 0, 'carries': 0}
        }
        
        for event in events:
            if not event.location:
                continue
                
            if event.type == 'Pass' and hasattr(event, 'end_location'):
                # Progressive pass: moves ball at least 30m toward goal OR 10m toward goal from attacking half
                start_x = event.location[0]
                end_x = event.end_location[0] if event.end_location else start_x
                
                progress = end_x - start_x  # Positive = toward goal
                
                is_progressive = (
                    progress >= 30 or  # 30m progress anywhere
                    (start_x >= 60 and progress >= 10)  # 10m progress from attacking half
                )
                
                if is_progressive and event.team in progressive:
                    progressive[event.team]['passes'] += 1
            
            elif event.type == 'Carry':
                # Similar logic for carries
                start_x = event.location[0]
                # Carry end location would need to be calculated from next event
                # Simplified for now
                if event.team in progressive:
                    progressive[event.team]['carries'] += 1
        
        return progressive
    
    def get_la_liga_matches(self, season: str = "2020-2021") -> List[StatsBombMatch]:
        """
        Get La Liga matches from StatsBomb open data
        
        Args:
            season: Season string
            
        Returns:
            List of matches
        """
        competitions = self.get_competitions()
        
        # Find La Liga competition
        la_liga = next((c for c in competitions 
                       if c.get('competition_name') == 'La Liga' and 
                          c.get('season_name') == season), None)
        
        if not la_liga:
            logger.warning(f"La Liga {season} not found in StatsBomb open data")
            return []
        
        return self.get_matches(la_liga['competition_id'], la_liga['season_id'])
    
    def export_match_data_for_ml(self, match_id: int, output_path: str) -> bool:
        """
        Export match data in format suitable for ML training
        
        Args:
            match_id: Match ID to export
            output_path: Path to save the data
            
        Returns:
            Success boolean
        """
        try:
            # Get all match data
            events = self.get_events(match_id)
            shots = self.get_shot_events(match_id)
            passes = self.get_pass_events(match_id)
            metrics = self.calculate_advanced_metrics(match_id)
            
            # Prepare for export
            match_data = {
                'match_id': match_id,
                'events_count': len(events),
                'shots': shots,
                'passes': passes,
                'advanced_metrics': metrics,
                'export_date': datetime.now().isoformat()
            }
            
            # Save to JSON
            with open(output_path, 'w') as f:
                json.dump(match_data, f, indent=2, default=str)
            
            logger.info(f"Match {match_id} data exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting match {match_id}: {e}")
            return False


# Utility functions
def get_available_competitions() -> List[Dict]:
    """Get list of available competitions in StatsBomb open data"""
    collector = StatsBombCollector()
    return collector.get_competitions()


def get_spanish_football_data() -> Dict:
    """
    Get Spanish football data from StatsBomb open data
    
    Returns:
        Dictionary with La Liga data
    """
    collector = StatsBombCollector()
    
    # Get La Liga matches (if available in open data)
    matches = collector.get_la_liga_matches("2020-2021")  # Adjust season as needed
    
    return {
        'competition': 'La Liga',
        'season': '2020-2021',
        'matches': matches,
        'match_count': len(matches),
        'collection_date': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    collector = StatsBombCollector()
    
    print("StatsBomb Collector - Example Usage")
    
    # Get available competitions
    competitions = collector.get_competitions()
    print(f"Available competitions: {len(competitions)}")
    
    if competitions:
        for comp in competitions[:3]:  # Show first 3
            print(f"- {comp.get('competition_name')} ({comp.get('season_name')})")
    
    # Note: Actual data collection would require specific competition/season IDs
    print("\nStatsBomb collector ready for use!")
    print("Use get_matches() and get_events() to collect detailed match data.")