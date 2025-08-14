from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    short_name = Column(String(10))
    logo = Column(String(255))
    league_id = Column(Integer, nullable=False)  # 140 for La Liga, 141 for Segunda
    founded = Column(Integer)
    venue_name = Column(String(100))
    venue_capacity = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, unique=True, nullable=False)
    home_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    away_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    league_id = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    round = Column(String(50))
    match_date = Column(DateTime, nullable=False)
    status = Column(String(20))  # NS, 1H, HT, 2H, FT, etc.
    
    # Results
    home_goals = Column(Integer)
    away_goals = Column(Integer)
    result = Column(String(1))  # 1, X, 2
    
    # Odds
    home_odds = Column(Float)
    draw_odds = Column(Float)
    away_odds = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])


class TeamStatistics(Base):
    __tablename__ = "team_statistics"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    season = Column(Integer, nullable=False)
    league_id = Column(Integer, nullable=False)
    
    # General stats
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    points = Column(Integer, default=0)
    position = Column(Integer)
    
    # Home/Away splits
    home_wins = Column(Integer, default=0)
    home_draws = Column(Integer, default=0)
    home_losses = Column(Integer, default=0)
    away_wins = Column(Integer, default=0)
    away_draws = Column(Integer, default=0)
    away_losses = Column(Integer, default=0)
    
    # Form (last 5 matches)
    form = Column(String(5))  # e.g., "WWDLW"
    
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team")


class QuinielaPrediction(Base):
    __tablename__ = "quiniela_predictions"
    
    id = Column(Integer, primary_key=True)
    week_number = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    
    # Prediction details
    predicted_result = Column(String(1), nullable=False)  # 1, X, 2
    confidence = Column(Float)  # 0.0 to 1.0
    home_probability = Column(Float)
    draw_probability = Column(Float)
    away_probability = Column(Float)
    
    # Model features used
    model_features = Column(JSON)
    model_version = Column(String(50))
    
    # Actual result (filled after match)
    actual_result = Column(String(1))
    is_correct = Column(Boolean)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    match = relationship("Match")


class QuinielaWeek(Base):
    __tablename__ = "quiniela_weeks"
    
    id = Column(Integer, primary_key=True)
    week_number = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    
    # Financial tracking
    bet_amount = Column(Float, default=0.0)
    potential_winnings = Column(Float, default=0.0)
    actual_winnings = Column(Float, default=0.0)
    profit_loss = Column(Float, default=0.0)
    
    # Performance metrics
    correct_predictions = Column(Integer, default=0)
    total_predictions = Column(Integer, default=15)
    accuracy_percentage = Column(Float, default=0.0)
    
    # Status
    is_completed = Column(Boolean, default=False)
    submission_date = Column(DateTime)
    results_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelPerformance(Base):
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    
    # Training data info
    training_samples = Column(Integer)
    training_date = Column(DateTime)
    
    # Feature importance
    feature_importance = Column(JSON)
    
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserQuiniela(Base):
    """
    Quinielas personales del usuario
    """
    __tablename__ = "user_quinielas"
    
    id = Column(Integer, primary_key=True, index=True)
    week_number = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    quiniela_date = Column(Date, nullable=False)
    cost = Column(Float, nullable=False)  # Lo que se gastó
    winnings = Column(Float, default=0.0)  # Lo que se ganó
    is_finished = Column(Boolean, default=False)  # Si la jornada terminó
    # Pleno al 15: predicción de goles para cada equipo en el partido 15
    pleno_al_15_home = Column(String(1), nullable=True)  # Goles equipo local: "0", "1", "2", "M" 
    pleno_al_15_away = Column(String(1), nullable=True)  # Goles equipo visitante: "0", "1", "2", "M"
    
    # Estadísticas de la quiniela
    total_predictions = Column(Integer, default=14)
    correct_predictions = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con las predicciones
    predictions = relationship("UserQuinielaPrediction", back_populates="quiniela", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserQuiniela(week={self.week_number}, season={self.season}, cost={self.cost})>"


class UserQuinielaPrediction(Base):
    """
    Predicciones individuales de cada partido en una quiniela del usuario
    """
    __tablename__ = "user_quiniela_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiniela_id = Column(Integer, ForeignKey("user_quinielas.id"), nullable=False)
    match_number = Column(Integer, nullable=False)  # 1-14
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)  # Partido real si está disponible
    
    # Equipos
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    
    # Predicción del usuario
    user_prediction = Column(String(1), nullable=False)  # "1", "X", "2"
    
    # Resultado real (se rellena cuando termine el partido)
    actual_result = Column(String(1), nullable=True)  # "1", "X", "2"
    is_correct = Column(Boolean, nullable=True)
    
    # Datos de la predicción del sistema
    system_prediction = Column(String(1), nullable=True)  # Lo que predijo el sistema
    confidence = Column(Float, nullable=True)  # Confianza del sistema
    explanation = Column(Text, nullable=True)  # Explicación de la predicción
    
    # Probabilidades del sistema
    prob_home = Column(Float, nullable=True)
    prob_draw = Column(Float, nullable=True)
    prob_away = Column(Float, nullable=True)
    
    # Metadatos
    match_date = Column(DateTime, nullable=True)
    league = Column(String, nullable=True)
    
    # Relaciones
    quiniela = relationship("UserQuiniela", back_populates="predictions")
    match = relationship("Match", foreign_keys=[match_id])
    
    def __repr__(self):
        return f"<UserQuinielaPrediction(match={self.match_number}, prediction='{self.user_prediction}')>"


class QuinielaWeekSchedule(Base):
    """
    Programación semanal de la Quiniela oficial
    """
    __tablename__ = "quiniela_week_schedule"
    
    id = Column(Integer, primary_key=True, index=True)
    week_number = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    deadline = Column(DateTime, nullable=False)  # Hora límite para apostar
    is_active = Column(Boolean, default=True)
    
    # Estado de la jornada
    is_predictions_ready = Column(Boolean, default=False)
    is_finished = Column(Boolean, default=False)
    results_available = Column(Boolean, default=False)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<QuinielaWeekSchedule(week={self.week_number}, season={self.season})>"


class CustomQuinielaConfig(Base):
    """
    Configuración personalizada de Quiniela seleccionada manualmente por el usuario
    """
    __tablename__ = "custom_quiniela_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    week_number = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    config_name = Column(String(100), nullable=False)  # Nombre descriptivo para la configuración
    
    # Lista de match_ids seleccionados (15 partidos)
    selected_match_ids = Column(JSON, nullable=False)  # Array de IDs de partidos seleccionados
    
    # ID del partido designado como Pleno al 15
    pleno_al_15_match_id = Column(Integer, nullable=False)
    
    # Información adicional
    total_matches = Column(Integer, default=15)
    la_liga_count = Column(Integer, default=0)  # Cuántos partidos de La Liga
    segunda_count = Column(Integer, default=0)  # Cuántos partidos de Segunda
    
    # Estado
    is_active = Column(Boolean, default=True)  # Si esta configuración está activa
    created_by_user = Column(Boolean, default=True)  # Creada manualmente por usuario
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CustomQuinielaConfig(name={self.config_name}, week={self.week_number}, season={self.season})>"


# =============================================================================
# ADVANCED STATISTICS MODELS - FASE 1: ESTADO DEL ARTE
# =============================================================================

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
    xa_total = Column(Float)  # Expected Assists total
    xa_per_match = Column(Float)  # xA promedio por partido
    xa_performance = Column(Float)  # Asistencias reales / xA
    
    # EXPECTED THREAT (xT) METRICS
    xt_total = Column(Float)  # Expected Threat total
    xt_per_possession = Column(Float)  # xT por posesión
    xt_final_third = Column(Float)  # xT en último tercio
    
    # PRESSING METRICS (PPDA = Passes Per Defensive Action)
    ppda_own = Column(Float)  # PPDA cuando el equipo defiende
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