from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Football Configuration
    api_football_key: str
    api_football_host: str = "v3.football.api-sports.io"
    
    # Database Configuration
    database_url: str
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # Application Configuration
    debug: bool = False
    secret_key: str
    
    # Betting Configuration
    initial_bankroll: float = 1000.0
    max_bet_percentage: float = 0.05
    min_odds_threshold: float = 1.5
    
    # Quiniela Pricing (Official Rates)
    precio_apuesta_simple: float = 0.75  # €0.75 per simple bet
    precio_elige_8: float = 0.50  # €0.50 for Elige 8 additional bet
    
    # Spanish Football League IDs (API-Football)
    la_liga_id: int = 140  # Primera División
    segunda_division_id: int = 141  # Segunda División
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()