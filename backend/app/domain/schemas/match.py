from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from .team import TeamResponse


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


class MatchCreate(BaseModel):
    api_id: int
    home_team_id: int
    away_team_id: int
    league_id: int
    season: int
    round: Optional[str] = None
    match_date: datetime
    status: Optional[str] = None


class MatchUpdate(BaseModel):
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    result: Optional[str] = None
    status: Optional[str] = None
    home_odds: Optional[float] = None
    draw_odds: Optional[float] = None
    away_odds: Optional[float] = None