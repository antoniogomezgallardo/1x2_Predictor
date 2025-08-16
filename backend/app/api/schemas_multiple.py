"""
Esquemas Pydantic para dobles, triples y Elige 8
Soporte completo para quinielas múltiples según normativa BOE
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator, Field
from enum import Enum


class BetType(str, Enum):
    """Tipos de apuesta según normativa oficial"""
    SIMPLE = "simple"
    MULTIPLE = "multiple"
    REDUCED_PRIMERA = "reduced_primera"
    REDUCED_SEGUNDA = "reduced_segunda"
    REDUCED_TERCERA = "reduced_tercera"
    REDUCED_CUARTA = "reduced_cuarta"
    REDUCED_QUINTA = "reduced_quinta"
    REDUCED_SEXTA = "reduced_sexta"


class PredictionMultiplicity(BaseModel):
    """Predicción con soporte para multiplicidad"""
    match_number: int = Field(..., ge=1, le=15, description="Número del partido (1-15)")
    match_id: Optional[int] = Field(None, description="ID del partido en BD")
    home_team: str = Field(..., description="Equipo local")
    away_team: str = Field(..., description="Equipo visitante")
    prediction_options: List[str] = Field(..., description="Opciones seleccionadas: ['1'], ['1','X'], etc.")
    multiplicity: int = Field(..., ge=1, le=3, description="1=simple, 2=doble, 3=triple")
    
    @validator('prediction_options')
    def validate_prediction_options(cls, v):
        """Validar opciones de predicción"""
        valid_options = ["1", "X", "2"]
        if not v or len(v) == 0:
            raise ValueError("Debe tener al menos una opción")
        if len(v) > 3:
            raise ValueError("Máximo 3 opciones (triple)")
        for option in v:
            if option not in valid_options:
                raise ValueError(f"Opción '{option}' no válida. Usar: 1, X, 2")
        if len(set(v)) != len(v):
            raise ValueError("No se pueden repetir opciones")
        return sorted(v)  # Ordenar para consistencia
    
    @validator('multiplicity', always=True)
    def validate_multiplicity_consistency(cls, v, values):
        """Validar que multiplicidad coincide con opciones"""
        if 'prediction_options' in values:
            expected_multiplicity = len(values['prediction_options'])
            if v != expected_multiplicity:
                raise ValueError(f"Multiplicidad {v} no coincide con {expected_multiplicity} opciones")
        return v


class Elige8Configuration(BaseModel):
    """Configuración del Elige 8"""
    enabled: bool = Field(False, description="Si está habilitado el Elige 8")
    selected_matches: List[int] = Field([], description="Números de partidos seleccionados (1-15)")
    predictions: List[str] = Field([], description="Predicciones específicas para Elige 8")
    
    @validator('selected_matches')
    def validate_selected_matches(cls, v, values):
        """Validar selección de partidos para Elige 8"""
        if values.get('enabled', False):
            if len(v) != 8:
                raise ValueError("Elige 8 requiere exactamente 8 partidos")
            if not all(1 <= match <= 15 for match in v):
                raise ValueError("Números de partido deben estar entre 1 y 15")
            if len(set(v)) != 8:
                raise ValueError("No se pueden repetir partidos en Elige 8")
        return sorted(v)  # Ordenar para consistencia
    
    @validator('predictions')
    def validate_predictions(cls, v, values):
        """Validar predicciones del Elige 8"""
        if values.get('enabled', False):
            if len(v) != 8:
                raise ValueError("Elige 8 requiere exactamente 8 predicciones")
            valid_options = ["1", "X", "2"]
            for pred in v:
                if pred not in valid_options:
                    raise ValueError(f"Predicción '{pred}' no válida para Elige 8")
        return v


class MultipleQuinielaCreate(BaseModel):
    """Crear quiniela con dobles, triples y Elige 8"""
    season: int = Field(..., description="Temporada")
    week_number: int = Field(..., description="Número de jornada")
    predictions: List[PredictionMultiplicity] = Field(..., description="Predicciones con multiplicidad")
    bet_type: BetType = Field(BetType.SIMPLE, description="Tipo de apuesta")
    elige_8: Optional[Elige8Configuration] = Field(None, description="Configuración Elige 8")
    
    # Pleno al 15 (opcional)
    pleno_al_15_home: Optional[str] = Field(None, description="Goles equipo local partido 15")
    pleno_al_15_away: Optional[str] = Field(None, description="Goles equipo visitante partido 15")
    
    @validator('predictions')
    def validate_predictions_count(cls, v):
        """Validar que hay exactamente 15 predicciones"""
        if len(v) != 15:
            raise ValueError("Debe haber exactamente 15 predicciones")
        
        # Validar numeración secuencial
        numbers = [p.match_number for p in v]
        expected = list(range(1, 16))
        if sorted(numbers) != expected:
            raise ValueError("Numeración de partidos debe ser secuencial 1-15")
        
        return v
    
    @validator('elige_8')
    def validate_elige_8_matches(cls, v, values):
        """Validar que partidos Elige 8 existen en predicciones"""
        if v and v.enabled and 'predictions' in values:
            prediction_numbers = {p.match_number for p in values['predictions']}
            for match_num in v.selected_matches:
                if match_num not in prediction_numbers:
                    raise ValueError(f"Elige 8: partido {match_num} no existe en predicciones")
        return v


class QuinielaValidationRequest(BaseModel):
    """Solicitud de validación de quiniela múltiple"""
    predictions: List[PredictionMultiplicity]
    elige_8: Optional[Elige8Configuration] = None


class QuinielaValidationResponse(BaseModel):
    """Respuesta de validación de quiniela"""
    valid: bool
    total_combinations: int
    base_cost: float
    elige_8_cost: float
    total_cost: float
    bet_type: str
    errors: List[str] = []
    warnings: List[str] = []
    
    # Información adicional
    breakdown: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)


class OfficialReduction(BaseModel):
    """Reducción oficial del BOE"""
    name: str = Field(..., description="Nombre de la reducción")
    triples: int = Field(..., description="Número de triples")
    dobles: int = Field(..., description="Número de dobles")
    combinations: int = Field(..., description="Total combinaciones")
    cost: float = Field(..., description="Costo en euros")
    description: str = Field(..., description="Descripción detallada")


class OfficialReductionsResponse(BaseModel):
    """Lista de reducciones oficiales disponibles"""
    reductions: List[OfficialReduction]
    total_available: int
    budget_recommendations: Dict[str, List[str]] = Field(default_factory=dict)


class MultipleQuinielaResponse(BaseModel):
    """Respuesta de quiniela múltiple creada"""
    id: int
    season: int
    week_number: int
    bet_type: str
    total_combinations: int
    base_cost: float
    elige_8_enabled: bool
    elige_8_cost: float
    total_cost: float
    created_at: str
    
    # Detalles de la configuración
    summary: Dict[str, Any] = Field(default_factory=dict)
    breakdown_by_match: List[Dict[str, Any]] = Field(default_factory=list)


class QuinielaCostCalculator(BaseModel):
    """Calculadora de costos en tiempo real"""
    multiplicities: List[int] = Field(..., description="Lista de multiplicidades por partido")
    elige_8_enabled: bool = Field(False, description="Si Elige 8 está activo")
    
    @validator('multiplicities')
    def validate_multiplicities(cls, v):
        """Validar multiplicidades"""
        if len(v) != 15:
            raise ValueError("Debe haber exactamente 15 multiplicidades")
        if not all(1 <= m <= 3 for m in v):
            raise ValueError("Multiplicidades deben estar entre 1 y 3")
        return v


class QuinielaCostResponse(BaseModel):
    """Respuesta de cálculo de costos"""
    total_combinations: int
    base_cost: float
    elige_8_cost: float
    total_cost: float
    cost_breakdown: Dict[str, Any]
    efficiency_metrics: Dict[str, float]
    budget_category: str  # "economica", "moderada", "alta", "profesional"


class QuinielaMultipleFilter(BaseModel):
    """Filtros para listar quinielas múltiples"""
    season: Optional[int] = None
    bet_type: Optional[BetType] = None
    elige_8_only: Optional[bool] = None
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class QuinielaMultipleList(BaseModel):
    """Lista de quinielas múltiples"""
    quinielas: List[MultipleQuinielaResponse]
    total_count: int
    total_invested: float
    total_combinations: int
    avg_cost_per_quiniela: float
    bet_type_summary: Dict[str, int]