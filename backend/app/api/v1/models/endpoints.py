from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from ....database.database import get_db
from ....domain.entities.match import Match
from ....domain.entities.team import Team
from ....domain.entities.statistics import TeamStatistics
from ....ml.predictor import QuinielaPredictor
from ....services_v2.statistics_service import StatisticsService

router = APIRouter()
logger = logging.getLogger(__name__)

# Global predictor instance (shared across app)
predictor = QuinielaPredictor()


@router.post("/train")
def train_model(
    season: int = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Train the prediction model with historical data for specified season"""
    current_year = datetime.now().year
    
    # If no season provided, use current year  
    if season is None:
        season = current_year
        logger.info(f"No season specified, using current year: {season}")
    
    logger.info(f"🎯 TRAINING REQUEST: Iniciando entrenamiento para temporada {season}")
    
    # Get historical matches with results for requested season
    completed_matches = db.query(Match).filter(
        Match.season == season,
        Match.result.isnot(None)
    ).all()
    
    logger.info(f"Training request for season {season}, found {len(completed_matches)} completed matches")
    
    training_season = season
    matches_to_use = completed_matches
    
    # If future season (like 2025) or current season without sufficient data
    if len(completed_matches) < 100:
        # For future seasons, offer fallback to previous season
        if season >= current_year:
            # Try previous season as fallback
            fallback_season = season - 1
            fallback_matches = db.query(Match).filter(
                Match.season == fallback_season,
                Match.result.isnot(None)
            ).all()
            
            logger.info(f"Season {season} insufficient data, checking fallback season {fallback_season}: {len(fallback_matches)} matches")
            
            if len(fallback_matches) >= 100:
                # Use previous season for training
                training_season = fallback_season
                matches_to_use = fallback_matches
            else:
                return {
                    "message": f"Ni la temporada {season} ni la temporada {fallback_season} tienen datos suficientes para entrenar.",
                    "matches_found_current": len(completed_matches),
                    "matches_found_fallback": len(fallback_matches),
                    "minimum_required": 100,
                    "recommendation": f"Espera a que se completen más partidos de {season}, o carga datos históricos de {fallback_season}.",
                    "status": "insufficient_data",
                    "note": "Para temporadas nuevas, el sistema usa el Predictor Básico hasta que haya suficientes datos de entrenamiento ML."
                }
        else:
            # Historical season without enough data
            raise HTTPException(
                status_code=400, 
                detail=f"La temporada {season} tiene datos históricos insuficientes. Se encontraron {len(completed_matches)} partidos, se necesitan al menos 100."
            )
    
    # Start training in background
    def train_model_task():
        try:
            logger.info(f"🚀 TRAINING STARTED: Iniciando entrenamiento ML para temporada {training_season}")
            logger.info(f"📊 TRAINING DATA: {len(matches_to_use)} partidos encontrados para entrenamiento")
            
            # Prepare training data
            statistics_service = StatisticsService(db)
            
            logger.info(f"⚙️  TRAINING STEP 1/4: Preparando datos de entrenamiento...")
            
            # Convert matches to training format
            training_data = []
            processed = 0
            for match in matches_to_use:
                if match.home_team and match.away_team and match.result:
                    match_data = {
                        'match_id': match.id,
                        'home_team': match.home_team,
                        'away_team': match.away_team,
                        'season': match.season,
                        'league_id': match.league_id,
                        'result': match.result,
                        'home_goals': match.home_goals or 0,
                        'away_goals': match.away_goals or 0,
                        'match_date': match.match_date
                    }
                    training_data.append(match_data)
                    processed += 1
                    
                    # Log progress every 50 matches
                    if processed % 50 == 0:
                        progress = (processed / len(matches_to_use)) * 100
                        logger.info(f"📈 TRAINING PROGRESS: {processed}/{len(matches_to_use)} partidos procesados ({progress:.1f}%)")
            
            logger.info(f"✅ TRAINING STEP 1/4: Completado - {len(training_data)} partidos válidos procesados")
            
            if len(training_data) >= 100:
                logger.info(f"🤖 TRAINING STEP 2/4: Entrenando modelo ML con {len(training_data)} muestras...")
                
                # Train the model
                training_result = predictor.train_model(training_data)
                logger.info(f"✅ TRAINING STEP 2/4: Modelo entrenado exitosamente")
                logger.info(f"📋 TRAINING RESULTS: {training_result}")
                
                logger.info(f"⚙️  TRAINING STEP 3/4: Configurando modelo...")
                
                # Mark as trained
                predictor.is_trained = True
                model_version = f"v{training_season}_{datetime.now().strftime('%Y%m%d_%H%M')}"
                predictor.model_version = model_version
                logger.info(f"🏷️  MODEL VERSION: {model_version}")
                
                logger.info(f"💾 TRAINING STEP 4/4: Guardando modelo...")
                
                # Save model (if save method exists)
                try:
                    model_path = f"data/models/quiniela_model_{training_season}.pkl"
                    if hasattr(predictor, 'save_model'):
                        predictor.save_model(model_path)
                        logger.info(f"✅ MODEL SAVED: Modelo guardado en {model_path}")
                    else:
                        logger.info(f"✅ MODEL READY: Modelo entrenado y listo (método save no disponible)")
                except Exception as save_error:
                    logger.warning(f"⚠️  SAVE WARNING: Entrenamiento exitoso pero guardado falló: {save_error}")
                
                logger.info(f"🎉 TRAINING COMPLETED: Proceso de entrenamiento completado exitosamente para temporada {training_season}")
                logger.info(f"🎯 TRAINING SUMMARY: {len(training_data)} muestras procesadas, modelo v{model_version} listo")
            else:
                logger.error(f"❌ TRAINING FAILED: Datos insuficientes después del procesamiento: {len(training_data)} partidos válidos (se necesitan ≥100)")
                logger.error(f"🔍 TRAINING DEBUG: Verifica la calidad de los datos de la temporada {training_season}")
                
        except Exception as e:
            logger.error(f"❌ TRAINING ERROR: El entrenamiento del modelo falló: {str(e)}")
            import traceback
            logger.error(f"🔍 TRAINING ERROR DETAILS: {traceback.format_exc()}")
            logger.error(f"💡 TRAINING SUGGESTION: Verifica los datos de entrada y conexión a BD")
    
    # Add background task
    background_tasks.add_task(train_model_task)
    
    return {
        "message": f"Entrenamiento del modelo iniciado en segundo plano usando datos de la temporada {training_season}.",
        "matches_found": len(matches_to_use),
        "training_season": training_season,
        "requested_season": season,
        "status": "training_started",
        "estimated_duration": "5-10 minutos",
        "note": "El entrenamiento se ejecuta en segundo plano. Verifica el estado del modelo en unos minutos.",
        "check_status_url": "/analytics/model-performance"
    }


@router.get("/training-status")
async def get_training_status():
    """Get detailed training status of the model"""
    try:
        is_trained = getattr(predictor, 'is_trained', False)
        model_version = getattr(predictor, 'model_version', None)
        
        status_details = {
            "is_trained": is_trained,
            "model_version": model_version,
            "training_status": "completed" if is_trained else "not_trained",
            "last_check": datetime.utcnow().isoformat(),
            "capabilities": {
                "basic_predictions": True,
                "ml_predictions": is_trained,
                "enhanced_predictions": is_trained,
                "fallback_mode": not is_trained
            }
        }
        
        if is_trained and model_version:
            # Extract season and timestamp from version
            try:
                version_parts = model_version.split('_')
                if len(version_parts) >= 2:
                    season = version_parts[0][1:]  # Remove 'v' prefix
                    timestamp = version_parts[1] + "_" + version_parts[2] if len(version_parts) >= 3 else version_parts[1]
                    status_details["trained_for_season"] = int(season)
                    status_details["training_timestamp"] = timestamp
                    status_details["model_ready_for"] = f"temporada {season}"
            except (ValueError, IndexError):
                pass
        
        return status_details
        
    except Exception as e:
        logger.error(f"Error getting training status: {str(e)}")
        return {
            "is_trained": False,
            "model_version": None,
            "training_status": "error",
            "error": str(e),
            "capabilities": {
                "basic_predictions": True,
                "ml_predictions": False,
                "enhanced_predictions": False,
                "fallback_mode": True
            },
            "last_check": datetime.utcnow().isoformat()
        }


@router.get("/requirements")
async def get_model_requirements():
    """
    Explain model requirements and prediction capabilities
    """
    return {
        "prediction_modes": {
            "basic_predictor": {
                "requires_training": False,
                "description": "Predictor heurístico basado en factores como ventaja local, experiencia de equipo, capacidad de estadio",
                "confidence_range": "30-45%",
                "data_required": "Información básica de equipos y estadios",
                "availability": "Siempre disponible",
                "quality": "Buena para inicios de temporada y cuando faltan datos históricos"
            },
            "ml_predictor": {
                "requires_training": True,
                "description": "Modelo ML entrenado con datos históricos de partidos",
                "confidence_range": "45-70%", 
                "data_required": "Mínimo 100 partidos históricos con resultados",
                "availability": "Después del entrenamiento",
                "quality": "Excelente cuando hay suficientes datos históricos"
            },
            "enhanced_predictor": {
                "requires_training": True,
                "description": "Combinación de ML + datos avanzados (xG, xA, etc.)",
                "confidence_range": "50-80%",
                "data_required": "Datos ML + datos avanzados de FBRef",
                "availability": "Con modelo entrenado + datos FBRef",
                "quality": "La mejor calidad predictiva disponible"
            }
        },
        "current_system_status": {
            "active_mode": "basic_predictor" if not getattr(predictor, 'is_trained', False) else "ml_predictor",
            "state_of_art_ready": True,  # Basic predictor siempre está listo
            "training_required_for_ml": not getattr(predictor, 'is_trained', False),
            "recommendation": "Las predicciones 'estado del arte' funcionan sin entrenamiento usando el predictor básico. El entrenamiento ML mejora la precisión cuando hay datos suficientes."
        },
        "important_note": "⚠️ Las predicciones estado del arte NO requieren entrenamiento ML. El sistema usa automáticamente el mejor predictor disponible (basic → ML → enhanced) según los datos disponibles."
    }