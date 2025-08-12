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
    pleno_al_15 = Column(String(1), nullable=True)  # "0", "1", "2", "M"
    
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