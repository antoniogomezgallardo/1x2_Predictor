from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date


class PredictionDetails(BaseModel):
    match_number: int
    home_team: str
    away_team: str
    match_date: Optional[str]
    predicted_result: str
    confidence: float
    probabilities: Dict[str, float]
    features_used: Optional[Dict[str, Any]]
    model_version: Optional[str]


class BettingRecommendation(BaseModel):
    match_number: int
    home_team: str
    away_team: str
    predicted_result: str
    confidence: float
    recommended_bet: float
    probabilities: Dict[str, float]


class BettingStrategy(BaseModel):
    total_stake: float
    recommended_bets: List[BettingRecommendation]
    number_of_bets: int
    percentage_of_bankroll: float


class QuinielaPredictionResponse(BaseModel):
    season: int
    week_number: int
    predictions: List[PredictionDetails]
    betting_strategy: BettingStrategy
    model_version: Optional[str]
    generated_at: datetime


class QuinielaPredictionDB(BaseModel):
    id: int
    week_number: int
    season: int
    match_id: int
    predicted_result: str
    confidence: Optional[float]
    home_probability: Optional[float]
    draw_probability: Optional[float]
    away_probability: Optional[float]
    actual_result: Optional[str]
    is_correct: Optional[bool]
    model_version: Optional[str]
    
    class Config:
        from_attributes = True


class HistoricalPredictionResponse(BaseModel):
    week_number: int
    season: int
    accuracy: float
    correct_predictions: int
    total_predictions: int
    profit_loss: float
    is_completed: bool
    predictions: List[QuinielaPredictionDB]


class UserQuinielaCreate(BaseModel):
    week_number: int
    season: int
    quiniela_date: date
    cost: float
    pleno_al_15_home: Optional[str] = None
    pleno_al_15_away: Optional[str] = None
    bet_type: str = 'simple'
    elige_8_enabled: bool = False


class UserQuinielaPredictionCreate(BaseModel):
    match_number: int
    home_team: str
    away_team: str
    user_prediction: str
    system_prediction: Optional[str] = None
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    match_date: Optional[datetime] = None
    league: Optional[str] = None


class CustomQuinielaConfigCreate(BaseModel):
    week_number: int
    season: int
    config_name: str
    selected_match_ids: List[int]
    pleno_al_15_match_id: int


class QuinielaWeekScheduleResponse(BaseModel):
    id: int
    week_number: int
    season: int
    week_start_date: date
    week_end_date: date
    deadline: datetime
    is_active: bool
    is_predictions_ready: bool
    is_finished: bool
    results_available: bool
    
    class Config:
        from_attributes = True