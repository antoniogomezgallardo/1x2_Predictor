from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import asyncio
import logging
import os
import io
from datetime import datetime
import pandas as pd

from ....database.database import get_db
from ....database.models import *
from ....services.advanced_data_collector import AdvancedDataCollector
from ....services.fbref_client import FBRefClient
from ....ml.enhanced_predictor import EnhancedQuinielaPredictor

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/collect/{season}")
async def collect_advanced_data(
    season: int,
    background_tasks: BackgroundTasks,
    league_ids: Optional[str] = "140,141",
    db: Session = Depends(get_db)
):
    """
    Initiate advanced data collection for state-of-the-art predictions
    Collects xG, xA, xT, PPDA, market intelligence, and external factors
    """
    try:
        # Parse league IDs
        leagues = [int(lid.strip()) for lid in league_ids.split(",")]
        
        def collect_data_task():
            try:
                logger.info(f"Starting advanced data collection for season {season}")
                collector = AdvancedDataCollector(db)
                
                # Run asynchronous collection
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    collector.collect_all_advanced_data(season, leagues)
                )
                loop.close()
                
                logger.info(f"Advanced data collection completed: {result}")
                
            except Exception as e:
                logger.error(f"Advanced data collection failed: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        background_tasks.add_task(collect_data_task)
        
        return {
            "message": "Advanced data collection started in background",
            "season": season,
            "leagues": leagues,
            "estimated_duration": "10-20 minutes",
            "status": "collection_started",
            "data_types": [
                "Advanced Team Statistics (xG, xA, xT, PPDA)",
                "Match Advanced Statistics",
                "Player Advanced Statistics",
                "Market Intelligence",
                "External Factors"
            ],
            "check_status": f"/advanced-data/status/{season}"
        }
        
    except Exception as e:
        logger.error(f"Error starting advanced data collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{season}")
async def get_advanced_data_status(season: int, db: Session = Depends(get_db)):
    """
    Get status of advanced data collection for a season
    """
    try:
        # Count advanced statistics data
        team_stats_count = db.query(AdvancedTeamStatistics).filter(
            AdvancedTeamStatistics.season == season
        ).count()
        
        match_stats_count = db.query(MatchAdvancedStatistics).join(Match).filter(
            Match.season == season
        ).count()
        
        player_stats_count = db.query(PlayerAdvancedStatistics).filter(
            PlayerAdvancedStatistics.season == season
        ).count()
        
        market_intel_count = db.query(MarketIntelligence).join(Match).filter(
            Match.season == season
        ).count()
        
        external_factors_count = db.query(ExternalFactors).join(Match).filter(
            Match.season == season
        ).count()
        
        # Get latest updates
        latest_team_stats = db.query(AdvancedTeamStatistics).filter(
            AdvancedTeamStatistics.season == season
        ).order_by(AdvancedTeamStatistics.last_updated.desc()).first()
        
        latest_match_stats = db.query(MatchAdvancedStatistics).join(Match).filter(
            Match.season == season
        ).order_by(MatchAdvancedStatistics.last_updated.desc()).first()
        
        # Expected counts
        total_teams = db.query(Team).count()
        total_matches = db.query(Match).filter(Match.season == season).count()
        
        return {
            "season": season,
            "collection_status": {
                "team_advanced_stats": {
                    "collected": team_stats_count,
                    "expected": total_teams,
                    "percentage": (team_stats_count / max(total_teams, 1)) * 100,
                    "last_updated": latest_team_stats.last_updated.isoformat() if latest_team_stats else None
                },
                "match_advanced_stats": {
                    "collected": match_stats_count,
                    "expected": total_matches,
                    "percentage": (match_stats_count / max(total_matches, 1)) * 100,
                    "last_updated": latest_match_stats.last_updated.isoformat() if latest_match_stats else None
                },
                "player_advanced_stats": {
                    "collected": player_stats_count,
                    "expected": total_teams * 3,  # 3 key players per team
                    "percentage": (player_stats_count / max(total_teams * 3, 1)) * 100
                },
                "market_intelligence": {
                    "collected": market_intel_count,
                    "expected": "upcoming_matches",
                    "description": "Market intelligence for upcoming matches"
                },
                "external_factors": {
                    "collected": external_factors_count,
                    "expected": "upcoming_matches",
                    "description": "Weather, injuries, motivation factors"
                }
            },
            "data_completeness": {
                "basic_ready": team_stats_count > 0,
                "advanced_ready": team_stats_count >= total_teams * 0.8,
                "state_of_art_ready": all([
                    team_stats_count >= total_teams * 0.8,
                    match_stats_count > 20,
                    player_stats_count > 0,
                    market_intel_count > 0
                ])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting advanced data status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-fbref")
async def test_fbref_connectivity():
    """
    Endpoint de diagnóstico para probar conectividad con FBRef
    """
    try:
        client = FBRefClient()
        
        # Probar conectividad con URLs simples
        test_results = {
            "fbref_connectivity": False,
            "la_liga_access": False,
            "segunda_access": False,
            "errors": [],
            "table_ids_found": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Test 1: La Liga
        try:
            la_liga_data = client.get_league_table_advanced(140, 2024)
            if la_liga_data:
                test_results["la_liga_access"] = True
                test_results["fbref_connectivity"] = True
            else:
                test_results["errors"].append("La Liga: No data returned")
        except Exception as e:
            test_results["errors"].append(f"La Liga error: {str(e)}")
        
        # Test 2: Segunda División  
        try:
            segunda_data = client.get_league_table_advanced(141, 2024)
            if segunda_data:
                test_results["segunda_access"] = True
                test_results["fbref_connectivity"] = True
            else:
                test_results["errors"].append("Segunda: No data returned")
        except Exception as e:
            test_results["errors"].append(f"Segunda error: {str(e)}")
        
        return test_results
        
    except Exception as e:
        logger.error(f"Error testing FBRef connectivity: {e}")
        return {
            "fbref_connectivity": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/team-stats/{team_id}")
async def get_team_advanced_stats(
    team_id: int,
    season: int,
    db: Session = Depends(get_db)
):
    """
    Get advanced statistics for a specific team
    """
    try:
        # Get basic team info
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get advanced statistics
        advanced_stats = db.query(AdvancedTeamStatistics).filter(
            AdvancedTeamStatistics.team_id == team_id,
            AdvancedTeamStatistics.season == season
        ).first()
        
        if not advanced_stats:
            return {
                "team_id": team_id,
                "team_name": team.name,
                "season": season,
                "has_advanced_stats": False,
                "message": "Advanced statistics not available for this team/season"
            }
        
        return {
            "team_id": team_id,
            "team_name": team.name,
            "season": season,
            "has_advanced_stats": True,
            "advanced_stats": {
                "expected_goals": {
                    "xg_for": advanced_stats.xg_for,
                    "xg_against": advanced_stats.xg_against,
                    "xg_net": advanced_stats.xg_for - advanced_stats.xg_against,
                    "xg_per_game": advanced_stats.xg_for / max(advanced_stats.matches_played, 1)
                },
                "expected_assists": {
                    "xa_for": advanced_stats.xa_for,
                    "xa_against": advanced_stats.xa_against,
                    "xa_net": advanced_stats.xa_for - advanced_stats.xa_against
                },
                "expected_threat": {
                    "xt_for": advanced_stats.xt_for,
                    "xt_against": advanced_stats.xt_against,
                    "xt_net": advanced_stats.xt_for - advanced_stats.xt_against
                },
                "defensive_actions": {
                    "ppda": advanced_stats.ppda,
                    "packing_rate": advanced_stats.packing_rate,
                    "progressive_distance": advanced_stats.progressive_distance
                }
            },
            "last_updated": advanced_stats.last_updated.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting team advanced stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match-stats/{match_id}")
async def get_match_advanced_stats(match_id: int, db: Session = Depends(get_db)):
    """
    Get advanced statistics for a specific match
    """
    try:
        # Get match info
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Get advanced match statistics
        match_stats = db.query(MatchAdvancedStatistics).filter(
            MatchAdvancedStatistics.match_id == match_id
        ).first()
        
        if not match_stats:
            return {
                "match_id": match_id,
                "home_team": match.home_team.name if match.home_team else "Unknown",
                "away_team": match.away_team.name if match.away_team else "Unknown",
                "has_advanced_stats": False,
                "message": "Advanced statistics not available for this match"
            }
        
        return {
            "match_id": match_id,
            "home_team": match.home_team.name if match.home_team else "Unknown",
            "away_team": match.away_team.name if match.away_team else "Unknown",
            "match_date": match.match_date.isoformat() if match.match_date else None,
            "has_advanced_stats": True,
            "advanced_stats": {
                "expected_goals": {
                    "home_xg": match_stats.home_xg,
                    "away_xg": match_stats.away_xg,
                    "total_xg": match_stats.home_xg + match_stats.away_xg
                },
                "expected_assists": {
                    "home_xa": match_stats.home_xa,
                    "away_xa": match_stats.away_xa
                },
                "expected_threat": {
                    "home_xt": match_stats.home_xt,
                    "away_xt": match_stats.away_xt
                },
                "defensive_metrics": {
                    "home_ppda": match_stats.home_ppda,
                    "away_ppda": match_stats.away_ppda
                },
                "quality_metrics": {
                    "shot_quality_home": match_stats.shot_quality_home,
                    "shot_quality_away": match_stats.shot_quality_away,
                    "chance_quality_home": match_stats.chance_quality_home,
                    "chance_quality_away": match_stats.chance_quality_away
                }
            },
            "last_updated": match_stats.last_updated.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting match advanced stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/league-rankings/{season}")
async def get_advanced_league_rankings(
    season: int,
    league_id: Optional[int] = None,
    metric: str = "xg_net",
    db: Session = Depends(get_db)
):
    """
    Get advanced league rankings based on different metrics
    """
    try:
        query = db.query(AdvancedTeamStatistics).join(Team).filter(
            AdvancedTeamStatistics.season == season
        )
        
        if league_id:
            query = query.filter(Team.league_id == league_id)
        
        teams_stats = query.all()
        
        if not teams_stats:
            return {
                "season": season,
                "league_id": league_id,
                "metric": metric,
                "rankings": [],
                "message": "No advanced statistics available for this season/league"
            }
        
        # Calculate metric values and sort
        rankings = []
        for stats in teams_stats:
            if metric == "xg_net":
                value = stats.xg_for - stats.xg_against
            elif metric == "xa_net":
                value = stats.xa_for - stats.xa_against
            elif metric == "xt_net":
                value = stats.xt_for - stats.xt_against
            elif metric == "ppda":
                value = stats.ppda
            else:
                value = getattr(stats, metric, 0)
            
            rankings.append({
                "team_id": stats.team_id,
                "team_name": stats.team.name,
                "league": "La Liga" if stats.team.league_id == 140 else "Segunda División",
                "metric_value": value,
                "matches_played": stats.matches_played
            })
        
        # Sort by metric (descending for most metrics, ascending for PPDA)
        reverse_sort = metric != "ppda"
        rankings.sort(key=lambda x: x["metric_value"], reverse=reverse_sort)
        
        # Add positions
        for i, team in enumerate(rankings):
            team["position"] = i + 1
        
        return {
            "season": season,
            "league_id": league_id,
            "metric": metric,
            "total_teams": len(rankings),
            "rankings": rankings
        }
        
    except Exception as e:
        logger.error(f"Error getting advanced league rankings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{season}")
async def export_advanced_data(
    season: int,
    format: str = "csv",
    data_type: str = "team_stats",
    db: Session = Depends(get_db)
):
    """
    Export advanced data in CSV/JSON format
    """
    try:
        if data_type == "team_stats":
            # Export team advanced statistics
            query = db.query(AdvancedTeamStatistics).join(Team).filter(
                AdvancedTeamStatistics.season == season
            )
            
            data = []
            for stats in query.all():
                data.append({
                    "team_name": stats.team.name,
                    "league": "La Liga" if stats.team.league_id == 140 else "Segunda División",
                    "season": season,
                    "matches_played": stats.matches_played,
                    "xg_for": stats.xg_for,
                    "xg_against": stats.xg_against,
                    "xa_for": stats.xa_for,
                    "xa_against": stats.xa_against,
                    "xt_for": stats.xt_for,
                    "xt_against": stats.xt_against,
                    "ppda": stats.ppda,
                    "packing_rate": stats.packing_rate,
                    "progressive_distance": stats.progressive_distance,
                    "last_updated": stats.last_updated.isoformat()
                })
            
        else:
            raise HTTPException(status_code=400, detail="Invalid data_type")
        
        if not data:
            raise HTTPException(status_code=404, detail="No data found for export")
        
        if format == "csv":
            # Create CSV
            df = pd.DataFrame(data)
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=advanced_{data_type}_{season}.csv"
                }
            )
        
        elif format == "json":
            return {
                "season": season,
                "data_type": data_type,
                "total_records": len(data),
                "data": data,
                "exported_at": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'")
        
    except Exception as e:
        logger.error(f"Error exporting advanced data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))