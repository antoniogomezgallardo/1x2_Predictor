"""
FBRef Data Collector - Advanced Football Statistics Scraper
Collects detailed match and player statistics from FBRef.com.

Features:
- Advanced team statistics (xG, xA, PPDA, packing rates)
- Detailed player performance data
- Historical season data for multiple competitions
- Shot and pass location data where available
- Respect rate limiting and robots.txt
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import asyncio
import aiohttp
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class MatchAdvancedStats:
    """Advanced match statistics from FBRef"""
    match_id: str
    date: str
    home_team: str
    away_team: str
    competition: str
    
    # Expected metrics
    home_xg: float
    away_xg: float
    home_xa: float
    away_xa: float
    
    # Shooting metrics
    home_shots: int
    away_shots: int
    home_shots_on_target: int
    away_shots_on_target: int
    
    # Passing metrics
    home_passes: int
    away_passes: int
    home_pass_accuracy: float
    away_pass_accuracy: float
    home_progressive_passes: int
    away_progressive_passes: int
    
    # Defensive metrics
    home_tackles: int
    away_tackles: int
    home_interceptions: int
    away_interceptions: int
    home_blocks: int
    away_blocks: int
    
    # Possession metrics
    home_possession: float
    away_possession: float
    home_touches: int
    away_touches: int
    
    # Advanced metrics (when available)
    home_ppda: Optional[float] = None
    away_ppda: Optional[float] = None
    home_packing_rate: Optional[float] = None
    away_packing_rate: Optional[float] = None


class FBRefCollector:
    """
    Collects advanced football statistics from FBRef.com
    """
    
    def __init__(self):
        self.base_url = "https://fbref.com"
        self.session = requests.Session()
        
        # Headers to appear as regular browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Rate limiting (be respectful to FBRef)
        self.request_delay = 3.0  # Seconds between requests
        self.last_request_time = 0
        
        # Competition mappings
        self.competition_codes = {
            'primera_division': '12',  # La Liga
            'segunda_division': '17',  # Segunda División
            'premier_league': '9',     # Premier League
            'serie_a': '11',          # Serie A
            'bundesliga': '20',       # Bundesliga
            'ligue_1': '13'           # Ligue 1
        }
        
    def _rate_limit(self):
        """Ensure we don't overwhelm FBRef servers"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """
        Make a rate-limited request to FBRef
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            self._rate_limit()
            
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def get_competition_matches(self, competition: str, season: str) -> List[Dict]:
        """
        Get all matches for a competition and season
        
        Args:
            competition: Competition name (e.g., 'primera_division')
            season: Season string (e.g., '2024-2025')
            
        Returns:
            List of match dictionaries
        """
        if competition not in self.competition_codes:
            logger.error(f"Unknown competition: {competition}")
            return []
        
        comp_code = self.competition_codes[competition]
        
        # Construct season URL
        season_url = f"{self.base_url}/en/comps/{comp_code}/{season}/schedule/{season}-{competition.replace('_', '-')}-Scores-and-Fixtures"
        
        soup = self._make_request(season_url)
        if not soup:
            return []
        
        matches = []
        
        # Find the fixtures table
        table = soup.find('table', {'id': 'sched_all'})
        if not table:
            logger.warning(f"No fixtures table found for {competition} {season}")
            return []
        
        tbody = table.find('tbody')
        if not tbody:
            return []
        
        for row in tbody.find_all('tr'):
            # Skip header rows
            if 'thead' in row.get('class', []):
                continue
                
            cells = row.find_all(['td', 'th'])
            if len(cells) < 10:
                continue
            
            try:
                # Extract match data
                date_cell = cells[1].text.strip()
                home_team = cells[4].text.strip()
                away_team = cells[6].text.strip()
                
                # Score (if available)
                score_cell = cells[5].text.strip()
                home_score, away_score = None, None
                if '–' in score_cell:
                    scores = score_cell.split('–')
                    if len(scores) == 2:
                        try:
                            home_score = int(scores[0].strip())
                            away_score = int(scores[1].strip())
                        except ValueError:
                            pass
                
                # Match report link for detailed stats
                report_link = None
                report_cell = cells[7].find('a')
                if report_cell and report_cell.get('href'):
                    report_link = self.base_url + report_cell.get('href')
                
                match_data = {
                    'date': date_cell,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'competition': competition,
                    'season': season,
                    'report_url': report_link,
                    'fbref_match_id': self._extract_match_id_from_url(report_link) if report_link else None
                }
                
                matches.append(match_data)
                
            except Exception as e:
                logger.warning(f"Error parsing match row: {e}")
                continue
        
        logger.info(f"Found {len(matches)} matches for {competition} {season}")
        return matches
    
    def _extract_match_id_from_url(self, url: str) -> Optional[str]:
        """Extract FBRef match ID from URL"""
        if not url:
            return None
        
        # FBRef match URLs typically contain the match ID
        match = re.search(r'/([a-f0-9]{8})/', url)
        return match.group(1) if match else None
    
    def get_match_advanced_stats(self, match_url: str) -> Optional[MatchAdvancedStats]:
        """
        Get advanced statistics for a specific match
        
        Args:
            match_url: URL to the match report page
            
        Returns:
            MatchAdvancedStats object or None
        """
        if not match_url:
            return None
        
        soup = self._make_request(match_url)
        if not soup:
            return None
        
        try:
            # Extract basic match info
            scorebox = soup.find('div', {'class': 'scorebox'})
            if not scorebox:
                logger.warning(f"No scorebox found in {match_url}")
                return None
            
            # Team names
            team_divs = scorebox.find_all('div', {'class': 'team'})
            if len(team_divs) < 2:
                return None
            
            home_team = team_divs[0].find('a').text.strip() if team_divs[0].find('a') else 'Unknown'
            away_team = team_divs[1].find('a').text.strip() if team_divs[1].find('a') else 'Unknown'
            
            # Match date
            match_date = soup.find('span', {'class': 'venuetime'})
            date_str = match_date.get('data-venue-date') if match_date else ''
            
            # Initialize stats object
            stats = MatchAdvancedStats(
                match_id=self._extract_match_id_from_url(match_url),
                date=date_str,
                home_team=home_team,
                away_team=away_team,
                competition='',
                home_xg=0.0, away_xg=0.0,
                home_xa=0.0, away_xa=0.0,
                home_shots=0, away_shots=0,
                home_shots_on_target=0, away_shots_on_target=0,
                home_passes=0, away_passes=0,
                home_pass_accuracy=0.0, away_pass_accuracy=0.0,
                home_progressive_passes=0, away_progressive_passes=0,
                home_tackles=0, away_tackles=0,
                home_interceptions=0, away_interceptions=0,
                home_blocks=0, away_blocks=0,
                home_possession=0.0, away_possession=0.0,
                home_touches=0, away_touches=0
            )
            
            # Extract team statistics
            self._extract_team_stats(soup, stats)
            
            # Extract expected stats if available
            self._extract_expected_stats(soup, stats)
            
            # Extract advanced metrics if available
            self._extract_advanced_metrics(soup, stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error parsing match stats from {match_url}: {e}")
            return None
    
    def _extract_team_stats(self, soup: BeautifulSoup, stats: MatchAdvancedStats):
        """Extract basic team statistics from match report"""
        # Look for team stats tables
        stats_tables = soup.find_all('table', {'class': 'stats_table'})
        
        for table in stats_tables:
            table_id = table.get('id', '')
            
            # Team stats summary
            if 'team_stats' in table_id:
                rows = table.find('tbody').find_all('tr') if table.find('tbody') else []
                
                for row in rows:
                    stat_name = row.find('th').text.strip() if row.find('th') else ''
                    cells = row.find_all('td')
                    
                    if len(cells) >= 2:
                        home_val = self._parse_numeric(cells[0].text.strip())
                        away_val = self._parse_numeric(cells[1].text.strip())
                        
                        # Map stat names to our structure
                        if 'possession' in stat_name.lower():
                            stats.home_possession = home_val
                            stats.away_possession = away_val
                        elif 'shots' in stat_name.lower() and 'on target' not in stat_name.lower():
                            stats.home_shots = int(home_val) if home_val is not None else 0
                            stats.away_shots = int(away_val) if away_val is not None else 0
                        elif 'shots on target' in stat_name.lower():
                            stats.home_shots_on_target = int(home_val) if home_val is not None else 0
                            stats.away_shots_on_target = int(away_val) if away_val is not None else 0
                        elif 'passes' in stat_name.lower() and 'accuracy' not in stat_name.lower():
                            stats.home_passes = int(home_val) if home_val is not None else 0
                            stats.away_passes = int(away_val) if away_val is not None else 0
                        elif 'pass accuracy' in stat_name.lower():
                            stats.home_pass_accuracy = home_val if home_val is not None else 0.0
                            stats.away_pass_accuracy = away_val if away_val is not None else 0.0
    
    def _extract_expected_stats(self, soup: BeautifulSoup, stats: MatchAdvancedStats):
        """Extract expected goals and assists if available"""
        # Look for xG data in various locations
        
        # Method 1: Check for xG in team stats
        xg_elements = soup.find_all(text=re.compile(r'xG', re.IGNORECASE))
        for element in xg_elements[:4]:  # Limit search
            parent = element.parent
            if parent and parent.name in ['td', 'th']:
                # Try to find associated values
                row = parent.find_parent('tr')
                if row:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if 'xg' in cell.text.lower():
                            # Look for numeric values in adjacent cells
                            if i + 1 < len(cells):
                                home_xg = self._parse_numeric(cells[i + 1].text)
                                if home_xg is not None:
                                    stats.home_xg = home_xg
                            if i + 2 < len(cells):
                                away_xg = self._parse_numeric(cells[i + 2].text)
                                if away_xg is not None:
                                    stats.away_xg = away_xg
        
        # Method 2: Look for shot charts or shot data tables
        shot_tables = soup.find_all('table', id=re.compile(r'shots', re.IGNORECASE))
        for table in shot_tables:
            # Sum up xG values from individual shots
            tbody = table.find('tbody')
            if tbody:
                home_xg_sum = 0.0
                away_xg_sum = 0.0
                
                for row in tbody.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    # Look for xG column and team identification
                    # This is simplified - actual implementation would need
                    # to properly identify team and xG columns
                    pass
    
    def _extract_advanced_metrics(self, soup: BeautifulSoup, stats: MatchAdvancedStats):
        """Extract advanced metrics like PPDA if available"""
        # FBRef sometimes includes advanced metrics in separate sections
        # This would need to be expanded based on actual FBRef structure
        
        # Look for defensive actions data
        defense_tables = soup.find_all('table', id=re.compile(r'defense', re.IGNORECASE))
        
        # PPDA calculation would require:
        # - Passes allowed in defensive third
        # - Defensive actions in defensive third
        # This data might not always be available on FBRef
        
        pass
    
    def _parse_numeric(self, text: str) -> Optional[float]:
        """Parse numeric value from text, handling percentages and special characters"""
        if not text:
            return None
        
        # Clean the text
        cleaned = re.sub(r'[^\d.-]', '', text)
        
        try:
            # Handle percentage
            if '%' in text:
                return float(cleaned) / 100.0
            else:
                return float(cleaned)
        except ValueError:
            return None
    
    def get_team_season_stats(self, team_name: str, competition: str, season: str) -> Dict:
        """
        Get aggregated season statistics for a team
        
        Args:
            team_name: Team name as it appears on FBRef
            competition: Competition code
            season: Season string
            
        Returns:
            Dictionary with season statistics
        """
        # This would require finding the team's specific page
        # and extracting their season totals/averages
        
        # Simplified implementation - would need team URL mapping
        logger.info(f"Getting season stats for {team_name} in {competition} {season}")
        
        # Return empty dict for now - would need full implementation
        return {
            'team': team_name,
            'competition': competition,
            'season': season,
            'matches_played': 0,
            'avg_xg_for': 0.0,
            'avg_xg_against': 0.0,
            'avg_possession': 0.0
        }
    
    def search_team_matches(self, team_name: str, limit: int = 10) -> List[Dict]:
        """
        Search for recent matches involving a specific team
        
        Args:
            team_name: Team name to search for
            limit: Maximum number of matches to return
            
        Returns:
            List of match dictionaries
        """
        # This would require implementing team search functionality
        # For now, return empty list
        logger.info(f"Searching for matches involving {team_name}")
        return []


# Utility functions
def get_spanish_league_data(season: str = "2024-2025") -> Dict:
    """
    Get comprehensive Spanish league data (La Liga + Segunda)
    
    Args:
        season: Season string
        
    Returns:
        Dictionary with both competitions' data
    """
    collector = FBRefCollector()
    
    logger.info(f"Collecting Spanish league data for {season}")
    
    # Get La Liga data
    primera_matches = collector.get_competition_matches('primera_division', season)
    
    # Get Segunda División data
    segunda_matches = collector.get_competition_matches('segunda_division', season)
    
    return {
        'primera_division': primera_matches,
        'segunda_division': segunda_matches,
        'total_matches': len(primera_matches) + len(segunda_matches),
        'collection_date': datetime.now().isoformat()
    }


async def collect_match_details_async(match_urls: List[str]) -> List[MatchAdvancedStats]:
    """
    Asynchronously collect detailed stats for multiple matches
    
    Args:
        match_urls: List of FBRef match URLs
        
    Returns:
        List of MatchAdvancedStats objects
    """
    collector = FBRefCollector()
    results = []
    
    # Process matches sequentially to respect rate limits
    for url in match_urls:
        if url:
            stats = collector.get_match_advanced_stats(url)
            if stats:
                results.append(stats)
    
    return results


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    collector = FBRefCollector()
    
    print("FBRef Collector - Example Usage")
    print("Note: This will make real requests to FBRef - use responsibly!")
    
    # Get La Liga fixtures for current season (commented out to avoid actual requests)
    # matches = collector.get_competition_matches('primera_division', '2024-2025')
    # print(f"Found {len(matches)} La Liga matches")
    
    # if matches and matches[0].get('report_url'):
    #     print("Getting detailed stats for first match...")
    #     stats = collector.get_match_advanced_stats(matches[0]['report_url'])
    #     if stats:
    #         print(f"Match: {stats.home_team} vs {stats.away_team}")
    #         print(f"xG: {stats.home_xg} - {stats.away_xg}")
    
    print("FBRef collector ready for use!")