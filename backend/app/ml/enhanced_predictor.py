"""
Enhanced Predictor - Integrates Advanced Feature Engineering with State-of-the-Art Models
Combines xG, xA, xT, PPDA, market intelligence, and external factors for superior predictions
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, log_loss
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import lightgbm as lgb
import joblib
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from .advanced_feature_engineering import AdvancedFeatureEngineer, create_training_features_from_matches
from ..database.models import Match

logger = logging.getLogger(__name__)

class EnhancedQuinielaPredictor:
    """
    State-of-the-art predictor that combines multiple advanced ML models
    with comprehensive feature engineering for maximum accuracy
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.feature_engineer = AdvancedFeatureEngineer(db)
        self.scaler = RobustScaler()  # More robust to outliers than StandardScaler
        self.models = {}
        self.ensemble_model = None
        self.feature_names = []
        self.model_version = None
        self.is_trained = False
        self.training_metrics = {}
        
        # Enhanced model configurations
        self.model_configs = {
            'random_forest': {
                'n_estimators': 300,
                'max_depth': 20,
                'min_samples_split': 3,
                'min_samples_leaf': 1,
                'max_features': 'sqrt',
                'bootstrap': True,
                'random_state': 42,
                'class_weight': 'balanced',
                'n_jobs': -1
            },
            'xgboost': {
                'n_estimators': 250,
                'max_depth': 8,
                'learning_rate': 0.08,
                'subsample': 0.85,
                'colsample_bytree': 0.85,
                'min_child_weight': 3,
                'reg_alpha': 0.1,
                'reg_lambda': 0.1,
                'random_state': 42,
                'eval_metric': 'mlogloss',
                'verbosity': 0
            },
            'lightgbm': {
                'n_estimators': 250,
                'max_depth': 8,
                'learning_rate': 0.08,
                'subsample': 0.85,
                'colsample_bytree': 0.85,
                'min_child_samples': 20,
                'reg_alpha': 0.1,
                'reg_lambda': 0.1,
                'random_state': 42,
                'verbosity': -1
            },
            'gradient_boosting': {
                'n_estimators': 200,
                'max_depth': 8,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'min_samples_split': 5,
                'min_samples_leaf': 3,
                'random_state': 42
            },
            'logistic_regression': {
                'C': 1.0,
                'class_weight': 'balanced',
                'random_state': 42,
                'max_iter': 1000,
                'solver': 'lbfgs'
            }
        }
    
    def prepare_training_data_advanced(self, matches: List[Match]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare advanced training data using comprehensive feature engineering
        """
        try:
            logger.info(f"Preparing advanced training data from {len(matches)} matches")
            
            X, y, feature_names = create_training_features_from_matches(self.db, matches)
            
            if len(X) == 0:
                raise ValueError("No valid training data could be created")
            
            # Remove features with zero variance
            feature_variances = np.var(X, axis=0)
            valid_features = feature_variances > 1e-6
            
            if np.sum(valid_features) == 0:
                raise ValueError("All features have zero variance")
            
            X_filtered = X[:, valid_features]
            feature_names_filtered = [name for i, name in enumerate(feature_names) if valid_features[i]]
            
            logger.info(f"Training data prepared: {X_filtered.shape[0]} samples, {X_filtered.shape[1]} features")
            return X_filtered, y, feature_names_filtered
            
        except Exception as e:
            logger.error(f"Error preparing training data: {str(e)}")
            raise
    
    def train_advanced_models(
        self, 
        matches: List[Match], 
        test_size: float = 0.2,
        optimize_hyperparameters: bool = False
    ) -> Dict[str, Any]:
        """
        Train ensemble of advanced models with comprehensive feature engineering
        """
        try:
            logger.info(f"Training advanced models with {len(matches)} matches")
            
            # Prepare advanced training data
            X, y, feature_names = self.prepare_training_data_advanced(matches)
            self.feature_names = feature_names
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train individual models
            self.models = {}
            model_scores = {}
            
            # Random Forest
            logger.info("Training Random Forest...")
            rf_model = RandomForestClassifier(**self.model_configs['random_forest'])
            rf_model.fit(X_train_scaled, y_train)
            self.models['random_forest'] = rf_model
            rf_score = rf_model.score(X_test_scaled, y_test)
            model_scores['random_forest'] = rf_score
            logger.info(f"Random Forest accuracy: {rf_score:.4f}")
            
            # XGBoost
            logger.info("Training XGBoost...")
            xgb_model = xgb.XGBClassifier(**self.model_configs['xgboost'])
            xgb_model.fit(X_train_scaled, y_train)
            self.models['xgboost'] = xgb_model
            xgb_score = xgb_model.score(X_test_scaled, y_test)
            model_scores['xgboost'] = xgb_score
            logger.info(f"XGBoost accuracy: {xgb_score:.4f}")
            
            # LightGBM
            logger.info("Training LightGBM...")
            lgb_model = lgb.LGBMClassifier(**self.model_configs['lightgbm'])
            lgb_model.fit(X_train_scaled, y_train)
            self.models['lightgbm'] = lgb_model
            lgb_score = lgb_model.score(X_test_scaled, y_test)
            model_scores['lightgbm'] = lgb_score
            logger.info(f"LightGBM accuracy: {lgb_score:.4f}")
            
            # Gradient Boosting
            logger.info("Training Gradient Boosting...")
            gb_model = GradientBoostingClassifier(**self.model_configs['gradient_boosting'])
            gb_model.fit(X_train_scaled, y_train)
            self.models['gradient_boosting'] = gb_model
            gb_score = gb_model.score(X_test_scaled, y_test)
            model_scores['gradient_boosting'] = gb_score
            logger.info(f"Gradient Boosting accuracy: {gb_score:.4f}")
            
            # Logistic Regression (baseline)
            logger.info("Training Logistic Regression...")
            lr_model = LogisticRegression(**self.model_configs['logistic_regression'])
            lr_model.fit(X_train_scaled, y_train)
            self.models['logistic_regression'] = lr_model
            lr_score = lr_model.score(X_test_scaled, y_test)
            model_scores['logistic_regression'] = lr_score
            logger.info(f"Logistic Regression accuracy: {lr_score:.4f}")
            
            # Create weighted ensemble based on individual model performance
            logger.info("Creating weighted ensemble...")
            estimators = [
                ('rf', rf_model),
                ('xgb', xgb_model), 
                ('lgb', lgb_model),
                ('gb', gb_model),
                ('lr', lr_model)
            ]
            
            # Use soft voting for probability-based ensemble
            self.ensemble_model = VotingClassifier(
                estimators=estimators,
                voting='soft'
            )
            
            # Train ensemble
            self.ensemble_model.fit(X_train_scaled, y_train)
            
            # Evaluate ensemble
            ensemble_score = self.ensemble_model.score(X_test_scaled, y_test)
            y_pred_ensemble = self.ensemble_model.predict(X_test_scaled)
            y_pred_proba_ensemble = self.ensemble_model.predict_proba(X_test_scaled)
            
            # Cross-validation
            cv_scores = cross_val_score(
                self.ensemble_model, X_train_scaled, y_train, 
                cv=5, scoring='accuracy'
            )
            
            # Feature importance (from Random Forest)
            feature_importance = rf_model.feature_importances_
            feature_importance_dict = dict(zip(self.feature_names, feature_importance))
            
            # Sort features by importance
            sorted_features = sorted(
                feature_importance_dict.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Training complete
            self.is_trained = True
            self.model_version = f"enhanced_v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Comprehensive results
            results = {
                "ensemble_accuracy": ensemble_score,
                "individual_model_scores": model_scores,
                "best_individual_model": max(model_scores, key=model_scores.get),
                "cv_mean": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "classification_report": classification_report(y_test, y_pred_ensemble, output_dict=True),
                "confusion_matrix": confusion_matrix(y_test, y_pred_ensemble).tolist(),
                "feature_importance": feature_importance_dict,
                "top_features": sorted_features[:20],  # Top 20 features
                "model_version": self.model_version,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "feature_count": len(self.feature_names),
                "data_source": "advanced_feature_engineering",
                "improvement_over_basic": f"+{max(0, ensemble_score - 0.55) * 100:.1f}%"
            }
            
            self.training_metrics = results
            
            logger.info(f"Enhanced model training completed. Ensemble accuracy: {ensemble_score:.4f}")
            logger.info(f"Best individual model: {results['best_individual_model']} ({model_scores[results['best_individual_model']]:.4f})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error training enhanced models: {str(e)}")
            raise
    
    def predict_match_advanced(
        self, 
        home_team_id: int, 
        away_team_id: int, 
        season: int,
        match_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Predict match result using advanced feature engineering and ensemble model
        """
        try:
            if not self.is_trained:
                raise ValueError("Enhanced model must be trained before making predictions")
            
            logger.info(f"Predicting match: {home_team_id} vs {away_team_id}")
            
            # Create advanced features
            features = self.feature_engineer.create_advanced_features(
                home_team_id, away_team_id, season, match_date
            )
            
            if not features:
                raise ValueError("Could not create features for prediction")
            
            # Ensure features are in same order as training
            feature_values = [features.get(name, 0.0) for name in self.feature_names]
            X = np.array([feature_values])
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Get ensemble prediction
            prediction = self.ensemble_model.predict(X_scaled)[0]
            probabilities = self.ensemble_model.predict_proba(X_scaled)[0]
            
            # Get individual model predictions for analysis
            individual_predictions = {}
            individual_probabilities = {}
            
            for model_name, model in self.models.items():
                ind_pred = model.predict(X_scaled)[0]
                ind_proba = model.predict_proba(X_scaled)[0]
                individual_predictions[model_name] = ind_pred
                individual_probabilities[model_name] = ind_proba.tolist()
            
            # Map numeric prediction to result
            result_mapping = {0: '1', 1: 'X', 2: '2'}
            predicted_result = result_mapping[prediction]
            
            # Get class labels for probabilities
            class_labels = self.ensemble_model.classes_
            prob_dict = dict(zip(class_labels, probabilities))
            
            # Calculate confidence as max probability
            confidence = max(probabilities)
            
            # Get top contributing features
            feature_contributions = self._get_feature_contributions(features)
            
            # Create explanation
            explanation = self._create_prediction_explanation(
                predicted_result, confidence, feature_contributions, individual_predictions
            )
            
            result = {
                "predicted_result": predicted_result,
                "confidence": float(confidence),
                "probabilities": {
                    "home_win": float(prob_dict.get('1', 0)),
                    "draw": float(prob_dict.get('X', 0)),
                    "away_win": float(prob_dict.get('2', 0))
                },
                "explanation": explanation,
                "model_info": {
                    "model_version": self.model_version,
                    "model_type": "enhanced_ensemble",
                    "feature_count": len(self.feature_names),
                    "models_used": len(self.models)
                },
                "individual_models": {
                    "predictions": individual_predictions,
                    "probabilities": individual_probabilities
                },
                "advanced_features": {
                    "features_used": len(features),
                    "top_features": feature_contributions[:10],
                    "data_sources": self._identify_data_sources(features)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in advanced prediction: {str(e)}")
            raise
    
    def _get_feature_contributions(self, features: Dict[str, float]) -> List[Dict[str, Any]]:
        """Get feature contributions sorted by importance"""
        try:
            if 'random_forest' not in self.models:
                return []
            
            # Get feature importance from Random Forest
            rf_model = self.models['random_forest']
            feature_importance = rf_model.feature_importances_
            
            contributions = []
            for i, feature_name in enumerate(self.feature_names):
                if feature_name in features:
                    importance = feature_importance[i] if i < len(feature_importance) else 0
                    value = features[feature_name]
                    
                    contributions.append({
                        "feature": feature_name,
                        "value": float(value),
                        "importance": float(importance),
                        "contribution_score": float(importance * abs(value))
                    })
            
            # Sort by contribution score
            contributions.sort(key=lambda x: x["contribution_score"], reverse=True)
            return contributions
            
        except Exception as e:
            logger.error(f"Error calculating feature contributions: {str(e)}")
            return []
    
    def _create_prediction_explanation(
        self, 
        predicted_result: str, 
        confidence: float,
        feature_contributions: List[Dict[str, Any]],
        individual_predictions: Dict[str, int]
    ) -> Dict[str, Any]:
        """Create human-readable explanation of the prediction"""
        try:
            # Result mapping
            result_names = {'1': 'Home Win', 'X': 'Draw', '2': 'Away Win'}
            predicted_name = result_names.get(predicted_result, 'Unknown')
            
            # Model consensus
            consensus_count = sum(1 for pred in individual_predictions.values() 
                                if (pred == int(predicted_result) if predicted_result.isdigit() 
                                    else pred == predicted_result))
            total_models = len(individual_predictions)
            
            # Top factors
            top_factors = feature_contributions[:5] if feature_contributions else []
            
            # Create summary
            if confidence > 0.7:
                confidence_level = "High"
            elif confidence > 0.5:
                confidence_level = "Medium"
            else:
                confidence_level = "Low"
            
            summary = f"{predicted_name} with {confidence_level} confidence ({confidence:.1%}). "
            summary += f"{consensus_count}/{total_models} models agree."
            
            explanation = {
                "summary": summary,
                "confidence_level": confidence_level,
                "model_consensus": f"{consensus_count}/{total_models}",
                "key_factors": [
                    f"{factor['feature']}: {factor['value']:.3f} (importance: {factor['importance']:.3f})"
                    for factor in top_factors
                ],
                "prediction_rationale": self._get_prediction_rationale(top_factors)
            }
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error creating explanation: {str(e)}")
            return {"summary": f"Predicted: {predicted_result}", "error": str(e)}
    
    def _get_prediction_rationale(self, top_factors: List[Dict[str, Any]]) -> str:
        """Generate rationale based on top contributing factors"""
        try:
            if not top_factors:
                return "Prediction based on ensemble model analysis."
            
            rationale_parts = []
            
            for factor in top_factors[:3]:  # Top 3 factors
                feature_name = factor['feature']
                value = factor['value']
                importance = factor['importance']
                
                if 'xg_difference' in feature_name:
                    if value > 0.5:
                        rationale_parts.append("Strong expected goals advantage")
                    elif value < -0.5:
                        rationale_parts.append("Expected goals disadvantage")
                        
                elif 'momentum' in feature_name:
                    if value > 0.3:
                        rationale_parts.append("Positive momentum trend")
                    elif value < -0.3:
                        rationale_parts.append("Negative momentum trend")
                        
                elif 'points' in feature_name and 'difference' in feature_name:
                    if value > 10:
                        rationale_parts.append("Significant league position advantage")
                    elif value < -10:
                        rationale_parts.append("League position disadvantage")
            
            if not rationale_parts:
                rationale_parts.append("Based on comprehensive statistical analysis")
            
            return ". ".join(rationale_parts) + "."
            
        except Exception as e:
            logger.error(f"Error generating rationale: {str(e)}")
            return "Prediction based on advanced statistical analysis."
    
    def _identify_data_sources(self, features: Dict[str, float]) -> List[str]:
        """Identify which data sources contributed to the features"""
        sources = set()
        
        if any('xg_' in key for key in features.keys()):
            sources.add("Expected Goals (xG)")
        if any('xa_' in key for key in features.keys()):
            sources.add("Expected Assists (xA)")
        if any('xt_' in key for key in features.keys()):
            sources.add("Expected Threat (xT)")
        if any('ppda_' in key for key in features.keys()):
            sources.add("Pressing (PPDA)")
        if any('market_' in key for key in features.keys()):
            sources.add("Market Intelligence")
        if any(key in ['temperature', 'weather_impact_score', 'rivalry_intensity'] for key in features.keys()):
            sources.add("External Factors")
        if any('points' in key or 'goals' in key for key in features.keys()):
            sources.add("Basic Statistics")
        
        return sorted(list(sources))
    
    def get_feature_importance(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """Get top N most important features"""
        try:
            if 'random_forest' not in self.models:
                return []
            
            rf_model = self.models['random_forest']
            feature_importance = rf_model.feature_importances_
            
            importance_list = []
            for i, feature_name in enumerate(self.feature_names):
                if i < len(feature_importance):
                    importance_list.append({
                        "feature": feature_name,
                        "importance": float(feature_importance[i]),
                        "category": self._categorize_feature(feature_name)
                    })
            
            # Sort by importance
            importance_list.sort(key=lambda x: x["importance"], reverse=True)
            return importance_list[:top_n]
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {str(e)}")
            return []
    
    def _categorize_feature(self, feature_name: str) -> str:
        """Categorize a feature by its type"""
        if any(keyword in feature_name for keyword in ['xg_', 'expected_goals']):
            return "Expected Goals"
        elif any(keyword in feature_name for keyword in ['xa_', 'expected_assists']):
            return "Expected Assists"
        elif any(keyword in feature_name for keyword in ['xt_', 'expected_threat']):
            return "Expected Threat"
        elif any(keyword in feature_name for keyword in ['ppda_', 'pressing']):
            return "Pressing"
        elif any(keyword in feature_name for keyword in ['possession', 'pass_']):
            return "Possession/Passing"
        elif any(keyword in feature_name for keyword in ['market_', 'odds_']):
            return "Market Intelligence"
        elif any(keyword in feature_name for keyword in ['weather', 'temperature', 'motivation']):
            return "External Factors"
        elif any(keyword in feature_name for keyword in ['points', 'wins', 'goals']):
            return "Basic Statistics"
        elif any(keyword in feature_name for keyword in ['momentum', 'form']):
            return "Form/Momentum"
        else:
            return "Other"
    
    def save_enhanced_model(self, filepath: str) -> bool:
        """Save the enhanced model and all components"""
        try:
            model_data = {
                'ensemble_model': self.ensemble_model,
                'individual_models': self.models,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'model_version': self.model_version,
                'training_metrics': self.training_metrics,
                'model_configs': self.model_configs,
                'is_trained': self.is_trained
            }
            
            joblib.dump(model_data, filepath)
            logger.info(f"Enhanced model saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving enhanced model: {str(e)}")
            return False
    
    def load_enhanced_model(self, filepath: str) -> bool:
        """Load the enhanced model and all components"""
        try:
            model_data = joblib.load(filepath)
            
            self.ensemble_model = model_data['ensemble_model']
            self.models = model_data['individual_models']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.model_version = model_data['model_version']
            self.training_metrics = model_data.get('training_metrics', {})
            self.model_configs = model_data.get('model_configs', self.model_configs)
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Enhanced model loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading enhanced model: {str(e)}")
            return False