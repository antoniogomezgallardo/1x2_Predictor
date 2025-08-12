"""
Servicio para generar explicaciones razonadas de las predicciones
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PredictionExplainer:
    """
    Genera explicaciones comprensibles para las predicciones del modelo ML
    """
    
    def __init__(self):
        self.explanation_templates = {
            "home_win": [
                "El equipo local tiene ventaja significativa",
                "Estadísticas favorecen claramente al equipo de casa",
                "El equipo local muestra mejor forma reciente"
            ],
            "draw": [
                "Los equipos están muy igualados",
                "Historial reciente sugiere un resultado ajustado",
                "Ambos equipos tienen estadísticas similares"
            ],
            "away_win": [
                "El equipo visitante tiene mejor forma",
                "Las estadísticas favorecen al equipo de fuera",
                "El equipo visitante ha demostrado solidez a domicilio"
            ]
        }
    
    def generate_explanation(self, match_data: Dict[str, Any], prediction: str, 
                           probabilities: Dict[str, float], features: Dict[str, float]) -> str:
        """
        Genera una explicación detallada de por qué se hizo esta predicción
        """
        try:
            home_team = match_data.get("home_team", {}).get("name", "Local")
            away_team = match_data.get("away_team", {}).get("name", "Visitante")
            
            explanation_parts = []
            
            # 1. Resultado principal y confianza
            confidence = max(probabilities.values()) if probabilities else 0.5
            confidence_level = self._get_confidence_level(confidence)
            
            result_text = {
                "1": f"Victoria de {home_team}",
                "X": "Empate",
                "2": f"Victoria de {away_team}"
            }.get(prediction, "Resultado incierto")
            
            explanation_parts.append(f"**Predicción: {result_text}** (Confianza: {confidence_level})")
            
            # 2. Factores clave que influyen en la decisión
            key_factors = self._identify_key_factors(features, match_data)
            if key_factors:
                explanation_parts.append("\n**Factores decisivos:**")
                for factor in key_factors[:3]:  # Top 3 factores
                    explanation_parts.append(f"• {factor}")
            
            # 3. Análisis estadístico
            stats_analysis = self._analyze_team_statistics(match_data, prediction)
            if stats_analysis:
                explanation_parts.append(f"\n**Análisis estadístico:**\n{stats_analysis}")
            
            # 4. Distribución de probabilidades
            explanation_parts.append(f"\n**Probabilidades:**")
            explanation_parts.append(f"• {home_team} gana: {probabilities.get('home_win', 0.33):.1%}")
            explanation_parts.append(f"• Empate: {probabilities.get('draw', 0.33):.1%}")
            explanation_parts.append(f"• {away_team} gana: {probabilities.get('away_win', 0.33):.1%}")
            
            # 5. Recomendación basada en confianza
            recommendation = self._generate_recommendation(confidence, prediction)
            explanation_parts.append(f"\n**Recomendación:** {recommendation}")
            
            return "\n".join(explanation_parts)
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return f"Predicción: {prediction} - Análisis automático generado por el sistema ML"
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convierte confianza numérica a texto descriptivo"""
        if confidence >= 0.8:
            return "Muy Alta"
        elif confidence >= 0.7:
            return "Alta"
        elif confidence >= 0.6:
            return "Media-Alta"
        elif confidence >= 0.5:
            return "Media"
        else:
            return "Baja"
    
    def _identify_key_factors(self, features: Dict[str, float], match_data: Dict[str, Any]) -> List[str]:
        """Identifica los factores más importantes para esta predicción"""
        factors = []
        
        # Ventaja local
        home_advantage = features.get('home_advantage', 0)
        if home_advantage > 0.1:
            factors.append("Fuerte ventaja del equipo local en casa")
        elif home_advantage < -0.1:
            factors.append("El equipo visitante tiene buen registro a domicilio")
        
        # Diferencia de puntos por partido
        ppg_diff = features.get('ppg_difference', 0)
        if ppg_diff > 0.5:
            home_team = match_data.get("home_team", {}).get("name", "Local")
            factors.append(f"{home_team} tiene mejor promedio de puntos por partido")
        elif ppg_diff < -0.5:
            away_team = match_data.get("away_team", {}).get("name", "Visitante")
            factors.append(f"{away_team} tiene mejor promedio de puntos por partido")
        
        # Diferencia de goles
        goal_diff = features.get('goal_diff_difference', 0)
        if goal_diff > 1.0:
            factors.append("Diferencia de goles favorable al equipo local")
        elif goal_diff < -1.0:
            factors.append("Diferencia de goles favorable al equipo visitante")
        
        # Porcentaje de victorias
        win_pct_diff = features.get('win_pct_diff', 0)
        if abs(win_pct_diff) > 0.2:
            if win_pct_diff > 0:
                factors.append("El equipo local tiene mejor porcentaje de victorias")
            else:
                factors.append("El equipo visitante tiene mejor porcentaje de victorias")
        
        # Factor ataque vs defensa
        attack_vs_defense = features.get('attack_vs_defense', 0)
        if attack_vs_defense > 0.3:
            factors.append("El ataque local supera claramente a la defensa visitante")
        elif attack_vs_defense < -0.3:
            factors.append("La defensa visitante es sólida contra el ataque local")
        
        return factors
    
    def _analyze_team_statistics(self, match_data: Dict[str, Any], prediction: str) -> str:
        """Analiza las estadísticas de los equipos"""
        home_stats = match_data.get("home_stats")
        away_stats = match_data.get("away_stats")
        
        if not home_stats or not away_stats:
            return "Datos estadísticos limitados para análisis detallado"
        
        analysis_parts = []
        
        # Análisis de forma
        home_win_rate = home_stats.wins / max(home_stats.matches_played, 1)
        away_win_rate = away_stats.wins / max(away_stats.matches_played, 1)
        
        home_team = match_data.get("home_team", {}).get("name", "Local")
        away_team = match_data.get("away_team", {}).get("name", "Visitante")
        
        analysis_parts.append(f"{home_team}: {home_win_rate:.1%} victorias ({home_stats.wins}V-{home_stats.draws}E-{home_stats.losses}D)")
        analysis_parts.append(f"{away_team}: {away_win_rate:.1%} victorias ({away_stats.wins}V-{away_stats.draws}E-{away_stats.losses}D)")
        
        # Análisis de goles
        home_goals_avg = home_stats.goals_for / max(home_stats.matches_played, 1)
        away_goals_avg = away_stats.goals_for / max(away_stats.matches_played, 1)
        
        analysis_parts.append(f"Goles por partido: {home_team} {home_goals_avg:.1f}, {away_team} {away_goals_avg:.1f}")
        
        # Solidez defensiva
        home_conceded_avg = home_stats.goals_against / max(home_stats.matches_played, 1)
        away_conceded_avg = away_stats.goals_against / max(away_stats.matches_played, 1)
        
        if home_conceded_avg < away_conceded_avg:
            analysis_parts.append(f"{home_team} tiene mejor defensa ({home_conceded_avg:.1f} vs {away_conceded_avg:.1f} goles recibidos)")
        elif away_conceded_avg < home_conceded_avg:
            analysis_parts.append(f"{away_team} tiene mejor defensa ({away_conceded_avg:.1f} vs {home_conceded_avg:.1f} goles recibidos)")
        
        return " | ".join(analysis_parts)
    
    def _generate_recommendation(self, confidence: float, prediction: str) -> str:
        """Genera recomendación de apuesta basada en confianza"""
        if confidence >= 0.75:
            return f"Apuesta recomendada en '{prediction}' - Alta confianza del modelo"
        elif confidence >= 0.65:
            return f"Apuesta moderada en '{prediction}' - Confianza media-alta"
        elif confidence >= 0.55:
            return f"Apuesta cautelosa en '{prediction}' - Confianza media"
        else:
            return "Partido incierto - Considerar no apostar o apuesta mínima"
    
    def generate_features_table(self, features: Dict[str, float], match_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Genera tabla con las características más importantes usadas en la predicción
        """
        important_features = [
            'home_advantage', 'ppg_difference', 'goal_diff_difference', 
            'win_pct_diff', 'attack_vs_defense', 'defense_vs_attack',
            'home_goals_per_game', 'away_goals_per_game', 
            'home_goals_against_per_game', 'away_goals_against_per_game'
        ]
        
        features_table = []
        
        for feature_name in important_features:
            if feature_name in features:
                feature_value = features[feature_name]
                description = self._get_feature_description(feature_name)
                impact = self._calculate_feature_impact(feature_name, feature_value)
                
                features_table.append({
                    'feature': description,
                    'value': round(feature_value, 3),
                    'impact': impact,
                    'interpretation': self._interpret_feature_value(feature_name, feature_value)
                })
        
        # Ordenar por impacto absoluto
        features_table.sort(key=lambda x: abs(x['value']), reverse=True)
        
        return features_table[:8]  # Top 8 características
    
    def _get_feature_description(self, feature_name: str) -> str:
        """Convierte nombres técnicos a descripciones comprensibles"""
        descriptions = {
            'home_advantage': 'Ventaja Local',
            'ppg_difference': 'Dif. Puntos/Partido',
            'goal_diff_difference': 'Dif. Goal Difference',
            'win_pct_diff': 'Dif. % Victorias',
            'attack_vs_defense': 'Ataque vs Defensa',
            'defense_vs_attack': 'Defensa vs Ataque',
            'home_goals_per_game': 'Goles Local/Partido',
            'away_goals_per_game': 'Goles Visitante/Partido',
            'home_goals_against_per_game': 'Goles Contra Local/Partido',
            'away_goals_against_per_game': 'Goles Contra Visitante/Partido'
        }
        return descriptions.get(feature_name, feature_name.replace('_', ' ').title())
    
    def _calculate_feature_impact(self, feature_name: str, value: float) -> str:
        """Calcula el impacto de una característica"""
        abs_value = abs(value)
        
        if abs_value > 1.0:
            return "Alto"
        elif abs_value > 0.5:
            return "Medio"
        elif abs_value > 0.2:
            return "Bajo"
        else:
            return "Mínimo"
    
    def _interpret_feature_value(self, feature_name: str, value: float) -> str:
        """Interpreta el valor de una característica"""
        if 'difference' in feature_name or 'diff' in feature_name:
            if value > 0.1:
                return "Favorece al Local"
            elif value < -0.1:
                return "Favorece al Visitante"
            else:
                return "Equilibrado"
        elif 'advantage' in feature_name:
            if value > 0.1:
                return "Ventaja Local"
            elif value < -0.1:
                return "Ventaja Visitante"
            else:
                return "Neutro"
        else:
            return f"{value:.2f}"