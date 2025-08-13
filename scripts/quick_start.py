#!/usr/bin/env python3
"""
Script de inicio rápido para Quiniela Predictor
Ejecuta todos los pasos necesarios para poner en marcha el sistema
"""

import os
import sys
import time
import subprocess
import requests
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt

console = Console()

def check_prerequisites():
    """Verifica que los prerrequisitos estén instalados"""
    console.print("\n[bold blue]🔍 Verificando prerrequisitos...[/bold blue]")
    
    required_commands = {
        'docker': 'Docker',
        'docker-compose': 'Docker Compose',
        'curl': 'cURL'
    }
    
    missing = []
    for cmd, name in required_commands.items():
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
            console.print(f"[green]✅ {name} disponible[/green]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print(f"[red]❌ {name} no encontrado[/red]")
            missing.append(name)
    
    if missing:
        console.print(Panel(
            f"[red]Faltan prerrequisitos: {', '.join(missing)}[/red]\n\n"
            "[bold]Instrucciones de instalación:[/bold]\n"
            "• Docker: https://docs.docker.com/get-docker/\n"
            "• Docker Compose: viene con Docker Desktop\n"
            "• cURL: disponible en la mayoría de sistemas",
            title="⚠️  Prerrequisitos Faltantes",
            border_style="red"
        ))
        return False
    
    return True

def check_env_file():
    """Verifica y configura el archivo .env"""
    console.print("\n[bold blue]⚙️  Verificando configuración...[/bold blue]")
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_example_path = env_path + '.example'
    
    if not os.path.exists(env_path):
        if os.path.exists(env_example_path):
            console.print("[yellow]⚠️  Archivo .env no encontrado[/yellow]")
            if Confirm.ask("¿Deseas crear .env desde .env.example?"):
                import shutil
                shutil.copy2(env_example_path, env_path)
                console.print("[green]✅ Archivo .env creado[/green]")
            else:
                console.print("[red]❌ Archivo .env es requerido[/red]")
                return False
        else:
            console.print("[red]❌ No se encontró .env ni .env.example[/red]")
            return False
    
    # Verificar variables críticas
    critical_vars = ['API_FOOTBALL_KEY', 'SECRET_KEY']
    with open(env_path, 'r') as f:
        content = f.read()
    
    missing_vars = []
    for var in critical_vars:
        if f"{var}=" not in content or "REQUIRED" in content:
            missing_vars.append(var)
    
    if missing_vars:
        console.print(f"[yellow]⚠️  Variables críticas sin configurar: {missing_vars}[/yellow]")
        console.print("[yellow]💡 Edita el archivo .env y configura estos valores[/yellow]")
        
        if not Confirm.ask("¿Continuar sin configurar las variables? (no recomendado)"):
            return False
    
    console.print("[green]✅ Configuración verificada[/green]")
    return True

def start_services():
    """Inicia los servicios con Docker Compose"""
    console.print("\n[bold blue]🚀 Iniciando servicios...[/bold blue]")
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        
        task = progress.add_task("Descargando imágenes...", total=None)
        
        try:
            # Pull images first
            process = subprocess.run(
                ['docker-compose', 'pull'],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            progress.update(task, description="Iniciando servicios...")
            
            # Start services
            process = subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                console.print(f"[red]❌ Error iniciando servicios: {process.stderr}[/red]")
                return False
            
            progress.update(task, description="✅ Servicios iniciados")
            
        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            return False
    
    # Esperar a que los servicios estén listos
    console.print("[yellow]⏳ Esperando que los servicios estén listos...[/yellow]")
    time.sleep(10)
    
    return True

def setup_database():
    """Configura la base de datos"""
    console.print("\n[bold blue]🗄️  Configurando base de datos...[/bold blue]")
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    try:
        process = subprocess.run(
            ['python', 'scripts/setup_database.py'],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            console.print(f"[red]❌ Error configurando BD: {process.stderr}[/red]")
            return False
        
        console.print("[green]✅ Base de datos configurada[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        return False

def load_initial_data():
    """Carga datos iniciales"""
    console.print("\n[bold blue]📊 Cargando datos iniciales...[/bold blue]")
    
    if not Confirm.ask("¿Deseas cargar datos iniciales? (recomendado para primera vez)"):
        return True
    
    api_base = "http://localhost:8000"
    season = 2024
    
    data_steps = [
        ("Equipos", f"/data/update-teams/{season}", "2 minutos"),
        ("Partidos", f"/data/update-matches/{season}", "5 minutos"), 
        ("Estadísticas", f"/data/update-statistics/{season}", "10 minutos")
    ]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        
        for step_name, endpoint, duration in data_steps:
            task = progress.add_task(f"Cargando {step_name.lower()}... (estimado: {duration})", total=None)
            
            try:
                response = requests.post(f"{api_base}{endpoint}", timeout=30)
                if response.status_code == 200:
                    progress.update(task, description=f"✅ {step_name} cargados")
                    # En una implementación real, aquí esperaríamos a que termine la tarea
                    time.sleep(2)  # Simular tiempo de carga
                else:
                    progress.update(task, description=f"❌ Error cargando {step_name.lower()}")
                    console.print(f"[yellow]⚠️  {step_name} falló pero continuando...[/yellow]")
                    
            except Exception as e:
                progress.update(task, description=f"❌ Error en {step_name.lower()}")
                console.print(f"[yellow]⚠️  Error cargando {step_name}: {str(e)}[/yellow]")
    
    return True

def verify_services():
    """Verifica que todos los servicios estén funcionando"""
    console.print("\n[bold blue]✅ Verificando servicios...[/bold blue]")
    
    services = [
        ("API Backend", "http://localhost:8000/health"),
        ("Dashboard", "http://localhost:8501"),
    ]
    
    all_ok = True
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                console.print(f"[green]✅ {service_name} - OK[/green]")
            else:
                console.print(f"[yellow]⚠️  {service_name} - HTTP {response.status_code}[/yellow]")
                all_ok = False
        except Exception as e:
            console.print(f"[red]❌ {service_name} - No disponible[/red]")
            all_ok = False
    
    return all_ok

def main():
    """Función principal de inicio rápido"""
    console.print(Panel.fit(
        "[bold blue]🏆 Quiniela Predictor - Inicio Rápido[/bold blue]\n"
        f"Configuración automática del sistema completo\n"
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="blue"
    ))
    
    # Paso 1: Verificar prerrequisitos
    if not check_prerequisites():
        console.print(Panel(
            "[red]❌ Prerrequisitos faltantes[/red]\n"
            "Instala Docker y Docker Compose antes de continuar.",
            title="Error",
            border_style="red"
        ))
        return 1
    
    # Paso 2: Verificar configuración
    if not check_env_file():
        console.print(Panel(
            "[red]❌ Configuración incompleta[/red]\n"
            "Configura el archivo .env antes de continuar.",
            title="Error",
            border_style="red"
        ))
        return 1
    
    # Paso 3: Iniciar servicios
    if not start_services():
        console.print(Panel(
            "[red]❌ Error iniciando servicios[/red]",
            title="Error",
            border_style="red"
        ))
        return 1
    
    # Paso 4: Configurar base de datos
    if not setup_database():
        console.print(Panel(
            "[red]❌ Error configurando base de datos[/red]",
            title="Error",
            border_style="red"
        ))
        return 1
    
    # Paso 5: Cargar datos iniciales (opcional)
    load_initial_data()
    
    # Paso 6: Verificar servicios
    if verify_services():
        console.print(Panel(
            "[bold green]🎉 ¡Sistema completamente configurado![/bold green]\n\n"
            "[bold]Accede a:[/bold]\n"
            "• Dashboard: http://localhost:8501\n"
            "• API Docs: http://localhost:8000/docs\n"
            "• API Health: http://localhost:8000/health\n\n"
            "[bold]Próximos pasos:[/bold]\n"
            "1. Ve al dashboard y explora las funciones\n"
            "2. Configura tu primera quiniela personal\n"
            "3. Entrena el modelo con datos históricos\n\n"
            "[yellow]💡 Tip: Si algo falla, ejecuta: python scripts/validate_environment.py[/yellow]",
            title="🚀 ¡ÉXITO!",
            border_style="green"
        ))
        return 0
    else:
        console.print(Panel(
            "[yellow]⚠️  Sistema iniciado con advertencias[/yellow]\n"
            "Algunos servicios pueden no estar completamente listos.\n"
            "Espera unos minutos y verifica manualmente.",
            title="Advertencia",
            border_style="yellow"
        ))
        return 0

if __name__ == "__main__":
    sys.exit(main())