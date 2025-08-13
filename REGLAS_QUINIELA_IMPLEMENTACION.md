# 🎯 Implementación de Reglas de la Quiniela Española

## 📋 Análisis de Reglas Actuales vs Implementación

### Reglas Oficiales Identificadas

#### 1. **Formato de Apuesta Básico**
- ✅ **14 partidos principales** con 3 opciones: 1 (local gana), X (empate), 2 (visitante gana)
- ✅ **Pleno al 15**: Partido especial con opciones adicionales de goles
- ❌ **FALTA**: Opción "M" (3+ goles) en Pleno al 15

#### 2. **Modalidades de Juego**
- ✅ **Simple**: Una combinación por boleto (implementado en "Mi Quiniela Personal")
- ❌ **FALTA**: Múltiple Directo (hasta 8 apuestas simples en un boleto)
- ❌ **FALTA**: Múltiple Reducido (6 tipos oficiales)
- ❌ **FALTA**: Múltiple Condicionado

#### 3. **Precios Oficiales**
- ❌ **FALTA**: Precio fijo 0,75€ por apuesta simple
- ❌ **FALTA**: Cálculo automático según modalidad

#### 4. **Sistema de Premios**
- ❌ **FALTA**: Categorías oficiales (Especial, 1ª a 5ª categoría)
- ❌ **FALTA**: Distribución de fondos según aciertos

#### 5. **Modalidad "Elige 8"**
- ❌ **FALTA**: Completamente no implementada

## 🚀 Plan de Implementación

### Fase 1: Corrección del Pleno al 15 (✅ COMPLETADO)

**Problema Identificado**: El Pleno al 15 usaba predicciones 1X2 en lugar de goles por equipo
**Solución Implementada**: Sistema correcto de predicción de goles para cada equipo (0, 1, 2, M)

**Cambios Implementados:**

1. **Backend - Modelo de Datos**:
```python
# En UserQuiniela model - IMPLEMENTADO
pleno_al_15_home = Column(String(1), nullable=True)  # Goles equipo local: "0", "1", "2", "M" 
pleno_al_15_away = Column(String(1), nullable=True)  # Goles equipo visitante: "0", "1", "2", "M"
```

2. **Backend - Validación**:
```python
# En quiniela_constants.py - IMPLEMENTADO
def validate_pleno_al_15(home_goals: str, away_goals: str) -> bool:
    return (home_goals in OPCIONES_PLENO_AL_15 and away_goals in OPCIONES_PLENO_AL_15)

OPCIONES_PLENO_AL_15 = ["0", "1", "2", "M"]  # Goles por equipo
```

3. **Dashboard - UI**:
```python
# En dashboard.py - IMPLEMENTADO
# Dos selectores separados para goles de cada equipo
pleno_home = st.selectbox("🏠 Goles de {home_team_name}", options=["0", "1", "2", "M"])
pleno_away = st.selectbox("✈️ Goles de {away_team_name}", options=["0", "1", "2", "M"])
```

### Fase 2: Sistema de Precios (Prioridad Alta)

**Implementar precios oficiales:**

1. **Backend - Configuración**:
```python
# En settings.py
PRECIO_APUESTA_SIMPLE = 0.75  # €
PRECIO_ELIGE_8 = 0.50  # €

# Precios reducidas oficiales
PRECIOS_REDUCIDAS = {
    1: 6.75,   # 4 triples, 9 apuestas
    2: 12.00,  # 7 dobles, 16 apuestas
    3: 18.00,  # 3 dobles + 3 triples, 24 apuestas
    4: 48.00,  # 2 triples + 6 dobles, 64 apuestas
    5: 60.75,  # 8 triples, 81 apuestas
    6: 99.00   # 11 dobles, 132 apuestas
}
```

2. **Cálculo Automático**:
```python
def calculate_quiniela_cost(tipo: str, num_apuestas: int, reducida_tipo: int = None):
    if tipo == "simple":
        return num_apuestas * PRECIO_APUESTA_SIMPLE
    elif tipo == "reducida" and reducida_tipo:
        return PRECIOS_REDUCIDAS[reducida_tipo]
    # ... más lógica
```

### Fase 3: Modalidades Múltiples (Prioridad Media)

**3.1 Múltiple Directo (2-8 apuestas simples)**
- Permitir crear hasta 8 combinaciones diferentes en un boleto
- Cada combinación tiene 14 pronósticos + Pleno al 15
- Costo = número_apuestas × 0.75€

**3.2 Múltiple Reducido - Las 6 Reducidas Oficiales**

Implementar cada reducida según normativa BOE:

```python
REDUCIDAS_OFICIALES = {
    1: {
        "nombre": "4 triples",
        "apuestas_total": 81,
        "apuestas_jugadas": 9,
        "precio": 6.75,
        "garantia_14_aciertos": 0.1111,
        "garantia_13_aciertos": 1.0
    },
    2: {
        "nombre": "7 dobles", 
        "apuestas_total": 128,
        "apuestas_jugadas": 16,
        "precio": 12.00
    },
    # ... rest of reductions
}
```

**3.3 Múltiple Condicionado**
- Sistema de condiciones (variantes, equis, doses)
- Aplicación a partidos específicos

### Fase 4: Sistema de Premios (Prioridad Media)

**Categorías Oficiales:**
```python
CATEGORIAS_PREMIOS = {
    "especial": {"aciertos": 14, "pleno": True, "descripcion": "14 + Pleno al 15"},
    "primera": {"aciertos": 14, "pleno": False, "descripcion": "14 aciertos"},
    "segunda": {"aciertos": 13, "pleno": False, "descripcion": "13 aciertos"},
    "tercera": {"aciertos": 12, "pleno": False, "descripcion": "12 aciertos"},
    "cuarta": {"aciertos": 11, "pleno": False, "descripcion": "11 aciertos"},
    "quinta": {"aciertos": 10, "pleno": False, "descripcion": "10 aciertos"}
}
```

**Simulación de Premios:**
- Calcular premios teóricos basados en probabilidades
- Mostrar ROI esperado por categoría
- Análisis histórico de distribución de premios

### Fase 5: Modalidad "Elige 8" (Prioridad Baja)

**Nueva Modalidad Completa:**
1. Seleccionar 8 de los 14 partidos
2. Precio adicional: 0.50€
3. Premios según número de aciertos (1-8)
4. UI separada en dashboard

## 🎨 Cambios en Dashboard

### Nueva Estructura de Navegación

```python
# dashboard.py - Nueva organización
SECCIONES = {
    "🎯 Quiniela Simple": "crear_quiniela_simple",
    "🎲 Quiniela Múltiple": "crear_quiniela_multiple", 
    "🔢 Quinielas Reducidas": "crear_quiniela_reducida",
    "🎪 Elige 8": "crear_elige_8",
    "📊 Mis Quinielas": "historial_quinielas",
    "💰 Análisis de Premios": "analisis_premios",
    # ... rest of sections
}
```

### UI Mejorado para Pleno al 15

```python
def render_pleno_al_15(partido_15):
    st.subheader(f"🏆 Pleno al 15: {partido_15['home_team']} vs {partido_15['away_team']}")
    
    opciones = {
        "1": f"🏠 {partido_15['home_team']} gana",
        "X": "🤝 Empate", 
        "2": f"✈️ {partido_15['away_team']} gana",
        "M": "⚽ 3 o más goles total"
    }
    
    pleno_prediction = st.radio(
        "Selecciona tu pronóstico para el Pleno al 15:",
        options=list(opciones.keys()),
        format_func=lambda x: opciones[x]
    )
```

### Calculadora de Costos

```python
def render_cost_calculator(tipo_quiniela, configuracion):
    costo = calculate_quiniela_cost(tipo_quiniela, configuracion)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Costo Total", f"{costo:.2f}€")
    with col2:
        st.metric("🎯 Num. Apuestas", configuracion.get('num_apuestas', 1))
    with col3:
        expected_return = calculate_expected_return(configuracion)
        st.metric("📈 ROI Esperado", f"{expected_return:.1%}")
```

## 🔄 Migración de Datos

### Actualización de Base de Datos

```sql
-- Añadir soporte para opción "M" en Pleno al 15
ALTER TABLE user_quiniela_predictions 
MODIFY COLUMN user_prediction VARCHAR(2);

-- Añadir campos para nuevas modalidades
ALTER TABLE user_quiniela 
ADD COLUMN modalidad ENUM('simple', 'multiple_directo', 'reducida', 'elige8'),
ADD COLUMN reducida_tipo INT,
ADD COLUMN costo_real DECIMAL(10,2);

-- Tabla para gestionar apuestas múltiples
CREATE TABLE user_quiniela_multiple (
    id INT PRIMARY KEY AUTO_INCREMENT,
    quiniela_id INT,
    apuesta_numero INT,
    -- ... campos de predicciones
    FOREIGN KEY (quiniela_id) REFERENCES user_quiniela(id)
);
```

## 📈 Métricas y Analytics

### Nuevos KPIs a Trackear

```python
METRICAS_QUINIELA = {
    "distribucion_modalidades": "% uso de cada modalidad",
    "aciertos_por_categoria": "Distribución de aciertos 10-14",
    "roi_por_modalidad": "Rentabilidad por tipo de apuesta",
    "uso_pleno_al_15": "Análisis opción M vs 1/X/2",
    "efectividad_reducidas": "Performance de cada reducida oficial"
}
```

### Dashboard de Análisis de Rendimiento

```python
def render_performance_analysis():
    st.subheader("📊 Análisis de Rendimiento por Modalidad")
    
    # Gráfico comparativo de ROI
    modalidades_roi = get_roi_by_modalidad()
    fig = px.bar(modalidades_roi, x='modalidad', y='roi', 
                 title="ROI por Modalidad de Quiniela")
    st.plotly_chart(fig)
    
    # Tabla de estadísticas detalladas
    stats_table = get_detailed_stats()
    st.dataframe(stats_table)
```

## 🎯 Cronograma de Implementación

### Sprint 1 (Semana 1-2): Correcciones Básicas ✅ COMPLETADO
- [x] ✅ Validación de temporadas (completado)
- [x] ✅ Corrección Pleno al 15 (predicción goles por equipo)
- [x] ✅ Ordenamiento correcto de partidos (La Liga alfabético + Segunda)
- [x] ✅ Sistema de borrado selectivo de datos
- [x] ✅ UI mejorado para creación de quinielas

### Sprint 2 (Semana 3-4): Modalidades Múltiples
- [ ] 🎲 Múltiple Directo (2-8 apuestas)
- [ ] 🔢 Reducida 1 y 2 (las más simples)
- [ ] 📊 Calculadora de costos
- [ ] 📈 Métricas básicas

### Sprint 3 (Semana 5-6): Reducidas Avanzadas
- [ ] 🏆 Reducidas 3, 4, 5, 6
- [ ] 🎪 Modalidad Elige 8
- [ ] 💎 Sistema de premios completo
- [ ] 📋 Validación según normativa BOE

### Sprint 4 (Semana 7-8): Optimización y Analytics
- [ ] 📊 Dashboard analítico avanzado
- [ ] 🔍 Análisis histórico de rendimiento
- [ ] 🚀 Optimización de UI/UX
- [ ] 📝 Documentación completa

## ⚠️ Consideraciones Importantes

### Legales y Regulatorias
- Verificar cumplimiento con normativa Loterías y Apuestas del Estado
- Incluir disclaimers sobre juego responsable
- Respetar precios oficiales exactos

### Técnicas
- Validación estricta según reglas BOE
- Testing exhaustivo de todas las modalidades
- Performance optimization para múltiples complejas

### UX/UI
- Interfaz intuitiva para usuarios no técnicos
- Explicaciones claras de cada modalidad
- Calculadoras y simuladores interactivos

---

**Próximos pasos**: Comenzar con la corrección del Pleno al 15 y el sistema de precios básico.