#!/usr/bin/env python3
"""
Script de validación del entorno para Quiniela Predictor
Verifica que todas las dependencias y configuraciones estén correctas
"""

import os
import sys
import requests
import subprocess
from typing import Dict, List, Tuple
from datetime import datetime
import psycopg2
import redis
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()

def check_environment_variables() -> Dict[str, bool]:
    """Verifica variables de entorno requeridas"""
    required_vars = [
        'API_FOOTBALL_KEY',
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL'
    ]
    
    results = {}
    for var in required_vars:
        value = os.getenv(var)
        results[var] = bool(value and value != f'your_{var.lower()}_here_REQUIRED')
    
    return results

def check_api_football_connection() -> Tuple[bool, str]:
    """Verifica conexión con API-Football"""
    api_key = os.getenv('API_FOOTBALL_KEY')
    if not api_key or 'REQUIRED' in api_key:
        return False, "API key not configured"
    
    try:
        headers = {
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': 'v3.football.api-sports.io'
        }
        
        response = requests.get(
            'https://v3.football.api-sports.io/status',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'response' in data:
                requests_remaining = data['response']['requests']['current']
                return True, f"Connected. Requests remaining: {requests_remaining}"
            else:
                return False, f"Invalid API response: {response.text}"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def check_database_connection() -> Tuple[bool, str]:
    """Verifica conexión con PostgreSQL"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return False, "DATABASE_URL not configured"
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return True, f"Connected to {version[0]}"
        
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def check_redis_connection() -> Tuple[bool, str]:
    """Verifica conexión con Redis"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        info = r.info()
        version = info.get('redis_version', 'Unknown')
        return True, f"Connected to Redis {version}"
        
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def check_docker_services() -> Dict[str, Tuple[bool, str]]:
    """Verifica servicios de Docker"""
    services = ['postgres', 'redis', 'api', 'dashboard']
    results = {}
    
    try:
        # Verificar si Docker está disponible
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        
        # Verificar estado de servicios
        result = subprocess.run(
            ['docker-compose', 'ps', '--services', '--filter', 'status=running'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        running_services = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        for service in services:
            if service in running_services:
                results[service] = (True, "Running")
            else:
                results[service] = (False, "Not running")
                
    except subprocess.CalledProcessError:
        for service in services:
            results[service] = (False, "Docker not available")
    
    return results

def check_python_dependencies() -> List[Tuple[str, bool, str]]:
    """Verifica dependencias de Python"""
    dependencies = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'psycopg2',
        'scikit-learn',
        'xgboost',
        'pandas',
        'numpy',
        'streamlit',
        'plotly',
        'requests',
        'redis',
        'celery'
    ]
    
    results = []
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            results.append((dep, True, "✅ Installed"))
        except ImportError:
            results.append((dep, False, "❌ Missing"))
    
    return results

def check_data_directories() -> Dict[str, bool]:
    """Verifica que existan los directorios de datos"""
    required_dirs = [
        'data',
        'data/raw',
        'data/processed',
        'data/models'
    ]
    
    results = {}
    base_path = os.path.dirname(os.path.dirname(__file__))
    
    for dir_name in required_dirs:
        dir_path = os.path.join(base_path, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            results[dir_name] = True
        else:
            results[dir_name] = True
    
    return results

def main():
    """Función principal de validación"""
    console.print(Panel.fit(
        "[bold blue]🏆 Quiniela Predictor - Validación del Entorno[/bold blue]\n"
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="blue"
    ))
    
    # Tabla de resultados
    table = Table(title="Resultados de Validación")
    table.add_column("Componente", style="cyan", no_wrap=True)
    table.add_column("Estado", justify="center")
    table.add_column("Detalles", style="yellow")
    
    all_good = True
    
    # 1. Variables de entorno
    console.print("\n[bold]1. Variables de Entorno[/bold]")
    env_vars = check_environment_variables()
    for var, status in env_vars.items():
        icon = "✅" if status else "❌"
        detail = "Configurada" if status else "FALTA CONFIGURAR"
        table.add_row(f"ENV: {var}", icon, detail)
        if not status:
            all_good = False
    
    # 2. Conexiones externas
    console.print("\n[bold]2. Conexiones Externas[/bold]")
    
    # API-Football
    api_status, api_detail = check_api_football_connection()
    icon = "✅" if api_status else "❌"
    table.add_row("API-Football", icon, api_detail)
    if not api_status:
        all_good = False
    
    # 3. Base de datos
    console.print("\n[bold]3. Base de Datos[/bold]")
    db_status, db_detail = check_database_connection()
    icon = "✅" if db_status else "❌"
    table.add_row("PostgreSQL", icon, db_detail)
    if not db_status:
        all_good = False
    
    # Redis
    redis_status, redis_detail = check_redis_connection()
    icon = "✅" if redis_status else "❌"
    table.add_row("Redis", icon, redis_detail)
    if not redis_status:
        all_good = False
    
    # 4. Servicios Docker
    console.print("\n[bold]4. Servicios Docker[/bold]")
    docker_services = check_docker_services()
    for service, (status, detail) in docker_services.items():
        icon = "✅" if status else "⚠️"
        table.add_row(f"Docker: {service}", icon, detail)
    
    # 5. Dependencias Python
    console.print("\n[bold]5. Dependencias Python[/bold]")
    python_deps = check_python_dependencies()
    missing_deps = []
    for dep, status, detail in python_deps:
        icon = "✅" if status else "❌"
        table.add_row(f"Python: {dep}", icon, detail)
        if not status:
            missing_deps.append(dep)
            all_good = False
    
    # 6. Directorios de datos
    console.print("\n[bold]6. Directorios de Datos[/bold]")
    data_dirs = check_data_directories()
    for dir_name, status in data_dirs.items():
        icon = "✅" if status else "❌"
        detail = "Existe" if status else "No existe"
        table.add_row(f"DIR: {dir_name}", icon, detail)
    
    # Mostrar tabla de resultados
    console.print(table)
    
    # Resumen final
    if all_good:
        console.print(Panel(
            "[bold green]✅ ¡Entorno completamente configurado![/bold green]\n"
            "Tu sistema está listo para ejecutar Quiniela Predictor.",
            title="✅ ÉXITO",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[bold red]❌ Configuración incompleta[/bold red]\n"
            "Revisa los elementos marcados con ❌ y configúralos antes de continuar.\n\n"
            "[bold]Pasos sugeridos:[/bold]\n"
            "1. Copia .env.example a .env y configura tus valores\n"
            "2. Instala dependencias faltantes: pip install -r requirements.txt\n"
            "3. Inicia servicios: docker-compose up -d\n"
            "4. Ejecuta setup de BD: python scripts/setup_database.py",
            title="⚠️  ACCIÓN REQUERIDA",
            border_style="red"
        ))
    
    # Información adicional
    if missing_deps:
        console.print(f"\n[bold red]Dependencias faltantes:[/bold red] {', '.join(missing_deps)}")
        console.print("[yellow]Ejecuta:[/yellow] pip install -r requirements.txt")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())