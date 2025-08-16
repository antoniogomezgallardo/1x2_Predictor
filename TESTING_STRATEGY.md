# 🧪 Estrategia de Testing - Quiniela Predictor v2.1.0

## 📋 **VISIÓN GENERAL**

Estrategia completa de testing para asegurar la calidad, estabilidad y confiabilidad del sistema de predicción de quinielas más avanzado.

## 🎯 **OBJETIVOS**

1. **Calidad del Código**: Detectar errores antes de producción
2. **Refactoring Seguro**: Permitir mejoras sin romper funcionalidades
3. **Documentación Viva**: Tests como especificación del comportamiento
4. **Confianza en Despliegues**: Deploy seguro en cualquier momento
5. **Performance**: Detectar regresiones de rendimiento

## 🏗️ **ESTRUCTURA DE TESTING**

### **Niveles de Testing (Pirámide)**

```
                    🔺 E2E Tests (5%)
                   🔺🔺 Integration Tests (25%)  
                🔺🔺🔺🔺 Unit Tests (70%)
```

### **1. Unit Tests (70% - Base de la Pirámide)**

**Responsabilidad**: Testear unidades individuales de código
**Velocidad**: Muy rápidas (< 100ms por test)
**Scope**: Funciones, métodos, clases aisladas

**Cobertura Mínima**: 80% en funciones críticas

**Areas Críticas**:
- ✅ Validadores de Quiniela (BOE compliance)
- ✅ Calculadoras de costos y combinaciones
- ✅ Feature engineering ML
- ✅ Parsers de datos (API-Football, FBRef)
- ✅ Utilidades matemáticas y estadísticas

### **2. Integration Tests (25% - Medio)**

**Responsabilidad**: Testear interacciones entre componentes
**Velocidad**: Moderadas (< 5s por test)
**Scope**: APIs, base de datos, servicios externos

**Areas Críticas**:
- ✅ Endpoints API completos
- ✅ Flujos de base de datos
- ✅ Integración con API-Football (mocked)
- ✅ ML Pipeline completo
- ✅ Authentication & Authorization

### **3. E2E Tests (5% - Cima)**

**Responsabilidad**: Testear flujos completos de usuario
**Velocidad**: Lentas (< 30s por test)
**Scope**: Aplicación completa en ambiente similar a producción

**Flujos Críticos**:
- ✅ Crear quiniela simple completa
- ✅ Crear quiniela múltiple con dobles/triples
- ✅ Entrenamiento de modelo ML
- ✅ Actualización de datos y predicciones

## 📁 **ORGANIZACIÓN DE ARCHIVOS**

```
tests/
├── conftest.py                 # Configuración global pytest
├── fixtures/                   # Datos de prueba reutilizables
│   ├── teams_data.json
│   ├── matches_data.json
│   └── predictions_data.json
├── unit/                       # Tests unitarios
│   ├── test_validators.py      # QuinielaValidator, BOE compliance
│   ├── test_calculators.py     # Costos, combinaciones
│   ├── test_ml_features.py     # Feature engineering
│   ├── test_parsers.py         # Data parsing
│   └── test_utils.py           # Utilidades
├── integration/                # Tests de integración
│   ├── test_api_endpoints.py   # Todos los endpoints
│   ├── test_database.py        # Operaciones DB
│   ├── test_ml_pipeline.py     # Pipeline ML completo
│   └── test_external_apis.py   # APIs externas (mocked)
├── e2e/                        # Tests end-to-end
│   ├── test_user_flows.py      # Flujos completos de usuario
│   └── test_dashboard.py       # Streamlit dashboard
└── performance/                # Tests de rendimiento
    ├── test_load.py            # Carga de endpoints
    └── test_ml_training.py     # Performance ML
```

## 🛠️ **HERRAMIENTAS Y CONFIGURACIÓN**

### **Stack Principal**

- **pytest**: Framework principal de testing
- **pytest-asyncio**: Support para async/await
- **httpx**: Cliente HTTP async para API testing
- **pytest-mock**: Mocking y patching
- **pytest-cov**: Coverage reporting
- **pytest-benchmark**: Performance testing
- **factory-boy**: Generación de datos de prueba
- **freezegun**: Mocking de tiempo/fechas

### **Coverage Requirements**

```python
# pytest.ini
[tool:pytest]
minversion = 6.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=backend/app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --asyncio-mode=auto
    -v
filterwarnings = ignore::DeprecationWarning
```

## 🎯 **CONVENCIONES Y ESTÁNDARES**

### **Naming Conventions**

```python
# Files: test_[module_name].py
test_validators.py
test_quiniela_calculator.py

# Classes: Test[FeatureName]
class TestQuinielaValidator:
class TestMLFeatureEngineering:

# Functions: test_[specific_behavior]
def test_calculate_combinations_with_valid_inputs():
def test_validate_quiniela_rejects_invalid_configuration():
def test_basic_predictor_handles_missing_data():
```

### **AAA Pattern (Arrange-Act-Assert)**

```python
def test_calculate_quiniela_cost():
    # Arrange
    multiplicities = [1, 2, 1, 3, 1]  # Simple, doble, simple, triple, simple
    
    # Act
    result = QuinielaValidator.calculate_combinations(multiplicities)
    
    # Assert
    assert result == 6  # 1*2*1*3*1 = 6 combinations
```

### **Fixtures Reutilizables**

```python
# conftest.py
@pytest.fixture
def sample_team():
    return Team(
        api_id=123,
        name="Real Madrid",
        short_name="RMA",
        league_id=140
    )

@pytest.fixture
def sample_quiniela_config():
    return {
        "week_number": 1,
        "season": 2025,
        "predictions": [
            {"match_number": 1, "prediction_options": ["1"]},
            {"match_number": 2, "prediction_options": ["X", "2"]},
            # ... 13 more
        ]
    }
```

## 🚀 **IMPLEMENTACIÓN POR FASES**

### **FASE 1: Foundation (Inmediato)**
- ✅ Configurar pytest.ini y conftest.py
- ✅ Tests críticos para QuinielaValidator
- ✅ Tests para calculadoras de costos
- ✅ Mock de APIs externas

### **FASE 2: Core Logic (1-2 semanas)**  
- ✅ Tests completos para ML feature engineering
- ✅ Tests para todos los endpoints críticos
- ✅ Tests de base de datos con transacciones
- ✅ Performance benchmarks básicos

### **FASE 3: Advanced (2-3 semanas)**
- ✅ E2E tests con Streamlit
- ✅ Load testing de endpoints
- ✅ CI/CD pipeline con GitHub Actions
- ✅ Test coverage >90%

## 📊 **MÉTRICAS Y MONITORING**

### **KPIs de Testing**

```bash
# Coverage mínimo por módulo
validators.py: 95%
calculators.py: 95%
ml/feature_engineering.py: 85%
api/endpoints.py: 80%
services/: 75%

# Performance benchmarks
API endpoints: < 200ms p95
ML training: < 30s for 1000 matches
Quiniela validation: < 10ms
```

### **Reportes Automáticos**

- **Coverage Report**: HTML dashboard generado automáticamente
- **Performance Report**: Tracking de regresiones de performance
- **Test Results**: Slack/email notifications en CI/CD

## 🔄 **CI/CD Integration**

### **Pre-commit Hooks**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Unit Tests
        entry: pytest tests/unit/
        language: system
        pass_filenames: false
```

### **GitHub Actions Pipeline**

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run Unit Tests
        run: pytest tests/unit/ -v
        
      - name: Run Integration Tests  
        run: pytest tests/integration/ -v
        
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

## 🎭 **Mocking Strategy**

### **APIs Externas**

```python
# tests/mocks/api_football_mock.py
@pytest.fixture
def mock_api_football_teams():
    return {
        "response": [
            {
                "team": {
                    "id": 541,
                    "name": "Real Madrid",
                    "code": "RMA"
                }
            }
        ]
    }
```

### **Base de Datos**

```python
# Usar base de datos real pero con transacciones que se revierten
@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

## 🏆 **BEST PRACTICES**

### **DO's**
- ✅ Un concepto por test
- ✅ Nombres descriptivos y específicos
- ✅ Tests independientes (no state sharing)
- ✅ Mock dependencies externas
- ✅ Assertiones específicas y claras
- ✅ Cleanup automático con fixtures

### **DON'Ts**
- ❌ Tests que dependen de orden de ejecución
- ❌ Hardcodear datos de producción
- ❌ Tests que tardan >30s (salvo E2E)
- ❌ Múltiples assertions no relacionadas
- ❌ Mock de código propio (solo dependencies)
- ❌ Tests sin cleanup

## 🎯 **PRÓXIMOS PASOS**

1. **Implementar pytest.ini y conftest.py**
2. **Crear tests para QuinielaValidator (crítico)**
3. **Testear endpoints reorganizados (Clean Architecture)**
4. **Configurar CI/CD pipeline básico**
5. **Establecer coverage goals por módulo**

---

**Objetivo**: Sistema de testing robusto que garantice la calidad del código y permita innovación rápida y segura.