from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ...infrastructure.database.base import Base


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


class UserQuiniela(Base):
    """
    Quinielas personales del usuario con soporte para dobles, triples y Elige 8
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
    
    # Sistema de dobles y triples
    bet_type = Column(String(20), default='simple')  # 'simple', 'multiple', 'reduced'
    total_combinations = Column(Integer, default=1)  # Total de combinaciones generadas
    base_cost = Column(Float, default=0.75)  # Costo base de la quiniela (sin Elige 8)
    
    # Elige 8 - Juego complementario
    elige_8_enabled = Column(Boolean, default=False)  # Si tiene Elige 8 activado
    elige_8_matches = Column(JSON, nullable=True)  # IDs de los 8 partidos seleccionados para Elige 8
    elige_8_cost = Column(Float, default=0.0)  # Costo del Elige 8 (€0.50 si activo)
    elige_8_predictions = Column(JSON, nullable=True)  # Predicciones específicas para Elige 8
    
    # Estadísticas de la quiniela
    total_predictions = Column(Integer, default=14)
    correct_predictions = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con las predicciones
    predictions = relationship("UserQuinielaPrediction", back_populates="quiniela", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserQuiniela(week={self.week_number}, season={self.season}, cost={self.cost}, type={self.bet_type})>"


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
    
    # Predicción del usuario (soporte para dobles y triples)
    user_prediction = Column(String(1), nullable=False)  # "1", "X", "2" - predicción principal
    multiplicity = Column(Integer, default=1)  # 1=simple, 2=doble, 3=triple
    prediction_options = Column(JSON, nullable=True)  # ["1"], ["1","X"], ["1","X","2"] - todas las opciones marcadas
    
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