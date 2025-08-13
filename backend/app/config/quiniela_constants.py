"""
Constantes oficiales de la Quiniela Española
Basado en la normativa de Loterías y Apuestas del Estado
"""

# Precios oficiales (en euros)
PRECIO_APUESTA_SIMPLE = 0.75  # €0.75 por apuesta simple
PRECIO_ELIGE_8 = 0.50  # €0.50 por modalidad Elige 8

# Reducidas oficiales autorizadas (BOE)
REDUCIDAS_OFICIALES = {
    1: {
        "nombre": "4 triples",
        "descripcion": "4 triples, 9 apuestas",
        "triples": 4,
        "dobles": 0,
        "apuestas_total": 81,  # 3^4
        "apuestas_jugadas": 9,
        "precio": 6.75,  # 9 × 0.75€
        "garantia_14_aciertos": 0.1111,  # 11.11%
        "garantia_13_aciertos": 1.0      # 100%
    },
    2: {
        "nombre": "7 dobles", 
        "descripcion": "7 dobles, 16 apuestas",
        "triples": 0,
        "dobles": 7,
        "apuestas_total": 128,  # 2^7
        "apuestas_jugadas": 16,
        "precio": 12.00  # 16 × 0.75€
    },
    3: {
        "nombre": "3 dobles + 3 triples",
        "descripcion": "3 dobles + 3 triples, 24 apuestas", 
        "triples": 3,
        "dobles": 3,
        "apuestas_total": 216,  # 2^3 × 3^3
        "apuestas_jugadas": 24,
        "precio": 18.00  # 24 × 0.75€
    },
    4: {
        "nombre": "2 triples + 6 dobles",
        "descripcion": "2 triples + 6 dobles, 64 apuestas",
        "triples": 2, 
        "dobles": 6,
        "apuestas_total": 576,  # 3^2 × 2^6
        "apuestas_jugadas": 64,
        "precio": 48.00  # 64 × 0.75€
    },
    5: {
        "nombre": "8 triples",
        "descripcion": "8 triples, 81 apuestas",
        "triples": 8,
        "dobles": 0,
        "apuestas_total": 6561,  # 3^8
        "apuestas_jugadas": 81,
        "precio": 60.75  # 81 × 0.75€
    },
    6: {
        "nombre": "11 dobles",
        "descripcion": "11 dobles, 132 apuestas",
        "triples": 0,
        "dobles": 11,
        "apuestas_total": 2048,  # 2^11
        "apuestas_jugadas": 132,
        "precio": 99.00  # 132 × 0.75€
    }
}

# Categorías de premios oficiales
CATEGORIAS_PREMIOS = {
    "especial": {
        "aciertos": 14,
        "pleno_al_15": True,
        "descripcion": "14 aciertos + Pleno al 15",
        "color": "#FFD700"  # Oro
    },
    "primera": {
        "aciertos": 14,
        "pleno_al_15": False,
        "descripcion": "14 aciertos",
        "color": "#C0C0C0"  # Plata
    },
    "segunda": {
        "aciertos": 13,
        "pleno_al_15": False,
        "descripcion": "13 aciertos",
        "color": "#CD7F32"  # Bronce
    },
    "tercera": {
        "aciertos": 12,
        "pleno_al_15": False,
        "descripcion": "12 aciertos",
        "color": "#4CAF50"  # Verde
    },
    "cuarta": {
        "aciertos": 11,
        "pleno_al_15": False,
        "descripcion": "11 aciertos",
        "color": "#2196F3"  # Azul
    },
    "quinta": {
        "aciertos": 10,
        "pleno_al_15": False,
        "descripcion": "10 aciertos",
        "color": "#FF9800"  # Naranja
    }
}

# Opciones válidas para cada tipo de predicción
OPCIONES_PARTIDOS = ["1", "X", "2"]  # Local gana, Empate, Visitante gana
OPCIONES_PLENO_AL_15 = ["0", "1", "2", "M"]  # Goles por equipo: 0, 1, 2, o M (3+ goles)

# Explicaciones detalladas del Pleno al 15
PLENO_AL_15_EXPLICACIONES = {
    "0": "El equipo no marca ningún gol",
    "1": "El equipo marca exactamente 1 gol", 
    "2": "El equipo marca exactamente 2 goles",
    "M": "El equipo marca 3 o más goles"
}

# Modalidades de juego
MODALIDADES = {
    "simple": {
        "nombre": "Simple",
        "min_apuestas": 1,
        "max_apuestas": 8,
        "descripcion": "Hasta 8 apuestas simples en un boleto"
    },
    "multiple_directo": {
        "nombre": "Múltiple Directo",
        "descripcion": "Combinaciones dobles/triples sin reducir"
    },
    "reducida": {
        "nombre": "Múltiple Reducido",
        "opciones": list(REDUCIDAS_OFICIALES.keys()),
        "descripcion": "Reducidas oficiales autorizadas"
    },
    "condicionado": {
        "nombre": "Múltiple Condicionado", 
        "descripcion": "Con condiciones (variantes, equis, doses)"
    },
    "elige_8": {
        "nombre": "Elige 8",
        "precio_adicional": PRECIO_ELIGE_8,
        "descripcion": "Modalidad adicional sobre 8 de los 14 partidos"
    }
}

def calculate_quiniela_cost(modalidad: str, configuracion: dict) -> float:
    """
    Calcula el costo de una quiniela según la modalidad y configuración
    
    Args:
        modalidad: Tipo de modalidad ('simple', 'reducida', etc.)
        configuracion: Parámetros específicos de la modalidad
    
    Returns:
        float: Costo total en euros
    """
    if modalidad == "simple":
        num_apuestas = configuracion.get("num_apuestas", 1)
        return num_apuestas * PRECIO_APUESTA_SIMPLE
    
    elif modalidad == "reducida":
        tipo_reducida = configuracion.get("tipo", 1)
        if tipo_reducida in REDUCIDAS_OFICIALES:
            return REDUCIDAS_OFICIALES[tipo_reducida]["precio"]
        else:
            raise ValueError(f"Tipo de reducida no válido: {tipo_reducida}")
    
    elif modalidad == "multiple_directo":
        num_dobles = configuracion.get("dobles", 0)
        num_triples = configuracion.get("triples", 0)
        
        # Calcular número total de apuestas
        total_apuestas = (2 ** num_dobles) * (3 ** num_triples)
        return total_apuestas * PRECIO_APUESTA_SIMPLE
    
    elif modalidad == "elige_8":
        # Requiere una apuesta simple base
        costo_base = calculate_quiniela_cost("simple", {"num_apuestas": 1})
        return costo_base + PRECIO_ELIGE_8
    
    else:
        raise ValueError(f"Modalidad no reconocida: {modalidad}")

def get_modalidad_info(modalidad: str) -> dict:
    """Obtiene información detallada de una modalidad"""
    return MODALIDADES.get(modalidad, {})

def get_reducida_info(tipo: int) -> dict:
    """Obtiene información detallada de una reducida oficial"""
    return REDUCIDAS_OFICIALES.get(tipo, {})

def validate_pleno_al_15(home_goals: str, away_goals: str) -> bool:
    """Valida que las predicciones del Pleno al 15 sean correctas (goles de cada equipo)"""
    return (home_goals in OPCIONES_PLENO_AL_15 and 
            away_goals in OPCIONES_PLENO_AL_15)

def validate_partido_prediction(prediction: str) -> bool:
    """Valida que la predicción de un partido sea correcta"""
    return prediction in OPCIONES_PARTIDOS