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
        
        # Headers más realistas para evitar detección como bot
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Ch-Ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'max-age=0'
        })
        
        self.rate_limit_delay = 8  # Aumentar a 8 segundos para evitar rate limiting
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
                'name': 'Segunda-Division',  # Sin tilde para FBRef
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
    
    def _make_request(self, url: str, retry_count: int = 3) -> Optional[BeautifulSoup]:
        """Hace una request HTTP con manejo de errores, rate limiting y retries"""
        for attempt in range(retry_count):
            try:
                self._respect_rate_limit()
                logger.info(f"Fetching: {url} (attempt {attempt + 1}/{retry_count})")
                
                # Añadir referer para simular navegación natural
                headers = {}
                if attempt > 0:
                    headers['Referer'] = 'https://fbref.com/'
                
                response = self.session.get(url, timeout=30, headers=headers)
                
                # Log del status code para debugging
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 403:
                    logger.warning(f"403 Forbidden on attempt {attempt + 1}. Waiting longer...")
                    if attempt < retry_count - 1:
                        time.sleep(15)  # Esperar 15 segundos antes del siguiente intento
                        continue
                    else:
                        logger.error(f"All attempts failed with 403 Forbidden for {url}")
                        return None
                
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                logger.info(f"Successfully fetched and parsed {url}")
                return soup
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 403:
                    logger.warning(f"403 Forbidden - FBRef may be blocking requests")
                    if attempt < retry_count - 1:
                        wait_time = (attempt + 1) * 10  # Wait progressively longer
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                logger.error(f"HTTP error fetching {url}: {e}")
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error fetching {url}: {e}")
                if attempt < retry_count - 1:
                    time.sleep(5)  # Wait 5 seconds before retry
                    continue
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error parsing {url}: {e}")
                return None
        
        logger.error(f"All {retry_count} attempts failed for {url}")
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
        
        # URL para estadísticas avanzadas de la liga con temporada específica
        league_name_clean = league_info['name'].replace(' ', '-')
        url = f"{self.base_url}/en/comps/{league_info['fbref_id']}/{season_str}/{season_str}-{league_name_clean}-Stats"
        
        logger.info(f"Fetching FBRef data for season {season_str} from: {url}")
        
        soup = self._make_request(url)
        if not soup:
            return None
        
        try:
            # Buscar tabla de estadísticas del equipo con múltiples patrones
            tables = soup.find_all('table')
            stats_table = None
            
            # Log todas las tablas encontradas para debugging
            logger.info(f"Found {len(tables)} tables total")
            table_ids = [table.get('id') for table in tables if table.get('id')]
            logger.info(f"Table IDs found: {table_ids}")
            
            # Patrones de búsqueda más flexibles (priorizar tablas de estadísticas de equipos)
            search_patterns = [
                'stats_squads_standard_for',  # Tabla principal de estadísticas de equipos
                'stats_standard',
                'stats_squads_standard',
                'overall',  # results2024-2025121_overall (fallback)
                'results',
                'league_table',
                'stats',
                'standings'
            ]
            
            for pattern in search_patterns:
                for table in tables:
                    table_id = table.get('id', '')
                    if pattern in table_id.lower():
                        stats_table = table
                        logger.info(f"Found stats table with pattern '{pattern}': {table_id}")
                        break
                if stats_table:
                    break
            
            # Si no encontramos por ID, buscar por clase o contenido
            if not stats_table:
                logger.info("Searching by table content...")
                for table in tables:
                    thead = table.find('thead')
                    if thead:
                        headers = [th.get_text(strip=True).lower() for th in thead.find_all(['th', 'td'])]
                        # Buscar headers típicos de tabla de liga
                        if any(header in headers for header in ['team', 'squad', 'mp', 'pts', 'gf', 'ga']):
                            stats_table = table
                            logger.info(f"Found stats table by content analysis")
                            break
            
            if not stats_table:
                logger.warning(f"No stats table found for league {league_id} season {season}")
                logger.info("This might be due to 403 Forbidden or changed HTML structure")
                return None
            
            # Extraer datos de la tabla con parsing adaptivo
            teams_data = self._parse_table_data(stats_table, league_id, season)
            if not teams_data:
                logger.warning(f"Failed to parse table data for league {league_id} season {season}")
                return None
            
            logger.info(f"Successfully extracted {len(teams_data)} teams for league {league_id} season {season}")
            return teams_data
            
        except Exception as e:
            logger.error(f"Error parsing league table: {e}")
            return None
    
    def _parse_table_data(self, table, league_id: int, season: int) -> List[Dict[str, Any]]:
        """
        Parsing adaptivo para diferentes tipos de tablas de FBRef
        """
        try:
            # Obtener headers para identificar el tipo de tabla
            thead = table.find('thead')
            headers = []
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            
            logger.info(f"Table headers found: {headers[:10]}...")  # Log primeros 10 headers
            
            rows = table.find('tbody').find_all('tr')
            teams_data = []
            
            for row in rows:
                if row.get('class') and 'thead' in row.get('class'):
                    continue
                
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:  # Mínimo: nombre equipo + algún dato
                    continue
                
                try:
                    # Extraer nombre del equipo (normalmente en primera columna)
                    team_name = cells[0].get_text(strip=True)
                    if not team_name or team_name.lower() in ['squad', 'team', '']:
                        continue
                    
                    team_data = {
                        'team_name': team_name,
                        'league_id': league_id,
                        'season': season,
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    # Parsing adaptivo basado en headers disponibles
                    if 'mp' in headers and len(cells) > 1:  # Matches Played
                        try:
                            team_data['matches_played'] = int(cells[1].get_text(strip=True) or 0)
                        except (ValueError, IndexError):
                            pass
                    
                    # Buscar columnas de goles, wins, etc.
                    for i, cell in enumerate(cells):
                        try:
                            cell_text = cell.get_text(strip=True)
                            if not cell_text:
                                continue
                                
                            # Intentar identificar qué tipo de dato es por posición y headers
                            if i < len(headers):
                                header = headers[i]
                                
                                # Mapear headers comunes
                                if header in ['w', 'wins'] and cell_text.isdigit():
                                    team_data['wins'] = int(cell_text)
                                elif header in ['d', 'draws'] and cell_text.isdigit():
                                    team_data['draws'] = int(cell_text)
                                elif header in ['l', 'losses'] and cell_text.isdigit():
                                    team_data['losses'] = int(cell_text)
                                elif header in ['gf', 'goals for'] and cell_text.replace('.', '').isdigit():
                                    team_data['goals_for'] = int(float(cell_text))
                                elif header in ['ga', 'goals against'] and cell_text.replace('.', '').isdigit():
                                    team_data['goals_against'] = int(float(cell_text))
                                elif header in ['gd', 'goal difference', '+/-'] and cell_text.replace('-', '').replace('+', '').isdigit():
                                    team_data['goal_difference'] = int(cell_text)
                                elif header in ['pts', 'points'] and cell_text.isdigit():
                                    team_data['points'] = int(cell_text)
                                elif 'xg' in header and cell_text.replace('.', '').isdigit():
                                    if 'against' in header or 'ga' in header:
                                        team_data['xg_against'] = float(cell_text)
                                    else:
                                        team_data['xg_for'] = float(cell_text)
                                        
                        except (ValueError, IndexError):
                            continue
                    
                    # Calcular campos derivados
                    if 'xg_for' in team_data and 'xg_against' in team_data:
                        team_data['xg_difference'] = team_data['xg_for'] - team_data['xg_against']
                    
                    # Solo añadir si tiene datos útiles
                    if len(team_data) > 4:  # Más que solo campos básicos
                        teams_data.append(team_data)
                        logger.info(f"Parsed team: {team_name} with {len(team_data)} fields")
                    
                except Exception as e:
                    logger.warning(f"Error parsing row for team data: {e}")
                    continue
            
            return teams_data
            
        except Exception as e:
            logger.error(f"Error in _parse_table_data: {e}")
            return []
    
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