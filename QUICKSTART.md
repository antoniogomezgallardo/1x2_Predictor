# 🚀 Guía de Inicio Rápido - Quiniela Predictor

## ⚡ Arranque en 5 Minutos

### Paso 1: Configuración Inicial

1. **Obtener API Key de API-Football**
   - Ir a https://dashboard.api-football.com/
   - Registrarse y obtener API Key Premium
   - Anotar la API Key

2. **Configurar Variables de Entorno**
```bash
# Copiar plantilla
cp .env.example .env

# Editar archivo .env
API_FOOTBALL_KEY=tu_api_key_aqui
SECRET_KEY=tu_secret_key_muy_seguro_de_al_menos_32_caracteres
```

### Paso 2: Arrancar con Docker (Recomendado)

```bash
# Arrancar todos los servicios
docker-compose up -d

# Verificar que están corriendo
docker-compose ps

# Ver logs si hay problemas
docker-compose logs api
docker-compose logs dashboard
```

### Paso 3: Configurar Base de Datos

```bash
# Crear tablas de la base de datos
docker-compose exec api python scripts/setup_database.py
```

### Paso 4: Cargar Datos Iniciales

```bash
# Actualizar equipos (tarda ~2 minutos)
curl -X POST "http://localhost:8000/data/update-teams/2024"

# Actualizar partidos (tarda ~5 minutos)
curl -X POST "http://localhost:8000/data/update-matches/2024"

# Actualizar estadísticas (tarda ~10 minutos)
curl -X POST "http://localhost:8000/data/update-statistics/2024"
```

### Paso 5: Entrenar Modelo

```bash
# Entrenar modelo con datos históricos (tarda ~15 minutos)
curl -X POST "http://localhost:8000/model/train" \
     -H "Content-Type: application/json" \
     -d '{"season": 2024}'
```

### Paso 6: Acceder al Dashboard

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

---

## 🐍 Instalación Manual (Sin Docker)

### Prerrequisitos

- Python 3.11+
- PostgreSQL 13+
- Redis 6+

### Paso 1: Entorno Python

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Base de Datos PostgreSQL

```bash
# Crear base de datos
createdb quiniela_predictor

# Configurar .env con la URL correcta
DATABASE_URL=postgresql://tu_usuario:tu_password@localhost:5432/quiniela_predictor
```

### Paso 3: Redis

```bash
# Iniciar Redis
redis-server

# O en Windows con WSL
sudo service redis-server start
```

### Paso 4: Configurar Base de Datos

```bash
python scripts/setup_database.py
```

### Paso 5: Arrancar Servicios

```bash
# Terminal 1: API Backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Dashboard
streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0
```

---

## 🔧 Verificación de Instalación

### 1. Comprobar API

```bash
curl http://localhost:8000/health
# Respuesta esperada: {"status":"healthy","timestamp":"..."}
```

### 2. Comprobar Base de Datos

```bash
curl http://localhost:8000/teams/
# Respuesta esperada: Lista de equipos (puede estar vacía inicialmente)
```

### 3. Comprobar Dashboard

- Ir a http://localhost:8501
- Debe mostrar el dashboard sin errores

---

## 📊 Primer Uso

### 1. Cargar Datos (Primera vez)

```bash
# Paso a paso con verificación
echo "Actualizando equipos..."
curl -X POST "http://localhost:8000/data/update-teams/2024"
sleep 60

echo "Actualizando partidos..."
curl -X POST "http://localhost:8000/data/update-matches/2024"
sleep 180

echo "Actualizando estadísticas..."
curl -X POST "http://localhost:8000/data/update-statistics/2024"
sleep 300

echo "Datos cargados!"
```

### 2. Verificar Datos

```bash
# Verificar equipos cargados
curl "http://localhost:8000/teams/" | jq length
# Debe devolver ~40 (20 de LaLiga + 20 de Segunda)

# Verificar partidos
curl "http://localhost:8000/matches/?season=2024&limit=10" | jq length
# Debe devolver partidos de la temporada
```

### 3. Entrenar Modelo

```bash
# Entrenar (solo cuando hay suficientes datos)
curl -X POST "http://localhost:8000/model/train" \
     -H "Content-Type: application/json" \
     -d '{"season": 2024}'

# Verificar entrenamiento
curl "http://localhost:8000/analytics/model-performance"
```

### 4. Generar Primera Predicción

```bash
# Generar predicciones para la jornada actual
python scripts/run_predictions.py --season 2024

# Ver predicciones en el dashboard
open http://localhost:8501
```

---

## 🔍 Acceso a Base de Datos

### Con Docker

```bash
# Conectar a PostgreSQL
docker-compose exec postgres psql -U quiniela_user -d quiniela_predictor

# Comandos SQL útiles
\dt                           # Listar tablas
SELECT COUNT(*) FROM teams;   # Contar equipos
SELECT COUNT(*) FROM matches; # Contar partidos
\q                           # Salir
```

### Manual

```bash
# Conectar a PostgreSQL
psql -U tu_usuario -d quiniela_predictor

# O con URL completa
psql postgresql://usuario:password@localhost:5432/quiniela_predictor
```

### Consultas Útiles

```sql
-- Ver equipos por liga
SELECT league_id, COUNT(*) FROM teams GROUP BY league_id;

-- Ver partidos recientes
SELECT home_team.name as home, away_team.name as away, result 
FROM matches m
JOIN teams home_team ON m.home_team_id = home_team.id
JOIN teams away_team ON m.away_team_id = away_team.id
WHERE m.season = 2024 AND m.result IS NOT NULL
ORDER BY m.match_date DESC LIMIT 10;

-- Ver predicciones
SELECT week_number, COUNT(*) as predictions, 
       AVG(confidence) as avg_confidence
FROM quiniela_predictions 
WHERE season = 2024 
GROUP BY week_number 
ORDER BY week_number DESC;

-- Rendimiento por jornada
SELECT week_number, accuracy_percentage, profit_loss
FROM quiniela_weeks 
WHERE season = 2024 AND is_completed = true
ORDER BY week_number DESC;
```

---

## 🐛 Solución de Problemas

### Error: "Database connection failed"

```bash
# Verificar PostgreSQL está corriendo
docker-compose ps postgres
# o manualmente: pg_isready

# Verificar configuración .env
cat .env | grep DATABASE_URL
```

### Error: "API key invalid"

```bash
# Verificar API key
curl -H "X-RapidAPI-Key: TU_API_KEY" \
     -H "X-RapidAPI-Host: v3.football.api-sports.io" \
     "https://v3.football.api-sports.io/status"
```

### Error: "Model not trained"

```bash
# Verificar si hay suficientes datos
curl "http://localhost:8000/matches/?season=2024" | jq length

# Si hay <100 partidos, necesitas más datos históricos
# Cargar temporadas anteriores o esperar más partidos
```

### Dashboard no carga

```bash
# Verificar que API está corriendo
curl http://localhost:8000/health

# Verificar logs del dashboard
docker-compose logs dashboard
```

### Memoria insuficiente

```bash
# Aumentar memoria Docker (8GB recomendado)
# En Docker Desktop > Settings > Resources > Memory

# O reducir tamaño modelo
# Editar backend/app/ml/predictor.py
# Reducir n_estimators de 200 a 100
```

---

## 📈 Uso Productivo

### 1. Automatización Semanal

```bash
# Crear script de actualización semanal
cat > update_weekly.sh << 'EOF'
#!/bin/bash
echo "Actualizando datos semanales..."
curl -X POST "http://localhost:8000/data/update-matches/2024"
sleep 60
curl -X POST "http://localhost:8000/data/update-statistics/2024"
sleep 120
python scripts/run_predictions.py --season 2024
echo "Actualización completada!"
EOF

chmod +x update_weekly.sh

# Ejecutar cada miércoles
crontab -e
# Añadir: 0 10 * * 3 /path/to/update_weekly.sh
```

### 2. Monitoreo

```bash
# Script de health check
cat > health_check.sh << 'EOF'
#!/bin/bash
API_STATUS=$(curl -s http://localhost:8000/health | jq -r .status)
if [ "$API_STATUS" != "healthy" ]; then
    echo "API is DOWN!"
    # Enviar alerta (email, Slack, etc.)
fi
EOF
```

### 3. Backup

```bash
# Backup automático base de datos
cat > backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U quiniela_user quiniela_predictor > backup_$DATE.sql
echo "Backup creado: backup_$DATE.sql"
EOF
```

---

## 🎯 Siguientes Pasos

1. **Configurar alertas** para predicciones de alta confianza
2. **Integrar con casa de apuestas** para automatización
3. **Optimizar modelo** con nuevos features
4. **Implementar backtesting** histórico
5. **Añadir análisis de lesiones** y suspensiones

¡Ya tienes el sistema funcionando! 🎉