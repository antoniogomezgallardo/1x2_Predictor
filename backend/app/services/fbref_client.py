"""
FBRef Data Client - Sistema de recolección de estadísticas avanzadas de fútbol
Recolecta datos de xG, xA, xT, PPDA, Pass Networks y otras métricas avanzadas
"""
import requests
import time
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, urlparse
import json

logger = logging.getLogger(__name__)

class FBRefClient:
    """
    Cliente para recolectar estadísticas avanzadas de fútbol desde FBRef
    Implementa rate limiting y manejo de errores robusto
    """
    
    def __init__(self):
        self.base_url = "https://fbref.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.rate_limit_delay = 3  # 3 segundos entre requests (respetar robots.txt)
        self.last_request_time = 0
        
        # Mapeo de ligas
        self.league_mappings = {
            140: {  # La Liga
                'fbref_id': '12',
                'name': 'La Liga',
                'country': 'Spain',
                'url_pattern': '/en/comps/12/La-Liga-Stats'
            },
            141: {  # Segunda División
                'fbref_id': '17',
                'name': 'Segunda División',
                'country': 'Spain', 
                'url_pattern': '/en/comps/17/Segunda-Division-Stats'
            }
        }
    
    def _respect_rate_limit(self):
        """Implementa rate limiting para respetar el servidor"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Hace una request HTTP con manejo de errores y rate limiting"""
        try:
            self._respect_rate_limit()
            logger.info(f"Fetching: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing {url}: {e}")
            return None
    
    def get_league_table_advanced(self, league_id: int, season: int) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene tabla de liga con estadísticas avanzadas
        Incluye xG, xGA, xGD y otras métricas
        """
        if league_id not in self.league_mappings:
            logger.error(f"League {league_id} not supported")
            return None
        
        league_info = self.league_mappings[league_id]
        season_str = f"{season}-{season+1}"
        
        # URL para estadísticas avanzadas de la liga
        url = f"{self.base_url}/en/comps/{league_info['fbref_id']}/{season_str}/stats/{season_str}-{league_info['name'].replace(' ', '-')}-Stats"
        
        soup = self._make_request(url)
        if not soup:
            return None
        
        try:
            # Buscar tabla de estadísticas del equipo
            tables = soup.find_all('table')
            stats_table = None
            
            for table in tables:
                if table.get('id') and 'stats_standard' in table.get('id'):
                    stats_table = table
                    break
            
            if not stats_table:
                logger.warning(f"No stats table found for league {league_id} season {season}")
                return None
            
            # Extraer datos de la tabla
            rows = stats_table.find('tbody').find_all('tr')
            teams_data = []
            
            for row in rows:
                if row.get('class') and 'thead' in row.get('class'):
                    continue
                
                cells = row.find_all(['td', 'th'])
                if len(cells) < 10:
                    continue
                
                try:
                    team_data = {
                        'team_name': cells[0].get_text(strip=True),
                        'matches_played': int(cells[2].get_text(strip=True) or 0),
                        'wins': int(cells[3].get_text(strip=True) or 0),
                        'draws': int(cells[4].get_text(strip=True) or 0),
                        'losses': int(cells[5].get_text(strip=True) or 0),
                        'goals_for': int(cells[6].get_text(strip=True) or 0),
                        'goals_against': int(cells[7].get_text(strip=True) or 0),
                        'goal_difference': int(cells[8].get_text(strip=True) or 0),
                        'points': int(cells[9].get_text(strip=True) or 0),
                        'league_id': league_id,
                        'season': season,
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    # Intentar extraer xG si está disponible
                    if len(cells) > 15:
                        try:
                            team_data['xg_for'] = float(cells[15].get_text(strip=True) or 0)
                            team_data['xg_against'] = float(cells[16].get_text(strip=True) or 0)
                            team_data['xg_difference'] = team_data['xg_for'] - team_data['xg_against']
                        except (ValueError, IndexError):
                            team_data['xg_for'] = None
                            team_data['xg_against'] = None
                            team_data['xg_difference'] = None
                    
                    teams_data.append(team_data)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(teams_data)} teams for league {league_id} season {season}")
            return teams_data
            
        except Exception as e:
            logger.error(f"Error parsing league table: {e}")
            return None
    
    def get_team_advanced_stats(self, team_name: str, league_id: int, season: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas avanzadas específicas de un equipo
        Incluye métricas como PPDA, Pass Networks, xT, etc.
        """
        if league_id not in self.league_mappings:
            return None
        
        league_info = self.league_mappings[league_id]
        season_str = f"{season}-{season+1}"
        
        # Buscar URL específica del equipo
        team_url = self._find_team_url(team_name, league_info['fbref_id'], season_str)
        if not team_url:
            return None
        
        soup = self._make_request(team_url)
        if not soup:
            return None
        
        try:
            advanced_stats = {
                'team_name': team_name,
                'league_id': league_id,
                'season': season,
                'last_updated': datetime.now().isoformat()
            }
            
            # Extraer estadísticas de posesión
            possession_stats = self._extract_possession_stats(soup)
            if possession_stats:
                advanced_stats.update(possession_stats)
            
            # Extraer estadísticas de pases
            passing_stats = self._extract_passing_stats(soup)
            if passing_stats:
                advanced_stats.update(passing_stats)
            
            # Extraer estadísticas defensivas
            defensive_stats = self._extract_defensive_stats(soup)
            if defensive_stats:
                advanced_stats.update(defensive_stats)
            
            # Extraer estadísticas de Expected Goals
            xg_stats = self._extract_xg_stats(soup)
            if xg_stats:
                advanced_stats.update(xg_stats)
            
            return advanced_stats
            
        except Exception as e:
            logger.error(f"Error extracting team stats for {team_name}: {e}")
            return None
    
    def _find_team_url(self, team_name: str, league_fbref_id: str, season_str: str) -> Optional[str]:
        """Encuentra la URL específica de un equipo"""
        # Implementación simplificada - en producción necesitaría búsqueda más sofisticada
        normalized_name = team_name.replace(' ', '-').replace('é', 'e').replace('ñ', 'n')
        team_url = f"{self.base_url}/en/squads/{normalized_name}/{season_str}"
        return team_url
    
    def _extract_possession_stats(self, soup: BeautifulSoup) -> Optional[Dict[str, float]]:
        """Extrae estadísticas de posesión del equipo"""
        try:
            stats = {}
            
            # Buscar tabla de posesión
            possession_table = soup.find('table', {'id': re.compile(r'stats_possession')})
            if possession_table:
                rows = possession_table.find('tbody').find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        try:
                            stats['possession_pct'] = float(cells[2].get_text(strip=True).replace('%', '') or 0)
                        except ValueError:
                            pass
            
            return stats if stats else None
            
        except Exception as e:
            logger.warning(f"Error extracting possession stats: {e}")
            return None
    
    def _extract_passing_stats(self, soup: BeautifulSoup) -> Optional[Dict[str, float]]:
        """Extrae estadísticas de pases avanzadas"""
        try:
            stats = {}
            
            # Buscar tabla de pases
            passing_table = soup.find('table', {'id': re.compile(r'stats_passing')})
            if passing_table:
                rows = passing_table.find('tbody').find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 10:
                        try:
                            stats['passes_completed'] = int(cells[4].get_text(strip=True) or 0)
                            stats['passes_attempted'] = int(cells[5].get_text(strip=True) or 0)
                            stats['pass_completion_pct'] = float(cells[6].get_text(strip=True).replace('%', '') or 0)
                            stats['progressive_passes'] = int(cells[9].get_text(strip=True) or 0)
                        except ValueError:
                            pass
            
            return stats if stats else None
            
        except Exception as e:
            logger.warning(f"Error extracting passing stats: {e}")
            return None
    
    def _extract_defensive_stats(self, soup: BeautifulSoup) -> Optional[Dict[str, float]]:
        """Extrae estadísticas defensivas incluyendo PPDA estimado"""
        try:
            stats = {}
            
            # Buscar tabla defensiva
            defensive_table = soup.find('table', {'id': re.compile(r'stats_defense')})
            if defensive_table:
                rows = defensive_table.find('tbody').find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 8:
                        try:
                            stats['tackles'] = int(cells[3].get_text(strip=True) or 0)
                            stats['interceptions'] = int(cells[5].get_text(strip=True) or 0)
                            stats['blocks'] = int(cells[6].get_text(strip=True) or 0)
                            
                            # PPDA estimado (passes allowed per defensive action)
                            defensive_actions = stats['tackles'] + stats['interceptions'] + stats['blocks']
                            if defensive_actions > 0:
                                # Estimación basada en posesión del oponente
                                estimated_opponent_passes = 400  # Promedio por partido
                                stats['ppda_estimated'] = estimated_opponent_passes / defensive_actions
                            
                        except ValueError:
                            pass
            
            return stats if stats else None
            
        except Exception as e:
            logger.warning(f"Error extracting defensive stats: {e}")
            return None
    
    def _extract_xg_stats(self, soup: BeautifulSoup) -> Optional[Dict[str, float]]:
        """Extrae estadísticas de Expected Goals detalladas"""
        try:
            stats = {}
            
            # Buscar tabla de shooting/xG
            shooting_table = soup.find('table', {'id': re.compile(r'stats_shooting')})
            if shooting_table:
                rows = shooting_table.find('tbody').find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 10:
                        try:
                            stats['shots_total'] = int(cells[3].get_text(strip=True) or 0)
                            stats['shots_on_target'] = int(cells[4].get_text(strip=True) or 0)
                            stats['xg_total'] = float(cells[8].get_text(strip=True) or 0)
                            stats['xg_per_shot'] = float(cells[9].get_text(strip=True) or 0)
                            
                            # Calcular eficiencia de xG
                            if stats['xg_total'] > 0:
                                goals_scored = int(cells[2].get_text(strip=True) or 0)
                                stats['xg_performance'] = goals_scored / stats['xg_total']
                            
                        except ValueError:
                            pass
            
            return stats if stats else None
            
        except Exception as e:
            logger.warning(f"Error extracting xG stats: {e}")
            return None
    
    def get_match_advanced_data(self, match_date: datetime, home_team: str, away_team: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos avanzados de un partido específico
        Incluye xG por tiempo, heat maps, etc.
        """
        try:
            # Esta función requeriría implementación más compleja
            # para encontrar el partido específico en FBRef
            
            logger.info(f"Getting match data for {home_team} vs {away_team} on {match_date.date()}")
            
            # Por ahora, devolvemos estructura básica
            match_data = {
                'match_date': match_date.isoformat(),
                'home_team': home_team,
                'away_team': away_team,
                'data_source': 'fbref',
                'advanced_stats_available': False,
                'last_updated': datetime.now().isoformat()
            }
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error getting match data: {e}")
            return None
    
    def get_player_advanced_stats(self, player_name: str, team_name: str, season: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas avanzadas de un jugador específico
        Útil para análisis de impacto individual
        """
        try:
            # Implementación futura para estadísticas de jugadores
            # Incluiría xG, xA, progressive carries, etc.
            
            player_stats = {
                'player_name': player_name,
                'team_name': team_name,
                'season': season,
                'data_source': 'fbref',
                'stats_available': False,
                'last_updated': datetime.now().isoformat()
            }
            
            return player_stats
            
        except Exception as e:
            logger.error(f"Error getting player stats for {player_name}: {e}")
            return None

# Funciones de utilidad
def normalize_team_name(team_name: str) -> str:
    """Normaliza nombres de equipos para matching con FBRef"""
    normalizations = {
        'Real Madrid': 'Real Madrid',
        'FC Barcelona': 'Barcelona',
        'Atletico Madrid': 'Atlético Madrid',
        'Athletic Club': 'Athletic Club',
        'Real Sociedad': 'Real Sociedad',
        # Añadir más normalizaciones según sea necesario
    }
    
    return normalizations.get(team_name, team_name)