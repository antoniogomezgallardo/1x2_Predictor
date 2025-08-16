from pydantic import BaseModel
from typing import Optional, List


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


class TeamStatisticsCreate(BaseModel):
    team_id: int
    season: int
    league_id: int
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0
    position: Optional[int] = None


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class ModelPerformanceResponse(BaseModel):
    model_version: Optional[str]
    is_trained: bool
    feature_importance: List[FeatureImportance]
    feature_count: int


class TrainingRequest(BaseModel):
    season: int
    min_matches: Optional[int] = 100


class UpdateDataRequest(BaseModel):
    season: int
    from_date: Optional[str] = None
    to_date: Optional[str] = None