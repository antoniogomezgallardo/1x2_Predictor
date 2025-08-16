# Backwards compatibility file
# Import all entities from the new domain structure
from ..domain.entities import *
from ..infrastructure.database.base import Base

# Re-export Base for compatibility
__all__ = [
    "Base",
    "Team",
    "Match", 
    "TeamStatistics",
    "ModelPerformance",
    "QuinielaPrediction",
    "QuinielaWeek",
    "UserQuiniela",
    "UserQuinielaPrediction", 
    "QuinielaWeekSchedule",
    "CustomQuinielaConfig",
    "AdvancedTeamStatistics",
    "MatchAdvancedStatistics", 
    "PlayerAdvancedStatistics",
    "MarketIntelligence",
    "ExternalFactors"
]