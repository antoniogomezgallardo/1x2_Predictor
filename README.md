# 🏆 Quiniela Predictor - Sistema de Predicción de Resultados

Sistema avanzado de predicción de resultados para la Quiniela Española utilizando Machine Learning e integración con API-Football.

## 🎯 Objetivo

Predecir los resultados de los 15 partidos semanales de la Quiniela Española (Primera y Segunda División) para generar beneficios consistentes mediante estrategias de apuestas inteligentes.

## ⚡ Características Principales

- **Predicciones ML**: Modelos ensemble (Random Forest + XGBoost) con +40 características
- **Dashboard Interactivo**: Visualización en tiempo real de predicciones y rendimiento
- **Gestión Personal de Quinielas**: Sistema completo para crear, guardar y trackear tus quinielas
- **Explicaciones Detalladas**: Cada predicción incluye análisis razonado y factores decisivos
- **Análisis Financiero**: Seguimiento de ROI, beneficios y estrategias de apuestas
- **Gestión de Datos**: Integración automática con API-Football
- **Historial Completo**: Tracking de precisión y rendimiento por jornada

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

### Prerrequisitos
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Cuenta API-Football (Premium)

### Instalación Local

1. **Clonar repositorio**:
```bash
git clone <repository-url>
cd 1x2_Predictor
```

2. **Configurar entorno**:
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
# Editar .env con tus credenciales
```

4. **Configurar base de datos**:
```bash
# Crear base de datos PostgreSQL
createdb quiniela_predictor

# Ejecutar migraciones
python scripts/setup_database.py
```

### Instalación con Docker

1. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env con API_FOOTBALL_KEY y SECRET_KEY
```

2. **Ejecutar con Docker Compose**:
```bash
docker-compose up -d
```

3. **Configurar base de datos**:
```bash
docker-compose exec api python scripts/setup_database.py
```

## 🎮 Uso del Sistema

### 1. Inicialización de Datos

```bash
# Actualizar equipos para temporada actual
curl -X POST "http://localhost:8000/data/update-teams/2024"

# Actualizar partidos
curl -X POST "http://localhost:8000/data/update-matches/2024"

# Actualizar estadísticas
curl -X POST "http://localhost:8000/data/update-statistics/2024"
```

### 2. Entrenamiento del Modelo

```bash
# Entrenar modelo con datos históricos
curl -X POST "http://localhost:8000/model/train" \
     -H "Content-Type: application/json" \
     -d '{"season": 2024}'

# O usar script directo
python scripts/train_model.py --season 2024
```

### 3. Generar Predicciones

```bash
# Predicciones automáticas para la jornada actual
python scripts/run_predictions.py --season 2024

# Predicciones para jornada específica
python scripts/run_predictions.py --season 2024 --week 15
```

### 4. Dashboard

Acceder al dashboard en: `http://localhost:8501`

#### Funcionalidades del Dashboard:

**🎯 Mi Quiniela Personal**
- **Próximos Partidos**: Ver predicciones con explicaciones detalladas
- **Mi Historial**: Tracking completo de tus quinielas guardadas
- **Actualizar Resultados**: Registrar resultados reales y calcular ganancias

**📊 Predicciones del Sistema**
- Predicciones automáticas para la jornada actual
- Estrategias de apuestas recomendadas
- Análisis de confianza por partido

**📈 Análisis de Rendimiento**
- Gráficos de precisión histórica
- Tracking de beneficios acumulados
- Métricas de rendimiento del modelo

**💰 Análisis Financiero**
- ROI detallado por jornada
- Beneficios/pérdidas acumulados
- Análisis de rentabilidad

**🔧 Gestión de Datos**
- Actualización de equipos y partidos
- Estado de la base de datos
- Herramientas de mantenimiento

**🤖 Modelo ML**
- Entrenamiento del modelo
- Importancia de características
- Métricas de rendimiento

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

### Predicciones
- `GET /predictions/current-week` - Predicciones actuales
- `GET /predictions/history` - Historial de predicciones
- `GET /quiniela/next-matches/{season}` - Próximos partidos con explicaciones
- `GET /predictions/quiniela-oficial/{season}` - Predicciones formato Quiniela oficial

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

### Versión 1.1 ✅ COMPLETADO
- [x] Sistema completo de gestión personal de quinielas
- [x] Explicaciones detalladas de predicciones con análisis razonado
- [x] Dashboard interactivo con 6 secciones principales
- [x] Tracking completo de ROI y beneficios personales
- [x] Base de datos expandida con tablas de usuario
- [x] API endpoints para gestión completa del usuario

### Versión 1.2
- [ ] Modelo de Deep Learning (LSTM/Transformer)
- [ ] Integración con múltiples casas de apuestas
- [ ] Alertas automáticas vía email/Telegram
- [ ] Análisis de lesiones y suspensiones

### Versión 1.3
- [ ] Frontend React/Vue avanzado
- [ ] API móvil (React Native)
- [ ] Backtesting histórico automático
- [ ] Integración con bases de datos adicionales

### Versión 2.0
- [ ] Multi-liga (Premier League, Serie A, etc.)
- [ ] Trading automático de apuestas
- [ ] Análisis de video con Computer Vision
- [ ] Marketplace de modelos ML

## 🆘 Soporte

Para soporte y preguntas:
- **Issues**: Usar GitHub Issues para bugs y features
- **Documentación**: Wiki del proyecto
- **Contacto**: [tu-email@ejemplo.com]

---

**⚠️ Disclaimer**: Este sistema es para fines educativos y de investigación. Las apuestas deportivas conllevan riesgo financiero. Apuesta responsablemente y dentro de tus posibilidades económicas.