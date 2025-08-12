# 🗄️ Configuración y Gestión de Base de Datos

## 📋 Resumen de la Base de Datos

**Motor**: PostgreSQL 15  
**Nombre**: `quiniela_predictor`  
**Usuario**: `quiniela_user` (Docker) / configurado manualmente  
**Puerto**: 5432  

## 🏗️ Esquema de Base de Datos

### Diagrama de Relaciones

```
teams (equipos)
├── id (PK)
├── api_id (unique)
├── name, short_name, logo
├── league_id (140=LaLiga, 141=Segunda)
└── venue_name, venue_capacity

team_statistics (estadísticas por temporada)
├── id (PK)
├── team_id (FK → teams.id)
├── season, league_id
├── matches_played, wins, draws, losses
├── goals_for, goals_against, points
├── position (en la liga)
├── home_*, away_* (estadísticas locales/visitante)
└── form (últimos 5 partidos)

matches (partidos)
├── id (PK)
├── api_id (unique)
├── home_team_id (FK → teams.id)
├── away_team_id (FK → teams.id)
├── league_id, season, round
├── match_date, status
├── home_goals, away_goals, result
└── *_odds (cuotas de apuestas)

quiniela_predictions (predicciones por partido)
├── id (PK)
├── week_number, season
├── match_id (FK → matches.id)
├── predicted_result, confidence
├── *_probability (probabilidades por resultado)
├── model_features (JSON), model_version
├── actual_result, is_correct
└── created_at

quiniela_weeks (jornadas completas)
├── id (PK)
├── week_number, season
├── bet_amount, *_winnings, profit_loss
├── correct_predictions, total_predictions
├── accuracy_percentage
├── is_completed, *_date
└── created_at

model_performance (rendimiento de modelos ML)
├── id (PK)
├── model_name, model_version
├── accuracy, precision, recall, f1_score
├── training_samples, training_date
├── feature_importance (JSON)
└── is_active
```

## 🛠️ Configuración Inicial

### Con Docker (Recomendado)

La configuración de PostgreSQL se maneja automáticamente:

```yaml
# docker-compose.yml
postgres:
  image: postgres:15
  environment:
    POSTGRES_DB: quiniela_predictor
    POSTGRES_USER: quiniela_user
    POSTGRES_PASSWORD: quiniela_password
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

### Configuración Manual

```bash
# 1. Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib  # Ubuntu/Debian
brew install postgresql                         # macOS

# 2. Crear usuario y base de datos
sudo -u postgres psql
CREATE USER quiniela_user WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE quiniela_predictor OWNER quiniela_user;
GRANT ALL PRIVILEGES ON DATABASE quiniela_predictor TO quiniela_user;
\q

# 3. Configurar .env
DATABASE_URL=postgresql://quiniela_user:tu_password_seguro@localhost:5432/quiniela_predictor
```

## 🚀 Creación de Tablas

### Método Automático

```bash
# Crear todas las tablas automáticamente
python scripts/setup_database.py
```

### Método Manual (SQL)

```sql
-- Conectar a la base de datos
psql postgresql://quiniela_user:password@localhost:5432/quiniela_predictor

-- Crear tabla teams
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    api_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10),
    logo VARCHAR(255),
    league_id INTEGER NOT NULL,
    founded INTEGER,
    venue_name VARCHAR(100),
    venue_capacity INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Crear tabla team_statistics
CREATE TABLE team_statistics (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    season INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    position INTEGER,
    home_wins INTEGER DEFAULT 0,
    home_draws INTEGER DEFAULT 0,
    home_losses INTEGER DEFAULT 0,
    away_wins INTEGER DEFAULT 0,
    away_draws INTEGER DEFAULT 0,
    away_losses INTEGER DEFAULT 0,
    form VARCHAR(5),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, season, league_id)
);

-- Crear tabla matches
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    api_id INTEGER UNIQUE NOT NULL,
    home_team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    round VARCHAR(50),
    match_date TIMESTAMP NOT NULL,
    status VARCHAR(20),
    home_goals INTEGER,
    away_goals INTEGER,
    result VARCHAR(1) CHECK (result IN ('1', 'X', '2')),
    home_odds FLOAT,
    draw_odds FLOAT,
    away_odds FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Crear tabla quiniela_predictions
CREATE TABLE quiniela_predictions (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    season INTEGER NOT NULL,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    predicted_result VARCHAR(1) NOT NULL CHECK (predicted_result IN ('1', 'X', '2')),
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    home_probability FLOAT CHECK (home_probability >= 0 AND home_probability <= 1),
    draw_probability FLOAT CHECK (draw_probability >= 0 AND draw_probability <= 1),
    away_probability FLOAT CHECK (away_probability >= 0 AND away_probability <= 1),
    model_features JSON,
    model_version VARCHAR(50),
    actual_result VARCHAR(1) CHECK (actual_result IN ('1', 'X', '2')),
    is_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(week_number, season, match_id)
);

-- Crear tabla quiniela_weeks
CREATE TABLE quiniela_weeks (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    season INTEGER NOT NULL,
    bet_amount FLOAT DEFAULT 0.0 CHECK (bet_amount >= 0),
    potential_winnings FLOAT DEFAULT 0.0 CHECK (potential_winnings >= 0),
    actual_winnings FLOAT DEFAULT 0.0 CHECK (actual_winnings >= 0),
    profit_loss FLOAT DEFAULT 0.0,
    correct_predictions INTEGER DEFAULT 0 CHECK (correct_predictions >= 0),
    total_predictions INTEGER DEFAULT 15 CHECK (total_predictions > 0),
    accuracy_percentage FLOAT DEFAULT 0.0 CHECK (accuracy_percentage >= 0 AND accuracy_percentage <= 100),
    is_completed BOOLEAN DEFAULT FALSE,
    submission_date TIMESTAMP,
    results_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(week_number, season)
);

-- Crear tabla model_performance
CREATE TABLE model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    accuracy FLOAT CHECK (accuracy >= 0 AND accuracy <= 1),
    precision FLOAT CHECK (precision >= 0 AND precision <= 1),
    recall FLOAT CHECK (recall >= 0 AND recall <= 1),
    f1_score FLOAT CHECK (f1_score >= 0 AND f1_score <= 1),
    training_samples INTEGER,
    training_date TIMESTAMP,
    feature_importance JSON,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Crear índices para optimizar consultas
CREATE INDEX idx_teams_api_id ON teams(api_id);
CREATE INDEX idx_teams_league_id ON teams(league_id);

CREATE INDEX idx_matches_api_id ON matches(api_id);
CREATE INDEX idx_matches_season ON matches(season);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_teams ON matches(home_team_id, away_team_id);

CREATE INDEX idx_team_statistics_team_season ON team_statistics(team_id, season);
CREATE INDEX idx_team_statistics_league ON team_statistics(league_id, season);

CREATE INDEX idx_predictions_week_season ON quiniela_predictions(week_number, season);
CREATE INDEX idx_predictions_match ON quiniela_predictions(match_id);

CREATE INDEX idx_weeks_season ON quiniela_weeks(season, week_number);

-- Comentarios en tablas
COMMENT ON TABLE teams IS 'Equipos de fútbol de La Liga y Segunda División';
COMMENT ON TABLE team_statistics IS 'Estadísticas por temporada de cada equipo';
COMMENT ON TABLE matches IS 'Partidos de fútbol con resultados y cuotas';
COMMENT ON TABLE quiniela_predictions IS 'Predicciones ML para cada partido';
COMMENT ON TABLE quiniela_weeks IS 'Resumen financiero y accuracy por jornada';
COMMENT ON TABLE model_performance IS 'Métricas de rendimiento de modelos ML';
```

## 📊 Consultas Útiles

### Verificación de Datos

```sql
-- Contar registros por tabla
SELECT 'teams' as tabla, COUNT(*) as registros FROM teams
UNION ALL
SELECT 'matches', COUNT(*) FROM matches
UNION ALL
SELECT 'team_statistics', COUNT(*) FROM team_statistics
UNION ALL
SELECT 'quiniela_predictions', COUNT(*) FROM quiniela_predictions
UNION ALL
SELECT 'quiniela_weeks', COUNT(*) FROM quiniela_weeks;

-- Equipos por liga
SELECT 
    CASE 
        WHEN league_id = 140 THEN 'La Liga'
        WHEN league_id = 141 THEN 'Segunda División'
        ELSE 'Otra liga'
    END as liga,
    COUNT(*) as equipos
FROM teams 
GROUP BY league_id;

-- Partidos por temporada y estado
SELECT 
    season,
    status,
    COUNT(*) as partidos
FROM matches 
WHERE season >= 2023
GROUP BY season, status
ORDER BY season DESC, status;
```

### Análisis de Rendimiento

```sql
-- Accuracy por jornada (últimas 10 jornadas)
SELECT 
    week_number as jornada,
    accuracy_percentage as accuracy,
    correct_predictions as aciertos,
    total_predictions as total,
    profit_loss as beneficio
FROM quiniela_weeks 
WHERE season = 2024 AND is_completed = true
ORDER BY week_number DESC
LIMIT 10;

-- Mejores predicciones por confianza
SELECT 
    qp.week_number,
    ht.name as equipo_local,
    at.name as equipo_visitante,
    qp.predicted_result as prediccion,
    qp.actual_result as resultado,
    qp.confidence as confianza,
    qp.is_correct as correcto
FROM quiniela_predictions qp
JOIN matches m ON qp.match_id = m.id
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
WHERE qp.season = 2024 
    AND qp.confidence > 0.7
    AND qp.actual_result IS NOT NULL
ORDER BY qp.confidence DESC
LIMIT 20;

-- Estadísticas generales del modelo
SELECT 
    AVG(accuracy_percentage) as accuracy_promedio,
    SUM(profit_loss) as beneficio_total,
    COUNT(*) as jornadas_completadas,
    SUM(bet_amount) as total_apostado,
    SUM(actual_winnings) as total_ganado
FROM quiniela_weeks 
WHERE season = 2024 AND is_completed = true;
```

### Análisis de Equipos

```sql
-- Top 10 equipos con mejor rendimiento en casa
SELECT 
    t.name as equipo,
    ts.home_wins as victorias_casa,
    ts.home_draws as empates_casa,
    ts.home_losses as derrotas_casa,
    ROUND(ts.home_wins::numeric / NULLIF(ts.home_wins + ts.home_draws + ts.home_losses, 0) * 100, 1) as win_rate_casa
FROM team_statistics ts
JOIN teams t ON ts.team_id = t.id
WHERE ts.season = 2024
ORDER BY win_rate_casa DESC NULLS LAST
LIMIT 10;

-- Equipos con mejor diferencia goleadora
SELECT 
    t.name as equipo,
    ts.goals_for as goles_favor,
    ts.goals_against as goles_contra,
    (ts.goals_for - ts.goals_against) as diferencia,
    ts.points as puntos,
    ts.position as posicion
FROM team_statistics ts
JOIN teams t ON ts.team_id = t.id
WHERE ts.season = 2024
ORDER BY diferencia DESC
LIMIT 10;
```

## 🔧 Mantenimiento

### Backup y Restauración

```bash
# Backup completo
pg_dump -h localhost -U quiniela_user -d quiniela_predictor > backup_$(date +%Y%m%d).sql

# Backup con Docker
docker-compose exec -T postgres pg_dump -U quiniela_user quiniela_predictor > backup_$(date +%Y%m%d).sql

# Restaurar backup
psql -h localhost -U quiniela_user -d quiniela_predictor < backup_20240812.sql

# Restaurar con Docker
cat backup_20240812.sql | docker-compose exec -T postgres psql -U quiniela_user quiniela_predictor
```

### Limpieza de Datos

```sql
-- Eliminar predicciones muy antiguas (más de 2 años)
DELETE FROM quiniela_predictions 
WHERE season < EXTRACT(YEAR FROM NOW()) - 2;

-- Eliminar estadísticas obsoletas
DELETE FROM team_statistics 
WHERE season < EXTRACT(YEAR FROM NOW()) - 3;

-- Limpiar modelos inactivos antiguos
DELETE FROM model_performance 
WHERE is_active = false 
    AND created_at < NOW() - INTERVAL '6 months';

-- Vacuum para recuperar espacio
VACUUM ANALYZE;
```

### Optimización

```sql
-- Reindexar tablas principales
REINDEX TABLE matches;
REINDEX TABLE quiniela_predictions;
REINDEX TABLE team_statistics;

-- Actualizar estadísticas de la base de datos
ANALYZE;

-- Ver tamaño de tablas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🔍 Herramientas de Administración

### Línea de Comandos

```bash
# Conectar a la base de datos
psql postgresql://quiniela_user:password@localhost:5432/quiniela_predictor

# Con Docker
docker-compose exec postgres psql -U quiniela_user quiniela_predictor

# Comandos útiles dentro de psql
\dt                    # Listar tablas
\d+ nombre_tabla       # Describir tabla
\di                    # Listar índices
\du                    # Listar usuarios
\l                     # Listar bases de datos
\q                     # Salir
```

### Herramientas Gráficas

**pgAdmin** (Recomendado)
```bash
# Instalar pgAdmin
pip install pgadmin4

# O usar versión web
docker run -p 80:80 \
    -e 'PGADMIN_DEFAULT_EMAIL=admin@admin.com' \
    -e 'PGADMIN_DEFAULT_PASSWORD=root' \
    dpage/pgadmin4
```

**DBeaver** (Multiplataforma)
- Descargar desde https://dbeaver.io/
- Configurar conexión PostgreSQL
- Host: localhost, Puerto: 5432, DB: quiniela_predictor

## 🚨 Solución de Problemas

### Error: "Connection refused"

```bash
# Verificar que PostgreSQL está corriendo
sudo systemctl status postgresql

# Con Docker
docker-compose ps postgres

# Verificar puerto
netstat -tulpn | grep 5432
```

### Error: "Authentication failed"

```bash
# Verificar credenciales en .env
cat .env | grep DATABASE_URL

# Resetear password del usuario
sudo -u postgres psql
ALTER USER quiniela_user PASSWORD 'nueva_password';
```

### Error: "Database does not exist"

```bash
# Crear base de datos
sudo -u postgres createdb quiniela_predictor

# Con Docker
docker-compose exec postgres createdb -U quiniela_user quiniela_predictor
```

### Base de datos corrupta

```bash
# Verificar integridad
sudo -u postgres pg_dump quiniela_predictor > /dev/null

# Reparar (último recurso)
sudo -u postgres reindexdb quiniela_predictor
```

## 📈 Monitoreo

### Consultas de Rendimiento

```sql
-- Consultas más lentas
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Tamaño de base de datos
SELECT pg_size_pretty(pg_database_size('quiniela_predictor'));

-- Conexiones activas
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Estadísticas de tablas
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables 
ORDER BY n_tup_ins DESC;
```

### Alertas Automatizadas

```bash
# Script de monitoreo
cat > monitor_db.sh << 'EOF'
#!/bin/bash
DB_SIZE=$(psql postgresql://quiniela_user:password@localhost:5432/quiniela_predictor -t -c "SELECT pg_database_size('quiniela_predictor');")
if [ $DB_SIZE -gt 1073741824 ]; then  # 1GB
    echo "Base de datos excede 1GB: $DB_SIZE bytes"
    # Enviar alerta
fi
EOF
```

---

**Última actualización**: 2024-08-12  
**Versión BD**: 1.0.0