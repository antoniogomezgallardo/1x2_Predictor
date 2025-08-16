from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ...infrastructure.database.base import Base


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