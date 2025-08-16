# Import all schemas to make them available for import
from .team import TeamResponse, TeamCreate, TeamUpdate
from .match import MatchResponse, MatchCreate, MatchUpdate
from .statistics import (
    TeamStatisticsResponse, TeamStatisticsCreate, FeatureImportance,
    ModelPerformanceResponse, TrainingRequest, UpdateDataRequest
)
from .quiniela import (
    PredictionDetails, BettingRecommendation, BettingStrategy,
    QuinielaPredictionResponse, QuinielaPredictionDB, HistoricalPredictionResponse,
    UserQuinielaCreate, UserQuinielaPredictionCreate, CustomQuinielaConfigCreate,
    QuinielaWeekScheduleResponse
)
from .analytics import WeeklyPerformance, FinancialSummaryResponse
from .advanced import (
    AdvancedTeamStatsResponse, MatchAdvancedStatsResponse, PlayerAdvancedStatsResponse,
    MarketIntelligenceResponse, ExternalFactorsResponse, AdvancedDataCollectionRequest,
    AdvancedDataStatusResponse
)

# Export all schemas for backwards compatibility
__all__ = [
    # Team schemas
    "TeamResponse", "TeamCreate", "TeamUpdate",
    
    # Match schemas
    "MatchResponse", "MatchCreate", "MatchUpdate",
    
    # Statistics schemas
    "TeamStatisticsResponse", "TeamStatisticsCreate", "FeatureImportance",
    "ModelPerformanceResponse", "TrainingRequest", "UpdateDataRequest",
    
    # Quiniela schemas
    "PredictionDetails", "BettingRecommendation", "BettingStrategy",
    "QuinielaPredictionResponse", "QuinielaPredictionDB", "HistoricalPredictionResponse",
    "UserQuinielaCreate", "UserQuinielaPredictionCreate", "CustomQuinielaConfigCreate",
    "QuinielaWeekScheduleResponse",
    
    # Analytics schemas
    "WeeklyPerformance", "FinancialSummaryResponse",
    
    # Advanced schemas
    "AdvancedTeamStatsResponse", "MatchAdvancedStatsResponse", "PlayerAdvancedStatsResponse",
    "MarketIntelligenceResponse", "ExternalFactorsResponse", "AdvancedDataCollectionRequest",
    "AdvancedDataStatusResponse"
]