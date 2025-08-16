from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from ....database.database import get_db
from ....database.models import QuinielaWeek
from ....ml.predictor import QuinielaPredictor

router = APIRouter()
logger = logging.getLogger(__name__)

# Global predictor instance (shared across app)
predictor = QuinielaPredictor()


@router.get("/model-performance")
async def get_model_performance():
    """Get current model performance metrics"""
    try:
        # Verificar si el predictor está inicializado y entrenado
        if not hasattr(predictor, 'is_trained') or not predictor.is_trained:
            return {
                "model_version": None,
                "is_trained": False,
                "feature_importance": [],
                "feature_count": 0,
                "message": "Model not trained yet. Train the model first."
            }
        
        # Intentar obtener feature importance de forma segura
        try:
            feature_importance = predictor.get_feature_importance(top_n=15)
        except:
            feature_importance = []
        
        # Intentar obtener feature names de forma segura
        try:
            feature_count = len(predictor.feature_names) if hasattr(predictor, 'feature_names') else 0
        except:
            feature_count = 0
        
        return {
            "model_version": getattr(predictor, 'model_version', "1.0.0"),
            "is_trained": True,
            "feature_importance": feature_importance,
            "feature_count": feature_count
        }
        
    except Exception as e:
        logger.error(f"Error getting model performance: {str(e)}")
        return {
            "model_version": None,
            "is_trained": False,
            "feature_importance": [],
            "feature_count": 0,
            "error": str(e)
        }


@router.get("/financial-summary")
async def get_financial_summary(season: int, db: Session = Depends(get_db)):
    """Get financial performance summary"""
    weeks = db.query(QuinielaWeek).filter_by(season=season, is_completed=True).all()
    
    total_bet = sum(week.bet_amount for week in weeks)
    total_winnings = sum(week.actual_winnings for week in weeks)
    total_profit = sum(week.profit_loss for week in weeks)
    
    weekly_performance = []
    for week in weeks:
        weekly_performance.append({
            "week_number": week.week_number,
            "bet_amount": week.bet_amount,
            "winnings": week.actual_winnings,
            "profit_loss": week.profit_loss,
            "accuracy": week.accuracy_percentage
        })
    
    return {
        "season": season,
        "total_weeks": len(weeks),
        "total_bet": total_bet,
        "total_winnings": total_winnings,
        "total_profit": total_profit,
        "roi_percentage": (total_profit / total_bet * 100) if total_bet > 0 else 0,
        "weekly_performance": weekly_performance
    }