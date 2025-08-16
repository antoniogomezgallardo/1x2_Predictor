from celery import Celery
from typing import Dict, Any

# This will be imported by the main celery app
celery_app = Celery("quiniela_predictor")

@celery_app.task
def update_teams_task(season: int) -> Dict[str, Any]:
    """
    Celery task to update teams data for a given season
    """
    try:
        # Import here to avoid circular imports
        from ..database.database import SessionLocal
        from ..services_v2.team_service import TeamService
        
        db = SessionLocal()
        try:
            team_service = TeamService(db)
            await team_service.update_teams(season)
            result = {"teams_updated": "success"}
        finally:
            db.close()
        
        return {
            "status": "success",
            "season": season,
            "teams_updated": result.get("teams_updated", 0),
            "message": f"Successfully updated {result.get('teams_updated', 0)} teams for season {season}"
        }
    except Exception as e:
        return {
            "status": "error",
            "season": season,
            "message": f"Error updating teams: {str(e)}"
        }

@celery_app.task
def update_matches_task(season: int) -> Dict[str, Any]:
    """
    Celery task to update matches data for a given season
    """
    try:
        from ..database.database import SessionLocal
        from ..services_v2.match_service import MatchService
        
        db = SessionLocal()
        try:
            match_service = MatchService(db)
            await match_service.update_matches(season)
            result = {"matches_updated": "success"}
        finally:
            db.close()
        
        return {
            "status": "success",
            "season": season,
            "matches_updated": result.get("matches_updated", 0),
            "message": f"Successfully updated {result.get('matches_updated', 0)} matches for season {season}"
        }
    except Exception as e:
        return {
            "status": "error",
            "season": season,
            "message": f"Error updating matches: {str(e)}"
        }

@celery_app.task
def update_statistics_task(season: int) -> Dict[str, Any]:
    """
    Celery task to update team statistics for a given season
    """
    try:
        from ..database.database import SessionLocal
        from ..services_v2.statistics_service import StatisticsService
        
        db = SessionLocal()
        try:
            statistics_service = StatisticsService(db)
            await statistics_service.update_team_statistics(season)
            result = {"statistics_updated": "success"}
        finally:
            db.close()
        
        return {
            "status": "success",
            "season": season,
            "statistics_updated": result.get("statistics_updated", 0),
            "message": f"Successfully updated statistics for {result.get('statistics_updated', 0)} teams in season {season}"
        }
    except Exception as e:
        return {
            "status": "error",
            "season": season,
            "message": f"Error updating statistics: {str(e)}"
        }

@celery_app.task
def train_model_task(season: int) -> Dict[str, Any]:
    """
    Celery task to train ML model
    """
    try:
        from ..ml.predictor import Predictor
        
        predictor = Predictor()
        result = predictor.train_model(season)
        
        return {
            "status": "success",
            "season": season,
            "accuracy": result.get("accuracy", 0.0),
            "message": f"Model trained successfully with accuracy: {result.get('accuracy', 0.0):.3f}"
        }
    except Exception as e:
        return {
            "status": "error",
            "season": season,
            "message": f"Error training model: {str(e)}"
        }

@celery_app.task
def generate_predictions_task(season: int, week: int) -> Dict[str, Any]:
    """
    Celery task to generate predictions for a specific week
    """
    try:
        from ..ml.predictor import Predictor
        
        predictor = Predictor()
        predictions = predictor.generate_predictions(season, week)
        
        return {
            "status": "success",
            "season": season,
            "week": week,
            "predictions_count": len(predictions),
            "predictions": predictions,
            "message": f"Generated {len(predictions)} predictions for season {season}, week {week}"
        }
    except Exception as e:
        return {
            "status": "error",
            "season": season,
            "week": week,
            "message": f"Error generating predictions: {str(e)}"
        }