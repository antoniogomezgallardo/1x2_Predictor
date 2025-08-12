"""
Optimizador específico para la Quiniela Española
Implementa estrategias avanzadas basadas en las reglas oficiales
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from itertools import combinations
import logging

logger = logging.getLogger(__name__)


class QuinielaOptimizer:
    """
    Optimizador especializado para la Quiniela Española
    Considera factores específicos del juego oficial
    """
    
    def __init__(self):
        # Configuración específica de la Quiniela Española
        self.num_matches = 14  # Partidos principales
        self.pleno_al_15_options = ['0', '1', '2', 'M']  # Opciones para el pleno
        self.min_prize_threshold = 10  # Mínimo aciertos para premio
        self.results_mapping = {'1': 'home_win', 'X': 'draw', '2': 'away_win'}
        
        # Factores de peso para optimización
        self.confidence_weight = 0.4
        self.value_weight = 0.3
        self.contrast_weight = 0.2
        self.form_weight = 0.1
    
    def select_quiniela_matches(self, available_matches: List[Dict], season: int) -> List[Dict]:
        """
        Selecciona los 14 partidos más óptimos para la quiniela de la jornada
        Basado en criterios específicos de la Quiniela Española
        """
        logger.info(f"Selecting optimal 14 matches from {len(available_matches)} available")
        
        if len(available_matches) < 14:
            logger.warning(f"Insufficient matches: {len(available_matches)}, need 14")
            return available_matches
        
        # Calcular puntuación de optimización para cada partido
        scored_matches = []
        for match in available_matches:
            score = self._calculate_match_score(match)
            scored_matches.append({
                'match': match,
                'optimization_score': score
            })
        
        # Ordenar por puntuación y seleccionar top 14
        scored_matches.sort(key=lambda x: x['optimization_score'], reverse=True)
        selected_matches = [item['match'] for item in scored_matches[:14]]
        
        logger.info(f"Selected 14 matches with optimization scores: {[round(item['optimization_score'], 3) for item in scored_matches[:14]]}")
        return selected_matches
    
    def _calculate_match_score(self, match: Dict) -> float:
        """
        Calcula puntuación de optimización para un partido
        Considera factores específicos de la Quiniela
        """
        score = 0.0
        
        # Factor 1: Calidad de datos disponibles
        data_quality = self._assess_data_quality(match)
        score += data_quality * 0.25
        
        # Factor 2: Importancia del partido (liga, posición en tabla)
        importance = self._assess_match_importance(match)
        score += importance * 0.20
        
        # Factor 3: Predictibilidad (evitar partidos muy aleatorios)
        predictability = self._assess_predictability(match)
        score += predictability * 0.25
        
        # Factor 4: Valor de apuesta (evitar favoritos extremos)
        betting_value = self._assess_betting_value(match)
        score += betting_value * 0.30
        
        return score
    
    def _assess_data_quality(self, match: Dict) -> float:
        """Evalúa la calidad de datos disponibles para el partido"""
        score = 0.0
        
        # Verificar estadísticas de equipos
        if match.get('home_stats') and match.get('away_stats'):
            score += 0.4
        
        # Verificar datos históricos
        if match.get('h2h_data'):
            score += 0.3
        
        # Verificar forma reciente
        if match.get('home_form') and match.get('away_form'):
            score += 0.3
        
        return min(score, 1.0)
    
    def _assess_match_importance(self, match: Dict) -> float:
        """Evalúa la importancia del partido"""
        score = 0.5  # Base score
        
        # Priorizar La Liga sobre Segunda División
        if match.get('league_id') == 140:  # La Liga
            score += 0.3
        elif match.get('league_id') == 141:  # Segunda División
            score += 0.1
        
        # Considerar jornada (partidos de final de temporada pueden ser menos predecibles)
        round_info = match.get('round', '')
        if 'final' in round_info.lower() or 'playoff' in round_info.lower():
            score += 0.2  # Partidos importantes
        
        return min(score, 1.0)
    
    def _assess_predictability(self, match: Dict) -> float:
        """Evalúa qué tan predecible es el partido"""
        score = 0.5
        
        home_stats = match.get('home_stats')
        away_stats = match.get('away_stats')
        
        if home_stats and away_stats:
            # Diferencia en puntos por partido
            home_ppg = home_stats.points / max(home_stats.matches_played, 1)
            away_ppg = away_stats.points / max(away_stats.matches_played, 1)
            ppg_diff = abs(home_ppg - away_ppg)
            
            # Diferencia moderada = más predecible
            if 0.5 <= ppg_diff <= 1.5:
                score += 0.3
            elif ppg_diff > 2.0:
                score += 0.1  # Muy desigual, menos interesante
            
            # Consistencia en resultados
            home_consistency = self._calculate_consistency(home_stats)
            away_consistency = self._calculate_consistency(away_stats)
            avg_consistency = (home_consistency + away_consistency) / 2
            score += avg_consistency * 0.2
        
        return min(score, 1.0)
    
    def _assess_betting_value(self, match: Dict) -> float:
        """Evalúa el valor de apuesta del partido"""
        score = 0.5
        
        # Evitar favoritos extremos (bajo valor) y resultados muy inciertos
        home_odds = match.get('home_odds', 2.0)
        draw_odds = match.get('draw_odds', 3.0)
        away_odds = match.get('away_odds', 2.0)
        
        if home_odds and draw_odds and away_odds:
            # Buscar partidos con odds balanceadas (mejor valor)
            odds_range = max(home_odds, draw_odds, away_odds) - min(home_odds, draw_odds, away_odds)
            
            if 1.0 <= odds_range <= 2.5:  # Rango óptimo
                score += 0.3
            elif odds_range > 3.0:  # Muy desbalanceado
                score -= 0.2
        
        return max(score, 0.0)
    
    def _calculate_consistency(self, stats) -> float:
        """Calcula la consistencia de un equipo"""
        if not stats or stats.matches_played < 5:
            return 0.3  # Datos insuficientes
        
        win_rate = stats.wins / stats.matches_played
        
        # Equipos con win rate entre 30-70% son más consistentes para pronósticos
        if 0.3 <= win_rate <= 0.7:
            return 0.8
        elif 0.1 <= win_rate <= 0.9:
            return 0.5
        else:
            return 0.2
    
    def generate_pleno_al_15_prediction(self, match_predictions: List[Dict]) -> str:
        """
        Genera predicción para el Pleno al 15 basado en análisis de goles
        Solo aplicable si se predicen correctamente los 14 partidos
        """
        if len(match_predictions) != 14:
            return '1'  # Default
        
        # Analizar tendencias de goles en los partidos seleccionados
        total_expected_goals = 0
        high_scoring_matches = 0
        
        for prediction in match_predictions:
            expected_goals = prediction.get('expected_goals', 2.5)
            total_expected_goals += expected_goals
            
            if expected_goals > 3.0:
                high_scoring_matches += 1
        
        avg_goals = total_expected_goals / 14
        
        # Lógica de predicción del Pleno al 15
        if avg_goals < 1.5 and high_scoring_matches <= 2:
            return '0'  # Jornada con pocos goles
        elif 1.5 <= avg_goals <= 2.2 and high_scoring_matches <= 4:
            return '1'  # Jornada normal
        elif 2.2 <= avg_goals <= 3.0 and high_scoring_matches <= 6:
            return '2'  # Jornada con algunos goles
        else:
            return 'M'  # Jornada con muchos goles
    
    def calculate_combination_value(self, predictions: List[Dict], bet_amount: float = 1.0) -> Dict:
        """
        Calcula el valor esperado de una combinación de predicciones
        Considera el sistema de premios de la Quiniela
        """
        total_confidence = 1.0
        for pred in predictions:
            total_confidence *= pred.get('confidence', 0.33)
        
        # Calcular probabilidades de diferentes niveles de acierto
        prob_10_plus = self._calculate_min_success_probability(predictions, 10)
        prob_12_plus = self._calculate_min_success_probability(predictions, 12)
        prob_14 = total_confidence
        
        # Estimación de premios (basado en datos históricos)
        estimated_prizes = {
            10: 15.0,   # €15 promedio para 10 aciertos
            11: 25.0,   # €25 promedio para 11 aciertos
            12: 80.0,   # €80 promedio para 12 aciertos
            13: 500.0,  # €500 promedio para 13 aciertos
            14: 15000.0 # €15,000 promedio para 14 aciertos + pleno
        }
        
        # Calcular valor esperado
        expected_value = (
            prob_10_plus * estimated_prizes[10] +
            prob_12_plus * estimated_prizes[12] +
            prob_14 * estimated_prizes[14]
        ) - bet_amount
        
        return {
            'expected_value': expected_value,
            'total_confidence': total_confidence,
            'prob_10_plus': prob_10_plus,
            'prob_14': prob_14,
            'roi_percentage': (expected_value / bet_amount) * 100
        }
    
    def _calculate_min_success_probability(self, predictions: List[Dict], min_successes: int) -> float:
        """
        Calcula probabilidad de obtener al menos min_successes aciertos
        Usando aproximación binomial
        """
        n = len(predictions)
        avg_prob = sum(pred.get('confidence', 0.33) for pred in predictions) / n
        
        # Aproximación usando distribución normal para n grande
        mean = n * avg_prob
        variance = n * avg_prob * (1 - avg_prob)
        std_dev = np.sqrt(variance)
        
        # Probabilidad de obtener al menos min_successes
        z_score = (min_successes - 0.5 - mean) / std_dev  # Corrección de continuidad
        prob = 1 - self._normal_cdf(z_score)
        
        return max(0.0, min(1.0, prob))
    
    def _normal_cdf(self, x: float) -> float:
        """Aproximación de la función de distribución acumulativa normal estándar"""
        return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 * x**2 / np.pi)))
    
    def suggest_multiple_combinations(self, base_predictions: List[Dict], budget: float = 10.0) -> List[Dict]:
        """
        Sugiere múltiples combinaciones para optimizar la inversión
        Estrategia de quinielas múltiples/reducidas
        """
        combinations = []
        
        # Identificar partidos con mayor incertidumbre
        uncertain_matches = []
        for i, pred in enumerate(base_predictions):
            if pred.get('confidence', 0) < 0.6:  # Baja confianza
                uncertain_matches.append(i)
        
        if len(uncertain_matches) <= 3 and budget >= 5.0:
            # Generar combinaciones múltiples para partidos inciertos
            for uncertain_idx in uncertain_matches[:2]:  # Máximo 2 partidos
                alternative = base_predictions.copy()
                
                # Cambiar predicción al segundo resultado más probable
                original_pred = alternative[uncertain_idx]['predicted_result']
                probs = alternative[uncertain_idx]['probabilities']
                
                # Encontrar segunda opción más probable
                sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_probs) > 1:
                    alternative[uncertain_idx]['predicted_result'] = sorted_probs[1][0]
                    alternative[uncertain_idx]['confidence'] = sorted_probs[1][1]
                    
                    combinations.append({
                        'predictions': alternative,
                        'variation': f"Partido {uncertain_idx + 1}: {original_pred} → {sorted_probs[1][0]}",
                        'investment': min(budget * 0.3, 3.0)
                    })
        
        # Combinación base (mayor confianza)
        combinations.insert(0, {
            'predictions': base_predictions,
            'variation': "Combinación principal",
            'investment': budget * 0.7
        })
        
        return combinations