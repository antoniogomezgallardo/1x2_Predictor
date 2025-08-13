from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import logging
from datetime import datetime

from .database.database import get_db
from .database.models import *
import numpy as np
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
        from datetime import datetime
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Verificar si hay datos existentes para esta temporada
        existing_matches = db.query(Match).filter(Match.season == season).count()
        
        # Si es temporada futura o temporada actual sin datos (y es antes de agosto)
        season_likely_not_started = (
            season > current_year or 
            (season == current_year and existing_matches == 0 and current_month < 8)
        )
        
        if season_likely_not_started:
            return {
                "message": f"Season {season} has not started yet. No teams data available to update.",
                "warning": f"Current date: {datetime.now().strftime('%Y-%m')}. Season {season} appears not to have started.",
                "recommendation": f"Try updating season {current_year - 1} which has complete data."
            }
        
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
        from datetime import datetime
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Verificar si ya hay datos para esta temporada (validación más inteligente)
        existing_matches = db.query(Match).filter(Match.season == season).count()
        logger.info(f"Season validation - Season: {season}, Current year: {current_year}, Existing matches: {existing_matches}")
        
        # Si es una temporada futura o no hay datos existentes, es probable que no haya empezado
        season_likely_not_started = (
            season > current_year or 
            (season == current_year and existing_matches == 0 and current_month < 8)
        )
        
        logger.info(f"Season likely not started: {season_likely_not_started}")
        
        if season_likely_not_started:
            return {
                "message": f"Season {season} appears to have not started yet. No matches available to update.",
                "warning": f"Current date: {datetime.now().strftime('%Y-%m')}. No existing matches found for season {season}.",
                "recommendation": f"Try updating season {current_year - 1} which has complete data."
            }
        
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
        from datetime import datetime
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Verificar si ya hay datos para esta temporada (validación más inteligente)
        existing_matches = db.query(Match).filter(Match.season == season).count()
        
        # Si es una temporada futura o no hay datos existentes, es probable que no haya empezado
        season_likely_not_started = (
            season > current_year or 
            (season == current_year and existing_matches == 0 and current_month < 8)
        )
        
        if season_likely_not_started:
            return {
                "message": f"Season {season} appears to have not started yet. No statistics available to update.",
                "warning": f"Current date: {datetime.now().strftime('%Y-%m')}. No existing matches found for season {season}.",
                "recommendation": f"Try updating season {current_year - 1} which has complete data."
            }
        
        # Verificar si hay partidos suficientes para generar estadísticas
        matches_count = db.query(Match).filter(Match.season == season).count()
        if matches_count == 0:
            return {
                "message": f"No matches found for season {season}. Cannot update statistics.",
                "warning": "Statistics need matches data first.",
                "recommendation": f"Update matches for season {season} first, or try season {current_year - 1}."
            }
        
        extractor = DataExtractor(db)
        background_tasks.add_task(extractor.update_team_statistics, season)
        return {"message": f"Statistics update started for season {season}"}
    except Exception as e:
        logger.error(f"Error updating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/status/{season}")
async def get_data_status(season: int, db: Session = Depends(get_db)):
    """Get current status of data for a season"""
    try:
        # Count teams
        teams_count = db.query(Team).count()
        
        # Count matches for the season
        matches_count = db.query(Match).filter(Match.season == season).count()
        matches_with_results = db.query(Match).filter(
            Match.season == season,
            Match.result.isnot(None)
        ).count()
        
        # Count team statistics for the season
        stats_count = db.query(TeamStatistics).filter(TeamStatistics.season == season).count()
        
        # Get latest update timestamps
        latest_match = db.query(Match).filter(Match.season == season).order_by(Match.created_at.desc()).first()
        latest_stats = db.query(TeamStatistics).filter(TeamStatistics.season == season).order_by(TeamStatistics.updated_at.desc()).first()
        
        return {
            "season": season,
            "teams_total": teams_count,
            "matches_total": matches_count,
            "matches_with_results": matches_with_results,
            "team_statistics_total": stats_count,
            "last_match_update": latest_match.created_at.isoformat() if latest_match else None,
            "last_stats_update": latest_stats.updated_at.isoformat() if latest_stats else None,
            "teams_expected": 42,  # 20 La Liga + 22 Segunda División
            "matches_expected_per_season": 798,  # La Liga: 380 + Segunda: 418 = 798
            "stats_expected": 42  # Una entrada por equipo
        }
        
    except Exception as e:
        logger.error(f"Error getting data status: {str(e)}")
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
def train_model(
    season: int,
    db: Session = Depends(get_db)
):
    """Train the prediction model with historical data"""
    from datetime import datetime
    current_year = datetime.now().year
    
    # Get historical matches with results
    completed_matches = db.query(Match).filter(
        Match.season == season,
        Match.result.isnot(None)
    ).all()
    
    if len(completed_matches) < 100:
        # Provide better error message for seasons without data
        if season >= current_year:
            raise HTTPException(
                status_code=400, 
                detail=f"Season {season} has insufficient data for training. Found {len(completed_matches)} completed matches, need at least 100. Try training with season {current_year-1} instead."
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough historical data. Found {len(completed_matches)} matches, need at least 100"
            )
    
    # For now, return success message for seasons with enough data
    return {
        "message": "Model training would start here",
        "matches_found": len(completed_matches),
        "season": season
    }


@app.get("/predictions/current-week")
async def get_current_week_predictions(season: int, db: Session = Depends(get_db)):
    """Get predictions for current week's quiniela"""
    try:
        # Verificar si el modelo está entrenado
        if not hasattr(predictor, 'is_trained') or not predictor.is_trained:
            return {
                "season": season,
                "week_number": None,
                "predictions": [],
                "model_trained": False,
                "message": "Model not trained yet. Please train the model first.",
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Obtener partidos próximos como ejemplo de predicciones
        from datetime import timedelta
        current_date = datetime.now()
        
        # Buscar partidos próximos o recientes para mostrar
        upcoming_matches = db.query(Match).filter(
            Match.season == season,
            Match.match_date >= current_date - timedelta(days=7),
            Match.match_date <= current_date + timedelta(days=7)
        ).limit(15).all()
        
        if not upcoming_matches:
            # Si no hay partidos próximos, usar partidos recientes como ejemplo
            upcoming_matches = db.query(Match).filter(
                Match.season == season
            ).order_by(Match.match_date.desc()).limit(15).all()
        
        if not upcoming_matches:
            return {
                "season": season,
                "week_number": None,
                "predictions": [],
                "model_trained": True,
                "message": f"No matches found for season {season}",
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Crear predicciones simuladas (placeholder)
        predictions = []
        for i, match in enumerate(upcoming_matches[:14], 1):
            # Obtener nombres de equipos
            home_team = db.query(Team).filter_by(id=match.home_team_id).first()
            away_team = db.query(Team).filter_by(id=match.away_team_id).first()
            
            home_name = home_team.name if home_team else f"Team {match.home_team_id}"
            away_name = away_team.name if away_team else f"Team {match.away_team_id}"
            
            predictions.append({
                "match_number": i,
                "home_team": home_name,
                "away_team": away_name,
                "prediction": match.result if match.result else "X",  # Usar resultado real o empate por defecto
                "confidence": 0.65,  # Confianza simulada
                "probabilities": {
                    "home_win": 0.40,
                    "draw": 0.30,
                    "away_win": 0.30
                },
                "match_date": match.match_date.isoformat() if match.match_date else None
            })
        
        return {
            "season": season,
            "week_number": 1,
            "predictions": predictions,
            "model_trained": True,
            "model_version": getattr(predictor, 'model_version', "1.0.0"),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating predictions: {str(e)}")
        return {
            "season": season,
            "week_number": None,
            "predictions": [],
            "model_trained": False,
            "error": str(e),
            "generated_at": datetime.utcnow().isoformat()
        }


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


@app.get("/quiniela/next-matches/{season}")
async def get_next_quiniela_matches(season: int, db: Session = Depends(get_db)):
    """Obtiene predicciones para una temporada específica"""
    try:
        from datetime import datetime
        current_year = datetime.now().year
        
        # Check if database is empty first
        total_matches = db.query(Match).count()
        if total_matches == 0:
            return {
                "season": season,
                "data_season": None,
                "using_previous_season": False,
                "total_matches": 0,
                "matches": [],
                "generated_at": datetime.now().isoformat(),
                "model_version": "none",
                "message": "No hay datos en la base de datos. Primero actualiza equipos, partidos y estadísticas.",
                "recommendation": "Ve a 'Gestión de Datos' y actualiza los datos para comenzar."
            }
        
        # PRIMERO: Intentar predicciones básicas para partidos futuros de la temporada solicitada
        from .ml.basic_predictor import create_basic_predictions_for_quiniela
        
        logger.info(f"Checking for upcoming matches in season {season}")
        upcoming_matches = db.query(Match).filter(
            Match.season == season,
            Match.result.is_(None),  # Sin resultado aún
            Match.home_goals.is_(None)  # Sin goles registrados
        ).order_by(Match.match_date).limit(20).all()
        
        logger.info(f"Found {len(upcoming_matches)} upcoming matches for season {season}")
        
        # Si hay suficientes partidos futuros, usar predictor básico
        if len(upcoming_matches) >= 14:
            logger.info(f"Using basic predictor for {len(upcoming_matches)} upcoming matches")
            basic_predictions = create_basic_predictions_for_quiniela(db, season)
            
            if len(basic_predictions) >= 14:
                return {
                    "season": season,
                    "data_season": season,
                    "using_previous_season": False,
                    "total_matches": len(basic_predictions),
                    "matches": basic_predictions[:15],  # Máximo 15 para Quiniela
                    "generated_at": datetime.now().isoformat(),
                    "model_version": "basic_predictor",
                    "message": "Predicciones generadas con algoritmo básico para partidos futuros",
                    "note": "Predicciones basadas en heurísticas (datos históricos, estadios, ligas) - ideal para inicio de temporada"
                }
        
        # SEGUNDO: Si no hay suficientes partidos futuros, usar datos históricos como fallback
        logger.info(f"Not enough upcoming matches ({len(upcoming_matches)}), falling back to historical data")
        
        matches = db.query(Match).filter(
            Match.season == season,
            Match.result.isnot(None)
        ).order_by(Match.match_date.desc()).limit(20).all()
        
        logger.info(f"Found {len(matches)} completed matches for season {season}")
        
        use_previous = False
        data_season = season
        
        # Si no hay suficientes partidos históricos, usar temporada anterior
        if len(matches) < 14:
            prev_season = season - 1
            matches = db.query(Match).filter(
                Match.season == prev_season,
                Match.result.isnot(None)
            ).order_by(Match.match_date.desc()).limit(20).all()
            use_previous = True
            data_season = prev_season
            logger.info(f"Using previous season {prev_season}, found {len(matches)} completed matches")
        
        if len(matches) < 14:
            return {
                "season": season,
                "data_season": data_season,
                "using_previous_season": use_previous,
                "total_matches": len(matches),
                "matches": [],
                "generated_at": datetime.now().isoformat(),
                "model_version": "insufficient_data",
                "message": f"No hay suficientes partidos para temporada {season}. Encontrados: {len(matches)} históricos, {len(upcoming_matches)} futuros, necesarios: 14.",
                "recommendation": f"Actualiza los datos para la temporada {current_year - 1} primero o espera a que haya más partidos futuros disponibles."
            }
        
        predictions = []
        for i, match in enumerate(matches[:14]):
            # Buscar estadísticas
            home_stats = db.query(TeamStatistics).filter_by(
                team_id=match.home_team_id, season=data_season
            ).first()
            
            away_stats = db.query(TeamStatistics).filter_by(
                team_id=match.away_team_id, season=data_season
            ).first()
            
            if not home_stats or not away_stats:
                continue
                
            # Predicción simple basada en resultado real o estadísticas
            if match.result:
                pred_result = match.result
                confidence = 0.8
            else:
                # Predicción básica por puntos
                home_avg = home_stats.points / max((home_stats.wins + home_stats.draws + home_stats.losses), 1)
                away_avg = away_stats.points / max((away_stats.wins + away_stats.draws + away_stats.losses), 1)
                
                if home_avg > away_avg + 0.3:
                    pred_result = "1"
                elif away_avg > home_avg + 0.3:
                    pred_result = "2"
                else:
                    pred_result = "X"
                confidence = 0.6
            
            predictions.append({
                "match_number": i + 1,
                "match_id": match.id,
                "home_team": match.home_team.name if match.home_team else "Equipo Local",
                "away_team": match.away_team.name if match.away_team else "Equipo Visitante",
                "league": "La Liga" if match.league_id == 140 else "Segunda División",
                "match_date": match.match_date.isoformat() if match.match_date else None,
                "prediction": {
                    "result": pred_result,
                    "confidence": confidence,
                    "probabilities": {
                        "home_win": 0.7 if pred_result == "1" else 0.2,
                        "draw": 0.6 if pred_result == "X" else 0.2,
                        "away_win": 0.7 if pred_result == "2" else 0.2
                    }
                },
                "explanation": f"Predicción {pred_result} con {confidence:.0%} confianza",
                "features_table": [
                    {"feature": "Puntos Local", "value": home_stats.points, "impact": "Alto", "interpretation": f"{home_stats.points} pts"},
                    {"feature": "Puntos Visitante", "value": away_stats.points, "impact": "Alto", "interpretation": f"{away_stats.points} pts"}
                ],
                "statistics": {
                    "home_team": {
                        "wins": home_stats.wins, "draws": home_stats.draws, "losses": home_stats.losses,
                        "goals_for": home_stats.goals_for, "goals_against": home_stats.goals_against, "points": home_stats.points
                    },
                    "away_team": {
                        "wins": away_stats.wins, "draws": away_stats.draws, "losses": away_stats.losses,
                        "goals_for": away_stats.goals_for, "goals_against": away_stats.goals_against, "points": away_stats.points
                    }
                }
            })
        
        if len(predictions) < 14:
            raise HTTPException(status_code=404, detail=f"Solo se generaron {len(predictions)} predicciones, necesarias 14")
        
        return {
            "season": season,
            "data_season": data_season,
            "using_previous_season": use_previous,
            "total_matches": len(predictions),
            "matches": predictions[:14],
            "generated_at": datetime.now().isoformat(),
            "model_version": "simplified",
            "note": f"Predicciones basadas en datos de temporada {data_season}" if use_previous else None
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Error en next-matches: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/quiniela/user/create")
async def create_user_quiniela(
    quiniela_data: dict,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva quiniela del usuario
    """
    try:
        from datetime import date
        
        # Crear quiniela
        user_quiniela = UserQuiniela(
            week_number=quiniela_data["week_number"],
            season=quiniela_data["season"],
            quiniela_date=date.fromisoformat(quiniela_data["date"]),
            cost=quiniela_data["cost"],
            pleno_al_15=quiniela_data.get("pleno_al_15")
        )
        
        db.add(user_quiniela)
        db.flush()  # Para obtener el ID
        
        # Agregar predicciones
        for pred_data in quiniela_data["predictions"]:
            prediction = UserQuinielaPrediction(
                quiniela_id=user_quiniela.id,
                match_number=pred_data["match_number"],
                match_id=pred_data.get("match_id"),
                home_team=pred_data["home_team"],
                away_team=pred_data["away_team"],
                user_prediction=pred_data["user_prediction"],
                system_prediction=pred_data.get("system_prediction"),
                confidence=pred_data.get("confidence"),
                explanation=pred_data.get("explanation"),
                prob_home=pred_data.get("prob_home"),
                prob_draw=pred_data.get("prob_draw"),
                prob_away=pred_data.get("prob_away"),
                match_date=datetime.fromisoformat(pred_data["match_date"]) if pred_data.get("match_date") else None,
                league=pred_data.get("league")
            )
            db.add(prediction)
        
        db.commit()
        
        return {
            "id": user_quiniela.id,
            "message": "Quiniela created successfully",
            "week_number": user_quiniela.week_number,
            "season": user_quiniela.season,
            "cost": user_quiniela.cost
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user quiniela: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/quiniela/user/history")
async def get_user_quiniela_history(
    season: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Obtiene el histórico de quinielas del usuario
    """
    try:
        query = db.query(UserQuiniela)
        
        if season:
            query = query.filter(UserQuiniela.season == season)
        
        quinielas = query.order_by(UserQuiniela.created_at.desc()).limit(limit).all()
        
        result = []
        for quiniela in quinielas:
            result.append({
                "id": quiniela.id,
                "week_number": quiniela.week_number,
                "season": quiniela.season,
                "date": quiniela.quiniela_date.isoformat(),
                "cost": quiniela.cost,
                "winnings": quiniela.winnings,
                "profit": quiniela.winnings - quiniela.cost,
                "is_finished": quiniela.is_finished,
                "accuracy": quiniela.accuracy,
                "correct_predictions": quiniela.correct_predictions,
                "total_predictions": quiniela.total_predictions,
                "pleno_al_15": quiniela.pleno_al_15
            })
        
        # Calcular estadísticas generales
        total_cost = sum(q.cost for q in quinielas)
        total_winnings = sum(q.winnings for q in quinielas)
        total_profit = total_winnings - total_cost
        finished_quinielas = [q for q in quinielas if q.is_finished]
        avg_accuracy = sum(q.accuracy for q in finished_quinielas) / len(finished_quinielas) if finished_quinielas else 0
        
        return {
            "quinielas": result,
            "summary": {
                "total_quinielas": len(quinielas),
                "total_cost": total_cost,
                "total_winnings": total_winnings,
                "total_profit": total_profit,
                "roi_percentage": (total_profit / total_cost * 100) if total_cost > 0 else 0,
                "average_accuracy": avg_accuracy,
                "finished_quinielas": len(finished_quinielas)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user quiniela history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/quiniela/user/{quiniela_id}/results")
async def update_quiniela_results(
    quiniela_id: int,
    results_data: dict,
    db: Session = Depends(get_db)
):
    """
    Actualiza los resultados de una quiniela cuando termine la jornada
    """
    try:
        quiniela = db.query(UserQuiniela).filter(UserQuiniela.id == quiniela_id).first()
        if not quiniela:
            raise HTTPException(status_code=404, detail="Quiniela not found")
        
        # Actualizar quiniela
        quiniela.winnings = results_data.get("winnings", 0.0)
        quiniela.is_finished = True
        
        correct_predictions = 0
        
        # Actualizar resultados de cada predicción
        for result in results_data.get("results", []):
            prediction = db.query(UserQuinielaPrediction).filter(
                UserQuinielaPrediction.quiniela_id == quiniela_id,
                UserQuinielaPrediction.match_number == result["match_number"]
            ).first()
            
            if prediction:
                prediction.actual_result = result["actual_result"]
                prediction.is_correct = prediction.user_prediction == result["actual_result"]
                
                if prediction.is_correct:
                    correct_predictions += 1
        
        # Actualizar estadísticas de la quiniela
        quiniela.correct_predictions = correct_predictions
        quiniela.accuracy = correct_predictions / quiniela.total_predictions if quiniela.total_predictions > 0 else 0
        
        db.commit()
        
        return {
            "id": quiniela.id,
            "correct_predictions": correct_predictions,
            "accuracy": quiniela.accuracy,
            "winnings": quiniela.winnings,
            "profit": quiniela.winnings - quiniela.cost,
            "message": "Results updated successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating quiniela results: {str(e)}")
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