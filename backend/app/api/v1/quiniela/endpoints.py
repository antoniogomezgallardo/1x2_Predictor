from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
import logging

from ....database.database import get_db
from ....database.models import *
from ....ml.basic_predictor import create_basic_predictions_for_quiniela, create_basic_predictions_for_matches, extract_spanish_jornada

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/next-matches/{season}")
async def get_next_quiniela_matches(season: int, db: Session = Depends(get_db)):
    """Obtiene predicciones para una temporada específica"""
    try:
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
            basic_result = create_basic_predictions_for_quiniela(db, season)
            
            if isinstance(basic_result, dict) and len(basic_result.get('predictions', [])) >= 14:
                predictions = basic_result['predictions']
                detected_round = basic_result.get('detected_round')
                round_type = basic_result.get('round_type', 'jornada')
                jornada_display = basic_result.get('jornada_display', 'Jornada 1')
                
                return {
                    "season": season,
                    "data_season": season,
                    "using_previous_season": False,
                    "total_matches": len(predictions),
                    "matches": predictions[:15],  # Máximo 15 para Quiniela
                    "generated_at": datetime.now().isoformat(),
                    "model_version": "basic_predictor",
                    "message": "Predicciones generadas con algoritmo básico para partidos futuros",
                    "note": "Predicciones basadas en heurísticas (datos históricos, estadios, ligas) - ideal para inicio de temporada",
                    "detected_round": detected_round,
                    "round_type": round_type,
                    "round_display": jornada_display
                }
            elif isinstance(basic_result, list) and len(basic_result) >= 14:
                # Fallback para compatibilidad con versión anterior
                return {
                    "season": season,
                    "data_season": season,
                    "using_previous_season": False,
                    "total_matches": len(basic_result),
                    "matches": basic_result[:15],
                    "generated_at": datetime.now().isoformat(),
                    "model_version": "basic_predictor",
                    "message": "Predicciones generadas con algoritmo básico para partidos futuros",
                    "note": "Predicciones basadas en heurísticas",
                    "detected_round": "desconocida",
                    "round_type": "jornada",
                    "round_display": "Jornada 1"
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


@router.post("/user/create")
async def create_user_quiniela(
    quiniela_data: dict,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva quiniela del usuario
    """
    try:
        # Procesar Pleno al 15 (formato: "home_goals-away_goals")
        pleno_al_15_data = quiniela_data.get("pleno_al_15", "1-1")
        if "-" in pleno_al_15_data:
            pleno_home, pleno_away = pleno_al_15_data.split("-", 1)
        else:
            # Backward compatibility - si viene en formato antiguo, asignar valores por defecto
            pleno_home, pleno_away = "1", "1"
        
        # Crear quiniela
        user_quiniela = UserQuiniela(
            week_number=quiniela_data["week_number"],
            season=quiniela_data["season"],
            quiniela_date=date.fromisoformat(quiniela_data["date"]),
            cost=quiniela_data["cost"],
            pleno_al_15_home=pleno_home,
            pleno_al_15_away=pleno_away
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


@router.get("/user/history")
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
                "pleno_al_15_home": quiniela.pleno_al_15_home,
                "pleno_al_15_away": quiniela.pleno_al_15_away
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


@router.put("/user/{quiniela_id}/results")
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


@router.post("/custom-config/save")
async def save_custom_quiniela_config(
    config_data: dict,
    db: Session = Depends(get_db)
):
    """
    Guarda una configuración personalizada de Quiniela seleccionada manualmente por el usuario
    """
    try:
        # Validar datos requeridos
        required_fields = ["week_number", "season", "config_name", "selected_match_ids", "pleno_al_15_match_id"]
        for field in required_fields:
            if field not in config_data:
                raise HTTPException(status_code=400, detail=f"Campo requerido '{field}' no encontrado")
        
        # Validar que se seleccionaron exactamente 15 partidos
        selected_matches = config_data["selected_match_ids"]
        if len(selected_matches) != 15:
            raise HTTPException(status_code=400, detail=f"Debe seleccionar exactamente 15 partidos. Seleccionados: {len(selected_matches)}")
        
        # Validar que el partido del Pleno al 15 está en la lista seleccionada
        pleno_match_id = config_data["pleno_al_15_match_id"]
        if pleno_match_id not in selected_matches:
            raise HTTPException(status_code=400, detail="El partido del Pleno al 15 debe estar entre los partidos seleccionados")
        
        # Validar que todos los partidos existen en la base de datos
        existing_match_ids = [m.id for m in db.query(Match.id).filter(Match.id.in_(selected_matches)).all()]
        missing_matches = set(selected_matches) - set(existing_match_ids)
        if missing_matches:
            raise HTTPException(status_code=404, detail=f"Partidos no encontrados: {missing_matches}")
        
        # Contar partidos por liga
        match_leagues = db.query(Match.league_id).filter(Match.id.in_(selected_matches)).all()
        la_liga_count = sum(1 for league in match_leagues if league[0] == 140)
        segunda_count = sum(1 for league in match_leagues if league[0] == 141)
        
        # Desactivar configuraciones previas para la misma semana/temporada
        db.query(CustomQuinielaConfig).filter(
            CustomQuinielaConfig.week_number == config_data["week_number"],
            CustomQuinielaConfig.season == config_data["season"]
        ).update({"is_active": False})
        
        # Crear nueva configuración
        new_config = CustomQuinielaConfig(
            week_number=config_data["week_number"],
            season=config_data["season"],
            config_name=config_data["config_name"],
            selected_match_ids=selected_matches,
            pleno_al_15_match_id=pleno_match_id,
            la_liga_count=la_liga_count,
            segunda_count=segunda_count,
            is_active=True,
            created_by_user=True
        )
        
        db.add(new_config)
        db.commit()
        
        # Obtener información detallada de los partidos seleccionados para respuesta
        selected_match_details = db.query(Match).filter(Match.id.in_(selected_matches)).all()
        match_info = []
        for match in selected_match_details:
            match_info.append({
                "id": match.id,
                "home_team": match.home_team.name if match.home_team else "TBD",
                "away_team": match.away_team.name if match.away_team else "TBD",
                "league": "La Liga" if match.league_id == 140 else "Segunda División",
                "match_date": match.match_date.isoformat() if match.match_date else None,
                "is_pleno_al_15": match.id == pleno_match_id
            })
        
        return {
            "id": new_config.id,
            "message": "Configuración personalizada guardada exitosamente",
            "config_name": new_config.config_name,
            "week_number": new_config.week_number,
            "season": new_config.season,
            "total_matches": len(selected_matches),
            "la_liga_count": la_liga_count,
            "segunda_count": segunda_count,
            "pleno_al_15_match_id": pleno_match_id,
            "selected_matches": match_info,
            "created_at": new_config.created_at.isoformat(),
            "status": "active"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving custom quiniela config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/from-config/{config_id}")
async def get_predictions_from_config(config_id: int, db: Session = Depends(get_db)):
    """
    Genera predicciones usando una configuración personalizada guardada
    """
    try:
        # Obtener configuración
        config = db.query(CustomQuinielaConfig).filter_by(id=config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
        # Obtener partidos de la configuración
        selected_matches = db.query(Match).filter(Match.id.in_(config.selected_match_ids)).all()
        
        if len(selected_matches) < 14:
            raise HTTPException(status_code=400, detail=f"Configuración inválida: solo {len(selected_matches)} partidos disponibles")
        
        # Generar predicciones básicas para estos partidos específicos
        predictions = create_basic_predictions_for_matches(db, selected_matches, config.season)
        
        return {
            "season": config.season,
            "config_name": config.config_name,
            "week_number": config.week_number,
            "data_season": config.season,
            "using_previous_season": False,
            "total_matches": len(predictions),
            "matches": predictions[:15],  # Máximo 15 para Quiniela
            "generated_at": datetime.now().isoformat(),
            "model_version": "basic_predictor_custom",
            "message": f"Predicciones generadas para configuración personalizada: {config.config_name}",
            "note": "Predicciones basadas en configuración personalizada de partidos seleccionados manualmente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating predictions from config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/custom-config/list")
async def get_custom_quiniela_configs(
    season: Optional[int] = None,
    only_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Obtiene las configuraciones personalizadas de Quiniela guardadas
    """
    try:
        query = db.query(CustomQuinielaConfig)
        
        if season:
            query = query.filter(CustomQuinielaConfig.season == season)
        
        if only_active:
            query = query.filter(CustomQuinielaConfig.is_active == True)
        
        configs = query.order_by(CustomQuinielaConfig.created_at.desc()).all()
        
        result = []
        for config in configs:
            # Obtener información de los partidos seleccionados
            selected_matches = db.query(Match).filter(Match.id.in_(config.selected_match_ids)).all()
            match_info = []
            for match in selected_matches:
                match_info.append({
                    "id": match.id,
                    "home_team": match.home_team.name if match.home_team else "TBD",
                    "away_team": match.away_team.name if match.away_team else "TBD",
                    "league": "La Liga" if match.league_id == 140 else "Segunda División",
                    "match_date": match.match_date.isoformat() if match.match_date else None,
                    "is_pleno_al_15": match.id == config.pleno_al_15_match_id
                })
            
            # CORRECCIÓN TEMPORAL: Corregir week_number incorrecto (33) a jornada real (1)
            week_number = config.week_number
            if week_number == 33:  # Datos incorrectos de la implementación anterior
                week_number = 1
                # Actualizar en la base de datos
                config.week_number = 1
                db.commit()
                logger.info(f"Corrected week_number from 33 to 1 for config {config.id}")
            
            result.append({
                "id": config.id,
                "config_name": config.config_name,
                "week_number": week_number,  # Usar el valor corregido
                "season": config.season,
                "total_matches": config.total_matches,
                "la_liga_count": config.la_liga_count,
                "segunda_count": config.segunda_count,
                "pleno_al_15_match_id": config.pleno_al_15_match_id,
                "is_active": config.is_active,
                "created_at": config.created_at.isoformat(),
                "selected_matches": match_info
            })
        
        return {
            "total_configs": len(result),
            "season_filter": season,
            "only_active": only_active,
            "configs": result
        }
        
    except Exception as e:
        logger.error(f"Error getting custom quiniela configs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/upcoming-by-round/{season}")
async def get_upcoming_matches_by_round(season: int, db: Session = Depends(get_db)):
    """
    Obtiene partidos de la próxima jornada para Primera y Segunda División
    """
    try:
        # Obtener la próxima jornada con partidos pendientes para cada liga
        la_liga_next_round_query = db.query(Match.round).filter(
            Match.season == season,
            Match.league_id == 140,
            Match.result.is_(None),  # Sin resultado
            Match.home_goals.is_(None)  # Sin goles
        ).order_by(Match.round).first()
        
        segunda_next_round_query = db.query(Match.round).filter(
            Match.season == season,
            Match.league_id == 141,
            Match.result.is_(None),  # Sin resultado
            Match.home_goals.is_(None)  # Sin goles
        ).order_by(Match.round).first()
        
        matches = []
        
        # Obtener partidos de La Liga de la próxima jornada
        if la_liga_next_round_query:
            la_liga_round = la_liga_next_round_query[0]
            la_liga_matches = db.query(Match).filter(
                Match.season == season,
                Match.league_id == 140,
                Match.round == la_liga_round,
                Match.result.is_(None)
            ).order_by(Match.match_date).all()
            matches.extend(la_liga_matches)
        
        # Obtener partidos de Segunda División de la próxima jornada
        if segunda_next_round_query:
            segunda_round = segunda_next_round_query[0]
            segunda_matches = db.query(Match).filter(
                Match.season == season,
                Match.league_id == 141,
                Match.round == segunda_round,
                Match.result.is_(None)
            ).order_by(Match.match_date).all()
            matches.extend(segunda_matches)
        
        # Convertir a formato API
        matches_data = []
        for match in matches[:30]:  # Limitar a 30 partidos
            matches_data.append({
                "id": match.id,
                "home_team": {
                    "id": match.home_team_id,
                    "name": match.home_team.name if match.home_team else "TBD"
                },
                "away_team": {
                    "id": match.away_team_id,
                    "name": match.away_team.name if match.away_team else "TBD"
                },
                "league_id": match.league_id,
                "match_date": match.match_date.isoformat() if match.match_date else None,
                "round": match.round,
                "season": match.season,
                "result": match.result
            })
        
        # Convertir rounds a jornadas españolas usando la misma lógica
        la_liga_jornada = None
        if la_liga_next_round_query:
            la_liga_round_raw = la_liga_next_round_query[0]
            # Extraer número de jornada desde el round
            la_liga_jornada = extract_spanish_jornada(la_liga_round_raw, [m for m in matches if m.league_id == 140])
            # Extraer solo el número
            if 'Jornada' in la_liga_jornada:
                try:
                    la_liga_jornada = int(la_liga_jornada.split('Jornada')[-1].strip())
                except:
                    la_liga_jornada = 1
            else:
                la_liga_jornada = 1
        
        segunda_jornada = None
        if segunda_next_round_query:
            segunda_round_raw = segunda_next_round_query[0]
            # Extraer número de jornada desde el round
            segunda_jornada = extract_spanish_jornada(segunda_round_raw, [m for m in matches if m.league_id == 141])
            # Extraer solo el número
            if 'Jornada' in segunda_jornada:
                try:
                    segunda_jornada = int(segunda_jornada.split('Jornada')[-1].strip())
                except:
                    segunda_jornada = 1
            else:
                segunda_jornada = 1
        
        return {
            "matches": matches_data,
            "total": len(matches_data),
            "season": season,
            "la_liga_round": la_liga_jornada,
            "segunda_round": segunda_jornada,
            "message": f"Próximos partidos para temporada {season}"
        }
        
    except Exception as e:
        logger.error(f"Error getting upcoming matches by round: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")