from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from ....database.database import get_db
from ....domain.entities.team import Team
from ....domain.entities.match import Match
from ....domain.entities.statistics import TeamStatistics
from ....services_v2.team_service import TeamService
from ....services_v2.match_service import MatchService
from ....services_v2.statistics_service import StatisticsService
from ....domain.schemas.team import TeamResponse
from ....domain.schemas.statistics import TeamStatisticsResponse
from ....domain.schemas.match import MatchResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/update-teams/{season}")
async def update_teams(season: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Update teams data for both La Liga and Segunda División"""
    try:
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Verificar si hay datos existentes para esta temporada
        existing_matches = db.query(Match).filter(Match.season == season).count()
        
        # Si es temporada futura o temporada actual sin datos (y es antes de agosto)
        season_likely_not_started = (
            season > current_year or 
            (season == current_year and existing_matches == 0 and current_month < 8)
        )
        
        if season_likely_not_started:
            return {
                "message": f"Season {season} has not started yet. No teams data available to update.",
                "warning": f"Current date: {datetime.now().strftime('%Y-%m')}. Season {season} appears not to have started.",
                "recommendation": f"Try updating season {current_year - 1} which has complete data."
            }
        
        team_service = TeamService(db)
        background_tasks.add_task(team_service.update_teams, season)
        return {"message": f"Teams update started for season {season}"}
    except Exception as e:
        logger.error(f"Error updating teams: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-matches/{season}")
async def update_matches(
    season: int, 
    background_tasks: BackgroundTasks,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update matches data for both leagues"""
    try:
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Verificar si ya hay datos para esta temporada (validación más inteligente)
        existing_matches = db.query(Match).filter(Match.season == season).count()
        logger.info(f"Season validation - Season: {season}, Current year: {current_year}, Existing matches: {existing_matches}")
        
        # Si es una temporada futura o no hay datos existentes, es probable que no haya empezado
        season_likely_not_started = (
            season > current_year or 
            (season == current_year and existing_matches == 0 and current_month < 8)
        )
        
        logger.info(f"Season likely not started: {season_likely_not_started}")
        
        if season_likely_not_started:
            return {
                "message": f"Season {season} appears to have not started yet. No matches available to update.",
                "warning": f"Current date: {datetime.now().strftime('%Y-%m')}. No existing matches found for season {season}.",
                "recommendation": f"Try updating season {current_year - 1} which has complete data."
            }
        
        match_service = MatchService(db)
        background_tasks.add_task(match_service.update_matches, season, from_date, to_date)
        return {"message": f"Matches update started for season {season}"}
    except Exception as e:
        logger.error(f"Error updating matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-statistics/{season}")
async def update_statistics(season: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Update team statistics"""
    try:
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Verificar si ya hay datos para esta temporada (validación más inteligente)
        existing_matches = db.query(Match).filter(Match.season == season).count()
        
        # Si es una temporada futura o no hay datos existentes, es probable que no haya empezado
        season_likely_not_started = (
            season > current_year or 
            (season == current_year and existing_matches == 0 and current_month < 8)
        )
        
        if season_likely_not_started:
            return {
                "message": f"Season {season} appears to have not started yet. No statistics available to update.",
                "warning": f"Current date: {datetime.now().strftime('%Y-%m')}. No existing matches found for season {season}.",
                "recommendation": f"Try updating season {current_year - 1} which has complete data."
            }
        
        # Verificar si hay partidos suficientes para generar estadísticas
        matches_count = db.query(Match).filter(Match.season == season).count()
        if matches_count == 0:
            return {
                "message": f"No matches found for season {season}. Cannot update statistics.",
                "warning": "Statistics need matches data first.",
                "recommendation": f"Update matches for season {season} first, or try season {current_year - 1}."
            }
        
        statistics_service = StatisticsService(db)
        background_tasks.add_task(statistics_service.update_team_statistics, season)
        return {"message": f"Statistics update started for season {season}"}
    except Exception as e:
        logger.error(f"Error updating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{season}")
async def get_data_status(season: int, db: Session = Depends(get_db)):
    """Get current status of data for a season"""
    try:
        # Count teams
        teams_count = db.query(Team).count()
        
        # Count matches for the season
        matches_count = db.query(Match).filter(Match.season == season).count()
        matches_with_results = db.query(Match).filter(
            Match.season == season,
            Match.result.isnot(None)
        ).count()
        
        # Count team statistics for the season
        stats_count = db.query(TeamStatistics).filter(TeamStatistics.season == season).count()
        
        # Get latest update timestamps
        latest_match = db.query(Match).filter(Match.season == season).order_by(Match.created_at.desc()).first()
        latest_stats = db.query(TeamStatistics).filter(TeamStatistics.season == season).order_by(TeamStatistics.updated_at.desc()).first()
        
        return {
            "season": season,
            "teams_total": teams_count,
            "matches_total": matches_count,
            "matches_with_results": matches_with_results,
            "team_statistics_total": stats_count,
            "last_match_update": latest_match.created_at.isoformat() if latest_match else None,
            "last_stats_update": latest_stats.updated_at.isoformat() if latest_stats else None,
            "teams_expected": 42,  # 20 La Liga + 22 Segunda División
            "matches_expected_per_season": 798,  # La Liga: 380 + Segunda: 418 = 798
            "stats_expected": 42  # Una entrada por equipo
        }
        
    except Exception as e:
        logger.error(f"Error getting data status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/", response_model=List[TeamResponse])
async def get_teams(league_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all teams, optionally filtered by league"""
    query = db.query(Team)
    if league_id:
        query = query.filter(Team.league_id == league_id)
    teams = query.all()
    return teams


@router.get("/teams/{team_id}/statistics", response_model=TeamStatisticsResponse)
async def get_team_statistics(team_id: int, season: int, db: Session = Depends(get_db)):
    """Get statistics for a specific team and season"""
    stats = db.query(TeamStatistics).filter_by(team_id=team_id, season=season).first()
    if not stats:
        raise HTTPException(status_code=404, detail="Statistics not found")
    return stats


@router.get("/matches/", response_model=List[MatchResponse])
async def get_matches(
    season: int,
    league_id: Optional[int] = None,
    team_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get matches with optional filters"""
    query = db.query(Match).filter(Match.season == season)
    
    if league_id:
        query = query.filter(Match.league_id == league_id)
    
    if team_id:
        query = query.filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        )
    
    matches = query.order_by(Match.match_date.desc()).limit(limit).all()
    return matches


@router.delete("/clear-statistics")
async def clear_statistics(season: Optional[int] = None, db: Session = Depends(get_db)):
    """Clear team statistics for debugging/testing"""
    try:
        if season:
            # Clear only for specific season
            deleted = db.query(TeamStatistics).filter(TeamStatistics.season == season).delete()
            db.commit()
            return {"message": f"Cleared {deleted} statistics entries for season {season}"}
        else:
            # Clear all statistics
            deleted = db.query(TeamStatistics).delete()
            db.commit()
            return {"message": f"Cleared all {deleted} statistics entries"}
    except Exception as e:
        logger.error(f"Error clearing statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))