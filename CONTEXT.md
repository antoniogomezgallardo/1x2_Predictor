# 📋 CONTEXT.md - Documentación Técnica del Sistema

## 🏗️ Arquitectura del Sistema

### Visión General
Sistema de predicción de resultados para la Quiniela Española que utiliza Machine Learning para analizar datos de fútbol y generar predicciones rentables.

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUINIELA PREDICTOR SYSTEM                   │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
   ┌─────────┐            ┌─────────┐            ┌─────────┐
   │ Data    │            │ ML      │            │ Web     │
   │ Layer   │            │ Engine  │            │ Layer   │
   └─────────┘            └─────────┘            └─────────┘
        │                       │                       │
   ┌─────────┐            ┌─────────┐            ┌─────────┐
   │API-Foot │            │Features │            │FastAPI  │
   │PostgreSQL│           │Predictor│            │Streamlit│
   │Redis    │            │Models   │            │Dashboard│
   └─────────┘            └─────────┘            └─────────┘
```

## 📂 Estructura de Directorios

```
1x2_Predictor/
├── backend/                    # Backend Python (FastAPI)
│   └── app/
│       ├── api/               # Esquemas Pydantic
│       │   ├── __init__.py
│       │   └── schemas.py     # Response/Request models
│       ├── config/            # Configuración de la app
│       │   ├── __init__.py
│       │   └── settings.py    # Variables de entorno
│       ├── database/          # Modelos y conexión DB
│       │   ├── __init__.py
│       │   ├── database.py    # SQLAlchemy setup
│       │   └── models.py      # Tablas de la BD
│       ├── ml/                # Machine Learning
│       │   ├── __init__.py
│       │   ├── feature_engineering.py # Extracción features
│       │   └── predictor.py   # Modelos ML
│       ├── services/          # Servicios externos
│       │   ├── __init__.py
│       │   ├── api_football_client.py # Cliente API
│       │   └── data_extractor.py      # ETL datos
│       ├── __init__.py
│       └── main.py           # FastAPI application
├── data/                     # Almacenamiento de datos
│   ├── raw/                 # Datos sin procesar
│   ├── processed/           # Datos procesados
│   └── models/              # Modelos ML entrenados
├── scripts/                 # Scripts de automatización
│   ├── setup_database.py   # Configuración inicial BD
│   └── run_predictions.py  # Generación predicciones
├── frontend/               # (Futuro) Frontend React/Vue
├── tests/                  # Tests unitarios
├── docs/                   # Documentación adicional
├── dashboard.py           # Dashboard Streamlit
├── docker-compose.yml     # Orquestación Docker
├── Dockerfile.api         # Container backend
├── Dockerfile.dashboard   # Container dashboard
├── requirements.txt       # Dependencias Python
├── .env.example          # Plantilla variables entorno
└── README.md             # Documentación principal
```

## 🗄️ Modelo de Base de Datos

### Tablas Principales

#### `teams` - Equipos de Fútbol
```sql
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    api_id INTEGER UNIQUE NOT NULL,           -- ID en API-Football
    name VARCHAR(100) NOT NULL,               -- Nombre completo
    short_name VARCHAR(10),                   -- Nombre corto
    logo VARCHAR(255),                        -- URL del logo
    league_id INTEGER NOT NULL,               -- 140=LaLiga, 141=Segunda
    founded INTEGER,                          -- Año fundación
    venue_name VARCHAR(100),                  -- Estadio
    venue_capacity INTEGER,                   -- Capacidad estadio
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `matches` - Partidos
```sql
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    api_id INTEGER UNIQUE NOT NULL,           -- ID en API-Football
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    round VARCHAR(50),                        -- Jornada
    match_date TIMESTAMP NOT NULL,
    status VARCHAR(20),                       -- NS, FT, etc.
    home_goals INTEGER,                       -- Goles local
    away_goals INTEGER,                       -- Goles visitante
    result VARCHAR(1),                        -- 1, X, 2
    home_odds FLOAT,                          -- Cuota local
    draw_odds FLOAT,                          -- Cuota empate
    away_odds FLOAT,                          -- Cuota visitante
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `team_statistics` - Estadísticas de Equipos
```sql
CREATE TABLE team_statistics (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    season INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    position INTEGER,                         -- Posición en liga
    home_wins INTEGER DEFAULT 0,             -- Estadísticas casa
    home_draws INTEGER DEFAULT 0,
    home_losses INTEGER DEFAULT 0,
    away_wins INTEGER DEFAULT 0,             -- Estadísticas fuera
    away_draws INTEGER DEFAULT 0,
    away_losses INTEGER DEFAULT 0,
    form VARCHAR(5),                         -- Últimos 5 partidos
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `quiniela_predictions` - Predicciones
```sql
CREATE TABLE quiniela_predictions (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    season INTEGER NOT NULL,
    match_id INTEGER REFERENCES matches(id),
    predicted_result VARCHAR(1) NOT NULL,    -- 1, X, 2
    confidence FLOAT,                        -- 0.0 a 1.0
    home_probability FLOAT,
    draw_probability FLOAT,
    away_probability FLOAT,
    model_features JSON,                     -- Features utilizadas
    model_version VARCHAR(50),
    actual_result VARCHAR(1),                -- Resultado real
    is_correct BOOLEAN,                      -- ¿Predicción correcta?
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `quiniela_weeks` - Jornadas Completas
```sql
CREATE TABLE quiniela_weeks (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    season INTEGER NOT NULL,
    bet_amount FLOAT DEFAULT 0.0,            -- Cantidad apostada
    potential_winnings FLOAT DEFAULT 0.0,    -- Ganancia potencial
    actual_winnings FLOAT DEFAULT 0.0,       -- Ganancia real
    profit_loss FLOAT DEFAULT 0.0,           -- P&L
    correct_predictions INTEGER DEFAULT 0,    -- Aciertos
    total_predictions INTEGER DEFAULT 15,     -- Total predicciones
    accuracy_percentage FLOAT DEFAULT 0.0,   -- % acierto
    is_completed BOOLEAN DEFAULT FALSE,       -- ¿Completada?
    submission_date TIMESTAMP,               -- Fecha envío
    results_date TIMESTAMP,                  -- Fecha resultados
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🤖 Sistema de Machine Learning

### Pipeline de Predicción

1. **Data Extraction** (`data_extractor.py`)
   - Obtiene datos de API-Football
   - Actualiza equipos, partidos, estadísticas
   - Calcula head-to-head y forma reciente

2. **Feature Engineering** (`feature_engineering.py`)
   - Extrae +30 características técnicas
   - Normaliza y escala datos
   - Crea variables derivadas

3. **Model Training** (`predictor.py`)
   - Ensemble: Random Forest + XGBoost
   - Validación cruzada 5-fold
   - Calibración de probabilidades

4. **Prediction Generation**
   - Genera predicciones para 15 partidos
   - Calcula confianza y probabilidades
   - Aplica estrategia de apuestas

### Features Principales (30+ variables)

#### Rendimiento de Equipos
- `home_win_pct`: % victorias local
- `away_win_pct`: % victorias visitante
- `home_ppg`: Puntos por partido local
- `away_ppg`: Puntos por partido visitante
- `ppg_difference`: Diferencia puntos por partido

#### Estadísticas de Goles
- `home_goals_per_game`: Goles por partido local
- `away_goals_per_game`: Goles por partido visitante
- `home_goals_against_per_game`: Goles recibidos local
- `away_goals_against_per_game`: Goles recibidos visitante
- `goal_diff_difference`: Diferencia goal average

#### Ventaja Local/Visitante
- `home_team_home_win_pct`: % victorias en casa del local
- `away_team_away_win_pct`: % victorias fuera del visitante
- `home_advantage`: Ventaja calculada de jugar en casa

#### Head-to-Head
- `h2h_home_wins`: % victorias históricas del local
- `h2h_draws`: % empates históricos
- `h2h_away_wins`: % victorias históricas del visitante
- `h2h_home_goals_avg`: Media goles local H2H
- `h2h_away_goals_avg`: Media goles visitante H2H

#### Forma Reciente (últimos 5 partidos)
- `home_form_points`: Puntos últimos 5 partidos local
- `away_form_points`: Puntos últimos 5 partidos visitante
- `form_difference`: Diferencia forma reciente

#### Posición en Liga
- `home_position`: Posición actual local
- `away_position`: Posición actual visitante
- `position_difference`: Diferencia posiciones
- `home_top_half`: ¿Local en top 10?
- `away_top_half`: ¿Visitante en top 10?

### Algoritmos de ML

#### Random Forest
```python
RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight='balanced'
)
```

#### XGBoost
```python
XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8
)
```

#### Ensemble
```python
VotingClassifier(
    estimators=[('rf', rf_model), ('xgb', xgb_model)],
    voting='soft'  # Promedio de probabilidades
)
```

## 🔧 API Endpoints

### Gestión de Datos
- `POST /data/update-teams/{season}` - Actualizar equipos
- `POST /data/update-matches/{season}` - Actualizar partidos  
- `POST /data/update-statistics/{season}` - Actualizar estadísticas

### Consultas
- `GET /teams/` - Listar equipos
- `GET /teams/{team_id}/statistics` - Estadísticas equipo
- `GET /matches/` - Listar partidos

### Machine Learning
- `POST /model/train` - Entrenar modelo
- `GET /analytics/model-performance` - Rendimiento modelo

### Predicciones
- `GET /predictions/current-week` - Predicciones actuales
- `GET /predictions/history` - Histórico predicciones

### Analytics
- `GET /analytics/financial-summary` - Resumen financiero

## 💰 Sistema de Gestión Financiera

### Estrategia de Apuestas

#### Criterio Kelly Simplificado
```python
def calculate_bet_size(confidence, bankroll, max_pct=0.05):
    if confidence > 0.6:  # Umbral mínimo confianza
        bet_size = (confidence - 0.5) * max_pct * bankroll
        return min(bet_size, max_pct * bankroll)
    return 0
```

#### Límites de Riesgo
- **Máximo por jornada**: 5% del bankroll
- **Mínimo confianza**: 60%
- **Stop-loss**: -20% bankroll inicial
- **Diversificación**: Máximo 3-5 apuestas por jornada

### Métricas de Rendimiento

#### KPIs Principales
- **Accuracy**: % aciertos por jornada
- **ROI**: Retorno sobre inversión
- **Sharpe Ratio**: Rendimiento ajustado por riesgo
- **Max Drawdown**: Máxima pérdida consecutiva

#### Objetivos
- **Accuracy mínima**: 40% (6/15 aciertos)
- **ROI objetivo**: 20-30% anual
- **Drawdown máximo**: -20%

## 🚀 Flujo de Operación

### Ciclo Semanal

1. **Lunes**: Actualización resultados jornada anterior
2. **Martes**: Re-entrenamiento modelo (si necesario)
3. **Miércoles**: Actualización datos equipos/estadísticas
4. **Jueves**: Generación predicciones nueva jornada
5. **Viernes**: Revisión estrategia apuestas
6. **Sábado-Domingo**: Ejecución apuestas

### Comandos Principales

```bash
# Actualizar datos
python scripts/setup_database.py
curl -X POST "localhost:8000/data/update-teams/2024"
curl -X POST "localhost:8000/data/update-matches/2024"
curl -X POST "localhost:8000/data/update-statistics/2024"

# Entrenar modelo
curl -X POST "localhost:8000/model/train" -d '{"season": 2024}'

# Generar predicciones
python scripts/run_predictions.py --season 2024

# Actualizar resultados
python scripts/run_predictions.py --season 2024 --week 15 --update-results
```

## 🔧 Configuración Técnica

### Variables de Entorno (.env)
```bash
# API Configuration
API_FOOTBALL_KEY=tu_api_key_aqui
API_FOOTBALL_HOST=v3.football.api-sports.io

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/quiniela_predictor

# Redis
REDIS_URL=redis://localhost:6379

# App
DEBUG=True
SECRET_KEY=tu_secret_key_seguro

# Betting
INITIAL_BANKROLL=1000.0
MAX_BET_PERCENTAGE=0.05
MIN_ODDS_THRESHOLD=1.5
```

### Dependencias Principales
```txt
fastapi==0.104.1              # Web framework
uvicorn==0.24.0               # ASGI server
sqlalchemy==2.0.23            # ORM
psycopg2-binary==2.9.9        # PostgreSQL driver
scikit-learn==1.3.2           # ML library
xgboost==2.0.2               # Gradient boosting
pandas==2.1.4                # Data manipulation
streamlit==1.28.2             # Dashboard
plotly==5.17.0               # Visualizations
httpx==0.25.2                # HTTP client
celery==5.3.4                # Task queue
redis==5.0.1                 # Cache/broker
```

## 🏥 Monitoreo y Salud

### Health Checks
- `GET /health` - Estado API
- `GET /analytics/model-performance` - Estado modelo
- Métricas de accuracy en tiempo real
- Alertas por baja performance

### Logs Importantes
- Accuracy por jornada
- Errores de predicción
- Límites API alcanzados
- Performance modelo drift

### Backup y Recuperación
- Backup diario base datos
- Versionado modelos ML
- Histórico predicciones
- Configuración en VCS

## 🛡️ Seguridad

### Consideraciones
- API keys en variables entorno
- Validación entrada datos
- Rate limiting API calls
- Logs seguros (sin credentials)

### Aspectos Legales
- Verificar legalidad apuestas deportivas
- Cumplir regulaciones locales
- Juego responsable
- Disclaimer riesgos financieros

---

**Última actualización**: 2024-08-12
**Versión**: 1.0.0
**Maintainer**: Sistema Quiniela Predictor