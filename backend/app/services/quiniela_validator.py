"""
Validador y calculadora para quinielas con dobles, triples y Elige 8
Según normativa oficial BOE-A-1998-17040
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, validator
import json


class QuinielaPrediction(BaseModel):
    """Predicción individual de un partido"""
    match_number: int
    match_id: Optional[int] = None
    home_team: str
    away_team: str
    prediction_options: List[str]  # ["1"], ["1","X"], ["1","X","2"]
    multiplicity: int = 1  # Calculado automáticamente
    
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
    def calculate_multiplicity(cls, v, values):
        """Calcular multiplicidad automáticamente"""
        if 'prediction_options' in values:
            return len(values['prediction_options'])
        return 1


class QuinielaElige8(BaseModel):
    """Configuración del Elige 8"""
    enabled: bool = False
    selected_matches: List[int] = []  # IDs de los 8 partidos seleccionados
    predictions: List[str] = []  # Predicciones específicas para esos 8 partidos
    
    @validator('selected_matches')
    def validate_selected_matches(cls, v, values):
        """Validar selección de partidos para Elige 8"""
        if values.get('enabled', False):
            if len(v) != 8:
                raise ValueError("Elige 8 requiere exactamente 8 partidos")
            if len(set(v)) != 8:
                raise ValueError("No se pueden repetir partidos en Elige 8")
        return v


class QuinielaValidationResult(BaseModel):
    """Resultado de validación de quiniela"""
    valid: bool
    total_combinations: int
    base_cost: float
    elige_8_cost: float
    total_cost: float
    bet_type: str
    errors: List[str] = []
    warnings: List[str] = []


class QuinielaValidator:
    """Validador de quinielas según normativa oficial"""
    
    # Constantes oficiales
    BASE_COST_PER_BET = 0.75  # €0.75 por apuesta
    ELIGE_8_COST = 0.50  # €0.50 por Elige 8
    MIN_TOTAL_COST = 1.50  # Mínimo €1.50 total
    MAX_COMBINATIONS = 31104  # Máximo según BOE
    MIN_COMBINATIONS = 2  # Mínimo 2 apuestas
    
    # Reducciones oficiales predefinidas
    OFFICIAL_REDUCTIONS = {
        'primera': {'triples': 4, 'dobles': 0, 'combinations': 81, 'cost': 60.75},
        'segunda': {'triples': 0, 'dobles': 7, 'combinations': 128, 'cost': 96.00},
        'tercera': {'triples': 3, 'dobles': 3, 'combinations': 216, 'cost': 162.00},
        'cuarta': {'triples': 2, 'dobles': 6, 'combinations': 576, 'cost': 432.00},
        'quinta': {'triples': 8, 'dobles': 0, 'combinations': 6561, 'cost': 4920.75},
        'sexta': {'triples': 0, 'dobles': 11, 'combinations': 2048, 'cost': 1536.00},
    }
    
    @classmethod
    def validate_quiniela(
        cls, 
        predictions: List[QuinielaPrediction], 
        elige_8: Optional[QuinielaElige8] = None
    ) -> QuinielaValidationResult:
        """
        Validar quiniela completa según normativa oficial
        """
        errors = []
        warnings = []
        
        # Validar número de partidos
        if len(predictions) != 15:
            errors.append(f"Quiniela debe tener exactamente 15 partidos, tiene {len(predictions)}")
        
        # Validar numeración secuencial
        expected_numbers = set(range(1, 16))
        actual_numbers = set(p.match_number for p in predictions)
        if actual_numbers != expected_numbers:
            missing = expected_numbers - actual_numbers
            extra = actual_numbers - expected_numbers
            if missing:
                errors.append(f"Faltan partidos: {sorted(missing)}")
            if extra:
                errors.append(f"Partidos duplicados o incorrectos: {sorted(extra)}")
        
        # Calcular combinaciones totales
        total_combinations = 1
        multiplicities = []
        
        for pred in predictions:
            multiplicity = len(pred.prediction_options)
            multiplicities.append(multiplicity)
            total_combinations *= multiplicity
            
            # Validar multiplicidad individual
            if multiplicity not in [1, 2, 3]:
                errors.append(f"Partido {pred.match_number}: multiplicidad inválida {multiplicity}")
        
        # Validar límites de combinaciones
        if total_combinations < cls.MIN_COMBINATIONS:
            errors.append(f"Mínimo {cls.MIN_COMBINATIONS} apuestas requeridas, calculadas {total_combinations}")
        
        if total_combinations > cls.MAX_COMBINATIONS:
            errors.append(f"Máximo {cls.MAX_COMBINATIONS} apuestas permitidas, calculadas {total_combinations}")
        
        # Determinar tipo de apuesta
        bet_type = cls._determine_bet_type(multiplicities)
        
        # Calcular costos
        base_cost = total_combinations * cls.BASE_COST_PER_BET
        elige_8_cost = cls.ELIGE_8_COST if (elige_8 and elige_8.enabled) else 0.0
        total_cost = base_cost + elige_8_cost
        
        # Validar costo mínimo
        if total_cost < cls.MIN_TOTAL_COST:
            errors.append(f"Apuesta mínima €{cls.MIN_TOTAL_COST}, calculada €{total_cost:.2f}")
        
        # Validar Elige 8
        if elige_8 and elige_8.enabled:
            elige_8_errors = cls._validate_elige_8(elige_8, predictions)
            errors.extend(elige_8_errors)
        
        # Generar advertencias
        if total_combinations > 1000:
            warnings.append(f"Apuesta de alto riesgo: {total_combinations} combinaciones (€{base_cost:.2f})")
        
        if bet_type == 'multiple' and total_combinations > 100:
            warnings.append("Considerar usar reducciones oficiales para optimizar cobertura/costo")
        
        return QuinielaValidationResult(
            valid=len(errors) == 0,
            total_combinations=total_combinations,
            base_cost=base_cost,
            elige_8_cost=elige_8_cost,
            total_cost=total_cost,
            bet_type=bet_type,
            errors=errors,
            warnings=warnings
        )
    
    @classmethod
    def _determine_bet_type(cls, multiplicities: List[int]) -> str:
        """Determinar tipo de apuesta basado en multiplicidades"""
        unique_multiplicities = set(multiplicities)
        
        if unique_multiplicities == {1}:
            return 'simple'
        elif len(unique_multiplicities) == 1:
            if 2 in unique_multiplicities:
                return 'reduced_doubles'
            elif 3 in unique_multiplicities:
                return 'reduced_triples'
        
        # Verificar si coincide con alguna reducción oficial
        dobles = multiplicities.count(2)
        triples = multiplicities.count(3)
        
        for name, config in cls.OFFICIAL_REDUCTIONS.items():
            if config['dobles'] == dobles and config['triples'] == triples:
                return f'reduced_{name}'
        
        return 'multiple'
    
    @classmethod
    def _validate_elige_8(cls, elige_8: QuinielaElige8, predictions: List[QuinielaPrediction]) -> List[str]:
        """Validar configuración de Elige 8"""
        errors = []
        
        if len(elige_8.selected_matches) != 8:
            errors.append(f"Elige 8 requiere exactamente 8 partidos, seleccionados {len(elige_8.selected_matches)}")
        
        # Verificar que los partidos seleccionados existen en la quiniela
        prediction_numbers = {p.match_number for p in predictions}
        for match_num in elige_8.selected_matches:
            if match_num not in prediction_numbers:
                errors.append(f"Elige 8: partido {match_num} no existe en la quiniela")
        
        # Verificar que las predicciones de Elige 8 son válidas
        if len(elige_8.predictions) != 8:
            errors.append(f"Elige 8 requiere 8 predicciones, proporcionadas {len(elige_8.predictions)}")
        
        for i, pred in enumerate(elige_8.predictions):
            if pred not in ["1", "X", "2"]:
                errors.append(f"Elige 8 predicción {i+1}: '{pred}' no válida (usar 1, X, 2)")
        
        return errors
    
    @classmethod
    def calculate_combinations(cls, multiplicities: List[int]) -> int:
        """Calcular número total de combinaciones"""
        total = 1
        for mult in multiplicities:
            total *= mult
        return total
    
    @classmethod
    def get_official_reduction_info(cls, reduction_name: str) -> Optional[Dict[str, Any]]:
        """Obtener información de una reducción oficial"""
        return cls.OFFICIAL_REDUCTIONS.get(reduction_name.lower())
    
    @classmethod
    def suggest_optimal_reductions(cls, budget: float) -> List[Dict[str, Any]]:
        """Sugerir reducciones óptimas según presupuesto"""
        suggestions = []
        
        for name, config in cls.OFFICIAL_REDUCTIONS.items():
            if config['cost'] <= budget:
                suggestions.append({
                    'name': name,
                    'cost': config['cost'],
                    'combinations': config['combinations'],
                    'coverage': f"{config['dobles']} dobles + {config['triples']} triples",
                    'efficiency': config['combinations'] / config['cost']
                })
        
        # Ordenar por eficiencia (combinaciones por euro)
        return sorted(suggestions, key=lambda x: x['efficiency'], reverse=True)


def create_simple_quiniela(predictions: List[str]) -> List[QuinielaPrediction]:
    """
    Crear quiniela simple a partir de lista de predicciones
    
    Args:
        predictions: Lista de 15 strings ["1", "X", "2", etc.]
    
    Returns:
        Lista de QuinielaPrediction configuradas como simples
    """
    if len(predictions) != 15:
        raise ValueError("Se requieren exactamente 15 predicciones")
    
    quiniela_predictions = []
    for i, pred in enumerate(predictions):
        quiniela_predictions.append(QuinielaPrediction(
            match_number=i + 1,
            home_team=f"Equipo Local {i+1}",
            away_team=f"Equipo Visitante {i+1}",
            prediction_options=[pred]
        ))
    
    return quiniela_predictions


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo 1: Quiniela simple
    simple_predictions = ["1"] * 13 + ["X", "2"]  # 13 unos, 1 empate, 1 dos
    quiniela_simple = create_simple_quiniela(simple_predictions)
    
    result = QuinielaValidator.validate_quiniela(quiniela_simple)
    print(f"Quiniela simple: {result.total_combinations} combinaciones, €{result.total_cost}")
    
    # Ejemplo 2: Quiniela con dobles
    quiniela_dobles = create_simple_quiniela(["1"] * 15)
    # Convertir algunos a dobles
    quiniela_dobles[0].prediction_options = ["1", "X"]
    quiniela_dobles[1].prediction_options = ["1", "2"]
    
    result = QuinielaValidator.validate_quiniela(quiniela_dobles)
    print(f"Quiniela con dobles: {result.total_combinations} combinaciones, €{result.total_cost}")
    
    # Ejemplo 3: Con Elige 8
    elige_8 = QuinielaElige8(
        enabled=True,
        selected_matches=[1, 2, 3, 4, 5, 6, 7, 8],
        predictions=["1", "X", "2", "1", "X", "2", "1", "X"]
    )
    
    result = QuinielaValidator.validate_quiniela(quiniela_simple, elige_8)
    print(f"Quiniela con Elige 8: {result.total_combinations} combinaciones, €{result.total_cost}")