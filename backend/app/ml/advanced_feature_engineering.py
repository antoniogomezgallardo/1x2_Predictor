"""
Advanced Feature Engineering - Integration of xG, xA, xT, PPDA and State-of-the-Art Metrics
Combines advanced statistics with existing features for enhanced prediction accuracy
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from ..database.models import (
    Team, Match, TeamStatistics, AdvancedTeamStatistics, 
    MatchAdvancedStatistics, PlayerAdvancedStatistics,
    MarketIntelligence, ExternalFactors
)

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """
    Advanced feature engineering system that combines:
    - Basic team statistics
    - Expected Goals (xG) and Expected Assists (xA)
    - Expected Threat (xT) metrics
    - Pressing metrics (PPDA)
    - Passing networks and possession metrics
    - Market intelligence
    - External factors (weather, injuries, motivation)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.feature_cache = {}
        
        # Feature weights for different metric types
        self.metric_weights = {
            'basic': 0.3,
            'expected_goals': 0.25,
            'expected_assists': 0.15,
            'expected_threat': 0.15,
            'pressing': 0.10,
            'market_intelligence': 0.08,
            'external_factors': 0.07
        }
    
    def create_advanced_features(
        self, 
        home_team_id: int, 
        away_team_id: int, 
        season: int,
        match_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Create comprehensive feature set for match prediction
        Combines all available advanced metrics
        """
        try:
            logger.info(f"Creating advanced features for teams {home_team_id} vs {away_team_id}")
            
            # Initialize feature dictionary
            features = {}
            
            # 1. Basic team statistics features
            basic_features = self._get_basic_team_features(home_team_id, away_team_id, season)
            features.update(basic_features)
            
            # 2. Advanced team statistics features
            advanced_features = self._get_advanced_team_features(home_team_id, away_team_id, season)
            features.update(advanced_features)
            
            # 3. Head-to-head advanced features
            h2h_features = self._get_h2h_advanced_features(home_team_id, away_team_id, season)
            features.update(h2h_features)
            
            # 4. Recent form features with advanced metrics
            form_features = self._get_recent_form_advanced_features(home_team_id, away_team_id, season)
            features.update(form_features)
            
            # 5. Market intelligence features
            if match_date:
                market_features = self._get_market_intelligence_features(home_team_id, away_team_id, match_date)
                features.update(market_features)
            
            # 6. External factors features
            if match_date:
                external_features = self._get_external_factors_features(home_team_id, away_team_id, match_date)
                features.update(external_features)
            
            # 7. Derived advanced features
            derived_features = self._calculate_derived_features(features)
            features.update(derived_features)
            
            # 8. Feature normalization and scaling
            normalized_features = self._normalize_features(features)
            
            logger.info(f"Generated {len(normalized_features)} advanced features")
            return normalized_features
            
        except Exception as e:
            logger.error(f"Error creating advanced features: {str(e)}")
            # Fallback to basic features
            return self._get_basic_team_features(home_team_id, away_team_id, season)
    
    def _get_basic_team_features(self, home_team_id: int, away_team_id: int, season: int) -> Dict[str, float]:
        """Get basic team statistics features"""
        try:
            # Get basic team statistics
            home_stats = self.db.query(TeamStatistics).filter(
                TeamStatistics.team_id == home_team_id,
                TeamStatistics.season == season
            ).first()
            
            away_stats = self.db.query(TeamStatistics).filter(
                TeamStatistics.team_id == away_team_id,
                TeamStatistics.season == season
            ).first()
            
            if not home_stats or not away_stats:
                logger.warning(f"Basic stats not found for teams {home_team_id}, {away_team_id}")
                return {}
            
            features = {
                # Home team basic features
                'home_points': home_stats.points or 0,
                'home_wins': home_stats.wins or 0,
                'home_draws': home_stats.draws or 0,
                'home_losses': home_stats.losses or 0,
                'home_goals_for': home_stats.goals_for or 0,
                'home_goals_against': home_stats.goals_against or 0,
                'home_matches_played': home_stats.matches_played or 1,
                
                # Away team basic features
                'away_points': away_stats.points or 0,
                'away_wins': away_stats.wins or 0,
                'away_draws': away_stats.draws or 0,
                'away_losses': away_stats.losses or 0,
                'away_goals_for': away_stats.goals_for or 0,
                'away_goals_against': away_stats.goals_against or 0,
                'away_matches_played': away_stats.matches_played or 1,
                
                # Derived basic features
                'home_points_per_game': home_stats.points / max(home_stats.matches_played, 1),
                'away_points_per_game': away_stats.points / max(away_stats.matches_played, 1),
                'home_goal_difference': (home_stats.goals_for or 0) - (home_stats.goals_against or 0),
                'away_goal_difference': (away_stats.goals_for or 0) - (away_stats.goals_against or 0),
                'points_difference': (home_stats.points or 0) - (away_stats.points or 0)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting basic team features: {str(e)}")
            return {}
    
    def _get_advanced_team_features(self, home_team_id: int, away_team_id: int, season: int) -> Dict[str, float]:
        """Get advanced team statistics features (xG, xA, xT, PPDA, etc.)"""
        try:
            # Get advanced team statistics
            home_advanced = self.db.query(AdvancedTeamStatistics).filter(
                AdvancedTeamStatistics.team_id == home_team_id,
                AdvancedTeamStatistics.season == season
            ).first()
            
            away_advanced = self.db.query(AdvancedTeamStatistics).filter(
                AdvancedTeamStatistics.team_id == away_team_id,
                AdvancedTeamStatistics.season == season
            ).first()
            
            if not home_advanced or not away_advanced:
                logger.warning(f"Advanced stats not found for teams {home_team_id}, {away_team_id}")
                return {}
            
            features = {
                # Expected Goals Features
                'home_xg_for': home_advanced.xg_for or 0,
                'home_xg_against': home_advanced.xg_against or 0,
                'home_xg_difference': home_advanced.xg_difference or 0,
                'home_xg_per_match': home_advanced.xg_per_match or 0,
                'home_xg_performance': home_advanced.xg_performance or 1.0,
                
                'away_xg_for': away_advanced.xg_for or 0,
                'away_xg_against': away_advanced.xg_against or 0,
                'away_xg_difference': away_advanced.xg_difference or 0,
                'away_xg_per_match': away_advanced.xg_per_match or 0,
                'away_xg_performance': away_advanced.xg_performance or 1.0,
                
                # Expected Assists Features
                'home_xa_total': home_advanced.xa_total or 0,
                'home_xa_per_match': home_advanced.xa_per_match or 0,
                'away_xa_total': away_advanced.xa_total or 0,
                'away_xa_per_match': away_advanced.xa_per_match or 0,
                
                # Expected Threat Features
                'home_xt_total': home_advanced.xt_total or 0,
                'home_xt_per_possession': home_advanced.xt_per_possession or 0,
                'away_xt_total': away_advanced.xt_total or 0,
                'away_xt_per_possession': away_advanced.xt_per_possession or 0,
                
                # Pressing Features (PPDA)
                'home_ppda_own': home_advanced.ppda_own or 10.0,
                'home_ppda_allowed': home_advanced.ppda_allowed or 10.0,
                'home_pressing_intensity': home_advanced.pressing_intensity or 0.5,
                'away_ppda_own': away_advanced.ppda_own or 10.0,
                'away_ppda_allowed': away_advanced.ppda_allowed or 10.0,
                'away_pressing_intensity': away_advanced.pressing_intensity or 0.5,
                
                # Possession Features
                'home_possession_pct': home_advanced.possession_pct or 50.0,
                'away_possession_pct': away_advanced.possession_pct or 50.0,
                'home_pass_completion_pct': home_advanced.pass_completion_pct or 80.0,
                'away_pass_completion_pct': away_advanced.pass_completion_pct or 80.0,
                
                # Attacking Features
                'home_shots_per_match': home_advanced.shots_per_match or 10.0,
                'home_shots_on_target_pct': home_advanced.shots_on_target_pct or 35.0,
                'away_shots_per_match': away_advanced.shots_per_match or 10.0,
                'away_shots_on_target_pct': away_advanced.shots_on_target_pct or 35.0,
                
                # Defensive Features
                'home_tackles_per_match': home_advanced.tackles_per_match or 15.0,
                'home_interceptions_per_match': home_advanced.interceptions_per_match or 10.0,
                'away_tackles_per_match': away_advanced.tackles_per_match or 15.0,
                'away_interceptions_per_match': away_advanced.interceptions_per_match or 10.0,
                
                # Form Features
                'home_momentum_score': home_advanced.momentum_score or 0.5,
                'away_momentum_score': away_advanced.momentum_score or 0.5,
                'home_recent_form_xg': home_advanced.recent_form_xg or 1.0,
                'away_recent_form_xg': away_advanced.recent_form_xg or 1.0
            }
            
            # Derived advanced features
            features.update({
                'xg_difference_gap': features['home_xg_difference'] - features['away_xg_difference'],
                'xg_performance_ratio': features['home_xg_performance'] / max(features['away_xg_performance'], 0.1),
                'pressing_intensity_gap': features['home_pressing_intensity'] - features['away_pressing_intensity'],
                'possession_balance': features['home_possession_pct'] - features['away_possession_pct'],
                'momentum_difference': features['home_momentum_score'] - features['away_momentum_score']
            })
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting advanced team features: {str(e)}")
            return {}
    
    def _get_h2h_advanced_features(self, home_team_id: int, away_team_id: int, season: int) -> Dict[str, float]:
        """Get head-to-head features based on recent advanced statistics"""
        try:
            # Get recent matches between these teams
            recent_h2h = self.db.query(Match).filter(
                ((Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id)) |
                ((Match.home_team_id == away_team_id) & (Match.away_team_id == home_team_id)),
                Match.season >= season - 2,  # Last 2 seasons
                Match.result.isnot(None)
            ).order_by(Match.match_date.desc()).limit(5).all()
            
            if not recent_h2h:
                return {
                    'h2h_home_xg_avg': 1.0,
                    'h2h_away_xg_avg': 1.0,
                    'h2h_home_wins': 0,
                    'h2h_draws': 0,
                    'h2h_away_wins': 0,
                    'h2h_matches_count': 0
                }
            
            h2h_stats = {'xg_home': [], 'xg_away': [], 'results': []}
            
            for match in recent_h2h:
                # Get advanced match statistics
                advanced_match = self.db.query(MatchAdvancedStatistics).filter(
                    MatchAdvancedStatistics.match_id == match.id
                ).first()
                
                if advanced_match:
                    if match.home_team_id == home_team_id:
                        h2h_stats['xg_home'].append(advanced_match.home_xg or 1.0)
                        h2h_stats['xg_away'].append(advanced_match.away_xg or 1.0)
                        h2h_stats['results'].append(match.result)
                    else:
                        h2h_stats['xg_home'].append(advanced_match.away_xg or 1.0)
                        h2h_stats['xg_away'].append(advanced_match.home_xg or 1.0)
                        h2h_stats['results'].append('2' if match.result == '1' else ('1' if match.result == '2' else 'X'))
            
            # Calculate H2H features
            features = {
                'h2h_home_xg_avg': np.mean(h2h_stats['xg_home']) if h2h_stats['xg_home'] else 1.0,
                'h2h_away_xg_avg': np.mean(h2h_stats['xg_away']) if h2h_stats['xg_away'] else 1.0,
                'h2h_home_wins': h2h_stats['results'].count('1'),
                'h2h_draws': h2h_stats['results'].count('X'),
                'h2h_away_wins': h2h_stats['results'].count('2'),
                'h2h_matches_count': len(recent_h2h)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting H2H advanced features: {str(e)}")
            return {}
    
    def _get_recent_form_advanced_features(self, home_team_id: int, away_team_id: int, season: int) -> Dict[str, float]:
        """Get recent form features using advanced metrics"""
        try:
            features = {}
            
            for team_id, prefix in [(home_team_id, 'home'), (away_team_id, 'away')]:
                # Get last 5 matches
                recent_matches = self.db.query(Match).filter(
                    (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
                    Match.season == season,
                    Match.result.isnot(None)
                ).order_by(Match.match_date.desc()).limit(5).all()
                
                if not recent_matches:
                    # Default values
                    features.update({
                        f'{prefix}_form_xg_avg': 1.0,
                        f'{prefix}_form_xa_avg': 0.5,
                        f'{prefix}_form_ppda_avg': 10.0,
                        f'{prefix}_form_wins': 0,
                        f'{prefix}_form_points': 0
                    })
                    continue
                
                xg_values, xa_values, ppda_values = [], [], []
                wins, points = 0, 0
                
                for match in recent_matches:
                    # Get advanced statistics
                    advanced_match = self.db.query(MatchAdvancedStatistics).filter(
                        MatchAdvancedStatistics.match_id == match.id
                    ).first()
                    
                    if advanced_match:
                        if match.home_team_id == team_id:
                            xg_values.append(advanced_match.home_xg or 1.0)
                            xa_values.append(advanced_match.home_xa or 0.5)
                            ppda_values.append(advanced_match.home_ppda or 10.0)
                            if match.result == '1':
                                wins += 1
                                points += 3
                            elif match.result == 'X':
                                points += 1
                        else:
                            xg_values.append(advanced_match.away_xg or 1.0)
                            xa_values.append(advanced_match.away_xa or 0.5)
                            ppda_values.append(advanced_match.away_ppda or 10.0)
                            if match.result == '2':
                                wins += 1
                                points += 3
                            elif match.result == 'X':
                                points += 1
                
                features.update({
                    f'{prefix}_form_xg_avg': np.mean(xg_values) if xg_values else 1.0,
                    f'{prefix}_form_xa_avg': np.mean(xa_values) if xa_values else 0.5,
                    f'{prefix}_form_ppda_avg': np.mean(ppda_values) if ppda_values else 10.0,
                    f'{prefix}_form_wins': wins,
                    f'{prefix}_form_points': points
                })
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting recent form features: {str(e)}")
            return {}
    
    def _get_market_intelligence_features(self, home_team_id: int, away_team_id: int, match_date: datetime) -> Dict[str, float]:
        """Get market intelligence features from betting data"""
        try:
            # Find upcoming match for market intelligence
            upcoming_match = self.db.query(Match).filter(
                Match.home_team_id == home_team_id,
                Match.away_team_id == away_team_id,
                Match.match_date >= match_date - timedelta(days=1),
                Match.match_date <= match_date + timedelta(days=1)
            ).first()
            
            if not upcoming_match:
                return {}
            
            # Get market intelligence
            market_intel = self.db.query(MarketIntelligence).filter(
                MarketIntelligence.match_id == upcoming_match.id
            ).first()
            
            if not market_intel:
                return {}
            
            features = {
                'market_prob_home': market_intel.market_prob_home or 0.33,
                'market_prob_draw': market_intel.market_prob_draw or 0.33,
                'market_prob_away': market_intel.market_prob_away or 0.33,
                'market_overround': market_intel.market_overround or 0.05,
                'home_odds_movement': market_intel.home_odds_movement or 0.0,
                'draw_odds_movement': market_intel.draw_odds_movement or 0.0,
                'away_odds_movement': market_intel.away_odds_movement or 0.0,
                'sharp_money_home': market_intel.sharp_money_home or 0.33,
                'sharp_money_away': market_intel.sharp_money_away or 0.33,
                'value_percentage': market_intel.value_percentage or 0.0,
                'market_efficiency_score': market_intel.market_efficiency_score or 0.8
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting market intelligence features: {str(e)}")
            return {}
    
    def _get_external_factors_features(self, home_team_id: int, away_team_id: int, match_date: datetime) -> Dict[str, float]:
        """Get external factors features (weather, injuries, motivation)"""
        try:
            # Find upcoming match for external factors
            upcoming_match = self.db.query(Match).filter(
                Match.home_team_id == home_team_id,
                Match.away_team_id == away_team_id,
                Match.match_date >= match_date - timedelta(days=1),
                Match.match_date <= match_date + timedelta(days=1)
            ).first()
            
            if not upcoming_match:
                return {}
            
            # Get external factors
            external = self.db.query(ExternalFactors).filter(
                ExternalFactors.match_id == upcoming_match.id
            ).first()
            
            if not external:
                return {}
            
            features = {
                'temperature': external.temperature or 20.0,
                'humidity': external.humidity or 60.0,
                'wind_speed': external.wind_speed or 10.0,
                'weather_impact_score': external.weather_impact_score or 0.1,
                'home_team_motivation': external.home_team_motivation or 0.7,
                'away_team_motivation': external.away_team_motivation or 0.7,
                'home_days_rest': external.home_days_rest or 5,
                'away_days_rest': external.away_days_rest or 5,
                'fatigue_factor_home': external.fatigue_factor_home or 1.0,
                'fatigue_factor_away': external.fatigue_factor_away or 1.0,
                'rivalry_intensity': external.rivalry_intensity or 0.3,
                'stakes_importance': external.stakes_importance or 0.5,
                'home_fan_sentiment': external.home_fan_sentiment or 0.7,
                'away_fan_sentiment': external.away_fan_sentiment or 0.7,
                'travel_distance': external.travel_distance or 200.0
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting external factors features: {str(e)}")
            return {}
    
    def _calculate_derived_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived features from existing ones"""
        try:
            derived = {}
            
            # Advanced ratios and differences
            if 'home_xg_per_match' in features and 'away_xg_per_match' in features:
                derived['xg_attack_ratio'] = features['home_xg_per_match'] / max(features['away_xg_per_match'], 0.1)
            
            if 'home_xg_against' in features and 'away_xg_against' in features:
                derived['xg_defense_ratio'] = features['away_xg_against'] / max(features['home_xg_against'], 0.1)
            
            if 'home_ppda_own' in features and 'away_ppda_own' in features:
                derived['pressing_dominance'] = (1/max(features['home_ppda_own'], 1)) - (1/max(features['away_ppda_own'], 1))
            
            if 'home_momentum_score' in features and 'away_momentum_score' in features:
                derived['momentum_advantage'] = features['home_momentum_score'] - features['away_momentum_score']
            
            # Market vs model discrepancy
            if 'market_prob_home' in features and 'home_xg_difference' in features:
                model_prob_home = max(0.1, min(0.8, 0.33 + features['home_xg_difference'] * 0.1))
                derived['market_model_discrepancy_home'] = features['market_prob_home'] - model_prob_home
            
            # Composite scores
            attack_strength = 0
            defense_strength = 0
            
            if 'home_xg_per_match' in features:
                attack_strength += features['home_xg_per_match'] * 0.4
            if 'home_xa_per_match' in features:
                attack_strength += features['home_xa_per_match'] * 0.3
            if 'home_shots_per_match' in features:
                attack_strength += (features['home_shots_per_match'] / 20) * 0.3
                
            derived['home_attack_strength'] = attack_strength
            
            if 'home_xg_against' in features:
                defense_strength += (2.0 - features['home_xg_against']) * 0.5
            if 'home_tackles_per_match' in features:
                defense_strength += (features['home_tackles_per_match'] / 20) * 0.3
            if 'home_interceptions_per_match' in features:
                defense_strength += (features['home_interceptions_per_match'] / 15) * 0.2
                
            derived['home_defense_strength'] = defense_strength
            
            return derived
            
        except Exception as e:
            logger.error(f"Error calculating derived features: {str(e)}")
            return {}
    
    def _normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Normalize features to appropriate ranges"""
        try:
            normalized = {}
            
            # Define normalization ranges for different feature types
            normalization_rules = {
                # Percentages (0-100 -> 0-1)
                'possession_pct': (0, 100),
                'pass_completion_pct': (0, 100),
                'shots_on_target_pct': (0, 100),
                'humidity': (0, 100),
                
                # Probabilities (already 0-1)
                'market_prob_': (0, 1),
                'xg_performance': (0, 3),
                'momentum_score': (0, 1),
                'team_motivation': (0, 1),
                'fatigue_factor_': (0, 1),
                'fan_sentiment': (0, 1),
                
                # xG values (typically 0-4 per match)
                'xg_': (0, 4),
                'xa_': (0, 3),
                'xt_': (0, 5),
                
                # PPDA (typically 5-20)
                'ppda_': (5, 20),
                
                # Counts that need scaling
                'shots_per_match': (0, 25),
                'tackles_per_match': (0, 30),
                'interceptions_per_match': (0, 25),
                
                # Temperature
                'temperature': (-10, 40),
                'wind_speed': (0, 50),
                
                # Days rest
                'days_rest': (1, 14),
                
                # Distance
                'travel_distance': (0, 1000)
            }
            
            for feature_name, value in features.items():
                # Find applicable normalization rule
                norm_range = None
                for rule_key, rule_range in normalization_rules.items():
                    if rule_key in feature_name:
                        norm_range = rule_range
                        break
                
                if norm_range:
                    min_val, max_val = norm_range
                    normalized_value = (value - min_val) / max(max_val - min_val, 1)
                    normalized[feature_name] = max(0, min(1, normalized_value))
                else:
                    # Default normalization for unknown features
                    if value > 100:  # Large numbers, likely need scaling
                        normalized[feature_name] = min(1, value / 1000)
                    elif value > 10:  # Medium numbers
                        normalized[feature_name] = min(1, value / 50)
                    else:
                        normalized[feature_name] = value
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing features: {str(e)}")
            return features
    
    def get_feature_importance_mapping(self) -> Dict[str, str]:
        """Get mapping of features to their importance categories"""
        return {
            # Critical features (highest impact)
            'xg_difference_gap': 'critical',
            'home_xg_difference': 'critical', 
            'away_xg_difference': 'critical',
            'momentum_difference': 'critical',
            'points_difference': 'critical',
            
            # High importance features
            'home_xg_performance': 'high',
            'away_xg_performance': 'high',
            'xg_attack_ratio': 'high',
            'pressing_dominance': 'high',
            'home_attack_strength': 'high',
            'home_defense_strength': 'high',
            
            # Medium importance features
            'home_xa_per_match': 'medium',
            'away_xa_per_match': 'medium',
            'home_possession_pct': 'medium',
            'away_possession_pct': 'medium',
            'market_prob_home': 'medium',
            'market_prob_away': 'medium',
            
            # Lower importance features
            'home_team_motivation': 'low',
            'away_team_motivation': 'low',
            'weather_impact_score': 'low',
            'rivalry_intensity': 'low',
            'travel_distance': 'low'
        }
    
    def get_feature_names(self) -> List[str]:
        """Get list of all possible feature names"""
        # This would return all possible feature names that can be generated
        # Used for model training and consistency
        basic_features = [
            'home_points', 'away_points', 'home_wins', 'away_wins',
            'home_draws', 'away_draws', 'home_losses', 'away_losses',
            'home_goals_for', 'away_goals_for', 'home_goals_against', 'away_goals_against',
            'home_points_per_game', 'away_points_per_game', 'points_difference'
        ]
        
        advanced_features = [
            'home_xg_for', 'away_xg_for', 'home_xg_against', 'away_xg_against',
            'home_xg_difference', 'away_xg_difference', 'home_xg_per_match', 'away_xg_per_match',
            'home_xg_performance', 'away_xg_performance', 'home_xa_total', 'away_xa_total',
            'home_xa_per_match', 'away_xa_per_match', 'home_xt_total', 'away_xt_total',
            'home_ppda_own', 'away_ppda_own', 'home_pressing_intensity', 'away_pressing_intensity',
            'home_possession_pct', 'away_possession_pct', 'home_momentum_score', 'away_momentum_score'
        ]
        
        derived_features = [
            'xg_difference_gap', 'xg_performance_ratio', 'pressing_dominance', 
            'momentum_advantage', 'home_attack_strength', 'home_defense_strength'
        ]
        
        return basic_features + advanced_features + derived_features


def create_training_features_from_matches(db: Session, matches: List[Match]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Create training feature matrix from a list of matches
    """
    try:
        engineer = AdvancedFeatureEngineer(db)
        
        X = []
        y = []
        feature_names = None
        
        for match in matches:
            if not match.result or not match.home_team_id or not match.away_team_id:
                continue
                
            # Create features for this match
            features = engineer.create_advanced_features(
                match.home_team_id, 
                match.away_team_id, 
                match.season,
                match.match_date
            )
            
            if not features:
                continue
            
            # Set feature names from first match
            if feature_names is None:
                feature_names = sorted(features.keys())
            
            # Create feature vector
            feature_vector = [features.get(name, 0.0) for name in feature_names]
            X.append(feature_vector)
            
            # Create target (result)
            if match.result == '1':
                y.append(0)  # Home win
            elif match.result == 'X':
                y.append(1)  # Draw
            else:  # '2'
                y.append(2)  # Away win
        
        if not X:
            logger.error("No valid training data created")
            return np.array([]), np.array([]), []
        
        logger.info(f"Created training data: {len(X)} samples, {len(feature_names)} features")
        return np.array(X), np.array(y), feature_names
        
    except Exception as e:
        logger.error(f"Error creating training features: {str(e)}")
        return np.array([]), np.array([]), []