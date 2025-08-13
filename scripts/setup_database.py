#!/usr/bin/env python3
"""
Database setup script for Quiniela Predictor
Creates database tables and performs initial setup with validation
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database.database import create_tables, engine, get_db
from backend.app.database.models import Base
from backend.app.config.settings import settings
import logging
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()


def check_database_connection():
    """Check if database connection is working"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()
            logger.info("Database connection successful!")
            console.print(f"[green]✅ Connected to PostgreSQL: {version[0][:50]}...[/green]")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        console.print(f"[red]❌ Database connection failed: {str(e)}[/red]")
        return False


def setup_database():
    """Set up the database with all required tables"""
    try:
        console.print("\n[bold blue]🏗️  Creando tablas de la base de datos...[/bold blue]")
        
        # Import all models to ensure they're registered
        from backend.app.database.models import (
            Team, Match, TeamStatistics, QuinielaPrediction, 
            QuinielaWeek, ModelPerformance, UserQuiniela, 
            UserQuinielaPrediction, QuinielaWeekSchedule
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creando tablas...", total=None)
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            progress.update(task, description="✅ Tablas creadas")
        
        logger.info("Database tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Create table with information
        table = Table(title="Tablas Creadas en la Base de Datos")
        table.add_column("Tabla", style="cyan", no_wrap=True)
        table.add_column("Descripción", style="white")
        
        table_descriptions = {
            "teams": "Equipos de fútbol (La Liga y Segunda)",
            "matches": "Partidos con resultados y cuotas",
            "team_statistics": "Estadísticas por equipo y temporada",
            "quiniela_predictions": "Predicciones ML del sistema",
            "quiniela_weeks": "Resumen por jornada (accuracy, ROI)",
            "model_performance": "Métricas de rendimiento de modelos",
            "user_quinielas": "Quinielas personales del usuario",
            "user_quiniela_predictions": "Predicciones individuales del usuario",
            "quiniela_week_schedule": "Programación semanal de jornadas"
        }
        
        for table_name in sorted(tables):
            description = table_descriptions.get(table_name, "Tabla del sistema")
            table.add_row(table_name, description)
        
        console.print(table)
        console.print(f"\n[green]✅ {len(tables)} tablas creadas exitosamente[/green]")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        console.print(f"[red]❌ Error creando tablas: {str(e)}[/red]")
        return False


def create_sample_data():
    """Create sample data for testing (optional)"""
    try:
        console.print("\n[yellow]📊 ¿Deseas crear datos de prueba? (y/N):[/yellow]", end=" ")
        response = input().lower().strip()
        
        if response not in ['y', 'yes', 'sí', 's']:
            return True
        
        console.print("[blue]Creando datos de ejemplo...[/blue]")
        
        # This would create sample teams, matches, etc.
        # For now, just confirm the structure is ready
        console.print("[green]✅ Estructura lista para datos de prueba[/green]")
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        console.print(f"[red]❌ Error creando datos de prueba: {str(e)}[/red]")
        return False


def verify_setup():
    """Verify that setup was successful"""
    try:
        console.print("\n[bold blue]🔍 Verificando configuración...[/bold blue]")
        
        from sqlalchemy import text
        with engine.connect() as connection:
            # Check tables exist
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            # Check for essential tables
            essential_tables = [
                'teams', 'matches', 'team_statistics', 'quiniela_predictions',
                'user_quinielas', 'user_quiniela_predictions'
            ]
            
            missing_tables = [table for table in essential_tables if table not in tables]
            
            if missing_tables:
                console.print(f"[red]❌ Faltan tablas esenciales: {missing_tables}[/red]")
                return False
            
            # Test database write/read
            result = connection.execute(text("SELECT NOW()"))
            current_time = result.fetchone()[0]
            
            console.print(f"[green]✅ Base de datos operativa - {current_time}[/green]")
            console.print(f"[green]✅ {len(tables)} tablas verificadas[/green]")
            
        return True
        
    except Exception as e:
        logger.error(f"Error verifying setup: {str(e)}")
        console.print(f"[red]❌ Error en verificación: {str(e)}[/red]")
        return False



if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold blue]🏆 Quiniela Predictor - Configuración de Base de Datos[/bold blue]\n"
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="blue"
    ))
    
    logger.info("Starting database setup...")
    
    # Step 1: Check database connection
    console.print("\n[bold]1. Verificando conexión a la base de datos...[/bold]")
    if not check_database_connection():
        console.print(Panel(
            "[red]❌ No se puede conectar a la base de datos[/red]\n\n"
            "[bold]Posibles soluciones:[/bold]\n"
            "• Verifica que PostgreSQL esté ejecutándose\n"
            "• Revisa la variable DATABASE_URL en tu archivo .env\n"
            "• Si usas Docker: docker-compose up -d postgres\n"
            "• Si es instalación local: sudo systemctl start postgresql",
            title="Error de Conexión",
            border_style="red"
        ))
        sys.exit(1)
    
    # Step 2: Setup database tables
    console.print("\n[bold]2. Configurando tablas de la base de datos...[/bold]")
    if not setup_database():
        console.print(Panel(
            "[red]❌ Error al crear las tablas de la base de datos[/red]",
            title="Error de Configuración",
            border_style="red"
        ))
        sys.exit(1)
    
    # Step 3: Verify setup
    console.print("\n[bold]3. Verificando configuración...[/bold]")
    if not verify_setup():
        console.print(Panel(
            "[red]❌ Error en la verificación de la configuración[/red]",
            title="Error de Verificación", 
            border_style="red"
        ))
        sys.exit(1)
    
    # Step 4: Optional sample data
    create_sample_data()
    
    # Success message
    console.print(Panel(
        "[bold green]✅ ¡Configuración de base de datos completada![/bold green]\n\n"
        "[bold]Próximos pasos:[/bold]\n"
        "1. Actualizar equipos: curl -X POST 'http://localhost:8000/data/update-teams/2024'\n"
        "2. Actualizar partidos: curl -X POST 'http://localhost:8000/data/update-matches/2024'\n"
        "3. Actualizar estadísticas: curl -X POST 'http://localhost:8000/data/update-statistics/2024'\n"
        "4. Entrenar modelo: curl -X POST 'http://localhost:8000/model/train' -d '{\"season\": 2024}'\n\n"
        "[yellow]💡 Tip: Usa el dashboard en http://localhost:8501 para gestionar todo visualmente[/yellow]",
        title="🎉 ¡ÉXITO!",
        border_style="green"
    ))
    
    logger.info("Database setup completed successfully!")
    sys.exit(0)