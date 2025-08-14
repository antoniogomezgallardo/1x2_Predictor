# 🏆 Quiniela Predictor - Sistema de Predicción de Resultados

Sistema avanzado de predicción de resultados para la Quiniela Española utilizando Machine Learning e integración con API-Football.

## 🎯 Objetivo

Predecir los resultados de los 15 partidos semanales de la Quiniela Española (Primera y Segunda División) para generar beneficios consistentes mediante estrategias de apuestas inteligentes.

## ⚡ Características Principales

- **🤖 Predicciones ML**: Modelos ensemble (Random Forest + XGBoost) con +40 características
- **📊 Dashboard Interactivo**: Visualización en tiempo real de predicciones y rendimiento
- **🎯 Gestión Personal de Quinielas**: Sistema completo para crear, guardar y trackear tus quinielas
- **⚙️ Configuración Personalizada**: Selecciona manualmente los 15 partidos de tu Quiniela
- **🔄 Selector Inteligente**: Elige entre configuraciones personalizadas o sistema automático
- **💡 Explicaciones Detalladas**: Cada predicción incluye análisis razonado y factores decisivos
- **💰 Análisis Financiero**: Seguimiento de ROI, beneficios y estrategias de apuestas
- **🔄 Gestión de Datos**: Integración automática con API-Football
- **📈 Historial Completo**: Tracking de precisión y rendimiento por jornada
- **🗺️ Soporte Multi-Temporada**: Compatible con temporadas 2023-2025, fallback automático
- **🚀 Setup Ultra-Rápido**: Configuración completa en 5 minutos con scripts automatizados

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API-Football  │───▶│   FastAPI       │───▶│   Dashboard     │
│   (Datos)       │    │   (Backend)     │    │   (Streamlit)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (Base Datos)  │
                       └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   ML Models     │
                       │   (Predicción)  │
                       └─────────────────┘
```

## 📊 Características del Modelo

### Features Principales:
- **Rendimiento de Equipos**: Win rate, puntos por partido, forma reciente
- **Estadísticas de Goles**: Promedio goles a favor/contra, diferencia goleadora
- **Ventaja Local/Visitante**: Performance específica según ubicación
- **Head-to-Head**: Historial directo entre equipos
- **Posición en Liga**: Ranking actual y tendencias
- **Forma Reciente**: Últimos 5 partidos y puntos obtenidos

### Algoritmos:
- **Ensemble Model**: Combinación de Random Forest y XGBoost
- **Validación Cruzada**: 5-fold para robustez
- **Calibración de Probabilidades**: Para confianza precisa
- **Feature Engineering**: +30 variables técnicas

## 🚀 Instalación y Configuración

### ⚡ Inicio Rápido (Recomendado)

**Solo necesitas Docker y 5 minutos:**

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd 1x2_Predictor

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu API_FOOTBALL_KEY y SECRET_KEY

# 3. ¡Iniciar todo automáticamente!
python scripts/quick_start.py
```

El script automático:
- ✅ Verifica prerrequisitos
- ✅ Inicia todos los servicios con Docker
- ✅ Configura la base de datos
- ✅ Carga datos iniciales (opcional)
- ✅ Verifica que todo funcione

**Accede inmediatamente a:**
- Dashboard: http://localhost:8501
- API: http://localhost:8000/docs

### 📋 Prerrequisitos
- [Docker Desktop](https://docs.docker.com/get-docker/) (incluye Docker Compose)
- Cuenta [API-Football Premium](https://dashboard.api-football.com/) 
- Editor de texto para configurar `.env`

### 🔧 Instalación Manual (Avanzado)

<details>
<summary>Clic para expandir instrucciones manuales</summary>

#### Prerrequisitos Adicionales
- Python 3.11+
- PostgreSQL 13+
- Redis 6+

#### Instalación Local

1. **Clonar repositorio**:
```bash
git clone <repository-url>
cd 1x2_Predictor
```

2. **Configurar entorno Python**:
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

3. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env con tus credenciales (ver sección Configuración)
```

4. **Configurar base de datos**:
```bash
# Crear base de datos PostgreSQL
createdb quiniela_predictor

# Ejecutar configuración
python scripts/setup_database.py
```

5. **Iniciar servicios manualmente**:
```bash
# Terminal 1: API Backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Dashboard
streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0

# Terminal 3: Redis (si no usas Docker)
redis-server
```

#### Instalación con Docker

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con API_FOOTBALL_KEY y SECRET_KEY

# 2. Ejecutar con Docker Compose
docker-compose up -d

# 3. Configurar base de datos
python scripts/setup_database.py
```

</details>

### ⚙️ Configuración de Variables de Entorno

El archivo `.env` contiene toda la configuración. **Variables críticas:**

```bash
# REQUERIDO: Tu API key de API-Football
API_FOOTBALL_KEY=tu_api_key_aqui

# REQUERIDO: Clave secreta (genera con: openssl rand -hex 32)
SECRET_KEY=tu_secret_key_muy_seguro_de_32_caracteres_minimo

# Base de datos (si usas Docker, no cambies esto)
DATABASE_URL=postgresql://quiniela_user:quiniela_password@localhost:5432/quiniela_predictor

# Configuración de apuestas
INITIAL_BANKROLL=1000.0      # Tu bankroll inicial en euros
MAX_BET_PERCENTAGE=0.05      # Máximo 5% del bankroll por jornada
MIN_CONFIDENCE_THRESHOLD=0.6 # Solo apostar con 60%+ confianza
```

### 🩺 Verificar Instalación

```bash
# Verificar que todo está configurado correctamente
python scripts/validate_environment.py

# Comprobar API
curl http://localhost:8000/health

# Comprobar Dashboard
open http://localhost:8501
```

## 🎮 Uso del Sistema

### 1. Inicialización de Datos

```bash
# Actualizar equipos para temporada actual
curl -X POST "http://localhost:8000/data/update-teams/2025"

# Actualizar partidos
curl -X POST "http://localhost:8000/data/update-matches/2025"

# Actualizar estadísticas
curl -X POST "http://localhost:8000/data/update-statistics/2025"
```

### 2. Entrenamiento del Modelo

```bash
# Entrenar modelo con datos históricos
curl -X POST "http://localhost:8000/model/train" \
     -H "Content-Type: application/json" \
     -d '{"season": 2025}'

# O usar script directo
python scripts/train_model.py --season 2025
```

### 3. Generar Predicciones

```bash
# Predicciones automáticas para la jornada actual
python scripts/run_predictions.py --season 2025

# Predicciones para jornada específica  
python scripts/run_predictions.py --season 2025 --week 15
```

### 4. Dashboard

Acceder al dashboard en: `http://localhost:8501`

#### Funcionalidades del Dashboard:

**🎯 Mi Quiniela Personal**
- **Selección de Partidos**: Elige entre configuraciones personalizadas o sistema automático
- **Próximos Partidos**: Ver predicciones con explicaciones detalladas
- **Mi Historial**: Tracking completo de tus quinielas guardadas
- **Actualizar Resultados**: Registrar resultados reales y calcular ganancias

**⚙️ Configuración Avanzada**
- **Selección Manual**: Elige exactamente 15 partidos de la próxima jornada
- **Partidos por Jornada**: Muestra partidos de Primera y Segunda División ordenados
- **Configuraciones Guardadas**: Administra y reutiliza tus selecciones personalizadas
- **Pleno al 15**: Designa qué partido usar para el Pleno al 15

**📊 Análisis y Rendimiento**
- **Predicciones del Sistema**: Predicciones automáticas para la jornada actual
- **Rendimiento Histórico**: Gráficos de precisión histórica
- **Análisis Financiero**: ROI detallado por jornada

**🔧 Administración**
- **Gestión de Datos**: Actualización de equipos y partidos
- **Estado de la base de datos**: Monitoreo del sistema
- **Modelo ML**: Entrenamiento del modelo e importancia de características

**📋 Información**
- **Reglas Oficiales**: Normativa completa de la Quiniela Española
- **Modalidades de Juego**: Simple, Múltiple, Reducidas
- **Estado de Implementación**: Qué funcionalidades están disponibles

## 📈 Estrategias de Apuestas

### Criterio Kelly Simplificado
- **Apuesta solo con confianza >60%**
- **Máximo 5% del bankroll por jornada**
- **Diversificación entre múltiples partidos**
- **Seguimiento de ROI semanal**

### Gestión de Riesgo
- **Bankroll inicial**: €1000 (configurable)
- **Stop-loss**: -20% del bankroll inicial
- **Take-profit**: Reinversión del 50% de ganancias

## 📊 Métricas de Rendimiento

### Objetivos de Precisión:
- **Mínimo aceptable**: 40% (6/15 aciertos)
- **Objetivo realista**: 50% (7-8/15 aciertos)
- **Excelente**: 60%+ (9+/15 aciertos)

### ROI Esperado:
- **Conservador**: 10-15% anual
- **Moderado**: 20-30% anual
- **Agresivo**: 40%+ anual (mayor riesgo)

## 🛠️ Estructura del Proyecto

```
1x2_Predictor/
├── backend/
│   ├── app/
│   │   ├── api/          # Esquemas Pydantic
│   │   ├── database/     # Modelos SQLAlchemy
│   │   ├── ml/           # Machine Learning
│   │   ├── services/     # Servicios (API Football)
│   │   └── config/       # Configuración
│   └── main.py           # FastAPI app
├── frontend/             # (Futuro: React/Vue)
├── scripts/              # Scripts utilitarios
├── data/
│   ├── raw/              # Datos sin procesar
│   ├── processed/        # Datos procesados
│   └── models/           # Modelos entrenados
├── dashboard.py          # Dashboard Streamlit
├── docker-compose.yml    # Orquestación Docker
└── requirements.txt      # Dependencias Python
```

## 🔧 API Endpoints

### Gestión de Datos
- `POST /data/update-teams/{season}` - Actualizar equipos
- `POST /data/update-matches/{season}` - Actualizar partidos
- `POST /data/update-statistics/{season}` - Actualizar estadísticas
- `GET /matches/upcoming-by-round/{season}` - Obtener partidos de próxima jornada

### Predicciones
- `GET /predictions/current-week` - Predicciones actuales
- `GET /predictions/history` - Historial de predicciones
- `GET /quiniela/next-matches/{season}` - Próximos partidos con explicaciones
- `GET /quiniela/from-config/{config_id}` - Predicciones desde configuración personalizada

### Configuraciones Personalizadas
- `POST /quiniela/custom-config/save` - Guardar configuración personalizada
- `GET /quiniela/custom-config/list` - Listar configuraciones guardadas

### Gestión Personal de Quinielas
- `POST /quiniela/user/create` - Crear nueva quiniela personal
- `GET /quiniela/user/history` - Historial de quinielas del usuario
- `PUT /quiniela/user/{id}/results` - Actualizar resultados y ganancias

### Analytics
- `GET /analytics/model-performance` - Rendimiento del modelo
- `GET /analytics/financial-summary` - Resumen financiero

### Modelo ML
- `POST /model/train` - Entrenar modelo
- `GET /model/status` - Estado del modelo

## ⚡ Desarrollo y Modificaciones

### 🔄 Regla de Oro para Docker

**IMPORTANTE**: Para que los cambios en el código se reflejen en la aplicación:

```bash
# SIEMPRE hacer rebuild sin caché después de cambios:
docker-compose build --no-cache [service-name]
docker-compose up -d [service-name]

# Ejemplos específicos:
docker-compose build --no-cache api      # Para cambios en backend/app/
docker-compose build --no-cache dashboard # Para cambios en dashboard.py
```

**¿Por qué es necesario?**
- Docker cachea las capas para acelerar builds
- Un simple `restart` NO aplica cambios en archivos Python
- Sin `--no-cache`, los cambios pueden no aparecer

**Workflow recomendado:**
1. 📝 Hacer cambios en código
2. 🔨 `docker-compose build --no-cache [service]`
3. 🚀 `docker-compose up -d [service]` 
4. ✅ Verificar cambios en http://localhost:8501

### 🚀 Scripts de Rebuild Rápido

Para simplificar el proceso, usa los scripts incluidos:

```bash
# Linux/Mac
./scripts/rebuild.sh [service]

# Windows  
scripts\rebuild.bat [service]

# Ejemplos:
./scripts/rebuild.sh api       # Solo API
./scripts/rebuild.sh dashboard # Solo Dashboard
./scripts/rebuild.sh           # Ambos servicios
```

## 📚 Mejores Prácticas

### Entrenamiento del Modelo
1. **Datos mínimos**: 100+ partidos completados
2. **Actualización**: Re-entrenar cada 4-6 semanas
3. **Validación**: Siempre usar validación cruzada
4. **Features**: Monitorear importancia de características

### Gestión de Apuestas
1. **Nunca apostar más del 5% del bankroll**
2. **Diversificar entre múltiples partidos**
3. **Registrar todas las apuestas**
4. **Revisar estrategia mensualmente**

### Monitoreo
1. **Accuracy tracking**: Por jornada y mensual
2. **ROI monitoring**: Semanal y acumulado
3. **Feature drift**: Cambios en importancia
4. **API limits**: Monitorear uso de API-Football

## 🚨 Consideraciones Importantes

### Limitaciones
- **Dependencia de datos externos** (API-Football)
- **Variabilidad inherente del fútbol**
- **Riesgo financiero** en todas las apuestas
- **Necesidad de capital inicial**

### Aspectos Legales
- **Verificar legalidad** de apuestas deportivas en tu jurisdicción
- **Juego responsable**: Establecer límites claros
- **Solo apostar dinero que puedas permitirte perder**

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -am 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 💡 Roadmap

### Versión 1.7 - Próximas Funcionalidades ⏳
- [ ] Sistema de notificaciones push para nuevos partidos
- [ ] Exportación de quinielas a PDF/Excel
- [ ] Análisis de tendencias por equipos específicos
- [ ] Integración con calendario de Google para recordatorios

### Versión 2.0 - Expansión Multi-Liga
- [ ] Premier League, Serie A, Bundesliga
- [ ] Sistema de apuestas multi-mercado
- [ ] Trading automático de apuestas
- [ ] Marketplace de modelos ML compartidos

## 📝 Últimos Cambios

### Versión 1.6.0 (2025-08-14) - Configuración Personalizada + Flujo Coherente 🎯

**⚙️ Sistema de Configuración Personalizada:**
- ✅ **Selección Manual de Partidos**: Elige exactamente 15 partidos de la próxima jornada
- ✅ **Próxima Jornada Inteligente**: Muestra automáticamente partidos de la siguiente jornada disponible
- ✅ **Configuraciones Guardadas**: Sistema completo para guardar, listar y gestionar configuraciones
- ✅ **Designación Pleno al 15**: Selecciona qué partido usar como Pleno al 15

**🔄 Flujo Coherente Mi Quiniela Personal:**
- ✅ **Selector de Configuración**: Dropdown para elegir entre configuraciones personalizadas o automático
- ✅ **Vista Previa Inteligente**: Muestra detalles de la configuración seleccionada (La Liga, Segunda, semana)
- ✅ **Integración Completa**: Las predicciones usan exactamente los partidos de la configuración seleccionada
- ✅ **Fallback Automático**: Si no hay configuraciones, usa el sistema automático tradicional

**🔄 Corrección de Inconsistencias:**
- ✅ **Botones Reordenados**: "Obtener Predicciones" (principal, izquierda) y "Actualizar Datos" (derecha)
- ✅ **Error 500 Corregido**: Añadidas columnas faltantes `pleno_al_15_home` y `pleno_al_15_away` en base de datos
- ✅ **Basic Predictor Arreglado**: Campo `predicted_result` y formato de probabilidades corregidos
- ✅ **Configuración Avanzada Mejorada**: Muestra partidos reales de próxima jornada, no aleatorios

**🏢 Nuevos Endpoints API:**
- ✅ `GET /matches/upcoming-by-round/{season}` - Partidos de próxima jornada por liga
- ✅ `POST /quiniela/custom-config/save` - Guardar configuración personalizada
- ✅ `GET /quiniela/custom-config/list` - Listar configuraciones con filtros
- ✅ `GET /quiniela/from-config/{config_id}` - Generar predicciones desde configuración

**🔧 Mejoras Técnicas:**
- ✅ **Nueva Función**: `create_basic_predictions_for_matches()` para partidos específicos
- ✅ **Tabla Extendida**: `CustomQuinielaConfig` para almacenar configuraciones personalizadas
- ✅ **Migración DB**: Script automático para añadir columnas faltantes
- ✅ **Interfaz Intuitiva**: Selectores, métricas y estados visuales mejorados

**🏆 Experiencia de Usuario:**
- ✅ **Flujo Lógico**: Configuración Avanzada → Mi Quiniela Personal → Resultados coherentes
- ✅ **Feedback Claro**: Mensajes explicativos sobre qué configuración se está usando
- ✅ **Estados Visuales**: 🔵 Activa / 🔴 Inactiva para configuraciones
- ✅ **Sugerencias Útiles**: Guía al usuario cuando no hay configuraciones

**🎮 Experiencia Mejorada:**

1. **🎯 Flujo Principal Optimizado:**
   - Configuración Avanzada → Seleccionar 15 partidos → Guardar configuración
   - Mi Quiniela Personal → Elegir configuración → Obtener predicciones coherentes
   - Sistema inteligente usa exactamente los partidos seleccionados

2. **⚙️ Control Total:**
   - Selecciona manualmente partidos de la próxima jornada real
   - Designa cuál de los 15 partidos será el Pleno al 15
   - Guarda múltiples configuraciones con nombres descriptivos
   - Activa/desactiva configuraciones según necesidad

3. **🔄 Coherencia Completa:**
   - Ya no hay discrepancias entre secciones
   - Los botones están en el orden lógico correcto
   - Todos los errores 500 han sido corregidos
   - Configuración Avanzada muestra partidos reales, no aleatorios

---

### Versión 1.5.0 (2025-08-13) - Corrección Pleno al 15 + Orden Oficial + Gestión Mejorada

**🏆 Pleno al 15 Oficial Implementado:**
- ✅ **Reglas BOE Cumplidas**: Predicción correcta de goles por equipo (0, 1, 2, M) según normativa oficial
- ✅ **UI Dual**: Dos selectores separados para goles del equipo local y visitante  
- ✅ **Backward Compatibility**: Sistema maneja formato anterior automáticamente

**📋 Orden Oficial de Partidos:**
- ✅ **Orden Auténtico**: Partidos ordenados como en Quiniela real (La Liga alfabético + Segunda)
- ✅ **SQL Optimizado**: Query con JOIN para ordenamiento correcto desde base de datos
- ✅ **Selección Inteligente**: Máximo 10 La Liga + completar con Segunda División hasta 15

**🗑️ Gestión de Datos Mejorada:**
- ✅ **Borrado Selectivo**: Elimina equipos, partidos y estadísticas pero preserva quinielas del usuario
- ✅ **Interfaz Clara**: Explicación detallada de qué se borra vs qué se preserva
- ✅ **Confirmación Segura**: Nuevo formato de confirmación "BORRAR_DATOS"

## 🆘 Soporte

Para soporte y preguntas:
- **Issues**: Usar GitHub Issues para bugs y features
- **Documentación**: Revisar CONTEXT.md para troubleshooting detallado
- **Docker Issues**: Usar `docker-compose build --no-cache` para cambios
- **Contacto**: [Crear issue en el repositorio]

---

**⚠️ Disclaimer**: Este sistema es para fines educativos y de investigación. Las apuestas deportivas conllevan riesgo financiero. Apuesta responsablemente y dentro de tus posibilidades económicas.