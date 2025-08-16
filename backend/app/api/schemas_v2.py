# Backwards compatibility file  
# Import all schemas from the new domain structure
from ..domain.schemas import *

# Re-export everything for compatibility
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