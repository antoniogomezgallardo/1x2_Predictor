"""
Advanced Data Collector - Sistema de recolección de datos avanzados
Orchestador principal para recolectar todas las fuentes de datos avanzadas
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .fbref_client import FBRefClient, normalize_team_name
from ..database.models import (
    Team, Match, AdvancedTeamStatistics, MatchAdvancedStatistics,
    PlayerAdvancedStatistics, MarketIntelligence, ExternalFactors
)

logger = logging.getLogger(__name__)

class AdvancedDataCollector:
    """
    Orchestador principal para recolección de datos avanzados
    Coordina múltiples fuentes para obtener datos de estado del arte
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.fbref_client = FBRefClient()
        self.collection_stats = {
            'teams_processed': 0,
            'matches_processed': 0,
            'players_processed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def collect_all_advanced_data(self, season: int, league_ids: List[int] = [140, 141]) -> Dict[str, Any]:
        """
        Recolecta todos los datos avanzados para una temporada
        Proceso completo de state-of-the-art data collection
        """
        logger.info(f"Starting advanced data collection for season {season}")
        self.collection_stats['start_time'] = datetime.now()
        
        try:
            # Paso 1: Recolectar estadísticas avanzadas de equipos
            await self._collect_team_advanced_stats(season, league_ids)
            
            # Paso 2: Recolectar estadísticas de partidos
            await self._collect_match_advanced_stats(season, league_ids)
            
            # Paso 3: Recolectar datos de jugadores clave
            await self._collect_player_advanced_stats(season, league_ids)
            
            # Paso 4: Recolectar inteligencia de mercado
            await self._collect_market_intelligence(season, league_ids)
            
            # Paso 5: Recolectar factores externos
            await self._collect_external_factors(season, league_ids)
            
            self.collection_stats['end_time'] = datetime.now()
            duration = self.collection_stats['end_time'] - self.collection_stats['start_time']
            
            logger.info(f"Advanced data collection completed in {duration.total_seconds():.2f} seconds")
            
            return {
                'status': 'completed',
                'season': season,
                'leagues': league_ids,
                'stats': self.collection_stats,
                'duration_seconds': duration.total_seconds(),
                'message': 'Advanced data collection completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error in advanced data collection: {e}")
            self.collection_stats['errors'] += 1
            return {
                'status': 'error',
                'season': season,
                'error': str(e),
                'stats': self.collection_stats
            }
    
    async def _collect_team_advanced_stats(self, season: int, league_ids: List[int]):
        """Recolecta estadísticas avanzadas de todos los equipos"""
        logger.info("Collecting advanced team statistics...")
        
        for league_id in league_ids:
            try:
                # Obtener equipos de la liga
                teams = self.db.query(Team).filter(Team.league_id == league_id).all()
                
                if not teams:
                    logger.warning(f"No teams found for league {league_id}")
                    continue
                
                # Recolectar datos de FBRef para la liga completa
                league_data = self.fbref_client.get_league_table_advanced(league_id, season)
                
                if not league_data:
                    logger.warning(f"No FBRef data available for league {league_id} season {season}")
                    continue
                
                # Procesar cada equipo
                for team in teams:
                    try:
                        # Buscar datos del equipo en los datos de la liga
                        team_data = None
                        normalized_name = normalize_team_name(team.name)
                        
                        for data in league_data:
                            if self._match_team_name(data['team_name'], normalized_name):
                                team_data = data
                                break
                        
                        if not team_data:
                            logger.warning(f"No FBRef data found for team {team.name}")
                            continue
                        
                        # Crear o actualizar estadísticas avanzadas
                        advanced_stats = self.db.query(AdvancedTeamStatistics).filter(
                            AdvancedTeamStatistics.team_id == team.id,
                            AdvancedTeamStatistics.season == season
                        ).first()
                        
                        if not advanced_stats:
                            advanced_stats = AdvancedTeamStatistics(
                                team_id=team.id,
                                season=season,
                                league_id=league_id
                            )
                            self.db.add(advanced_stats)
                        
                        # Actualizar con datos de FBRef
                        self._update_team_advanced_stats(advanced_stats, team_data)
                        
                        # Obtener estadísticas específicas del equipo
                        team_specific_data = self.fbref_client.get_team_advanced_stats(
                            team.name, league_id, season
                        )
                        
                        if team_specific_data:
                            self._update_team_specific_stats(advanced_stats, team_specific_data)
                        
                        self.collection_stats['teams_processed'] += 1
                        
                        # Rate limiting entre equipos
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error processing team {team.name}: {e}")
                        self.collection_stats['errors'] += 1
                        continue
                
                # Commit después de cada liga
                self.db.commit()
                logger.info(f"Completed advanced stats collection for league {league_id}")
                
            except Exception as e:
                logger.error(f"Error collecting stats for league {league_id}: {e}")
                self.collection_stats['errors'] += 1
                continue
    
    async def _collect_match_advanced_stats(self, season: int, league_ids: List[int]):
        """Recolecta estadísticas avanzadas de partidos"""
        logger.info("Collecting advanced match statistics...")
        
        # Obtener partidos recientes con resultados
        recent_matches = self.db.query(Match).filter(
            Match.season == season,
            Match.league_id.in_(league_ids),
            Match.result.isnot(None),
            Match.match_date > datetime.now() - timedelta(days=30)  # Últimos 30 días
        ).limit(50).all()  # Limitar para testing
        
        for match in recent_matches:
            try:
                # Verificar si ya tenemos estadísticas avanzadas
                existing_stats = self.db.query(MatchAdvancedStatistics).filter(
                    MatchAdvancedStatistics.match_id == match.id
                ).first()
                
                if existing_stats:
                    continue  # Ya tenemos datos para este partido
                
                # Obtener datos avanzados del partido
                match_data = self.fbref_client.get_match_advanced_data(
                    match.match_date, 
                    match.home_team.name if match.home_team else "Unknown",
                    match.away_team.name if match.away_team else "Unknown"
                )
                
                if match_data:
                    # Crear estadísticas avanzadas del partido
                    advanced_match_stats = MatchAdvancedStatistics(
                        match_id=match.id,
                        data_source='fbref'
                    )
                    
                    # Calcular estadísticas estimadas basadas en datos disponibles
                    self._calculate_estimated_match_stats(advanced_match_stats, match, match_data)
                    
                    self.db.add(advanced_match_stats)
                    self.collection_stats['matches_processed'] += 1
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing match {match.id}: {e}")
                self.collection_stats['errors'] += 1
                continue
        
        self.db.commit()
        logger.info(f"Completed match statistics collection")
    
    async def _collect_player_advanced_stats(self, season: int, league_ids: List[int]):
        """Recolecta estadísticas avanzadas de jugadores clave"""
        logger.info("Collecting player advanced statistics...")
        
        # Por ahora, crear entradas placeholder para jugadores clave
        # En implementación completa, se integraría con API de jugadores
        
        teams = self.db.query(Team).filter(Team.league_id.in_(league_ids)).all()
        
        for team in teams[:5]:  # Limitar para testing
            try:
                # Crear estadísticas placeholder para jugadores clave
                key_players = [
                    {'name': f'{team.name} Key Player 1', 'position': 'FWD'},
                    {'name': f'{team.name} Key Player 2', 'position': 'MID'},
                    {'name': f'{team.name} Key Player 3', 'position': 'DEF'}
                ]
                
                for player_info in key_players:
                    existing_player = self.db.query(PlayerAdvancedStatistics).filter(
                        PlayerAdvancedStatistics.player_name == player_info['name'],
                        PlayerAdvancedStatistics.team_id == team.id,
                        PlayerAdvancedStatistics.season == season
                    ).first()
                    
                    if not existing_player:
                        player_stats = PlayerAdvancedStatistics(
                            player_api_id=0,  # Placeholder
                            player_name=player_info['name'],
                            team_id=team.id,
                            season=season,
                            position=player_info['position'],
                            data_source='placeholder'
                        )
                        
                        # Generar estadísticas estimadas
                        self._generate_placeholder_player_stats(player_stats)
                        
                        self.db.add(player_stats)
                        self.collection_stats['players_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing players for team {team.name}: {e}")
                self.collection_stats['errors'] += 1
                continue
        
        self.db.commit()
        logger.info("Completed player statistics collection")
    
    async def _collect_market_intelligence(self, season: int, league_ids: List[int]):
        """Recolecta inteligencia de mercado"""
        logger.info("Collecting market intelligence...")
        
        # Obtener próximos partidos
        upcoming_matches = self.db.query(Match).filter(
            Match.season == season,
            Match.league_id.in_(league_ids),
            Match.result.is_(None),
            Match.match_date > datetime.now(),
            Match.match_date < datetime.now() + timedelta(days=7)
        ).limit(20).all()
        
        for match in upcoming_matches:
            try:
                # Verificar si ya tenemos inteligencia de mercado
                existing_intel = self.db.query(MarketIntelligence).filter(
                    MarketIntelligence.match_id == match.id
                ).first()
                
                if existing_intel:
                    continue
                
                # Crear inteligencia de mercado con datos estimados
                market_intel = MarketIntelligence(
                    match_id=match.id,
                    data_source='estimated',
                    time_before_match=int((match.match_date - datetime.now()).total_seconds() / 3600)
                )
                
                # Generar datos estimados basados en cuotas existentes
                self._generate_market_intelligence(market_intel, match)
                
                self.db.add(market_intel)
                
            except Exception as e:
                logger.error(f"Error processing market data for match {match.id}: {e}")
                self.collection_stats['errors'] += 1
                continue
        
        self.db.commit()
        logger.info("Completed market intelligence collection")
    
    async def _collect_external_factors(self, season: int, league_ids: List[int]):
        """Recolecta factores externos"""
        logger.info("Collecting external factors...")
        
        # Obtener próximos partidos
        upcoming_matches = self.db.query(Match).filter(
            Match.season == season,
            Match.league_id.in_(league_ids),
            Match.result.is_(None),
            Match.match_date > datetime.now(),
            Match.match_date < datetime.now() + timedelta(days=7)
        ).limit(20).all()
        
        for match in upcoming_matches:
            try:
                # Verificar si ya tenemos factores externos
                existing_factors = self.db.query(ExternalFactors).filter(
                    ExternalFactors.match_id == match.id
                ).first()
                
                if existing_factors:
                    continue
                
                # Crear factores externos estimados
                external_factors = ExternalFactors(
                    match_id=match.id,
                    data_quality=0.7  # Estimación
                )
                
                # Generar factores estimados
                self._generate_external_factors(external_factors, match)
                
                self.db.add(external_factors)
                
            except Exception as e:
                logger.error(f"Error processing external factors for match {match.id}: {e}")
                self.collection_stats['errors'] += 1
                continue
        
        self.db.commit()
        logger.info("Completed external factors collection")
    
    def _match_team_name(self, fbref_name: str, local_name: str) -> bool:
        """Compara nombres de equipos para matching"""
        fbref_clean = fbref_name.lower().strip()
        local_clean = local_name.lower().strip()
        
        # Matching exacto
        if fbref_clean == local_clean:
            return True
        
        # Matching parcial
        if fbref_clean in local_clean or local_clean in fbref_clean:
            return True
        
        # Mapping específico para equipos españoles
        mappings = {
            'real madrid': ['real madrid cf', 'real madrid'],
            'barcelona': ['fc barcelona', 'barcelona'],
            'atletico madrid': ['atletico de madrid', 'atlético madrid'],
            'athletic club': ['athletic bilbao', 'athletic'],
            'real sociedad': ['real sociedad de futbol'],
            'real betis': ['real betis balompie'],
            'celta vigo': ['rc celta de vigo', 'celta'],
            'valencia': ['valencia cf'],
            'sevilla': ['sevilla fc'],
            'villarreal': ['villarreal cf'],
            'espanyol': ['rcd espanyol'],
            'getafe': ['getafe cf'],
            'osasuna': ['ca osasuna'],
            'alaves': ['deportivo alaves'],
            'mallorca': ['rcd mallorca'],
            'cadiz': ['cadiz cf'],
            'elche': ['elche cf'],
            'levante': ['levante ud'],
            'rayo vallecano': ['rayo vallecano de madrid']
        }
        
        for key, variants in mappings.items():
            if key in fbref_clean and any(variant in local_clean for variant in variants):
                return True
            if key in local_clean and any(variant in fbref_clean for variant in variants):
                return True
        
        return False
    
    def _update_team_advanced_stats(self, stats: AdvancedTeamStatistics, data: Dict[str, Any]):
        """Actualiza estadísticas avanzadas del equipo con datos de FBRef"""
        stats.data_source = 'fbref'
        stats.last_updated = datetime.now()
        stats.matches_analyzed = data.get('matches_played', 0)
        
        # Expected Goals
        stats.xg_for = data.get('xg_for')
        stats.xg_against = data.get('xg_against')
        stats.xg_difference = data.get('xg_difference')
        
        if stats.matches_analyzed > 0:
            stats.xg_per_match = stats.xg_for / stats.matches_analyzed if stats.xg_for else 0
            # Calcular eficiencia xG
            goals_for = data.get('goals_for', 0)
            if stats.xg_for and stats.xg_for > 0:
                stats.xg_performance = goals_for / stats.xg_for
    
    def _update_team_specific_stats(self, stats: AdvancedTeamStatistics, data: Dict[str, Any]):
        """Actualiza estadísticas específicas del equipo"""
        if not data:
            return
        
        # Possession
        stats.possession_pct = data.get('possession_pct')
        
        # Passing
        stats.pass_completion_pct = data.get('pass_completion_pct')
        stats.progressive_passes = data.get('progressive_passes')
        
        # Defensive
        stats.tackles_per_match = data.get('tackles', 0) / max(stats.matches_analyzed, 1)
        stats.interceptions_per_match = data.get('interceptions', 0) / max(stats.matches_analyzed, 1)
        stats.blocks_per_match = data.get('blocks', 0) / max(stats.matches_analyzed, 1)
        
        # PPDA estimado
        stats.ppda_own = data.get('ppda_estimated')
        
        # Expected Goals detallados
        stats.shots_per_match = data.get('shots_total', 0) / max(stats.matches_analyzed, 1)
        if data.get('shots_on_target') and data.get('shots_total'):
            stats.shots_on_target_pct = data['shots_on_target'] / data['shots_total'] * 100
    
    def _calculate_estimated_match_stats(self, stats: MatchAdvancedStatistics, match: Match, data: Dict[str, Any]):
        """Calcula estadísticas estimadas del partido"""
        stats.data_quality_score = 0.6  # Estimación
        
        # Expected Goals estimados basados en resultados reales
        if match.home_goals is not None and match.away_goals is not None:
            # Estimación simple: ajustar xG basado en goles reales
            total_goals = match.home_goals + match.away_goals
            
            if total_goals > 0:
                stats.home_xg = match.home_goals * 0.8 + (total_goals * 0.4) * (match.home_goals / total_goals)
                stats.away_xg = match.away_goals * 0.8 + (total_goals * 0.4) * (match.away_goals / total_goals)
            else:
                stats.home_xg = 0.5
                stats.away_xg = 0.5
            
            # Distribución por tiempo
            stats.home_xg_first_half = stats.home_xg * 0.45
            stats.home_xg_second_half = stats.home_xg * 0.55
            stats.away_xg_first_half = stats.away_xg * 0.45
            stats.away_xg_second_half = stats.away_xg * 0.55
        
        # Expected Assists estimados
        stats.home_xa = stats.home_xg * 0.7 if stats.home_xg else 0
        stats.away_xa = stats.away_xg * 0.7 if stats.away_xg else 0
        
        # Expected Threat estimado
        stats.home_xt = stats.home_xg * 1.2 if stats.home_xg else 0
        stats.away_xt = stats.away_xg * 1.2 if stats.away_xg else 0
        
        # Métricas estimadas
        stats.match_tempo = 12.5  # Promedio de pases por minuto
        stats.match_intensity = 0.7  # Intensidad estimada
    
    def _generate_placeholder_player_stats(self, player_stats: PlayerAdvancedStatistics):
        """Genera estadísticas placeholder para jugadores"""
        import random
        
        position_multipliers = {
            'FWD': {'xg': 1.5, 'xa': 0.8, 'defensive': 0.3},
            'MID': {'xg': 0.8, 'xa': 1.2, 'defensive': 0.7},
            'DEF': {'xg': 0.3, 'xa': 0.5, 'defensive': 1.5},
            'GK': {'xg': 0.1, 'xa': 0.2, 'defensive': 2.0}
        }
        
        multiplier = position_multipliers.get(player_stats.position, position_multipliers['MID'])
        
        player_stats.player_xg = random.uniform(0.1, 0.8) * multiplier['xg']
        player_stats.player_xa = random.uniform(0.1, 0.6) * multiplier['xa']
        player_stats.xg_per_90 = player_stats.player_xg
        player_stats.xa_per_90 = player_stats.player_xa
        player_stats.defensive_actions = int(random.uniform(1, 8) * multiplier['defensive'])
        player_stats.player_impact_score = random.uniform(0.3, 0.9)
    
    def _generate_market_intelligence(self, intel: MarketIntelligence, match: Match):
        """Genera inteligencia de mercado estimada"""
        import random
        
        # Usar cuotas existentes como base
        if match.home_odds and match.draw_odds and match.away_odds:
            intel.opening_home = match.home_odds * random.uniform(0.95, 1.05)
            intel.opening_draw = match.draw_odds * random.uniform(0.95, 1.05)
            intel.opening_away = match.away_odds * random.uniform(0.95, 1.05)
            
            intel.closing_home = match.home_odds
            intel.closing_draw = match.draw_odds
            intel.closing_away = match.away_odds
            
            # Movimientos de cuotas
            intel.home_odds_movement = intel.closing_home - intel.opening_home
            intel.draw_odds_movement = intel.closing_draw - intel.opening_draw
            intel.away_odds_movement = intel.closing_away - intel.opening_away
            
            # Probabilidades implícitas
            total_prob = (1/intel.closing_home) + (1/intel.closing_draw) + (1/intel.closing_away)
            intel.market_prob_home = (1/intel.closing_home) / total_prob
            intel.market_prob_draw = (1/intel.closing_draw) / total_prob
            intel.market_prob_away = (1/intel.closing_away) / total_prob
            intel.market_overround = total_prob - 1
            
            # Consenso
            if intel.market_prob_home > intel.market_prob_draw and intel.market_prob_home > intel.market_prob_away:
                intel.consensus_favorite = 'HOME'
            elif intel.market_prob_away > intel.market_prob_draw:
                intel.consensus_favorite = 'AWAY'
            else:
                intel.consensus_favorite = 'DRAW'
    
    def _generate_external_factors(self, factors: ExternalFactors, match: Match):
        """Genera factores externos estimados"""
        import random
        
        # Clima estimado
        factors.temperature = random.uniform(10, 30)
        factors.humidity = random.uniform(40, 80)
        factors.wind_speed = random.uniform(0, 20)
        factors.weather_condition = random.choice(['sunny', 'cloudy', 'partly_cloudy'])
        factors.weather_impact_score = random.uniform(0.0, 0.3)
        
        # Motivación estimada
        factors.home_team_motivation = random.uniform(0.6, 1.0)
        factors.away_team_motivation = random.uniform(0.6, 1.0)
        
        # Descanso
        factors.home_days_rest = random.randint(3, 7)
        factors.away_days_rest = random.randint(3, 7)
        factors.fatigue_factor_home = max(0.1, 1.0 - (7 - factors.home_days_rest) * 0.1)
        factors.fatigue_factor_away = max(0.1, 1.0 - (7 - factors.away_days_rest) * 0.1)
        
        # Factores psicológicos
        factors.rivalry_intensity = random.uniform(0.1, 0.9)
        factors.stakes_importance = random.uniform(0.3, 1.0)
        
        # Sentiment estimado
        factors.home_fan_sentiment = random.uniform(0.4, 0.9)
        factors.away_fan_sentiment = random.uniform(0.4, 0.9)
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Retorna el estado actual de la recolección"""
        return {
            'stats': self.collection_stats,
            'is_running': self.collection_stats['start_time'] and not self.collection_stats['end_time']
        }