#!/usr/bin/env python3
"""
Migración de Base de Datos v2.1.0
Añade soporte para dobles, triples y Elige 8 manteniendo compatibilidad

Autor: Sistema 1x2_Predictor
Fecha: 15 Agosto 2025
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.database.connection import get_db
from backend.app.database.models import Base, engine
from sqlalchemy import text, inspect, Column, String, Integer, Float, Boolean, JSON
from sqlalchemy.exc import OperationalError, ProgrammingError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Migrador de base de datos con rollback automático"""
    
    def __init__(self):
        self.db = next(get_db())
        self.inspector = inspect(engine)
        self.backup_tables = []
        
    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Verificar si una columna existe en la tabla"""
        try:
            columns = self.inspector.get_columns(table_name)
            return any(col['name'] == column_name for col in columns)
        except Exception as e:
            logger.warning(f"No se pudo verificar columna {column_name} en {table_name}: {e}")
            return False
    
    def backup_critical_data(self):
        """Crear backup de datos críticos antes de migración"""
        logger.info("🔄 Creando backup de datos críticos...")
        
        try:
            # Backup de quinielas de usuario
            result = self.db.execute(text("SELECT COUNT(*) FROM user_quinielas"))
            user_quinielas_count = result.scalar()
            
            result = self.db.execute(text("SELECT COUNT(*) FROM user_quiniela_predictions"))
            predictions_count = result.scalar()
            
            logger.info(f"📊 Datos a preservar:")
            logger.info(f"   • Quinielas de usuario: {user_quinielas_count}")
            logger.info(f"   • Predicciones: {predictions_count}")
            
            # Crear tabla temporal de backup si hay datos importantes
            if user_quinielas_count > 0:
                self.db.execute(text("""
                    CREATE TABLE IF NOT EXISTS backup_user_quinielas_v2_1_0 AS 
                    SELECT * FROM user_quinielas
                """))
                logger.info("✅ Backup de user_quinielas creado")
            
            if predictions_count > 0:
                self.db.execute(text("""
                    CREATE TABLE IF NOT EXISTS backup_user_quiniela_predictions_v2_1_0 AS 
                    SELECT * FROM user_quiniela_predictions
                """))
                logger.info("✅ Backup de predicciones creado")
                
            self.db.commit()
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            self.db.rollback()
            raise
    
    def add_column_if_not_exists(self, table_name: str, column_definition: str):
        """Añadir columna si no existe"""
        column_name = column_definition.split()[0]
        
        if not self.check_column_exists(table_name, column_name):
            try:
                logger.info(f"➕ Añadiendo columna {column_name} a {table_name}")
                self.db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}"))
                logger.info(f"✅ Columna {column_name} añadida exitosamente")
            except Exception as e:
                logger.error(f"❌ Error añadiendo columna {column_name}: {e}")
                raise
        else:
            logger.info(f"ℹ️ Columna {column_name} ya existe en {table_name}")
    
    def migrate_user_quinielas(self):
        """Migrar tabla user_quinielas para soporte dobles/triples/Elige8"""
        logger.info("🔄 Migrando tabla user_quinielas...")
        
        # Nuevas columnas para sistema de dobles y triples
        new_columns = [
            "bet_type VARCHAR(20) DEFAULT 'simple'",
            "total_combinations INTEGER DEFAULT 1",
            "base_cost FLOAT DEFAULT 0.75",
            
            # Campos para Elige 8
            "elige_8_enabled BOOLEAN DEFAULT FALSE",
            "elige_8_matches JSON",
            "elige_8_cost FLOAT DEFAULT 0.0",
            "elige_8_predictions JSON"
        ]
        
        for column_def in new_columns:
            self.add_column_if_not_exists("user_quinielas", column_def)
        
        # Actualizar datos existentes con valores por defecto
        try:
            logger.info("🔄 Actualizando quinielas existentes con valores por defecto...")
            
            # Calcular costo base correcto para quinielas existentes
            self.db.execute(text("""
                UPDATE user_quinielas 
                SET 
                    bet_type = 'simple',
                    total_combinations = 1,
                    base_cost = COALESCE(cost, 0.75),
                    elige_8_enabled = FALSE,
                    elige_8_cost = 0.0
                WHERE bet_type IS NULL
            """))
            
            updated_rows = self.db.rowcount
            logger.info(f"✅ {updated_rows} quinielas existentes actualizadas")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando datos existentes: {e}")
            raise
    
    def migrate_user_quiniela_predictions(self):
        """Migrar tabla user_quiniela_predictions para soporte múltiple"""
        logger.info("🔄 Migrando tabla user_quiniela_predictions...")
        
        # Nuevas columnas para predicciones múltiples
        new_columns = [
            "multiplicity INTEGER DEFAULT 1",
            "prediction_options JSON"
        ]
        
        for column_def in new_columns:
            self.add_column_if_not_exists("user_quiniela_predictions", column_def)
        
        # Convertir predicciones existentes al nuevo formato
        try:
            logger.info("🔄 Convirtiendo predicciones existentes al nuevo formato...")
            
            self.db.execute(text("""
                UPDATE user_quiniela_predictions 
                SET 
                    multiplicity = 1,
                    prediction_options = JSON_ARRAY(user_prediction)
                WHERE multiplicity IS NULL AND user_prediction IS NOT NULL
            """))
            
            updated_rows = self.db.rowcount
            logger.info(f"✅ {updated_rows} predicciones convertidas al nuevo formato")
            
        except Exception as e:
            logger.error(f"❌ Error convirtiendo predicciones: {e}")
            raise
    
    def verify_migration(self):
        """Verificar que la migración fue exitosa"""
        logger.info("🔍 Verificando migración...")
        
        # Verificar columnas de user_quinielas
        required_columns = [
            'bet_type', 'total_combinations', 'base_cost',
            'elige_8_enabled', 'elige_8_matches', 'elige_8_cost', 'elige_8_predictions'
        ]
        
        for column in required_columns:
            if not self.check_column_exists('user_quinielas', column):
                raise Exception(f"Migración fallida: columna {column} no existe en user_quinielas")
        
        # Verificar columnas de user_quiniela_predictions
        prediction_columns = ['multiplicity', 'prediction_options']
        
        for column in prediction_columns:
            if not self.check_column_exists('user_quiniela_predictions', column):
                raise Exception(f"Migración fallida: columna {column} no existe en user_quiniela_predictions")
        
        # Verificar integridad de datos
        try:
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM user_quinielas 
                WHERE bet_type IS NULL OR total_combinations IS NULL
            """))
            null_count = result.scalar()
            
            if null_count > 0:
                raise Exception(f"Migración fallida: {null_count} registros con datos nulos")
            
            logger.info("✅ Verificación de migración exitosa")
            
        except Exception as e:
            logger.error(f"❌ Error en verificación: {e}")
            raise
    
    def cleanup_backup_tables(self):
        """Limpiar tablas de backup después de migración exitosa"""
        logger.info("🧹 Limpiando tablas de backup...")
        
        try:
            # Solo limpiar si la migración fue completamente exitosa
            backup_tables = [
                'backup_user_quinielas_v2_1_0',
                'backup_user_quiniela_predictions_v2_1_0'
            ]
            
            for table in backup_tables:
                try:
                    self.db.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    logger.info(f"🗑️ Tabla backup {table} eliminada")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo eliminar tabla backup {table}: {e}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error limpiando backups: {e}")
    
    def rollback_migration(self):
        """Rollback en caso de error crítico"""
        logger.error("🔄 Ejecutando rollback de migración...")
        
        try:
            self.db.rollback()
            logger.info("✅ Rollback de transacción completado")
            
            # Informar sobre tablas de backup disponibles
            logger.info("📦 Tablas de backup disponibles para restauración manual:")
            logger.info("   • backup_user_quinielas_v2_1_0")
            logger.info("   • backup_user_quiniela_predictions_v2_1_0")
            
        except Exception as e:
            logger.error(f"❌ Error en rollback: {e}")
    
    def run_migration(self):
        """Ejecutar migración completa"""
        logger.info("🚀 Iniciando migración de base de datos v2.1.0")
        logger.info("📋 Añadiendo soporte para dobles, triples y Elige 8")
        
        try:
            # Paso 1: Backup de datos críticos
            self.backup_critical_data()
            
            # Paso 2: Migrar user_quinielas
            self.migrate_user_quinielas()
            
            # Paso 3: Migrar user_quiniela_predictions
            self.migrate_user_quiniela_predictions()
            
            # Paso 4: Commit de cambios
            self.db.commit()
            logger.info("💾 Cambios guardados en base de datos")
            
            # Paso 5: Verificar migración
            self.verify_migration()
            
            # Paso 6: Limpiar backups (opcional)
            # self.cleanup_backup_tables()  # Comentado para mantener backups por seguridad
            
            logger.info("🎉 Migración v2.1.0 completada exitosamente")
            logger.info("✅ Sistema listo para dobles, triples y Elige 8")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en migración: {e}")
            self.rollback_migration()
            return False
        
        finally:
            self.db.close()


def main():
    """Función principal para ejecutar migración"""
    print("🎯 Migración Base de Datos v2.1.0 - Dobles, Triples y Elige 8")
    print("=" * 60)
    
    try:
        # Verificar conexión a base de datos
        logger.info("🔌 Verificando conexión a base de datos...")
        migrator = DatabaseMigrator()
        logger.info("✅ Conexión establecida correctamente")
        
        # Mostrar información del estado actual
        logger.info("📊 Analizando estado actual de la base de datos...")
        
        # Ejecutar migración
        success = migrator.run_migration()
        
        if success:
            print("\n🎉 ¡MIGRACIÓN EXITOSA!")
            print("✅ Base de datos actualizada a v2.1.0")
            print("🚀 Sistema listo para usar dobles, triples y Elige 8")
            print("\n📋 Próximos pasos:")
            print("   1. Implementar endpoints API para dobles/triples")
            print("   2. Desarrollar interfaz dashboard")
            print("   3. Testing completo del sistema")
            return 0
        else:
            print("\n❌ MIGRACIÓN FALLIDA")
            print("🔄 Se ha ejecutado rollback automático")
            print("📦 Tablas de backup disponibles para restauración manual")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Error crítico en migración: {e}")
        print(f"\n💥 Error crítico: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)