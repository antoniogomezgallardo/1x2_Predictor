from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class TeamResponse(BaseModel):
    id: int
    name: str
    short_name: Optional[str]
    logo: Optional[str]
    league_id: int
    founded: Optional[int]
    venue_name: Optional[str]
    
    class Config:
        from_attributes = True


class TeamStatisticsResponse(BaseModel):
    team_id: int
    season: int
    league_id: int
    matches_played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int
    position: Optional[int]
    home_wins: int
    home_draws: int
    home_losses: int
    away_wins: int
    away_draws: int
    away_losses: int
    form: Optional[str]
    
    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: int
    home_team: TeamResponse
    away_team: TeamResponse
    league_id: int
    season: int
    round: Optional[str]
    match_date: datetime
    status: Optional[str]
    home_goals: Optional[int]
    away_goals: Optional[int]
    result: Optional[str]
    home_odds: Optional[float]
    draw_odds: Optional[float]
    away_odds: Optional[float]
    
    class Config:
        from_attributes = True


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


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class ModelPerformanceResponse(BaseModel):
    model_version: Optional[str]
    is_trained: bool
    feature_importance: List[FeatureImportance]
    feature_count: int


class WeeklyPerformance(BaseModel):
    week_number: int
    bet_amount: float
    winnings: float
    profit_loss: float
    accuracy: float


class FinancialSummaryResponse(BaseModel):
    season: int
    total_weeks: int
    total_bet: float
    total_winnings: float
    total_profit: float
    roi_percentage: float
    weekly_performance: List[WeeklyPerformance]


class TrainingRequest(BaseModel):
    season: int
    min_matches: Optional[int] = 100


class UpdateDataRequest(BaseModel):
    season: int
    from_date: Optional[str] = None
    to_date: Optional[str] = None