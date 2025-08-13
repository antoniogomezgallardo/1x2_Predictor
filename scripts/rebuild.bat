@echo off
REM Script para rebuild rápido de servicios Docker sin caché (Windows)
REM Uso: scripts\rebuild.bat [service-name]

setlocal enabledelayedexpansion

set SERVICE=%1
if "%SERVICE%"=="" set SERVICE=all

set VALID=0
if "%SERVICE%"=="api" set VALID=1
if "%SERVICE%"=="dashboard" set VALID=1
if "%SERVICE%"=="all" set VALID=1
if "%SERVICE%"=="-h" goto :help
if "%SERVICE%"=="--help" goto :help

if %VALID%==0 (
    echo ❌ Error: Servicio '%SERVICE%' no válido
    echo.
    goto :help
)

echo 🚀 Iniciando rebuild sin caché para: %SERVICE%
echo.

if "%SERVICE%"=="api" goto :rebuild_api
if "%SERVICE%"=="dashboard" goto :rebuild_dashboard
if "%SERVICE%"=="all" goto :rebuild_all

:rebuild_api
echo 🔨 Building API sin caché...
docker-compose build --no-cache api
echo 🚀 Starting API...
docker-compose up -d api
echo ✅ API rebuildeado exitosamente
echo.
echo 📡 API disponible en: http://localhost:8000
echo 📖 Docs API en: http://localhost:8000/docs
goto :end

:rebuild_dashboard
echo 🔨 Building Dashboard sin caché...
docker-compose build --no-cache dashboard
echo 🚀 Starting Dashboard...
docker-compose up -d dashboard
echo ✅ Dashboard rebuildeado exitosamente
echo.
echo 📊 Dashboard disponible en: http://localhost:8501
goto :end

:rebuild_all
echo 🔨 Building API sin caché...
docker-compose build --no-cache api
echo 🚀 Starting API...
docker-compose up -d api
echo ✅ API rebuildeado exitosamente
echo.
echo 🔨 Building Dashboard sin caché...
docker-compose build --no-cache dashboard
echo 🚀 Starting Dashboard...
docker-compose up -d dashboard
echo ✅ Dashboard rebuildeado exitosamente
echo.
echo 🎉 Ambos servicios rebuildeados exitosamente
echo 📊 Dashboard: http://localhost:8501
echo 📡 API: http://localhost:8000
echo 📖 API Docs: http://localhost:8000/docs
goto :end

:help
echo 🔧 Script de Rebuild sin Caché para Docker (Windows)
echo.
echo Uso: scripts\rebuild.bat [service]
echo.
echo Servicios disponibles:
echo   api       - Rebuild solo el backend API (backend/app/)
echo   dashboard - Rebuild solo el dashboard (dashboard.py)
echo   all       - Rebuild ambos servicios (por defecto)
echo.
echo Ejemplos:
echo   scripts\rebuild.bat api       # Solo API
echo   scripts\rebuild.bat dashboard # Solo Dashboard
echo   scripts\rebuild.bat           # Ambos servicios
goto :end

:end
echo.
echo ⚠️  Recuerda: Siempre usa rebuild sin caché después de cambios en código
echo 💡 Para más info: ver README.md sección 'Desarrollo y Modificaciones'
pause