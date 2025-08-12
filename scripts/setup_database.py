#!/usr/bin/env python3
"""
Database setup script for Quiniela Predictor
Creates database tables and performs initial setup
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database.database import create_tables, engine
from backend.app.database.models import Base
from backend.app.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """Set up the database with all required tables"""
    try:
        logger.info("Creating database tables...")
        
        # Import all models to ensure they're registered
        from backend.app.database.models import (
            Team, Match, TeamStatistics, QuinielaPrediction, 
            QuinielaWeek, ModelPerformance
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully!")
        logger.info(f"Connected to database: {settings.database_url}")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info("Created tables:")
        for table in tables:
            logger.info(f"  - {table}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False


def check_database_connection():
    """Check if database connection is working"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("Starting database setup...")
    
    # Check connection first
    if not check_database_connection():
        logger.error("Cannot connect to database. Please check your configuration.")
        sys.exit(1)
    
    # Setup database
    if setup_database():
        logger.info("Database setup completed successfully!")
    else:
        logger.error("Database setup failed!")
        sys.exit(1)