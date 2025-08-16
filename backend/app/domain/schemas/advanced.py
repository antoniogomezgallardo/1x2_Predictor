from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AdvancedTeamStatsResponse(BaseModel):
    id: int
    team_id: int
    season: int
    league_id: int
    data_source: str
    last_updated: datetime
    matches_analyzed: int
    
    # xG metrics
    xg_for: Optional[float]
    xg_against: Optional[float]
    xg_difference: Optional[float]
    xg_per_match: Optional[float]
    xg_performance: Optional[float]
    
    # xA metrics
    xa_for: Optional[float]
    xa_against: Optional[float]
    xa_per_match: Optional[float]
    xa_performance: Optional[float]
    
    # xT metrics
    xt_for: Optional[float]
    xt_against: Optional[float]
    xt_per_possession: Optional[float]
    xt_final_third: Optional[float]
    
    # Pressing metrics
    ppda: Optional[float]
    ppda_allowed: Optional[float]
    pressing_intensity: Optional[float]
    high_turnovers: Optional[int]
    
    class Config:
        from_attributes = True


class MatchAdvancedStatsResponse(BaseModel):
    id: int
    match_id: int
    data_source: str
    last_updated: datetime
    data_quality_score: Optional[float]
    
    # xG metrics
    home_xg: Optional[float]
    away_xg: Optional[float]
    home_xg_first_half: Optional[float]
    away_xg_first_half: Optional[float]
    home_xg_second_half: Optional[float]
    away_xg_second_half: Optional[float]
    
    # xA metrics
    home_xa: Optional[float]
    away_xa: Optional[float]
    
    # xT metrics
    home_xt: Optional[float]
    away_xt: Optional[float]
    
    # Pressing metrics
    home_ppda: Optional[float]
    away_ppda: Optional[float]
    home_high_turnovers: Optional[int]
    away_high_turnovers: Optional[int]
    
    # Quality metrics
    shot_quality_home: Optional[float]
    shot_quality_away: Optional[float]
    chance_quality_home: Optional[float]
    chance_quality_away: Optional[float]
    
    class Config:
        from_attributes = True


class PlayerAdvancedStatsResponse(BaseModel):
    id: int
    player_api_id: int
    player_name: str
    team_id: int
    season: int
    position: Optional[str]
    data_source: str
    last_updated: datetime
    minutes_played: int
    matches_played: int
    
    # xG and xA metrics
    player_xg: Optional[float]
    player_xa: Optional[float]
    xg_per_90: Optional[float]
    xa_per_90: Optional[float]
    
    # xT metrics
    player_xt: Optional[float]
    xt_per_90: Optional[float]
    
    # Impact metrics
    player_impact_score: Optional[float]
    
    class Config:
        from_attributes = True


class MarketIntelligenceResponse(BaseModel):
    id: int
    match_id: int
    data_source: str
    collection_time: datetime
    time_before_match: Optional[int]
    
    # Opening odds
    opening_home: Optional[float]
    opening_draw: Optional[float]
    opening_away: Optional[float]
    
    # Closing odds
    closing_home: Optional[float]
    closing_draw: Optional[float]
    closing_away: Optional[float]
    
    # Market probabilities
    market_prob_home: Optional[float]
    market_prob_draw: Optional[float]
    market_prob_away: Optional[float]
    market_overround: Optional[float]
    
    # Value opportunities
    value_bet_indicator: Optional[str]
    value_percentage: Optional[float]
    consensus_favorite: Optional[str]
    
    class Config:
        from_attributes = True


class ExternalFactorsResponse(BaseModel):
    id: int
    match_id: int
    last_updated: datetime
    data_quality: Optional[float]
    
    # Weather conditions
    temperature: Optional[float]
    humidity: Optional[float]
    wind_speed: Optional[float]
    precipitation: Optional[float]
    weather_condition: Optional[str]
    weather_impact_score: Optional[float]
    
    # Team motivation
    home_team_motivation: Optional[float]
    away_team_motivation: Optional[float]
    home_recent_form: Optional[float]
    away_recent_form: Optional[float]
    
    # Injury impact
    home_key_players_out: Optional[int]
    away_key_players_out: Optional[int]
    home_injury_impact: Optional[float]
    away_injury_impact: Optional[float]
    
    # Fatigue factors
    home_days_rest: Optional[int]
    away_days_rest: Optional[int]
    fatigue_factor_home: Optional[float]
    fatigue_factor_away: Optional[float]
    
    class Config:
        from_attributes = True


class AdvancedDataCollectionRequest(BaseModel):
    season: int
    league_ids: Optional[str] = "140,141"


class AdvancedDataStatusResponse(BaseModel):
    season: int
    collection_status: Dict[str, Any]
    data_completeness: Dict[str, bool]