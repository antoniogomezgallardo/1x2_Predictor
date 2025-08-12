#!/usr/bin/env python3
"""
Script to run weekly predictions for the Spanish Quiniela
Can be scheduled to run automatically each week
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from backend.app.database.database import SessionLocal
from backend.app.services.data_extractor import DataExtractor
from backend.app.ml.predictor import QuinielaPredictor
from backend.app.database.models import QuinielaPrediction, QuinielaWeek, Match
from backend.app.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_weekly_predictions(season: int, week_number: int = None):
    """Run predictions for a specific week"""
    db = SessionLocal()
    
    try:
        logger.info(f"Starting predictions for season {season}")
        
        # Initialize services
        extractor = DataExtractor(db)
        predictor = QuinielaPredictor()
        
        # Load trained model
        model_path = f"data/models/quiniela_model_{season}.joblib"
        if os.path.exists(model_path):
            predictor.load_model(model_path)
            logger.info(f"Loaded model from {model_path}")
        else:
            logger.error(f"No trained model found at {model_path}")
            return False
        
        # Get current week data
        logger.info("Fetching current week match data...")
        quiniela_data = await extractor.get_quiniela_data(season, week_number)
        
        if not quiniela_data:
            logger.error("No matches found for current week")
            return False
        
        logger.info(f"Found {len(quiniela_data)} matches for prediction")
        
        # Make predictions
        predictions = predictor.predict_quiniela(quiniela_data)
        
        # Determine week number if not provided
        if week_number is None:
            # Try to determine from match data or use current week logic
            week_number = datetime.now().isocalendar()[1]  # ISO week number
        
        # Save predictions to database
        logger.info("Saving predictions to database...")
        
        # Create or get quiniela week record
        quiniela_week = db.query(QuinielaWeek).filter_by(
            season=season, week_number=week_number
        ).first()
        
        if not quiniela_week:
            quiniela_week = QuinielaWeek(
                season=season,
                week_number=week_number,
                submission_date=datetime.utcnow()
            )
            db.add(quiniela_week)
            db.commit()
        
        # Save individual predictions
        for prediction in predictions:
            # Find corresponding match in database
            match = db.query(Match).filter_by(
                api_id=prediction.get('fixture_id')  # This would come from match data
            ).first()
            
            if not match:
                logger.warning(f"Match not found for prediction {prediction['match_number']}")
                continue
            
            # Check if prediction already exists
            existing_prediction = db.query(QuinielaPrediction).filter_by(
                week_number=week_number,
                season=season,
                match_id=match.id
            ).first()
            
            if existing_prediction:
                # Update existing prediction
                existing_prediction.predicted_result = prediction['predicted_result']
                existing_prediction.confidence = prediction['confidence']
                existing_prediction.home_probability = prediction['probabilities']['home_win']
                existing_prediction.draw_probability = prediction['probabilities']['draw']
                existing_prediction.away_probability = prediction['probabilities']['away_win']
                existing_prediction.model_features = prediction.get('features_used', {})
                existing_prediction.model_version = prediction.get('model_version')
            else:
                # Create new prediction
                new_prediction = QuinielaPrediction(
                    week_number=week_number,
                    season=season,
                    match_id=match.id,
                    predicted_result=prediction['predicted_result'],
                    confidence=prediction['confidence'],
                    home_probability=prediction['probabilities']['home_win'],
                    draw_probability=prediction['probabilities']['draw'],
                    away_probability=prediction['probabilities']['away_win'],
                    model_features=prediction.get('features_used', {}),
                    model_version=prediction.get('model_version')
                )
                db.add(new_prediction)
        
        db.commit()
        
        # Calculate betting strategy
        betting_strategy = predictor.calculate_betting_strategy(
            predictions, 
            settings.initial_bankroll,
            settings.max_bet_percentage
        )
        
        # Update quiniela week with betting info
        quiniela_week.bet_amount = betting_strategy['total_stake']
        quiniela_week.total_predictions = len(predictions)
        db.commit()
        
        # Print summary
        logger.info("=" * 50)
        logger.info("PREDICCIONES GENERADAS")
        logger.info("=" * 50)
        logger.info(f"Temporada: {season}")
        logger.info(f"Jornada: {week_number}")
        logger.info(f"Total partidos: {len(predictions)}")
        
        for prediction in predictions:
            confidence_emoji = "🟢" if prediction['confidence'] > 0.7 else "🟡" if prediction['confidence'] > 0.5 else "🔴"
            logger.info(f"{prediction['match_number']:2d}. {prediction['home_team']} vs {prediction['away_team']}: "
                       f"{prediction['predicted_result']} {confidence_emoji} ({prediction['confidence']:.1%})")
        
        logger.info("=" * 50)
        logger.info("ESTRATEGIA DE APUESTAS")
        logger.info("=" * 50)
        logger.info(f"Apuesta total recomendada: €{betting_strategy['total_stake']:.2f}")
        logger.info(f"Número de apuestas: {betting_strategy['number_of_bets']}")
        logger.info(f"Porcentaje del bankroll: {betting_strategy['percentage_of_bankroll']:.1f}%")
        
        if betting_strategy['recommended_bets']:
            logger.info("\nApuestas específicas recomendadas:")
            for bet in betting_strategy['recommended_bets']:
                logger.info(f"  {bet['home_team']} vs {bet['away_team']}: "
                           f"{bet['predicted_result']} - €{bet['recommended_bet']:.2f} "
                           f"(confianza: {bet['confidence']:.1%})")
        
        logger.info("Predicciones guardadas exitosamente!")
        return True
        
    except Exception as e:
        logger.error(f"Error running predictions: {str(e)}")
        db.rollback()
        return False
    
    finally:
        db.close()


async def update_results(season: int, week_number: int):
    """Update actual results for completed matches"""
    db = SessionLocal()
    
    try:
        logger.info(f"Updating results for season {season}, week {week_number}")
        
        # Get predictions for the week
        predictions = db.query(QuinielaPrediction).filter_by(
            season=season, week_number=week_number
        ).all()
        
        correct_predictions = 0
        total_predictions = len(predictions)
        
        for prediction in predictions:
            match = prediction.match
            
            if match.result:  # If match has a result
                prediction.actual_result = match.result
                prediction.is_correct = (prediction.predicted_result == match.result)
                
                if prediction.is_correct:
                    correct_predictions += 1
        
        # Update week summary
        quiniela_week = db.query(QuinielaWeek).filter_by(
            season=season, week_number=week_number
        ).first()
        
        if quiniela_week:
            quiniela_week.correct_predictions = correct_predictions
            quiniela_week.accuracy_percentage = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
            quiniela_week.is_completed = True
            quiniela_week.results_date = datetime.utcnow()
            
            # Calculate actual winnings (simplified - would need actual betting logic)
            # For now, assume a basic calculation
            base_winning = 100  # Base winning amount for getting all correct
            quiniela_week.actual_winnings = base_winning * (correct_predictions / 15) if correct_predictions >= 10 else 0
            quiniela_week.profit_loss = quiniela_week.actual_winnings - quiniela_week.bet_amount
        
        db.commit()
        
        logger.info(f"Results updated: {correct_predictions}/{total_predictions} correct predictions")
        logger.info(f"Accuracy: {(correct_predictions / total_predictions * 100):.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating results: {str(e)}")
        db.rollback()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Quiniela predictions')
    parser.add_argument('--season', type=int, default=2024, help='Season year')
    parser.add_argument('--week', type=int, help='Week number (optional)')
    parser.add_argument('--update-results', action='store_true', help='Update results for completed matches')
    
    args = parser.parse_args()
    
    if args.update_results:
        if not args.week:
            logger.error("Week number required when updating results")
            sys.exit(1)
        
        success = asyncio.run(update_results(args.season, args.week))
    else:
        success = asyncio.run(run_weekly_predictions(args.season, args.week))
    
    if not success:
        sys.exit(1)