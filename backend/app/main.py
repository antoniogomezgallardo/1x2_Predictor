from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import logging
from datetime import datetime

from .database.database import get_db
from .database.models import *
from .services.data_extractor import DataExtractor
from .services.api_football_client import APIFootballClient
from .ml.predictor import QuinielaPredictor
from .api.schemas import *
from .config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Quiniela Predictor API",
    description="API for predicting Spanish football quiniela results",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global predictor instance
predictor = QuinielaPredictor()


@app.get("/")
async def root():
    return {"message": "Quiniela Predictor API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/data/update-teams/{season}")
async def update_teams(season: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Update teams data for both La Liga and Segunda División"""
    try:
        extractor = DataExtractor(db)
        background_tasks.add_task(extractor.update_teams, season)
        return {"message": f"Teams update started for season {season}"}
    except Exception as e:
        logger.error(f"Error updating teams: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/data/update-matches/{season}")
async def update_matches(
    season: int, 
    background_tasks: BackgroundTasks,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update matches data for both leagues"""
    try:
        extractor = DataExtractor(db)
        background_tasks.add_task(extractor.update_matches, season, from_date, to_date)
        return {"message": f"Matches update started for season {season}"}
    except Exception as e:
        logger.error(f"Error updating matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/data/update-statistics/{season}")
async def update_statistics(season: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Update team statistics"""
    try:
        extractor = DataExtractor(db)
        background_tasks.add_task(extractor.update_team_statistics, season)
        return {"message": f"Statistics update started for season {season}"}
    except Exception as e:
        logger.error(f"Error updating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/teams/", response_model=List[TeamResponse])
async def get_teams(league_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all teams, optionally filtered by league"""
    query = db.query(Team)
    if league_id:
        query = query.filter(Team.league_id == league_id)
    teams = query.all()
    return teams


@app.get("/teams/{team_id}/statistics", response_model=TeamStatisticsResponse)
async def get_team_statistics(team_id: int, season: int, db: Session = Depends(get_db)):
    """Get statistics for a specific team and season"""
    stats = db.query(TeamStatistics).filter_by(team_id=team_id, season=season).first()
    if not stats:
        raise HTTPException(status_code=404, detail="Statistics not found")
    return stats


@app.get("/matches/", response_model=List[MatchResponse])
async def get_matches(
    season: int,
    league_id: Optional[int] = None,
    team_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get matches with optional filters"""
    query = db.query(Match).filter(Match.season == season)
    
    if league_id:
        query = query.filter(Match.league_id == league_id)
    
    if team_id:
        query = query.filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        )
    
    matches = query.order_by(Match.match_date.desc()).limit(limit).all()
    return matches


@app.post("/model/train")
async def train_model(
    season: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Train the prediction model with historical data"""
    try:
        # Get historical matches with results
        completed_matches = db.query(Match).filter(
            Match.season == season,
            Match.result.isnot(None)
        ).all()
        
        if len(completed_matches) < 100:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough historical data. Found {len(completed_matches)} matches, need at least 100"
            )
        
        # Convert to format needed for training
        extractor = DataExtractor(db)
        training_data = []
        
        for match in completed_matches:
            # Get comprehensive match data
            match_data = {
                "home_team": {"api_id": match.home_team.api_id, "name": match.home_team.name},
                "away_team": {"api_id": match.away_team.api_id, "name": match.away_team.name},
                "result": match.result,
                "home_stats": db.query(TeamStatistics).filter_by(
                    team_id=match.home_team_id, season=season
                ).first(),
                "away_stats": db.query(TeamStatistics).filter_by(
                    team_id=match.away_team_id, season=season
                ).first(),
            }
            
            # Add empty lists for API data (would need to fetch in real implementation)
            match_data.update({
                "h2h_data": [],
                "home_form": [],
                "away_form": []
            })
            
            training_data.append(match_data)
        
        # Train model in background
        def train_task():
            try:
                results = predictor.train_model(training_data)
                logger.info(f"Model training completed with accuracy: {results['accuracy']:.3f}")
                return results
            except Exception as e:
                logger.error(f"Model training failed: {str(e)}")
                raise e
        
        background_tasks.add_task(train_task)
        
        return {
            "message": "Model training started",
            "training_samples": len(training_data),
            "season": season
        }
        
    except Exception as e:
        logger.error(f"Error starting model training: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/current-week", response_model=QuinielaPredictionResponse)
async def get_current_week_predictions(season: int, db: Session = Depends(get_db)):
    """Get predictions for current week's quiniela"""
    try:
        if not predictor.is_trained:
            raise HTTPException(status_code=400, detail="Model not trained yet")
        
        # Get current week quiniela data
        extractor = DataExtractor(db)
        quiniela_data = await extractor.get_quiniela_data(season)
        
        if not quiniela_data:
            raise HTTPException(status_code=404, detail="No matches found for current week")
        
        # Make predictions
        predictions = predictor.predict_quiniela(quiniela_data)
        
        # Calculate betting strategy
        betting_strategy = predictor.calculate_betting_strategy(
            predictions, 
            settings.initial_bankroll, 
            settings.max_bet_percentage
        )
        
        return {
            "season": season,
            "week_number": 1,  # Would need to determine actual week
            "predictions": predictions,
            "betting_strategy": betting_strategy,
            "model_version": predictor.model_version,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error generating predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/quiniela-oficial/{season}")
async def get_quiniela_oficial_predictions(season: int, db: Session = Depends(get_db)):
    """
    Genera predicciones específicas para la Quiniela Española oficial
    Incluye selección de 14 partidos + Pleno al 15 + análisis de valor
    """
    try:
        if not predictor.is_trained:
            raise HTTPException(status_code=400, detail="Model not trained yet")
        
        # Obtener partidos disponibles para la jornada
        extractor = DataExtractor(db)
        
        # Buscar partidos próximos (implementación simplificada)
        from datetime import datetime, timedelta
        current_date = datetime.now()
        
        # Obtener partidos de los próximos 7 días
        upcoming_matches = db.query(Match).filter(
            Match.season == season,
            Match.match_date >= current_date,
            Match.match_date <= current_date + timedelta(days=7),
            Match.result.is_(None)  # Solo partidos no jugados
        ).all()
        
        if not upcoming_matches:
            # Si no hay partidos próximos, usar los últimos partidos como ejemplo
            upcoming_matches = db.query(Match).filter(
                Match.season == season,
                Match.result.isnot(None)
            ).order_by(Match.match_date.desc()).limit(20).all()
        
        if len(upcoming_matches) < 14:
            raise HTTPException(
                status_code=404, 
                detail=f"Insufficient matches for Quiniela. Found {len(upcoming_matches)}, need at least 14"
            )
        
        # Preparar datos de partidos para el predictor
        matches_data = []
        for match in upcoming_matches:
            # Obtener estadísticas de equipos
            home_stats = db.query(TeamStatistics).filter_by(
                team_id=match.home_team_id, season=season
            ).first()
            
            away_stats = db.query(TeamStatistics).filter_by(
                team_id=match.away_team_id, season=season
            ).first()
            
            match_data = {
                "home_team": {
                    "api_id": match.home_team.api_id if match.home_team else None,
                    "name": match.home_team.name if match.home_team else "Unknown"
                },
                "away_team": {
                    "api_id": match.away_team.api_id if match.away_team else None,
                    "name": match.away_team.name if match.away_team else "Unknown"
                },
                "league_id": match.league_id,
                "match_date": match.match_date.isoformat() if match.match_date else None,
                "round": match.round,
                "home_stats": home_stats,
                "away_stats": away_stats,
                "home_odds": match.home_odds,
                "draw_odds": match.draw_odds,
                "away_odds": match.away_odds,
                "h2h_data": [],  # Simplificado por ahora
                "home_form": [],  # Simplificado por ahora
                "away_form": []   # Simplificado por ahora
            }
            matches_data.append(match_data)
        
        # Generar predicciones oficiales de Quiniela
        quiniela_predictions = predictor.predict_quiniela_official(matches_data, season)
        
        return quiniela_predictions
        
    except Exception as e:
        logger.error(f"Error generating Quiniela oficial predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/history", response_model=List[HistoricalPredictionResponse])
async def get_prediction_history(season: int, limit: int = 10, db: Session = Depends(get_db)):
    """Get historical prediction performance"""
    weeks = db.query(QuinielaWeek).filter_by(season=season).order_by(
        QuinielaWeek.week_number.desc()
    ).limit(limit).all()
    
    result = []
    for week in weeks:
        predictions = db.query(QuinielaPrediction).filter_by(
            season=season, week_number=week.week_number
        ).all()
        
        result.append({
            "week_number": week.week_number,
            "season": season,
            "accuracy": week.accuracy_percentage,
            "correct_predictions": week.correct_predictions,
            "total_predictions": week.total_predictions,
            "profit_loss": week.profit_loss,
            "is_completed": week.is_completed,
            "predictions": predictions
        })
    
    return result


@app.get("/analytics/model-performance")
async def get_model_performance():
    """Get current model performance metrics"""
    if not predictor.is_trained:
        raise HTTPException(status_code=400, detail="Model not trained yet")
    
    feature_importance = predictor.get_feature_importance(top_n=15)
    
    return {
        "model_version": predictor.model_version,
        "is_trained": predictor.is_trained,
        "feature_importance": feature_importance,
        "feature_count": len(predictor.feature_names)
    }


@app.get("/analytics/financial-summary")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)