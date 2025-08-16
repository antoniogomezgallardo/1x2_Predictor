from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ...infrastructure.database.base import Base


class AdvancedTeamStatistics(Base):
    """
    Estadísticas avanzadas de equipos recolectadas de FBRef y otras fuentes
    Incluye xG, xA, xT, PPDA, Pass Networks y métricas de vanguardia
    """
    __tablename__ = "advanced_team_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    season = Column(Integer, nullable=False)
    league_id = Column(Integer, nullable=False)
    
    # Metadata
    data_source = Column(String(50), nullable=False, default='fbref')  # fbref, opta, etc.
    last_updated = Column(DateTime, default=datetime.utcnow)
    matches_analyzed = Column(Integer, default=0)
    
    # EXPECTED GOALS (xG) METRICS
    xg_for = Column(Float)  # Expected Goals a favor
    xg_against = Column(Float)  # Expected Goals en contra
    xg_difference = Column(Float)  # Diferencia xG
    xg_per_match = Column(Float)  # xG promedio por partido
    xg_performance = Column(Float)  # Goles reales / xG (eficiencia)
    
    # EXPECTED ASSISTS (xA) METRICS
    xa_for = Column(Float)  # Expected Assists total
    xa_against = Column(Float)  # Expected Assists en contra
    xa_per_match = Column(Float)  # xA promedio por partido
    xa_performance = Column(Float)  # Asistencias reales / xA
    
    # EXPECTED THREAT (xT) METRICS
    xt_for = Column(Float)  # Expected Threat total
    xt_against = Column(Float)  # Expected Threat en contra
    xt_per_possession = Column(Float)  # xT por posesión
    xt_final_third = Column(Float)  # xT en último tercio
    
    # PRESSING METRICS (PPDA = Passes Per Defensive Action)
    ppda = Column(Float)  # PPDA cuando el equipo defiende
    ppda_allowed = Column(Float)  # PPDA cuando el oponente defiende
    pressing_intensity = Column(Float)  # Intensidad de presión
    high_turnovers = Column(Integer)  # Recuperaciones en campo rival
    
    # POSSESSION METRICS
    possession_pct = Column(Float)  # Porcentaje de posesión
    possession_final_third = Column(Float)  # Posesión en último tercio
    possession_penalty_area = Column(Float)  # Posesión en área rival
    
    # PASSING NETWORKS
    pass_completion_pct = Column(Float)  # % de pases completados
    progressive_passes = Column(Integer)  # Pases progresivos
    progressive_distance = Column(Float)  # Distancia progresiva total
    passes_into_box = Column(Integer)  # Pases al área
    packing_rate = Column(Float)  # Tasa de empaquetamiento
    pass_network_centrality = Column(Float)  # Centralidad de red de pases
    
    # DEFENSIVE METRICS
    tackles_per_match = Column(Float)  # Tackles por partido
    interceptions_per_match = Column(Float)  # Intercepciones por partido
    blocks_per_match = Column(Float)  # Bloqueos por partido
    clearances_per_match = Column(Float)  # Despejes por partido
    defensive_actions_per_match = Column(Float)  # Acciones defensivas totales
    
    # ATTACKING METRICS
    shots_per_match = Column(Float)  # Tiros por partido
    shots_on_target_pct = Column(Float)  # % tiros a puerta
    big_chances_created = Column(Integer)  # Grandes ocasiones creadas
    big_chances_missed = Column(Integer)  # Grandes ocasiones falladas
    goal_conversion_rate = Column(Float)  # Tasa de conversión de goles
    
    # TRANSITIONS
    counter_attacks = Column(Integer)  # Contraataques realizados
    counter_attack_goals = Column(Integer)  # Goles de contraataque
    set_piece_goals = Column(Integer)  # Goles de jugadas a balón parado
    
    # FORM AND MOMENTUM
    recent_form_xg = Column(Float)  # xG en últimos 5 partidos
    momentum_score = Column(Float)  # Puntuación de momento (calculada)
    performance_trend = Column(String(20))  # 'improving', 'stable', 'declining'
    
    # Relaciones
    team = relationship("Team", foreign_keys=[team_id])
    
    def __repr__(self):
        return f"<AdvancedTeamStatistics(team_id={self.team_id}, season={self.season}, xG={self.xg_for})>"


class MatchAdvancedStatistics(Base):
    """
    Estadísticas avanzadas de partidos individuales
    Datos detallados por partido para análisis granular
    """
    __tablename__ = "match_advanced_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    
    # Metadata
    data_source = Column(String(50), nullable=False, default='fbref')
    last_updated = Column(DateTime, default=datetime.utcnow)
    data_quality_score = Column(Float)  # 0-1, calidad de los datos
    
    # EXPECTED GOALS POR EQUIPO
    home_xg = Column(Float)
    away_xg = Column(Float)
    home_xg_first_half = Column(Float)
    away_xg_first_half = Column(Float)
    home_xg_second_half = Column(Float)
    away_xg_second_half = Column(Float)
    
    # EXPECTED ASSISTS
    home_xa = Column(Float)
    away_xa = Column(Float)
    
    # EXPECTED THREAT
    home_xt = Column(Float)
    away_xt = Column(Float)
    
    # PRESSING METRICS
    home_ppda = Column(Float)  # Passes allowed per defensive action
    away_ppda = Column(Float)
    home_high_turnovers = Column(Integer)
    away_high_turnovers = Column(Integer)
    
    # POSSESSION DETAILED
    home_possession = Column(Float)
    away_possession = Column(Float)
    home_possession_final_third = Column(Float)
    away_possession_final_third = Column(Float)
    
    # PASSING METRICS
    home_pass_accuracy = Column(Float)
    away_pass_accuracy = Column(Float)
    home_progressive_passes = Column(Integer)
    away_progressive_passes = Column(Integer)
    home_passes_into_box = Column(Integer)
    away_passes_into_box = Column(Integer)
    
    # SHOTS AND FINISHING
    home_shots = Column(Integer)
    away_shots = Column(Integer)
    home_shots_on_target = Column(Integer)
    away_shots_on_target = Column(Integer)
    home_big_chances = Column(Integer)
    away_big_chances = Column(Integer)
    
    # DEFENSIVE ACTIONS
    home_tackles = Column(Integer)
    away_tackles = Column(Integer)
    home_interceptions = Column(Integer)
    away_interceptions = Column(Integer)
    home_blocks = Column(Integer)
    away_blocks = Column(Integer)
    
    # TEMPO AND RHYTHM
    match_tempo = Column(Float)  # Pases por minuto promedio
    match_intensity = Column(Float)  # Intensidad del partido (calculada)
    home_build_up_speed = Column(Float)  # Velocidad de construcción
    away_build_up_speed = Column(Float)
    
    # SITUATIONAL PERFORMANCE
    home_performance_vs_xg = Column(Float)  # Goles vs xG
    away_performance_vs_xg = Column(Float)
    match_unpredictability = Column(Float)  # Qué tan impredecible fue el resultado
    
    # ADVANCED INSIGHTS
    tactical_approach_home = Column(String(50))  # 'defensive', 'balanced', 'attacking'
    tactical_approach_away = Column(String(50))
    key_moment_minute = Column(Integer)  # Minuto del momento clave
    key_moment_type = Column(String(50))  # 'goal', 'red_card', 'injury', etc.
    
    # QUALITY METRICS
    shot_quality_home = Column(Float)  # xG promedio por tiro
    shot_quality_away = Column(Float)
    chance_quality_home = Column(Float)  # xA promedio por oportunidad
    chance_quality_away = Column(Float)
    
    # Relaciones
    match = relationship("Match", foreign_keys=[match_id])
    
    def __repr__(self):
        return f"<MatchAdvancedStatistics(match_id={self.match_id}, home_xG={self.home_xg}, away_xG={self.away_xg})>"


class PlayerAdvancedStatistics(Base):
    """
    Estadísticas avanzadas de jugadores individuales
    Para análisis de impacto de jugadores clave
    """
    __tablename__ = "player_advanced_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    player_api_id = Column(Integer, nullable=False)  # ID del jugador en API-Football
    player_name = Column(String(100), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    season = Column(Integer, nullable=False)
    position = Column(String(20))  # 'GK', 'DEF', 'MID', 'FWD'
    
    # Metadata
    data_source = Column(String(50), nullable=False, default='fbref')
    last_updated = Column(DateTime, default=datetime.utcnow)
    minutes_played = Column(Integer, default=0)
    matches_played = Column(Integer, default=0)
    
    # EXPECTED GOALS AND ASSISTS
    player_xg = Column(Float)
    player_xa = Column(Float)
    xg_per_90 = Column(Float)
    xa_per_90 = Column(Float)
    
    # EXPECTED THREAT
    player_xt = Column(Float)
    xt_per_90 = Column(Float)
    
    # PROGRESSIVE ACTIONS
    progressive_passes = Column(Integer)
    progressive_carries = Column(Integer)
    progressive_distance = Column(Float)
    
    # CREATION AND FINISHING
    big_chances_created = Column(Integer)
    big_chances_missed = Column(Integer)
    shot_quality = Column(Float)  # xG por tiro
    
    # DEFENSIVE CONTRIBUTION
    defensive_actions = Column(Integer)
    successful_dribbles_against = Column(Integer)
    aerial_duels_won_pct = Column(Float)
    
    # IMPACT METRICS
    team_performance_with_player = Column(Float)  # xG difference when playing
    team_performance_without_player = Column(Float)  # xG difference when not playing
    player_impact_score = Column(Float)  # Calculado: contribución al equipo
    
    # Relaciones
    team = relationship("Team", foreign_keys=[team_id])
    
    def __repr__(self):
        return f"<PlayerAdvancedStatistics(name={self.player_name}, team_id={self.team_id}, xG={self.player_xg})>"


class MarketIntelligence(Base):
    """
    Inteligencia de mercado y análisis de cuotas
    Para incorporar conocimiento del mercado de apuestas
    """
    __tablename__ = "market_intelligence"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    
    # Metadata
    data_source = Column(String(50), nullable=False)  # 'bet365', 'pinnacle', etc.
    collection_time = Column(DateTime, default=datetime.utcnow)
    time_before_match = Column(Integer)  # Horas antes del partido
    
    # OPENING ODDS
    opening_home = Column(Float)
    opening_draw = Column(Float)
    opening_away = Column(Float)
    
    # CLOSING ODDS
    closing_home = Column(Float)
    closing_draw = Column(Float)
    closing_away = Column(Float)
    
    # MARKET MOVEMENTS
    home_odds_movement = Column(Float)  # Cambio en cuotas locales
    draw_odds_movement = Column(Float)
    away_odds_movement = Column(Float)
    total_volume_estimate = Column(Float)  # Volumen estimado de apuestas
    
    # IMPLIED PROBABILITIES
    market_prob_home = Column(Float)
    market_prob_draw = Column(Float)
    market_prob_away = Column(Float)
    market_overround = Column(Float)  # Margen de la casa
    
    # SMART MONEY INDICATORS
    sharp_money_home = Column(Float)  # % dinero profesional en local
    sharp_money_draw = Column(Float)
    sharp_money_away = Column(Float)
    public_betting_home = Column(Float)  # % apuestas públicas en local
    
    # VALUE OPPORTUNITIES
    value_bet_indicator = Column(String(10))  # 'HOME', 'DRAW', 'AWAY', 'NONE'
    value_percentage = Column(Float)  # % de valor encontrado
    kelly_criterion_home = Column(Float)  # Tamaño de apuesta Kelly
    kelly_criterion_draw = Column(Float)
    kelly_criterion_away = Column(Float)
    
    # MARKET CONSENSUS
    bookmaker_count = Column(Integer)  # Número de casas analizadas
    consensus_favorite = Column(String(10))  # 'HOME', 'DRAW', 'AWAY'
    market_efficiency_score = Column(Float)  # Qué tan eficiente es el mercado
    
    # Relaciones
    match = relationship("Match", foreign_keys=[match_id])
    
    def __repr__(self):
        return f"<MarketIntelligence(match_id={self.match_id}, consensus={self.consensus_favorite})>"


class ExternalFactors(Base):
    """
    Factores externos que pueden influir en el rendimiento
    Clima, lesiones, motivación, etc.
    """
    __tablename__ = "external_factors"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow)
    data_quality = Column(Float)  # 0-1
    
    # WEATHER CONDITIONS
    temperature = Column(Float)  # Temperatura en celsius
    humidity = Column(Float)  # Humedad %
    wind_speed = Column(Float)  # Velocidad del viento km/h
    precipitation = Column(Float)  # Precipitación mm
    weather_condition = Column(String(50))  # 'sunny', 'rainy', 'cloudy', etc.
    weather_impact_score = Column(Float)  # Impacto estimado del clima
    
    # TEAM MOTIVATION FACTORS
    home_team_motivation = Column(Float)  # 0-1 basado en objetivos
    away_team_motivation = Column(Float)
    home_recent_form = Column(Float)  # Forma reciente
    away_recent_form = Column(Float)
    
    # INJURIES AND SUSPENSIONS
    home_key_players_out = Column(Integer)  # Jugadores clave ausentes
    away_key_players_out = Column(Integer)
    home_injury_impact = Column(Float)  # Impacto estimado de lesiones
    away_injury_impact = Column(Float)
    
    # FIXTURE CONGESTION
    home_days_rest = Column(Integer)  # Días de descanso
    away_days_rest = Column(Integer)
    home_recent_minutes = Column(Integer)  # Minutos jugados últimos 7 días
    away_recent_minutes = Column(Integer)
    fatigue_factor_home = Column(Float)  # Factor de fatiga
    fatigue_factor_away = Column(Float)
    
    # PSYCHOLOGICAL FACTORS
    home_pressure_level = Column(Float)  # Presión mediática/afición
    away_pressure_level = Column(Float)
    rivalry_intensity = Column(Float)  # Intensidad del derbi/rivalidad
    stakes_importance = Column(Float)  # Importancia del partido
    
    # SOCIAL SENTIMENT
    home_fan_sentiment = Column(Float)  # Sentiment en redes sociales
    away_fan_sentiment = Column(Float)
    media_attention = Column(Float)  # Atención mediática
    betting_public_sentiment = Column(Float)  # Sentiment del público apostador
    
    # TRAVEL AND LOGISTICS
    travel_distance = Column(Float)  # Distancia viajada por visitante
    travel_time = Column(Float)  # Tiempo de viaje
    time_zone_change = Column(Integer)  # Cambio de horario
    
    # Relaciones
    match = relationship("Match", foreign_keys=[match_id])
    
    def __repr__(self):
        return f"<ExternalFactors(match_id={self.match_id}, weather={self.weather_condition})>"