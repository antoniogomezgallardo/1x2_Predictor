import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import joblib
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import logging
from .feature_engineering import FeatureEngineer


class QuinielaPredictor:
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.scaler = StandardScaler()
        self.model = None
        self.feature_names = []
        self.model_version = None
        self.is_trained = False
        
        # Model hyperparameters
        self.rf_params = {
            'n_estimators': 200,
            'max_depth': 15,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42,
            'class_weight': 'balanced'
        }
        
        self.xgb_params = {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'eval_metric': 'mlogloss'
        }
    
    def prepare_training_data(self, historical_matches: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from historical matches"""
        X_list = []
        y_list = []
        
        for match_data in historical_matches:
            # Extract features
            features = self.feature_engineer.extract_features(match_data)
            
            # Get result (1, X, 2)
            result = match_data.get("result")
            if result in ["1", "X", "2"]:
                feature_values = list(features.values())
                X_list.append(feature_values)
                y_list.append(result)
        
        if not X_list:
            raise ValueError("No valid training data found")
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        self.feature_names = list(features.keys())
        
        return X, y
    
    def train_model(self, historical_matches: List[Dict[str, Any]], 
                   test_size: float = 0.2) -> Dict[str, Any]:
        """Train the prediction model"""
        logging.info(f"Training model with {len(historical_matches)} matches")
        
        # Prepare data
        X, y = self.prepare_training_data(historical_matches)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create individual models
        rf_model = RandomForestClassifier(**self.rf_params)
        xgb_model = xgb.XGBClassifier(**self.xgb_params)
        
        # Create ensemble model
        self.model = VotingClassifier(
            estimators=[
                ('rf', rf_model),
                ('xgb', xgb_model)
            ],
            voting='soft'
        )
        
        # Train model
        logging.info("Training ensemble model...")
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)
        
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='accuracy')
        
        # Feature importance (from Random Forest component of the ensemble)
        rf_estimator = self.model.named_estimators_['rf']
        rf_feature_importance = rf_estimator.feature_importances_
        feature_importance_dict = dict(zip(self.feature_names, rf_feature_importance))
        
        self.is_trained = True
        self.model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            "accuracy": accuracy,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "feature_importance": feature_importance_dict,
            "model_version": self.model_version,
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
        
        logging.info(f"Model training completed. Accuracy: {accuracy:.3f}")
        return results
    
    def predict_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict result for a single match"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Extract features
        features = self.feature_engineer.extract_features(match_data)
        
        # Ensure features are in the same order as training
        feature_values = [features.get(name, 0) for name in self.feature_names]
        X = np.array([feature_values])
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Make prediction
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        # Get class labels (they should be ['1', '2', 'X'] in sorted order)
        classes = self.model.classes_
        
        # Create probability dictionary
        prob_dict = dict(zip(classes, probabilities))
        
        # Calculate confidence (max probability)
        confidence = max(probabilities)
        
        result = {
            "predicted_result": prediction,
            "confidence": confidence,
            "probabilities": {
                "home_win": prob_dict.get("1", 0),
                "draw": prob_dict.get("X", 0),
                "away_win": prob_dict.get("2", 0)
            },
            "features_used": features,
            "model_version": self.model_version
        }
        
        return result
    
    def predict_quiniela(self, matches_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict results for a full quiniela (15 matches)"""
        predictions = []
        
        for i, match_data in enumerate(matches_data):
            try:
                prediction = self.predict_match(match_data)
                prediction["match_number"] = i + 1
                prediction["home_team"] = match_data.get("home_team", {}).get("name", "Unknown")
                prediction["away_team"] = match_data.get("away_team", {}).get("name", "Unknown")
                prediction["match_date"] = match_data.get("match_date")
                predictions.append(prediction)
            except Exception as e:
                logging.error(f"Error predicting match {i+1}: {str(e)}")
                # Add default prediction in case of error
                predictions.append({
                    "match_number": i + 1,
                    "predicted_result": "X",
                    "confidence": 0.33,
                    "probabilities": {"home_win": 0.33, "draw": 0.34, "away_win": 0.33},
                    "error": str(e),
                    "home_team": match_data.get("home_team", {}).get("name", "Unknown"),
                    "away_team": match_data.get("away_team", {}).get("name", "Unknown"),
                    "match_date": match_data.get("match_date")
                })
        
        return predictions
    
    def calculate_betting_strategy(self, predictions: List[Dict[str, Any]], 
                                 bankroll: float, max_bet_pct: float = 0.05) -> Dict[str, Any]:
        """Calculate optimal betting strategy based on predictions and confidence"""
        total_confidence = sum(pred["confidence"] for pred in predictions)
        recommended_bets = []
        total_stake = 0
        
        for prediction in predictions:
            # Kelly Criterion inspired betting
            confidence = prediction["confidence"]
            
            # Only bet if confidence is above threshold
            if confidence > 0.6:  # 60% confidence threshold
                # Calculate bet size based on confidence and bankroll
                bet_amount = (confidence - 0.5) * max_bet_pct * bankroll
                bet_amount = min(bet_amount, max_bet_pct * bankroll)  # Cap at max percentage
                bet_amount = max(bet_amount, 0)  # Ensure positive
                
                if bet_amount > 0:
                    recommended_bets.append({
                        "match_number": prediction["match_number"],
                        "home_team": prediction["home_team"],
                        "away_team": prediction["away_team"],
                        "predicted_result": prediction["predicted_result"],
                        "confidence": confidence,
                        "recommended_bet": bet_amount,
                        "probabilities": prediction["probabilities"]
                    })
                    total_stake += bet_amount
        
        return {
            "total_stake": total_stake,
            "recommended_bets": recommended_bets,
            "number_of_bets": len(recommended_bets),
            "percentage_of_bankroll": (total_stake / bankroll) * 100 if bankroll > 0 else 0
        }
    
    def predict_quiniela_official(self, matches_data: List[Dict[str, Any]], season: int) -> Dict[str, Any]:
        """
        Genera predicciones específicas para la Quiniela Española oficial
        Considera las reglas específicas: 14 partidos + Pleno al 15
        """
        from .quiniela_optimizer import QuinielaOptimizer
        
        optimizer = QuinielaOptimizer()
        
        # Paso 1: Seleccionar los 14 mejores partidos para la quiniela
        if len(matches_data) > 14:
            selected_matches = optimizer.select_quiniela_matches(matches_data, season)
            logging.info(f"Selected {len(selected_matches)} matches from {len(matches_data)} available")
        else:
            selected_matches = matches_data
            logging.warning(f"Only {len(matches_data)} matches available, need 14 for official Quiniela")
        
        # Paso 2: Generar predicciones para los 14 partidos
        match_predictions = []
        for i, match_data in enumerate(selected_matches[:14]):
            features = self.feature_engineer.extract_features(match_data)
            if features:
                feature_values = np.array([list(features.values())])
                feature_values_scaled = self.scaler.transform(feature_values)
                
                # Predicción
                prediction = self.model.predict(feature_values_scaled)[0]
                probabilities = self.model.predict_proba(feature_values_scaled)[0]
                
                # Mapear probabilidades a resultados
                prob_dict = {
                    "home_win": probabilities[0] if len(probabilities) > 0 else 0.33,
                    "draw": probabilities[1] if len(probabilities) > 1 else 0.33,
                    "away_win": probabilities[2] if len(probabilities) > 2 else 0.33
                }
                
                # Mapear predicción a formato Quiniela
                result_mapping = {"home_win": "1", "draw": "X", "away_win": "2"}
                quiniela_result = result_mapping.get(prediction, "X")
                
                # Calcular goles esperados para el Pleno al 15
                expected_goals = self._estimate_expected_goals(match_data, features)
                
                match_predictions.append({
                    "match_number": i + 1,
                    "home_team": match_data.get("home_team", {}).get("name", "Unknown"),
                    "away_team": match_data.get("away_team", {}).get("name", "Unknown"),
                    "predicted_result": quiniela_result,
                    "confidence": max(prob_dict.values()),
                    "probabilities": prob_dict,
                    "expected_goals": expected_goals,
                    "match_date": match_data.get("match_date"),
                    "league": "La Liga" if match_data.get("league_id") == 140 else "Segunda División"
                })
        
        # Paso 3: Generar predicción del Pleno al 15
        pleno_al_15 = optimizer.generate_pleno_al_15_prediction(match_predictions)
        
        # Paso 4: Calcular valor esperado de la quiniela
        quiniela_value = optimizer.calculate_combination_value(match_predictions)
        
        # Paso 5: Generar combinaciones múltiples si es beneficioso
        multiple_combinations = optimizer.suggest_multiple_combinations(match_predictions)
        
        # Paso 6: Calcular estadísticas de la quiniela
        avg_confidence = sum(p['confidence'] for p in match_predictions) / len(match_predictions)
        high_confidence_matches = sum(1 for p in match_predictions if p['confidence'] > 0.7)
        
        return {
            "quiniela_type": "oficial_espanola",
            "total_matches": len(match_predictions),
            "predictions": match_predictions,
            "pleno_al_15": {
                "prediction": pleno_al_15,
                "description": f"Predicción de goles: {pleno_al_15}",
                "note": "Solo válido si aciertas los 14 partidos"
            },
            "statistics": {
                "average_confidence": avg_confidence,
                "high_confidence_matches": high_confidence_matches,
                "expected_accuracy": avg_confidence,
                "la_liga_matches": sum(1 for p in match_predictions if p.get('league') == 'La Liga'),
                "segunda_matches": sum(1 for p in match_predictions if p.get('league') == 'Segunda División')
            },
            "value_analysis": quiniela_value,
            "multiple_combinations": multiple_combinations,
            "betting_recommendation": {
                "recommended": quiniela_value['expected_value'] > 0,
                "confidence_level": "Alta" if avg_confidence > 0.65 else "Media" if avg_confidence > 0.55 else "Baja",
                "strategy": "Conservadora" if high_confidence_matches < 8 else "Agresiva"
            },
            "generated_at": datetime.now().isoformat(),
            "model_version": self.model_version
        }
    
    def _estimate_expected_goals(self, match_data: Dict, features: Dict) -> float:
        """
        Estima el número esperado de goles para un partido
        Usado para el Pleno al 15
        """
        home_stats = match_data.get("home_stats")
        away_stats = match_data.get("away_stats")
        
        if home_stats and away_stats:
            # Goles promedio por partido
            home_goals_avg = home_stats.goals_for / max(home_stats.matches_played, 1)
            away_goals_avg = away_stats.goals_for / max(away_stats.matches_played, 1)
            
            # Goles concedidos promedio
            home_conceded_avg = home_stats.goals_against / max(home_stats.matches_played, 1)
            away_conceded_avg = away_stats.goals_against / max(away_stats.matches_played, 1)
            
            # Estimación usando promedios
            expected_home_goals = (home_goals_avg + away_conceded_avg) / 2
            expected_away_goals = (away_goals_avg + home_conceded_avg) / 2
            
            total_expected = expected_home_goals + expected_away_goals
            
            # Ajustar por factores del partido
            if features.get('home_advantage', 0) > 0.1:
                total_expected *= 1.1  # Ventaja local aumenta goles
            
            return max(0.5, min(6.0, total_expected))  # Límites razonables
        
        return 2.5  # Default esperado
    
    def save_model(self, filepath: str) -> None:
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "model_version": self.model_version,
            "timestamp": datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        logging.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """Load trained model from disk"""
        model_data = joblib.load(filepath)
        
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.feature_names = model_data["feature_names"]
        self.model_version = model_data["model_version"]
        self.is_trained = True
        
        logging.info(f"Model loaded from {filepath}, version: {self.model_version}")
    
    def get_feature_importance(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """Get top N most important features"""
        if not self.is_trained:
            raise ValueError("Model must be trained before getting feature importance")
        
        # Get feature importance from Random Forest component
        rf_model = self.model.named_estimators_['rf']
        importance_scores = rf_model.feature_importances_
        
        feature_importance = [
            {"feature": name, "importance": score}
            for name, score in zip(self.feature_names, importance_scores)
        ]
        
        # Sort by importance
        feature_importance.sort(key=lambda x: x["importance"], reverse=True)
        
        return feature_importance[:top_n]