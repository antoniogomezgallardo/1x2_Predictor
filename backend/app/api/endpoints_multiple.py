"""
Endpoints API para dobles, triples y Elige 8
Implementación completa según normativa BOE-A-1998-17040
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
from datetime import datetime

from backend.app.database.database import get_db
from backend.app.database.models import UserQuiniela, UserQuinielaPrediction
from backend.app.api.schemas_multiple import (
    MultipleQuinielaCreate,
    MultipleQuinielaResponse,
    QuinielaValidationRequest,
    QuinielaValidationResponse,
    OfficialReductionsResponse,
    OfficialReduction,
    QuinielaCostCalculator,
    QuinielaCostResponse,
    QuinielaMultipleFilter,
    QuinielaMultipleList,
    BetType
)
from backend.app.services.quiniela_validator import (
    QuinielaValidator,
    QuinielaPrediction,
    QuinielaElige8,
    create_simple_quiniela
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quiniela/multiple", tags=["Quinielas Múltiples"])


@router.post("/validate", response_model=QuinielaValidationResponse)
def validate_multiple_quiniela(
    request: QuinielaValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validar configuración de quiniela múltiple antes de crear
    """
    try:
        # Convertir a formato interno del validador
        predictions = []
        for pred in request.predictions:
            predictions.append(QuinielaPrediction(
                match_number=pred.match_number,
                match_id=pred.match_id,
                home_team=pred.home_team,
                away_team=pred.away_team,
                prediction_options=pred.prediction_options
            ))
        
        # Configurar Elige 8 si está presente
        elige_8 = None
        if request.elige_8 and request.elige_8.enabled:
            elige_8 = QuinielaElige8(
                enabled=True,
                selected_matches=request.elige_8.selected_matches,
                predictions=request.elige_8.predictions
            )
        
        # Validar con el sistema oficial
        result = QuinielaValidator.validate_quiniela(predictions, elige_8)
        
        # Añadir información adicional
        breakdown = {
            "multiplicities": [len(p.prediction_options) for p in predictions],
            "combinations_by_match": [len(p.prediction_options) for p in predictions],
            "cost_per_bet": QuinielaValidator.BASE_COST_PER_BET,
            "elige_8_cost": QuinielaValidator.ELIGE_8_COST if (elige_8 and elige_8.enabled) else 0
        }
        
        # Sugerencias basadas en el resultado
        suggestions = []
        if result.total_combinations > 1000:
            suggestions.append("Considera usar reducciones oficiales para optimizar coste/cobertura")
        if result.bet_type == 'multiple' and result.total_combinations < 10:
            suggestions.append("Podrías añadir más dobles para mejorar las posibilidades")
        
        return QuinielaValidationResponse(
            valid=result.valid,
            total_combinations=result.total_combinations,
            base_cost=result.base_cost,
            elige_8_cost=result.elige_8_cost,
            total_cost=result.total_cost,
            bet_type=result.bet_type,
            errors=result.errors,
            warnings=result.warnings,
            breakdown=breakdown,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error validando quiniela múltiple: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en validación: {str(e)}"
        )


@router.post("/calculate-cost", response_model=QuinielaCostResponse)
def calculate_quiniela_cost(
    calculator: QuinielaCostCalculator,
    db: Session = Depends(get_db)
):
    """
    Calcular costo de quiniela en tiempo real
    """
    try:
        # Calcular combinaciones totales
        total_combinations = QuinielaValidator.calculate_combinations(calculator.multiplicities)
        
        # Calcular costos
        base_cost = total_combinations * QuinielaValidator.BASE_COST_PER_BET
        elige_8_cost = QuinielaValidator.ELIGE_8_COST if calculator.elige_8_enabled else 0
        total_cost = base_cost + elige_8_cost
        
        # Desglose detallado
        cost_breakdown = {
            "combinations_per_match": calculator.multiplicities,
            "total_combinations": total_combinations,
            "cost_per_bet": QuinielaValidator.BASE_COST_PER_BET,
            "base_calculation": f"{total_combinations} × €{QuinielaValidator.BASE_COST_PER_BET}",
            "elige_8_addition": elige_8_cost if calculator.elige_8_enabled else 0
        }
        
        # Métricas de eficiencia
        efficiency_metrics = {
            "combinations_per_euro": total_combinations / total_cost if total_cost > 0 else 0,
            "cost_per_combination": total_cost / total_combinations if total_combinations > 0 else 0,
            "dobles_count": calculator.multiplicities.count(2),
            "triples_count": calculator.multiplicities.count(3),
            "simples_count": calculator.multiplicities.count(1)
        }
        
        # Categoría de presupuesto
        if total_cost <= 10:
            budget_category = "economica"
        elif total_cost <= 100:
            budget_category = "moderada"
        elif total_cost <= 500:
            budget_category = "alta"
        else:
            budget_category = "profesional"
        
        return QuinielaCostResponse(
            total_combinations=total_combinations,
            base_cost=base_cost,
            elige_8_cost=elige_8_cost,
            total_cost=total_cost,
            cost_breakdown=cost_breakdown,
            efficiency_metrics=efficiency_metrics,
            budget_category=budget_category
        )
        
    except Exception as e:
        logger.error(f"Error calculando costo: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en cálculo: {str(e)}"
        )


@router.get("/reductions/official", response_model=OfficialReductionsResponse)
def get_official_reductions(
    budget_max: float = None,
    db: Session = Depends(get_db)
):
    """
    Obtener lista de reducciones oficiales del BOE
    """
    try:
        # Obtener reducciones oficiales del validador
        reductions_data = QuinielaValidator.OFFICIAL_REDUCTIONS
        
        reductions = []
        for name, config in reductions_data.items():
            reduction = OfficialReduction(
                name=name.title(),
                triples=config['triples'],
                dobles=config['dobles'],
                combinations=config['combinations'],
                cost=config['cost'],
                description=f"{config['dobles']} dobles + {config['triples']} triples = {config['combinations']} combinaciones"
            )
            
            # Filtrar por presupuesto si se especifica
            if budget_max is None or reduction.cost <= budget_max:
                reductions.append(reduction)
        
        # Ordenar por costo
        reductions.sort(key=lambda x: x.cost)
        
        # Recomendaciones por presupuesto
        budget_recommendations = {
            "economica": [r.name for r in reductions if r.cost <= 100],
            "moderada": [r.name for r in reductions if 100 < r.cost <= 500],
            "alta": [r.name for r in reductions if 500 < r.cost <= 2000],
            "profesional": [r.name for r in reductions if r.cost > 2000]
        }
        
        return OfficialReductionsResponse(
            reductions=reductions,
            total_available=len(reductions),
            budget_recommendations=budget_recommendations
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo reducciones oficiales: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo reducciones oficiales"
        )


@router.post("/create", response_model=MultipleQuinielaResponse)
def create_multiple_quiniela(
    quiniela: MultipleQuinielaCreate,
    db: Session = Depends(get_db)
):
    """
    Crear quiniela múltiple con dobles, triples y Elige 8
    """
    try:
        # Validar antes de crear
        predictions = []
        for pred in quiniela.predictions:
            predictions.append(QuinielaPrediction(
                match_number=pred.match_number,
                match_id=pred.match_id,
                home_team=pred.home_team,
                away_team=pred.away_team,
                prediction_options=pred.prediction_options
            ))
        
        elige_8 = None
        if quiniela.elige_8 and quiniela.elige_8.enabled:
            elige_8 = QuinielaElige8(
                enabled=True,
                selected_matches=quiniela.elige_8.selected_matches,
                predictions=quiniela.elige_8.predictions
            )
        
        # Validar configuración
        validation = QuinielaValidator.validate_quiniela(predictions, elige_8)
        if not validation.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuración inválida: {', '.join(validation.errors)}"
            )
        
        # Crear quiniela en base de datos
        db_quiniela = UserQuiniela(
            week_number=quiniela.week_number,
            season=quiniela.season,
            quiniela_date=datetime.now().date(),
            cost=validation.total_cost,
            bet_type=validation.bet_type,
            total_combinations=validation.total_combinations,
            base_cost=validation.base_cost,
            elige_8_enabled=elige_8.enabled if elige_8 else False,
            elige_8_matches=elige_8.selected_matches if elige_8 else None,
            elige_8_cost=validation.elige_8_cost,
            elige_8_predictions=elige_8.predictions if elige_8 else None,
            pleno_al_15_home=quiniela.pleno_al_15_home,
            pleno_al_15_away=quiniela.pleno_al_15_away,
            total_predictions=15
        )
        
        db.add(db_quiniela)
        db.flush()  # Para obtener el ID
        
        # Crear predicciones individuales
        breakdown_by_match = []
        for pred in quiniela.predictions:
            # Tomar la primera opción como predicción principal
            main_prediction = pred.prediction_options[0]
            
            db_prediction = UserQuinielaPrediction(
                quiniela_id=db_quiniela.id,
                match_number=pred.match_number,
                match_id=pred.match_id,
                home_team=pred.home_team,
                away_team=pred.away_team,
                user_prediction=main_prediction,
                multiplicity=pred.multiplicity,
                prediction_options=pred.prediction_options
            )
            
            db.add(db_prediction)
            
            # Añadir al breakdown
            breakdown_by_match.append({
                "match_number": pred.match_number,
                "teams": f"{pred.home_team} vs {pred.away_team}",
                "options": pred.prediction_options,
                "multiplicity": pred.multiplicity,
                "combinations": pred.multiplicity
            })
        
        db.commit()
        
        # Preparar respuesta
        summary = {
            "total_matches": 15,
            "simples": sum(1 for p in quiniela.predictions if len(p.prediction_options) == 1),
            "dobles": sum(1 for p in quiniela.predictions if len(p.prediction_options) == 2),
            "triples": sum(1 for p in quiniela.predictions if len(p.prediction_options) == 3),
            "elige_8_active": elige_8.enabled if elige_8 else False,
            "cost_breakdown": {
                "base": validation.base_cost,
                "elige_8": validation.elige_8_cost,
                "total": validation.total_cost
            }
        }
        
        return MultipleQuinielaResponse(
            id=db_quiniela.id,
            season=db_quiniela.season,
            week_number=db_quiniela.week_number,
            bet_type=db_quiniela.bet_type,
            total_combinations=db_quiniela.total_combinations,
            base_cost=db_quiniela.base_cost,
            elige_8_enabled=db_quiniela.elige_8_enabled,
            elige_8_cost=db_quiniela.elige_8_cost,
            total_cost=db_quiniela.cost,
            created_at=db_quiniela.created_at.isoformat(),
            summary=summary,
            breakdown_by_match=breakdown_by_match
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando quiniela múltiple: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando quiniela: {str(e)}"
        )


@router.get("/list", response_model=QuinielaMultipleList)
def list_multiple_quinielas(
    filters: QuinielaMultipleFilter = Depends(),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Listar quinielas múltiples con filtros
    """
    try:
        query = db.query(UserQuiniela)
        
        # Aplicar filtros
        if filters.season:
            query = query.filter(UserQuiniela.season == filters.season)
        
        if filters.bet_type:
            query = query.filter(UserQuiniela.bet_type == filters.bet_type.value)
        
        if filters.elige_8_only:
            query = query.filter(UserQuiniela.elige_8_enabled == True)
        
        if filters.min_cost:
            query = query.filter(UserQuiniela.cost >= filters.min_cost)
        
        if filters.max_cost:
            query = query.filter(UserQuiniela.cost <= filters.max_cost)
        
        # Obtener resultados
        total_count = query.count()
        quinielas = query.order_by(UserQuiniela.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convertir a respuesta
        quiniela_responses = []
        total_invested = 0
        total_combinations = 0
        bet_type_summary = {}
        
        for q in quinielas:
            total_invested += q.cost
            total_combinations += q.total_combinations
            
            bet_type_summary[q.bet_type] = bet_type_summary.get(q.bet_type, 0) + 1
            
            quiniela_responses.append(MultipleQuinielaResponse(
                id=q.id,
                season=q.season,
                week_number=q.week_number,
                bet_type=q.bet_type,
                total_combinations=q.total_combinations,
                base_cost=q.base_cost,
                elige_8_enabled=q.elige_8_enabled,
                elige_8_cost=q.elige_8_cost,
                total_cost=q.cost,
                created_at=q.created_at.isoformat()
            ))
        
        avg_cost = total_invested / len(quinielas) if quinielas else 0
        
        return QuinielaMultipleList(
            quinielas=quiniela_responses,
            total_count=total_count,
            total_invested=total_invested,
            total_combinations=total_combinations,
            avg_cost_per_quiniela=avg_cost,
            bet_type_summary=bet_type_summary
        )
        
    except Exception as e:
        logger.error(f"Error listando quinielas múltiples: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo lista de quinielas"
        )