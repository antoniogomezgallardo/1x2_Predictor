from pydantic import BaseModel
from typing import List


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