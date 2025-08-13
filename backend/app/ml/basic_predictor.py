"""
Sistema de predicciones básico para primeras jornadas sin datos históricos
Utiliza heurísticas simples basadas en datos disponibles de equipos
"""
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..database.models import Team, Match
import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BasicPredictor:
    """Predictor básico que funciona sin datos históricos ML"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def predict_match(self, home_team: Team, away_team: Team) -> Dict[str, Any]:
        """
        Predice resultado de un partido usando heurísticas básicas
        """
        # Calcular ventaja local básica
        home_advantage = 0.15  # 15% ventaja por jugar en casa
        
        # Heurística 1: Antiguedad del club (más antiguo = más experiencia)
        home_experience = self._calculate_experience_score(home_team)
        away_experience = self._calculate_experience_score(away_team)
        
        # Heurística 2: Capacidad del estadio (mayor capacidad = más apoyo)
        home_stadium_factor = self._calculate_stadium_factor(home_team)
        away_stadium_factor = self._calculate_stadium_factor(away_team)
        
        # Heurística 3: Liga del equipo (La Liga vs Segunda)
        home_league_factor = self._calculate_league_factor(home_team)
        away_league_factor = self._calculate_league_factor(away_team)
        
        # Calcular puntuación base para cada equipo
        home_score = (
            home_experience * 0.3 +
            home_stadium_factor * 0.2 +
            home_league_factor * 0.3 +
            home_advantage * 0.2
        )
        
        away_score = (
            away_experience * 0.3 +
            away_stadium_factor * 0.2 +
            away_league_factor * 0.3
        )
        
        # Normalizar puntuaciones
        total_score = home_score + away_score
        if total_score > 0:
            home_prob_raw = home_score / total_score
            away_prob_raw = away_score / total_score
        else:
            home_prob_raw = 0.5
            away_prob_raw = 0.5
        
        # Ajustar probabilidades para incluir empate
        # Empate más probable cuando equipos están equilibrados
        balance_factor = abs(home_prob_raw - away_prob_raw)
        draw_prob = 0.25 + (0.15 * (1 - balance_factor))  # 25-40% empate
        
        # Redistribuir probabilidades
        remaining_prob = 1.0 - draw_prob
        home_prob = home_prob_raw * remaining_prob
        away_prob = away_prob_raw * remaining_prob
        
        # Añadir algo de aleatoriedad para evitar predicciones demasiado deterministas
        randomness = 0.05  # 5% de factor aleatorio
        random_factor = random.uniform(-randomness, randomness)
        
        home_prob += random_factor
        away_prob -= random_factor
        draw_prob += random_factor * 0.5
        
        # Normalizar para que sumen 1.0
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total  
        away_prob /= total
        
        # Determinar predicción más probable
        if home_prob > draw_prob and home_prob > away_prob:
            prediction = "1"
            confidence = home_prob
        elif away_prob > draw_prob and away_prob > home_prob:
            prediction = "2"
            confidence = away_prob
        else:
            prediction = "X"
            confidence = draw_prob
        
        # Generar explicación
        explanation = self._generate_explanation(
            home_team, away_team, prediction, 
            home_prob, draw_prob, away_prob
        )
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "home_probability": home_prob,
            "draw_probability": draw_prob,
            "away_probability": away_prob,
            "explanation": explanation,
            "method": "basic_heuristic"
        }
    
    def _calculate_experience_score(self, team: Team) -> float:
        """Calcula puntuación basada en experiencia del club"""
        if not team.founded:
            return 0.5  # Valor neutral si no hay datos
        
        current_year = datetime.now().year
        years_active = current_year - team.founded
        
        # Normalizar: equipos muy antiguos tienen ventaja
        if years_active > 100:
            return 1.0
        elif years_active > 50:
            return 0.8
        elif years_active > 25:
            return 0.6
        else:
            return 0.4
    
    def _calculate_stadium_factor(self, team: Team) -> float:
        """Calcula factor basado en capacidad del estadio"""
        if not team.venue_capacity:
            return 0.5  # Valor neutral
        
        capacity = team.venue_capacity
        
        # Normalizar capacidades típicas del fútbol español
        if capacity > 80000:  # Bernabéu, Camp Nou
            return 1.0
        elif capacity > 50000:  # Estadios grandes
            return 0.8
        elif capacity > 30000:  # Estadios medianos
            return 0.6
        elif capacity > 15000:  # Estadios pequeños
            return 0.4
        else:
            return 0.2
    
    def _calculate_league_factor(self, team: Team) -> float:
        """Calcula factor basado en la liga del equipo"""
        if team.league_id == 140:  # La Liga
            return 1.0
        elif team.league_id == 141:  # Segunda División
            return 0.7
        else:
            return 0.5  # Valor neutral para otras ligas
    
    def _generate_explanation(self, home_team: Team, away_team: Team, 
                            prediction: str, home_prob: float, 
                            draw_prob: float, away_prob: float) -> str:
        """Genera explicación legible de la predicción"""
        
        pred_map = {"1": "Victoria local", "X": "Empate", "2": "Victoria visitante"}
        result_text = pred_map.get(prediction, "Resultado incierto")
        
        explanation = f"**{result_text}** ({home_prob:.1%} - {draw_prob:.1%} - {away_prob:.1%})\n\n"
        
        # Analizar factores clave
        factors = []
        
        # Factor liga
        if home_team.league_id == 140 and away_team.league_id == 141:
            factors.append(f"🏆 {home_team.short_name or home_team.name} milita en Primera División")
        elif away_team.league_id == 140 and home_team.league_id == 141:
            factors.append(f"🏆 {away_team.short_name or away_team.name} milita en Primera División")
        
        # Factor experiencia
        home_years = datetime.now().year - (home_team.founded or 1900)
        away_years = datetime.now().year - (away_team.founded or 1900)
        
        if abs(home_years - away_years) > 25:
            older_team = home_team if home_years > away_years else away_team
            factors.append(f"📅 {older_team.short_name or older_team.name} tiene más experiencia histórica")
        
        # Factor estadio
        if home_team.venue_capacity and home_team.venue_capacity > 40000:
            factors.append(f"🏟️ Ventaja del estadio {home_team.venue_name} ({home_team.venue_capacity:,} espectadores)")
        
        # Ventaja local
        factors.append("🏠 Ventaja de jugar en casa")
        
        if factors:
            explanation += "**Factores clave:**\n"
            for factor in factors[:3]:  # Máximo 3 factores
                explanation += f"• {factor}\n"
        
        explanation += f"\n*Predicción basada en heurísticas básicas (datos históricos, capacidad estadio, liga)*"
        
        return explanation

def create_basic_predictions_for_quiniela(db: Session, season: int) -> List[Dict[str, Any]]:
    """
    Crea predicciones básicas para una Quiniela completa (14-15 partidos)
    """
    predictor = BasicPredictor(db)
    predictions = []
    
    try:
        # Buscar próximos partidos sin resultado
        upcoming_matches = db.query(Match).filter(
            Match.season == season,
            Match.result.is_(None),  # Sin resultado aún
            Match.home_goals.is_(None)  # Sin goles registrados
        ).order_by(Match.match_date).limit(20).all()  # Obtener 20 para seleccionar los mejores 15
        
        logger.info(f"Found {len(upcoming_matches)} upcoming matches for season {season}")
        
        if len(upcoming_matches) < 14:
            logger.warning(f"Only {len(upcoming_matches)} upcoming matches found, need at least 14 for Quiniela")
            return []
        
        # Seleccionar los primeros 15 partidos más próximos
        selected_matches = upcoming_matches[:15]
        
        for match in selected_matches:
            # Obtener equipos
            home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
            away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
            
            if not home_team or not away_team:
                logger.warning(f"Missing team data for match {match.id}")
                continue
            
            # Generar predicción
            prediction = predictor.predict_match(home_team, away_team)
            
            # Formatear para respuesta compatible con dashboard
            match_prediction = {
                "match_number": len(predictions) + 1,
                "match_id": match.id,
                "home_team": home_team.name,
                "away_team": away_team.name,
                "league": "La Liga" if home_team.league_id == 140 else "Segunda División",
                "match_date": match.match_date.isoformat() if match.match_date else None,
                "prediction": {
                    "result": prediction["prediction"],
                    "confidence": prediction["confidence"],
                    "probabilities": {
                        "home_win": prediction["home_probability"],
                        "draw": prediction["draw_probability"],
                        "away_win": prediction["away_probability"]
                    }
                },
                "explanation": f"Predicción {prediction['prediction']} con {prediction['confidence']:.0%} confianza - {prediction['explanation']}",
                "features_table": [
                    {"feature": "Método", "value": "Heurístico", "impact": "Alto", "interpretation": "Predicción básica para inicio de temporada"},
                    {"feature": "Liga Local", "value": "La Liga" if home_team.league_id == 140 else "Segunda", "impact": "Medio", "interpretation": f"Equipo local en {'Primera' if home_team.league_id == 140 else 'Segunda'}"},
                    {"feature": "Liga Visitante", "value": "La Liga" if away_team.league_id == 140 else "Segunda", "impact": "Medio", "interpretation": f"Equipo visitante en {'Primera' if away_team.league_id == 140 else 'Segunda'}"}
                ],
                "statistics": {
                    "home_team": {
                        "wins": 0, "draws": 0, "losses": 0,
                        "goals_for": 0, "goals_against": 0, "points": 0,
                        "note": "Temporada nueva - sin estadísticas"
                    },
                    "away_team": {
                        "wins": 0, "draws": 0, "losses": 0,
                        "goals_for": 0, "goals_against": 0, "points": 0,
                        "note": "Temporada nueva - sin estadísticas"
                    }
                },
                "method": "basic_predictor"
            }
            
            predictions.append(match_prediction)
        
        logger.info(f"Generated {len(predictions)} basic predictions")
        return predictions
        
    except Exception as e:
        logger.error(f"Error generating basic predictions: {str(e)}")
        return []