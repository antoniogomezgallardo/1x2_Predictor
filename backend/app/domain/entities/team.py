from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from ...infrastructure.database.base import Base


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