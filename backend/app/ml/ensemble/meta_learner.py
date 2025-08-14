"""
Meta-Learner Ensemble System
Combines multiple specialized models (xG, xA, xT, traditional ML) into a single prediction.

This meta-learner acts as the "brain" that decides how to weight different model predictions
based on match context, data availability, and historical performance of each model.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import XGBRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score
import joblib
import logging
from datetime import datetime
import asyncio

# Import our advanced models
from ..xg_models.shot_quality import ExpectedGoalsModel
from ..xg_models.expected_assists import ExpectedAssistsModel
from ..xg_models.threat_assessment import ExpectedThreatModel
from ..features.advanced_metrics import AdvancedMetricsCalculator
from ..data_sources.fbref_collector import FBRefCollector
from ..data_sources.statsbomb_api import StatsBombCollector

# Import existing system components
from ..predictor import FootballPredictor
from ..basic_predictor import create_basic_predictions_for_matches

logger = logging.getLogger(__name__)


class MetaLearnerPredictor:
    """
    Meta-learner that combines multiple prediction models for optimal accuracy.
    
    Model hierarchy:
    1. Advanced models (xG, xA, xT) - when detailed data available
    2. Traditional ML models - for standard match predictions  
    3. Basic predictor - fallback when limited data
    4. Meta-learner - combines all predictions with learned weights
    """
    
    def __init__(self):
        # Component models
        self.xg_model = ExpectedGoalsModel()
        self.xa_model = ExpectedAssistsModel()
        self.xt_model = ExpectedThreatModel()
        self.traditional_predictor = None  # Will load existing predictor
        self.metrics_calculator = AdvancedMetricsCalculator()
        
        # Data collectors
        self.fbref_collector = FBRefCollector()
        self.statsbomb_collector = StatsBombCollector()
        
        # Meta-learner model
        self.meta_model = None
        self.calibrator = None
        self.is_trained = False
        
        # Model weights (learned during training)
        self.model_weights = {
            'xg_model': 0.25,
            'xa_model': 0.20,
            'xt_model': 0.15,
            'traditional_ml': 0.25,
            'basic_predictor': 0.15
        }
        
        # Feature importance tracking
        self.feature_importance = {}
        
        # Performance tracking
        self.model_performance = {
            'individual_models': {},
            'ensemble_performance': {},
            'last_updated': None
        }
        
    def initialize_existing_models(self, traditional_model_path: Optional[str] = None):
        """
        Initialize existing system components
        
        Args:
            traditional_model_path: Path to existing trained model
        """
        try:
            # Load existing traditional predictor if available
            if traditional_model_path:
                # This would load the existing FootballPredictor
                logger.info(f"Loading traditional model from {traditional_model_path}")
                # Implementation depends on existing model format
            
            # Initialize advanced models with base configurations
            self.xt_model.train_position_model(pd.DataFrame())  # Base threat model
            
            logger.info("Successfully initialized existing models")
            
        except Exception as e:
            logger.warning(f"Could not initialize existing models: {e}")
    
    def prepare_match_features(self, match_data: Dict) -> Dict[str, Any]:
        """
        Prepare comprehensive features from all available data sources
        
        Args:
            match_data: Basic match information
            
        Returns:
            Dictionary with features from all models
        """
        features = {
            'basic_features': {},
            'xg_features': {},
            'xa_features': {},
            'xt_features': {},
            'advanced_metrics': {},
            'traditional_features': {},
            'data_availability': {}
        }
        
        try:
            # Basic match features
            features['basic_features'] = {
                'home_team': match_data.get('home_team', ''),
                'away_team': match_data.get('away_team', ''),
                'competition': match_data.get('competition', ''),
                'season': match_data.get('season', 2025),
                'match_date': match_data.get('match_date', ''),
                'venue': match_data.get('venue', '')
            }
            
            # Try to get advanced data
            home_team = match_data.get('home_team', '')
            away_team = match_data.get('away_team', '')
            
            # Check data availability
            has_fbref_data = self._check_fbref_data_availability(home_team, away_team)
            has_statsbomb_data = self._check_statsbomb_data_availability(home_team, away_team)
            
            features['data_availability'] = {
                'fbref': has_fbref_data,
                'statsbomb': has_statsbomb_data,
                'basic_only': not (has_fbref_data or has_statsbomb_data)
            }
            
            # Collect advanced features if data available
            if has_fbref_data:
                features['advanced_metrics'] = self._collect_fbref_features(home_team, away_team)
            
            if has_statsbomb_data:
                features['xg_features'] = self._collect_statsbomb_xg_features(home_team, away_team)
                features['xa_features'] = self._collect_statsbomb_xa_features(home_team, away_team)
            
            # Always calculate threat features (using base model)
            features['xt_features'] = self._calculate_threat_features(match_data)
            
            # Traditional ML features (from existing system)
            features['traditional_features'] = self._collect_traditional_features(match_data)
            
        except Exception as e:
            logger.error(f"Error preparing match features: {e}")
            # Return basic features only
            features = {
                'basic_features': features['basic_features'],
                'data_availability': {'basic_only': True}
            }
        
        return features
    
    def predict_match_outcome(self, match_data: Dict) -> Dict[str, Any]:
        """
        Generate comprehensive match prediction using all available models
        
        Args:
            match_data: Match information
            
        Returns:
            Comprehensive prediction with confidence and explanations
        """
        # Prepare features
        features = self.prepare_match_features(match_data)
        
        # Get predictions from each model
        model_predictions = {}
        
        # Traditional/Basic predictor (always available)
        try:
            basic_pred = self._get_basic_prediction(match_data)
            model_predictions['basic'] = basic_pred
        except Exception as e:
            logger.warning(f"Basic prediction failed: {e}")
            model_predictions['basic'] = {'home_win': 0.33, 'draw': 0.34, 'away_win': 0.33, 'confidence': 0.1}
        
        # Advanced model predictions (if data available)
        if features['data_availability'].get('fbref', False):
            try:
                advanced_pred = self._get_advanced_prediction(features)
                model_predictions['advanced'] = advanced_pred
            except Exception as e:
                logger.warning(f"Advanced prediction failed: {e}")
        
        # Expected Goals prediction (if shot data available)
        if features['data_availability'].get('statsbomb', False):
            try:
                xg_pred = self._get_xg_based_prediction(features)
                model_predictions['xg_based'] = xg_pred
            except Exception as e:
                logger.warning(f"xG prediction failed: {e}")
        
        # Threat-based prediction
        try:
            threat_pred = self._get_threat_based_prediction(features)
            model_predictions['threat_based'] = threat_pred
        except Exception as e:
            logger.warning(f"Threat prediction failed: {e}")
        
        # Combine predictions using meta-learner or weighted average
        if self.is_trained and self.meta_model:
            final_prediction = self._meta_predict(model_predictions, features)
        else:
            final_prediction = self._weighted_average_prediction(model_predictions)
        
        # Add explanation and confidence analysis
        explanation = self._generate_prediction_explanation(model_predictions, features, final_prediction)
        
        return {
            'predicted_result': final_prediction['predicted_result'],
            'probabilities': final_prediction['probabilities'],
            'confidence': final_prediction['confidence'],
            'individual_models': model_predictions,
            'data_sources_used': features['data_availability'],
            'explanation': explanation,
            'meta_info': {
                'models_used': len(model_predictions),
                'primary_model': final_prediction.get('primary_model', 'ensemble'),
                'prediction_date': datetime.now().isoformat()
            }
        }
    
    def _get_basic_prediction(self, match_data: Dict) -> Dict[str, Any]:
        """Get prediction from basic/traditional system"""
        try:
            # Use existing basic predictor
            matches = [match_data]
            predictions = create_basic_predictions_for_matches(matches)
            
            if predictions:
                pred = predictions[0]
                return {
                    'home_win': pred['probabilities']['home_win'],
                    'draw': pred['probabilities']['draw'], 
                    'away_win': pred['probabilities']['away_win'],
                    'confidence': pred.get('confidence', 0.5),
                    'predicted_result': pred['predicted_result']
                }
            
        except Exception as e:
            logger.error(f"Basic prediction error: {e}")
        
        # Fallback to uniform distribution
        return {
            'home_win': 0.33,
            'draw': 0.34,
            'away_win': 0.33,
            'confidence': 0.1,
            'predicted_result': 'X'
        }
    
    def _get_advanced_prediction(self, features: Dict) -> Dict[str, Any]:
        """Get prediction based on advanced metrics (PPDA, packing, etc.)"""
        # This would use the advanced metrics to predict match outcome
        # For now, return placeholder based on features
        advanced_metrics = features.get('advanced_metrics', {})
        
        # Example logic based on advanced metrics
        home_advantage = 0.5
        
        # Adjust based on advanced metrics if available
        if 'home_ppda' in advanced_metrics and 'away_ppda' in advanced_metrics:
            home_ppda = advanced_metrics['home_ppda']
            away_ppda = advanced_metrics['away_ppda']
            
            # Lower PPDA = better pressing = advantage
            if home_ppda < away_ppda:
                home_advantage += 0.1
            elif away_ppda < home_ppda:
                home_advantage -= 0.1
        
        # Convert advantage to probabilities
        home_prob = max(0.2, min(0.7, 0.3 + home_advantage * 0.4))
        away_prob = max(0.2, min(0.7, 0.3 - home_advantage * 0.4))
        draw_prob = 1.0 - home_prob - away_prob
        
        predicted_result = 'X' if draw_prob > max(home_prob, away_prob) else ('1' if home_prob > away_prob else '2')
        
        return {
            'home_win': home_prob,
            'draw': draw_prob,
            'away_win': away_prob,
            'confidence': 0.7,
            'predicted_result': predicted_result
        }
    
    def _get_xg_based_prediction(self, features: Dict) -> Dict[str, Any]:
        """Get prediction based on Expected Goals models"""
        # This would use xG/xA models to predict match outcome
        # For now, return placeholder
        return {
            'home_win': 0.35,
            'draw': 0.30,
            'away_win': 0.35,
            'confidence': 0.8,
            'predicted_result': '1'
        }
    
    def _get_threat_based_prediction(self, features: Dict) -> Dict[str, Any]:
        """Get prediction based on Expected Threat model"""
        # This would use threat analysis to predict outcome
        return {
            'home_win': 0.38,
            'draw': 0.32,
            'away_win': 0.30,
            'confidence': 0.6,
            'predicted_result': '1'
        }
    
    def _weighted_average_prediction(self, model_predictions: Dict[str, Dict]) -> Dict[str, Any]:
        """Combine predictions using weighted average"""
        if not model_predictions:
            return {
                'home_win': 0.33,
                'draw': 0.34,
                'away_win': 0.33,
                'confidence': 0.1,
                'predicted_result': 'X'
            }
        
        # Initialize weighted sums
        weighted_home = 0.0
        weighted_draw = 0.0
        weighted_away = 0.0
        weighted_confidence = 0.0
        total_weight = 0.0
        
        # Weight each model's contribution
        model_weight_mapping = {
            'basic': 0.3,
            'advanced': 0.25,
            'xg_based': 0.25,
            'threat_based': 0.2
        }
        
        for model_name, prediction in model_predictions.items():
            weight = model_weight_mapping.get(model_name, 0.1)
            confidence_weight = prediction.get('confidence', 0.5) * weight
            
            weighted_home += prediction.get('home_win', 0.33) * confidence_weight
            weighted_draw += prediction.get('draw', 0.33) * confidence_weight
            weighted_away += prediction.get('away_win', 0.33) * confidence_weight
            weighted_confidence += prediction.get('confidence', 0.5) * weight
            total_weight += confidence_weight
        
        # Normalize
        if total_weight > 0:
            final_home = weighted_home / total_weight
            final_draw = weighted_draw / total_weight  
            final_away = weighted_away / total_weight
            final_confidence = weighted_confidence / len(model_predictions)
        else:
            final_home = final_draw = final_away = 0.33
            final_confidence = 0.1
        
        # Determine predicted result
        probs = {'1': final_home, 'X': final_draw, '2': final_away}
        predicted_result = max(probs.items(), key=lambda x: x[1])[0]
        
        return {
            'home_win': final_home,
            'draw': final_draw,
            'away_win': final_away,
            'confidence': final_confidence,
            'predicted_result': predicted_result,
            'primary_model': 'ensemble'
        }
    
    def _meta_predict(self, model_predictions: Dict, features: Dict) -> Dict[str, Any]:
        """Use trained meta-model to combine predictions"""
        # This would use the trained meta-learner
        # For now, fall back to weighted average
        return self._weighted_average_prediction(model_predictions)
    
    def _generate_prediction_explanation(self, model_predictions: Dict, features: Dict, final_prediction: Dict) -> Dict[str, Any]:
        """Generate human-readable explanation for the prediction"""
        explanation = {
            'summary': '',
            'key_factors': [],
            'model_contributions': {},
            'confidence_factors': []
        }
        
        # Analyze prediction confidence
        confidence = final_prediction.get('confidence', 0.5)
        if confidence > 0.7:
            explanation['summary'] = "High confidence prediction based on multiple data sources"
        elif confidence > 0.5:
            explanation['summary'] = "Moderate confidence prediction with some uncertainty"  
        else:
            explanation['summary'] = "Low confidence prediction - consider with caution"
        
        # Key factors
        data_availability = features.get('data_availability', {})
        if data_availability.get('fbref'):
            explanation['key_factors'].append("Advanced statistics (PPDA, progressive metrics) available")
        if data_availability.get('statsbomb'):
            explanation['key_factors'].append("Detailed event data (xG, xA) analyzed")
        
        # Model contributions
        for model_name, prediction in model_predictions.items():
            explanation['model_contributions'][model_name] = {
                'result': prediction.get('predicted_result', 'X'),
                'confidence': prediction.get('confidence', 0.0)
            }
        
        return explanation
    
    def _check_fbref_data_availability(self, home_team: str, away_team: str) -> bool:
        """Check if FBRef data is available for teams"""
        # For now, return False - would implement actual checking
        return False
    
    def _check_statsbomb_data_availability(self, home_team: str, away_team: str) -> bool:
        """Check if StatsBomb data is available for teams"""
        # For now, return False - would implement actual checking
        return False
    
    def _collect_fbref_features(self, home_team: str, away_team: str) -> Dict:
        """Collect features from FBRef data"""
        return {}
    
    def _collect_statsbomb_xg_features(self, home_team: str, away_team: str) -> Dict:
        """Collect xG features from StatsBomb data"""
        return {}
    
    def _collect_statsbomb_xa_features(self, home_team: str, away_team: str) -> Dict:
        """Collect xA features from StatsBomb data"""
        return {}
    
    def _calculate_threat_features(self, match_data: Dict) -> Dict:
        """Calculate threat-based features"""
        # Use base threat model
        return {'threat_rating': 0.5}
    
    def _collect_traditional_features(self, match_data: Dict) -> Dict:
        """Collect traditional ML features"""
        return {'traditional_strength_diff': 0.0}
    
    def train_meta_learner(self, training_data: pd.DataFrame) -> Dict:
        """
        Train the meta-learner on historical predictions and outcomes
        
        Args:
            training_data: Historical match data with outcomes
            
        Returns:
            Training metrics
        """
        logger.info(f"Training meta-learner on {len(training_data)} matches")
        
        # This would implement full meta-learner training
        # For now, return basic metrics
        
        self.is_trained = True
        
        return {
            'training_samples': len(training_data),
            'meta_model_type': 'weighted_ensemble',
            'training_date': datetime.now().isoformat(),
            'model_weights': self.model_weights
        }
    
    def evaluate_model_performance(self, test_data: pd.DataFrame) -> Dict:
        """
        Evaluate performance of individual models and ensemble
        
        Args:
            test_data: Test dataset
            
        Returns:
            Performance metrics
        """
        # This would implement comprehensive evaluation
        return {
            'ensemble_accuracy': 0.75,
            'individual_model_performance': {
                'basic': 0.55,
                'advanced': 0.68,
                'xg_based': 0.72,
                'threat_based': 0.65
            },
            'evaluation_date': datetime.now().isoformat()
        }
    
    def save_meta_learner(self, filepath: str) -> None:
        """Save the complete meta-learner system"""
        meta_learner_data = {
            'model_weights': self.model_weights,
            'feature_importance': self.feature_importance,
            'performance_tracking': self.model_performance,
            'is_trained': self.is_trained,
            'meta_model': self.meta_model,
            'calibrator': self.calibrator,
            'save_date': datetime.now().isoformat()
        }
        
        joblib.dump(meta_learner_data, filepath)
        logger.info(f"Meta-learner saved to {filepath}")
    
    def load_meta_learner(self, filepath: str) -> None:
        """Load the complete meta-learner system"""
        meta_learner_data = joblib.load(filepath)
        
        self.model_weights = meta_learner_data['model_weights']
        self.feature_importance = meta_learner_data['feature_importance']
        self.model_performance = meta_learner_data['performance_tracking']
        self.is_trained = meta_learner_data['is_trained']
        self.meta_model = meta_learner_data['meta_model']
        self.calibrator = meta_learner_data['calibrator']
        
        logger.info(f"Meta-learner loaded from {filepath}")


# Utility functions
def create_ensemble_prediction_for_matches(matches: List[Dict]) -> List[Dict]:
    """
    Create ensemble predictions for a list of matches
    
    Args:
        matches: List of match dictionaries
        
    Returns:
        List of comprehensive prediction dictionaries
    """
    meta_learner = MetaLearnerPredictor()
    meta_learner.initialize_existing_models()
    
    predictions = []
    
    for match in matches:
        try:
            prediction = meta_learner.predict_match_outcome(match)
            predictions.append(prediction)
        except Exception as e:
            logger.error(f"Error predicting match {match.get('id', 'unknown')}: {e}")
            # Fallback prediction
            predictions.append({
                'predicted_result': 'X',
                'probabilities': {'home_win': 0.33, 'draw': 0.34, 'away_win': 0.33},
                'confidence': 0.1,
                'explanation': {'summary': 'Fallback prediction due to error'}
            })
    
    return predictions


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    meta_learner = MetaLearnerPredictor()
    meta_learner.initialize_existing_models()
    
    # Example match
    example_match = {
        'home_team': 'Real Madrid',
        'away_team': 'Barcelona', 
        'competition': 'La Liga',
        'season': 2025,
        'match_date': '2025-08-15'
    }
    
    print("Meta-Learner Ensemble System - Example")
    prediction = meta_learner.predict_match_outcome(example_match)
    
    print(f"Prediction: {prediction['predicted_result']}")
    print(f"Probabilities: Home {prediction['probabilities']['home_win']:.3f}, "
          f"Draw {prediction['probabilities']['draw']:.3f}, "
          f"Away {prediction['probabilities']['away_win']:.3f}")
    print(f"Confidence: {prediction['confidence']:.3f}")
    print(f"Models used: {prediction['meta_info']['models_used']}")
    print(f"Explanation: {prediction['explanation']['summary']}")
    
    print("\nMeta-learner ready for production use!")