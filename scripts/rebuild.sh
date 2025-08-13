#!/bin/bash
# Script para rebuild rápido de servicios Docker sin caché
# Uso: ./scripts/rebuild.sh [service-name]

set -e

SERVICE=${1:-"all"}
VALID_SERVICES=("api" "dashboard" "all")

# Función para mostrar ayuda
show_help() {
    echo "🔧 Script de Rebuild sin Caché para Docker"
    echo ""
    echo "Uso: ./scripts/rebuild.sh [service]"
    echo ""
    echo "Servicios disponibles:"
    echo "  api       - Rebuild solo el backend API (backend/app/)"
    echo "  dashboard - Rebuild solo el dashboard (dashboard.py)"
    echo "  all       - Rebuild ambos servicios (por defecto)"
    echo ""
    echo "Ejemplos:"
    echo "  ./scripts/rebuild.sh api       # Solo API"
    echo "  ./scripts/rebuild.sh dashboard # Solo Dashboard"
    echo "  ./scripts/rebuild.sh           # Ambos servicios"
}

# Validar argumento
if [[ "$SERVICE" == "-h" ]] || [[ "$SERVICE" == "--help" ]]; then
    show_help
    exit 0
fi

if [[ ! " ${VALID_SERVICES[@]} " =~ " ${SERVICE} " ]]; then
    echo "❌ Error: Servicio '$SERVICE' no válido"
    echo ""
    show_help
    exit 1
fi

echo "🚀 Iniciando rebuild sin caché para: $SERVICE"
echo ""

# Función para rebuild de un servicio específico
rebuild_service() {
    local svc=$1
    echo "🔨 Building $svc sin caché..."
    docker-compose build --no-cache "$svc"
    
    echo "🚀 Starting $svc..."
    docker-compose up -d "$svc"
    
    echo "✅ $svc rebuildeado exitosamente"
}

# Ejecutar rebuild según servicio
case $SERVICE in
    "api")
        rebuild_service "api"
        echo ""
        echo "📡 API disponible en: http://localhost:8000"
        echo "📖 Docs API en: http://localhost:8000/docs"
        ;;
    "dashboard")
        rebuild_service "dashboard"
        echo ""
        echo "📊 Dashboard disponible en: http://localhost:8501"
        ;;
    "all")
        rebuild_service "api"
        echo ""
        rebuild_service "dashboard"
        echo ""
        echo "🎉 Ambos servicios rebuildeados exitosamente"
        echo "📊 Dashboard: http://localhost:8501"
        echo "📡 API: http://localhost:8000"
        echo "📖 API Docs: http://localhost:8000/docs"
        ;;
esac

echo ""
echo "⚠️  Recuerda: Siempre usa rebuild sin caché después de cambios en código"
echo "💡 Para más info: ver README.md sección 'Desarrollo y Modificaciones'"