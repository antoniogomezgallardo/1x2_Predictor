# 🚀 Guía de Inicio Rápido - Quiniela Predictor

## ⚡ Inicio Ultra-Rápido (5 minutos)

**¿Primera vez? ¡Usa nuestro script automático!**

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd 1x2_Predictor

# 2. Configurar API key (¡IMPORTANTE!)
cp .env.example .env
# Editar .env y agregar tu API_FOOTBALL_KEY y SECRET_KEY

# 3. ¡Ejecutar script automático!
python scripts/quick_start.py
```

**¡Eso es todo!** El script automático:
- ✅ Verifica que tengas Docker instalado
- ✅ Configura todos los servicios
- ✅ Crea la base de datos
- ✅ Te pregunta si quieres cargar datos de ejemplo
- ✅ Verifica que todo funcione

**Al final tendrás acceso a:**
- 🎯 Dashboard: http://localhost:8501
- 🔧 API: http://localhost:8000/docs
- ⚽ Sistema completo funcionando

---

## 📋 Prerrequisitos Mínimos

**Solo necesitas:**
1. **Docker Desktop** - [Descargar aquí](https://docs.docker.com/get-docker/)
2. **API-Football Key** - [Obtener aquí](https://dashboard.api-football.com/) (Premium)
3. **5 minutos de tu tiempo** ⏱️

**No necesitas:**
- ❌ Instalar Python
- ❌ Instalar PostgreSQL 
- ❌ Instalar Redis
- ❌ Configurar dependencias
- ❌ Crear bases de datos manualmente

---

## 🔧 Configuración Manual (Si prefieres control total)

### Paso 1: Preparar el Entorno

```bash
# Clonar repositorio
git clone <repository-url>
cd 1x2_Predictor

# Copiar configuración
cp .env.example .env
```

### Paso 2: Configurar Variables Críticas

Edita el archivo `.env` con tu editor favorito:

```bash
# 🔑 REQUERIDO: Tu API key de API-Football
API_FOOTBALL_KEY=tu_api_key_premium_aqui

# 🔐 REQUERIDO: Clave secreta (genera una segura)
SECRET_KEY=tu_clave_secreta_muy_segura_de_32_caracteres_minimo

# 💰 Configuración de apuestas (opcional, valores por defecto)
INITIAL_BANKROLL=1000.0           # Tu bankroll inicial en euros
MAX_BET_PERCENTAGE=0.05           # Máximo 5% por jornada
MIN_CONFIDENCE_THRESHOLD=0.6      # Solo apostar con 60%+ confianza
```

**💡 Tip:** Para generar una clave secreta segura:
```bash
# En Linux/Mac:
openssl rand -hex 32

# En Windows PowerShell:
[System.Web.Security.Membership]::GeneratePassword(32, 0)
```

### Paso 3: Iniciar Servicios

```bash
# Con Docker (Recomendado)
docker-compose up -d

# Esperar 30 segundos para que todo arranque
```

### Paso 4: Configurar Base de Datos

```bash
# Configurar automáticamente
python scripts/setup_database.py

# O manualmente con Docker
docker-compose exec api python scripts/setup_database.py
```

### Paso 5: Verificar Instalación

```bash
# Script de validación completo
python scripts/validate_environment.py

# Verificaciones rápidas
curl http://localhost:8000/health    # API ✅
curl http://localhost:8501           # Dashboard ✅
```

---

## 📊 Primer Uso del Sistema

### 1. Acceder al Dashboard

Abre tu navegador en: **http://localhost:8501**

Verás 6 secciones principales:
- 🎯 **Mi Quiniela Personal** - Crear y gestionar tus quinielas con selector de configuraciones
- ⚙️ **Configuración Avanzada** - Selecciona manualmente los 15 partidos de tu Quiniela
- 📊 **Predicciones del Sistema** - Ver predicciones automáticas
- 📈 **Análisis de Rendimiento** - Gráficos de precisión
- 💰 **Análisis Financiero** - ROI y beneficios
- 🔧 **Gestión de Datos** - Actualizar equipos y partidos
- 🤖 **Modelo ML** - Entrenar y configurar el modelo

### 2. Cargar Datos Iniciales (Primera vez)

**Opción A: Desde el Dashboard**
1. Ve a "🔧 Gestión de Datos"
2. Haz clic en "Actualizar Equipos 2024"
3. Espera 2 minutos, luego "Actualizar Partidos 2024" 
4. Espera 5 minutos, luego "Actualizar Estadísticas 2024"

**Opción B: Desde terminal**
```bash
# Paso a paso con verificación
echo "🏈 Actualizando equipos..."
curl -X POST "http://localhost:8000/data/update-teams/2024"
sleep 60

echo "⚽ Actualizando partidos..."
curl -X POST "http://localhost:8000/data/update-matches/2024"
sleep 180

echo "📊 Actualizando estadísticas..."
curl -X POST "http://localhost:8000/data/update-statistics/2024"
sleep 300

echo "✅ ¡Datos cargados!"
```

### 3. Entrenar tu Primer Modelo

**Desde el Dashboard:**
1. Ve a "🤖 Modelo ML"
2. Haz clic en "Entrenar Modelo"
3. Espera 10-15 minutos
4. Verifica métricas de rendimiento

**Desde terminal:**
```bash
curl -X POST "http://localhost:8000/model/train" \
     -H "Content-Type: application/json" \
     -d '{"season": 2024}'
```

### 4. Crear tu Primera Quiniela

**Opción A: Configuración Personalizada (Recomendado)**
1. Ve a "⚙️ Configuración Avanzada"
2. Selecciona exactamente 15 partidos de la próxima jornada
3. Designa cuál será el "Pleno al 15"
4. Guarda la configuración con un nombre descriptivo
5. Ve a "🎯 Mi Quiniela Personal"
6. Selecciona tu configuración en el dropdown
7. Haz clic en "🎯 Obtener Predicciones"
8. Revisa y ajusta predicciones
9. Guarda tu quiniela

**Opción B: Sistema Automático**
1. Ve a "🎯 Mi Quiniela Personal"
2. Selecciona "Sistema automático" en el dropdown
3. Haz clic en "🎯 Obtener Predicciones"
4. Revisa predicciones automáticas
5. Guarda tu quiniela

---

## 🎯 Casos de Uso Principales

### Caso 1: Análisis de Partidos
```
1. Dashboard → "Predicciones del Sistema"
2. Ver partidos de la jornada actual
3. Revisar explicaciones detalladas
4. Analizar probabilidades y confianza
5. Decidir estrategia de apuestas
```

### Caso 2: Gestión Personal de Quinielas
```
1. Dashboard → "Configuración Avanzada" 
2. Seleccionar 15 partidos manualmente
3. Guardar configuración personalizada
4. Dashboard → "Mi Quiniela Personal"
5. Elegir configuración en selector
6. "Obtener Predicciones"
7. Guardar quiniela
8. Cuando termine la jornada: "Actualizar Resultados"
9. Ver ROI y estadísticas en "Mi Historial"
```

### Caso 3: Análisis de Rendimiento
```
1. Dashboard → "Análisis de Rendimiento"
2. Ver gráficos de precisión histórica
3. Analizar tendencias por mes/jornada
4. Identificar fortalezas del modelo
```

### Caso 4: Configuración Personalizada
```
1. Dashboard → "Configuración Avanzada"
2. Ver partidos de próxima jornada
3. Seleccionar exactamente 15 partidos
4. Designar partido para Pleno al 15
5. Guardar configuración con nombre
6. Activar/desactivar configuraciones
7. Usar en "Mi Quiniela Personal"
```

### Caso 5: Gestión Financiera
```
1. Dashboard → "Análisis Financiero"
2. Configurar bankroll inicial
3. Revisar ROI acumulado
4. Analizar beneficios por jornada
5. Ajustar estrategia de apuestas
```

---

## 🛠️ Comandos Útiles

### Gestión de Servicios
```bash
# Iniciar todo
docker-compose up -d

# Ver estado
docker-compose ps

# Ver logs
docker-compose logs api
docker-compose logs dashboard

# Parar todo
docker-compose down

# Reiniciar un servicio
docker-compose restart api
```

### Gestión de Datos
```bash
# Actualizar datos (API endpoints)
curl -X POST "http://localhost:8000/data/update-teams/2025"
curl -X POST "http://localhost:8000/data/update-matches/2025" 
curl -X POST "http://localhost:8000/data/update-statistics/2025"

# Entrenar modelo
curl -X POST "http://localhost:8000/model/train" -d '{"season": 2025}'

# Ver estado del modelo
curl "http://localhost:8000/analytics/model-performance"
```

### Configuraciones Personalizadas (v1.6.0)
```bash
# Obtener partidos de próxima jornada
curl "http://localhost:8000/matches/upcoming-by-round/2025"

# Listar configuraciones guardadas
curl "http://localhost:8000/quiniela/custom-config/list?season=2025"

# Generar predicciones desde configuración
curl "http://localhost:8000/quiniela/from-config/1"

# Guardar nueva configuración (POST con JSON)
curl -X POST "http://localhost:8000/quiniela/custom-config/save" -d '{...}'
```

### Base de Datos
```bash
# Conectar a PostgreSQL
docker-compose exec postgres psql -U quiniela_user quiniela_predictor

# Backup
docker-compose exec -T postgres pg_dump -U quiniela_user quiniela_predictor > backup.sql

# Restaurar
cat backup.sql | docker-compose exec -T postgres psql -U quiniela_user quiniela_predictor
```

---

## 🔍 Verificación y Troubleshooting

### Verificar que Todo Funciona

```bash
# Script completo de validación
python scripts/validate_environment.py

# Verificaciones individuales
curl http://localhost:8000/health        # API OK
curl http://localhost:8501               # Dashboard OK
docker-compose ps                        # Servicios corriendo
```

### Problemas Comunes

#### ❌ "API key invalid"
```bash
# Verificar API key
curl -H "X-RapidAPI-Key: TU_API_KEY" \
     -H "X-RapidAPI-Host: v3.football.api-sports.io" \
     "https://v3.football.api-sports.io/status"

# Solución: Verifica que tu API key sea Premium y esté correcta en .env
```

#### ❌ "Database connection failed"
```bash
# Verificar PostgreSQL
docker-compose ps postgres

# Reiniciar si es necesario
docker-compose restart postgres
docker-compose exec postgres psql -U quiniela_user -d quiniela_predictor -c "SELECT 1;"
```

#### ❌ "Dashboard no carga"
```bash
# Verificar logs
docker-compose logs dashboard

# Reiniciar dashboard
docker-compose restart dashboard
```

#### ❌ "Model not trained"
```bash
# Verificar datos suficientes (mínimo 100 partidos)
curl "http://localhost:8000/matches/?season=2025" | grep -o '"id"' | wc -l

# Entrenar si hay suficientes datos
curl -X POST "http://localhost:8000/model/train" -d '{"season": 2025}'
```

---

## 📚 Próximos Pasos

### Nivel Básico ⭐
- [x] ✅ Sistema funcionando
- [ ] 📊 Explorar dashboard completo
- [ ] 🎯 Crear primera quiniela personal
- [ ] 📈 Ver análisis de rendimiento

### Nivel Intermedio ⭐⭐
- [ ] 🤖 Entrenar modelo con más datos históricos
- [ ] 💰 Configurar estrategia de apuestas personalizada
- [ ] 📊 Analizar importancia de características
- [ ] 🔄 Automatizar actualizaciones semanales

### Nivel Avanzado ⭐⭐⭐
- [ ] 🔧 Personalizar parámetros del modelo
- [ ] 📈 Implementar backtesting histórico
- [ ] 🎮 Integrar con casas de apuestas
- [ ] 🚀 Escalar a múltiples ligas

---

## 🆘 Obtener Ayuda

### Documentación
- **README.md** - Información general del proyecto
- **CONTEXT.md** - Documentación técnica detallada
- **DATABASE.md** - Esquema y gestión de base de datos

### Validación Automática
```bash
# Ejecutar diagnóstico completo
python scripts/validate_environment.py

# Si algo falla, el script te dirá exactamente qué hacer
```

### Logs y Debug
```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs específicos
docker-compose logs api
docker-compose logs dashboard
docker-compose logs postgres
```

### Reset Completo (Si todo falla)
```bash
# Parar y limpiar todo
docker-compose down -v
docker system prune -f

# Empezar de cero
python scripts/quick_start.py
```

---

**🎉 ¡Listo! Ya tienes tu sistema de predicción de Quinielas completamente funcional.**

## 🗓️ Gestión de Temporadas

### Temporada Actual (2025)
El sistema está configurado para trabajar con la temporada 2025 por defecto. Sin embargo, como la temporada aún no ha comenzado:

- ✅ **Dashboard automático**: Al seleccionar temporada 2025, el sistema usará automáticamente datos de 2024
- ✅ **Notificación clara**: Se informa al usuario qué temporada se está usando
- ✅ **Fallback inteligente**: Busca datos en 2025 → 2024 → error informativo

### Temporadas Disponibles
- **2025** - Temporada actual (usa datos 2024 como fallback)
- **2024** - Temporada anterior (datos completos)
- **2023** - Temporada histórica (datos completos)

### ⚙️ Cómo Funciona el Fallback

```bash
# Para temporada 2025 (sin datos)
1. Sistema busca partidos en 2025 ❌
2. Sistema busca partidos en 2024 ✅
3. Dashboard muestra: "ℹ️ Predicciones basadas en datos de temporada 2024"
```

---

## 🎯 Flujo Recomendado - Nueva Funcionalidad (v1.6.0)

### ⚙️ Configuración Personalizada + Mi Quiniela Personal

**👍 Flujo Optimizado:**
1. **Configuración Avanzada** → Selecciona 15 partidos de la próxima jornada
2. **Guarda configuración** con nombre descriptivo (ej: "Jornada 1 - Agosto 2025")
3. **Mi Quiniela Personal** → Elige tu configuración en el selector
4. **Obtener Predicciones** → Ver predicciones para tus partidos seleccionados
5. **Sistema coherente** → Los partidos son exactamente los que elegiste

### 🔮 Características Clave (v1.6.0)

- **🔄 Selector Inteligente**: Dropdown con todas tus configuraciones
- **📊 Vista Previa**: Muestra La Liga (X), Segunda (Y), Semana Z
- **🔵 Estados Visuales**: Activa/Inactiva para cada configuración  
- **🔄 Fallback Automático**: Si no tienes configuraciones, usa sistema automático
- **🎯 Coherencia Total**: Configuración Avanzada ↔️ Mi Quiniela Personal

### 🆕 Beneficios de la Nueva Versión

- ✅ **Control Total**: Elige exactamente qué 15 partidos usar
- ✅ **Próxima Jornada Real**: Muestra partidos de la siguiente jornada disponible
- ✅ **Pleno al 15 Designado**: Selecciona cuál será tu partido especial
- ✅ **Múltiples Configuraciones**: Guarda y reutiliza diferentes selecciones
- ✅ **Flujo Lógico**: Sin inconsistencias entre secciones
- ✅ **Experiencia Mejorada**: Interfaz clara, feedback inmediato

**💡 Tip Final:** Usa el dashboard primero para familiarizarte con el sistema. La nueva funcionalidad de configuración personalizada te da control total sobre tu Quiniela.

**⚠️ Importante:** Recuerda que este sistema es para fines educativos. Apuesta responsablemente y solo dinero que puedas permitirte perder.