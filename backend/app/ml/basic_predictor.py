"""
Sistema de predicciones básico para primeras jornadas sin datos históricos
Utiliza heurísticas simples basadas en datos disponibles de equipos
"""
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..database.models import Team, Match, TeamStatistics
import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BasicPredictor:
    """Predictor básico que funciona sin datos históricos ML"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def predict_match(self, home_team: Team, away_team: Team, use_historical: bool = True) -> Dict[str, Any]:
        """
        Predice resultado de un partido usando heurísticas básicas + datos históricos
        """
        # Calcular ventaja local básica
        home_advantage = 0.15  # 15% ventaja por jugar en casa
        
        # Heurística 1: Rendimiento histórico (si está disponible)
        if use_historical:
            home_historical = self._get_historical_performance(home_team)
            away_historical = self._get_historical_performance(away_team)
        else:
            home_historical = 0.5
            away_historical = 0.5
        
        # Heurística 2: Antiguedad del club (más antiguo = más experiencia)
        home_experience = self._calculate_experience_score(home_team)
        away_experience = self._calculate_experience_score(away_team)
        
        # Heurística 3: Capacidad del estadio (mayor capacidad = más apoyo)
        home_stadium_factor = self._calculate_stadium_factor(home_team)
        away_stadium_factor = self._calculate_stadium_factor(away_team)
        
        # Heurística 4: Liga del equipo (La Liga vs Segunda)
        home_league_factor = self._calculate_league_factor(home_team)
        away_league_factor = self._calculate_league_factor(away_team)
        
        # Pesos adaptables según disponibilidad de datos históricos
        if use_historical and (home_historical != 0.5 or away_historical != 0.5):
            # Con datos históricos: mayor peso a rendimiento pasado
            weights = {
                'historical': 0.4,
                'experience': 0.2,
                'stadium': 0.15,
                'league': 0.25
            }
        else:
            # Sin datos históricos: distribuir pesos entre otros factores
            weights = {
                'historical': 0.0,
                'experience': 0.35,
                'stadium': 0.25,
                'league': 0.4
            }
        
        # Calcular puntuación base para cada equipo
        home_score = (
            home_historical * weights['historical'] +
            home_experience * weights['experience'] +
            home_stadium_factor * weights['stadium'] +
            home_league_factor * weights['league'] +
            home_advantage * 0.15  # Ventaja local siempre presente
        )
        
        away_score = (
            away_historical * weights['historical'] +
            away_experience * weights['experience'] +
            away_stadium_factor * weights['stadium'] +
            away_league_factor * weights['league']
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
            home_prob, draw_prob, away_prob, use_historical, weights
        )
        
        return {
            "predicted_result": prediction,  # Campo esperado por el código que lo usa
            "prediction": prediction,        # Mantener compatibilidad
            "confidence": confidence,
            "probabilities": {
                "home_win": home_prob,
                "draw": draw_prob,
                "away_win": away_prob
            },
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
    
    def _get_historical_performance(self, team: Team) -> float:
        """
        Obtiene rendimiento histórico del equipo basado en temporadas anteriores
        Devuelve puntuación normalizada entre 0.0 y 1.0
        """
        try:
            current_year = datetime.now().year
            historical_seasons = [current_year - 1, current_year - 2]  # 2024, 2023
            
            total_performance = 0.0
            seasons_found = 0
            
            for season in historical_seasons:
                # Buscar estadísticas del equipo en esa temporada
                stats = self.db.query(TeamStatistics).filter(
                    TeamStatistics.team_id == team.id,
                    TeamStatistics.season == season
                ).first()
                
                if stats and stats.matches_played > 0:
                    # Calcular rendimiento normalizado
                    # Máximo teórico: 3 puntos por partido
                    points_per_game = stats.points / stats.matches_played
                    performance_score = min(points_per_game / 3.0, 1.0)  # Normalizar a [0,1]
                    
                    # Pesar temporadas más recientes
                    weight = 0.7 if season == current_year - 1 else 0.3
                    total_performance += performance_score * weight
                    seasons_found += weight
                    
                    logger.debug(f"Team {team.name} season {season}: {stats.points} pts in {stats.matches_played} matches = {performance_score:.3f}")
            
            if seasons_found > 0:
                normalized_performance = total_performance / seasons_found
                logger.debug(f"Team {team.name} historical performance: {normalized_performance:.3f}")
                return normalized_performance
            else:
                # No hay datos históricos disponibles
                logger.debug(f"Team {team.name}: No historical data found")
                return 0.5  # Valor neutral
                
        except Exception as e:
            logger.warning(f"Error getting historical performance for {team.name}: {e}")
            return 0.5  # Valor neutral en caso de error
    
    def _generate_explanation(self, home_team: Team, away_team: Team, 
                            prediction: str, home_prob: float, 
                            draw_prob: float, away_prob: float, 
                            use_historical: bool = True, weights: dict = None) -> str:
        """Genera explicación legible de la predicción"""
        
        pred_map = {"1": "Victoria local", "X": "Empate", "2": "Victoria visitante"}
        result_text = pred_map.get(prediction, "Resultado incierto")
        
        explanation = f"**{result_text}** ({home_prob:.1%} - {draw_prob:.1%} - {away_prob:.1%})\n\n"
        
        # Analizar factores clave
        factors = []
        
        # Información sobre datos históricos
        if use_historical and weights and weights.get('historical', 0) > 0:
            factors.append(f"📊 Análisis incluye datos de temporadas anteriores (peso: {weights['historical']:.0%})")
        
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
            for factor in factors[:4]:  # Máximo 4 factores
                explanation += f"• {factor}\n"
        
        # Descripción del método usado
        method_desc = "datos históricos + heurísticas" if (use_historical and weights and weights.get('historical', 0) > 0) else "heurísticas básicas"
        explanation += f"\n*Predicción basada en {method_desc} (experiencia, capacidad estadio, liga, rendimiento)*"
        
        return explanation

def create_basic_predictions_for_matches(db: Session, matches: List[Match], season: int) -> List[Dict[str, Any]]:
    """
    Crea predicciones básicas para una lista específica de partidos
    Usado para configuraciones personalizadas de Quiniela
    """
    predictor = BasicPredictor(db)
    predictions = []
    
    try:
        logger.info(f"Generating predictions for {len(matches)} custom selected matches")
        
        # Generar predicción para cada partido en orden
        for i, match in enumerate(matches[:15], 1):  # Máximo 15 partidos
            # Obtener equipos
            home_team = db.query(Team).filter_by(id=match.home_team_id).first()
            away_team = db.query(Team).filter_by(id=match.away_team_id).first()
            
            if not home_team or not away_team:
                logger.warning(f"Teams not found for match {match.id}")
                continue
            
            # Generar predicción usando el predictor básico
            prediction = predictor.predict_match(home_team, away_team)
            
            # Obtener estadisticas si están disponibles
            home_stats = db.query(TeamStatistics).filter_by(
                team_id=home_team.id, season=season
            ).first()
            away_stats = db.query(TeamStatistics).filter_by(
                team_id=away_team.id, season=season
            ).first()
            
            # Crear entrada para Quiniela
            prediction_entry = {
                "match_number": i,
                "match_id": match.id,
                "home_team": home_team.name,
                "away_team": away_team.name,
                "league": "La Liga" if match.league_id == 140 else "Segunda División",
                "match_date": match.match_date.isoformat() if match.match_date else None,
                "prediction": {
                    "result": prediction["predicted_result"],
                    "confidence": prediction["confidence"],
                    "probabilities": prediction["probabilities"]
                },
                "explanation": prediction.get("explanation", "Predicción básica personalizada")
            }
            
            # Añadir estadisticas si están disponibles
            if home_stats or away_stats:
                prediction_entry["statistics"] = {
                    "home_team": {
                        "wins": home_stats.wins if home_stats else 0,
                        "draws": home_stats.draws if home_stats else 0,
                        "losses": home_stats.losses if home_stats else 0,
                        "goals_for": home_stats.goals_for if home_stats else 0,
                        "goals_against": home_stats.goals_against if home_stats else 0,
                        "points": home_stats.points if home_stats else 0
                    },
                    "away_team": {
                        "wins": away_stats.wins if away_stats else 0,
                        "draws": away_stats.draws if away_stats else 0,
                        "losses": away_stats.losses if away_stats else 0,
                        "goals_for": away_stats.goals_for if away_stats else 0,
                        "goals_against": away_stats.goals_against if away_stats else 0,
                        "points": away_stats.points if away_stats else 0
                    }
                }
            
            predictions.append(prediction_entry)
            
        logger.info(f"Generated {len(predictions)} predictions for custom matches")
        return predictions
        
    except Exception as e:
        logger.error(f"Error generating predictions for custom matches: {str(e)}")
        return []


def create_basic_predictions_for_quiniela(db: Session, season: int) -> List[Dict[str, Any]]:
    """
    Crea predicciones básicas para una Quiniela completa (14-15 partidos)
    Selecciona partidos de las ligas españolas (La Liga + Segunda División)
    """
    predictor = BasicPredictor(db)
    predictions = []
    
    try:
        # Definir ligas españolas para Quiniela
        SPANISH_LEAGUES = [140, 141]  # La Liga, Segunda División
        
        # Buscar próximos partidos sin resultado de las ligas españolas
        # NOTA: Orden crucial para Quiniela oficial - La Liga primero, luego Segunda División
        # Hacer join con equipos para poder ordenar por nombre de equipo local
        from ..database.models import Team
        upcoming_matches = db.query(Match).join(
            Team, Match.home_team_id == Team.id
        ).filter(
            Match.season == season,
            Match.league_id.in_(SPANISH_LEAGUES),  # Solo ligas españolas
            Match.result.is_(None),  # Sin resultado aún
            Match.home_goals.is_(None)  # Sin goles registrados
        ).order_by(
            Match.league_id.desc(),  # La Liga (140) primero, Segunda (141) después
            Team.name,               # Orden alfabético por equipo local (tradicional Quiniela)
            Match.match_date         # Luego por fecha dentro de cada equipo
        ).all()
        
        logger.info(f"Found {len(upcoming_matches)} upcoming Spanish league matches for season {season}")
        
        if len(upcoming_matches) < 14:
            logger.warning(f"Only {len(upcoming_matches)} upcoming Spanish matches found, need at least 14 for Quiniela")
            return []
        
        # Estrategia de selección inteligente para Quiniela:
        # 1. Intentar obtener partidos de la misma jornada
        # 2. Priorizar La Liga (140) sobre Segunda División (141)
        # 3. Seleccionar hasta 15 partidos
        
        selected_matches = []
        
        # Agrupar por jornadas y fechas cercanas
        from collections import defaultdict
        matches_by_round = defaultdict(list)
        
        for match in upcoming_matches:
            # Agrupar por jornada si está disponible, sino por fecha
            group_key = match.round if match.round else match.match_date.strftime('%Y-%m-%d')
            matches_by_round[group_key].append(match)
        
        # Buscar la jornada con más partidos disponibles
        best_round = None
        best_count = 0
        
        for round_key, round_matches in matches_by_round.items():
            # Filtrar solo partidos de ligas españolas
            spanish_matches = [m for m in round_matches if m.league_id in SPANISH_LEAGUES]
            
            if len(spanish_matches) > best_count:
                best_count = len(spanish_matches)
                best_round = round_key
        
        logger.info(f"Best round found: {best_round} with {best_count} Spanish matches")
        
        if best_round and best_count >= 10:
            # Usar partidos de la mejor jornada
            round_matches = matches_by_round[best_round]
            
            # ORDEN OFICIAL QUINIELA: La Liga primero (ordenados), Segunda División después
            la_liga_matches = [m for m in round_matches if m.league_id == 140]
            segunda_matches = [m for m in round_matches if m.league_id == 141]
            
            # Los partidos ya vienen ordenados correctamente desde la query SQL
            # La Liga primero en orden alfabético, Segunda División después
            
            # Combinar: máximo 10 de La Liga + completar con Segunda hasta 15 (orden oficial)
            selected_matches = la_liga_matches[:10] + segunda_matches[:5]
            selected_matches = selected_matches[:15]  # Máximo 15
            
            logger.info(f"Selected {len(selected_matches)} matches from round {best_round} in OFFICIAL ORDER: {len([m for m in selected_matches if m.league_id == 140])} La Liga + {len([m for m in selected_matches if m.league_id == 141])} Segunda")
        else:
            # Fallback: seleccionar los primeros 15 partidos más próximos
            selected_matches = upcoming_matches[:15]
            logger.info(f"Fallback: Selected first 15 upcoming matches")
        
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