#!/usr/bin/env python3
"""
Test específico para verificar si API-Football proporciona datos adecuados para Quiniela
"""
import asyncio
import httpx
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

async def test_quiniela_data():
    """Test if we can get Quiniela-compatible data from API-Football"""
    headers = {
        "X-RapidAPI-Host": "v3.football.api-sports.io",
        "X-RapidAPI-Key": API_KEY
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== TESTING QUINIELA DATA AVAILABILITY ===")
        
        # Test 1: Check what seasons are available
        print("\n1. Testing available seasons...")
        for season in [2023, 2024, 2025]:
            print(f"\n--- Season {season} ---")
            
            # Check La Liga
            response = await client.get(
                f"{BASE_URL}/fixtures",
                headers=headers,
                params={"league": 140, "season": season, "status": "NS"}  # NS = Not Started
            )
            
            if response.status_code == 200:
                data = response.json()
                upcoming_matches = data.get("response", [])
                print(f"La Liga upcoming matches: {len(upcoming_matches)}")
                
                if upcoming_matches:
                    first_match = upcoming_matches[0]
                    date = first_match['fixture']['date']
                    home = first_match['teams']['home']['name']
                    away = first_match['teams']['away']['name']
                    print(f"Next match: {home} vs {away} on {date}")
            
            # Check Segunda Division  
            response = await client.get(
                f"{BASE_URL}/fixtures",
                headers=headers,
                params={"league": 141, "season": season, "status": "NS"}
            )
            
            if response.status_code == 200:
                data = response.json()
                upcoming_segunda = data.get("response", [])
                print(f"Segunda Division upcoming matches: {len(upcoming_segunda)}")
                
                total_upcoming = len(upcoming_matches) + len(upcoming_segunda)
                print(f"TOTAL UPCOMING: {total_upcoming}")
                
                if total_upcoming >= 14:
                    print(f"✅ Season {season} HAS ENOUGH matches for Quiniela ({total_upcoming})")
                    return season
                else:
                    print(f"❌ Season {season} not enough matches ({total_upcoming} < 14)")
        
        # Test 2: Check current round/matchday
        print("\n2. Testing current rounds...")
        current_season = 2024  # Start with most likely current season
        
        # Get current round for La Liga
        response = await client.get(
            f"{BASE_URL}/fixtures/rounds",
            headers=headers,
            params={"league": 140, "season": current_season, "current": "true"}
        )
        
        if response.status_code == 200:
            data = response.json()
            current_rounds = data.get("response", [])
            if current_rounds:
                current_round = current_rounds[0]
                print(f"Current La Liga round: {current_round}")
                
                # Get fixtures for current round
                fixtures_response = await client.get(
                    f"{BASE_URL}/fixtures",
                    headers=headers,
                    params={"league": 140, "season": current_season, "round": current_round}
                )
                
                if fixtures_response.status_code == 200:
                    fixtures_data = fixtures_response.json()
                    current_fixtures = fixtures_data.get("response", [])
                    print(f"Fixtures in current round: {len(current_fixtures)}")
                    
                    # Check match status
                    upcoming_count = 0
                    for fixture in current_fixtures:
                        status = fixture['fixture']['status']['short']
                        if status in ['NS', 'TBD']:  # Not Started or To Be Determined
                            upcoming_count += 1
                    
                    print(f"Upcoming fixtures in round: {upcoming_count}")
        
        # Test 3: Check for next 7 days
        print("\n3. Testing next 7 days...")
        today = datetime.now()
        next_week = today + timedelta(days=7)
        
        date_from = today.strftime("%Y-%m-%d")
        date_to = next_week.strftime("%Y-%m-%d")
        
        # La Liga
        response = await client.get(
            f"{BASE_URL}/fixtures",
            headers=headers,
            params={
                "league": 140, 
                "season": current_season,
                "from": date_from,
                "to": date_to
            }
        )
        
        laliga_next_week = 0
        if response.status_code == 200:
            data = response.json()
            laliga_next_week = len(data.get("response", []))
            print(f"La Liga matches next 7 days: {laliga_next_week}")
        
        # Segunda Division
        response = await client.get(
            f"{BASE_URL}/fixtures",
            headers=headers,
            params={
                "league": 141, 
                "season": current_season,
                "from": date_from,
                "to": date_to
            }
        )
        
        segunda_next_week = 0
        if response.status_code == 200:
            data = response.json()
            segunda_next_week = len(data.get("response", []))
            print(f"Segunda Division matches next 7 days: {segunda_next_week}")
        
        total_next_week = laliga_next_week + segunda_next_week
        print(f"\nTOTAL matches next 7 days: {total_next_week}")
        
        if total_next_week >= 14:
            print(f"✅ PERFECT! Next 7 days have enough matches for Quiniela")
        else:
            print(f"❌ Not enough matches in next 7 days for Quiniela")
        
        # Test 4: Try to find any weekend with 14+ matches
        print("\n4. Scanning weekends for Quiniela opportunities...")
        for week_offset in range(4):  # Check next 4 weeks
            weekend_start = today + timedelta(days=(week_offset*7))
            weekend_end = weekend_start + timedelta(days=2)  # Saturday + Sunday
            
            weekend_from = weekend_start.strftime("%Y-%m-%d")
            weekend_to = weekend_end.strftime("%Y-%m-%d")
            
            print(f"\nWeekend {weekend_from} to {weekend_to}:")
            
            # Check both leagues
            total_weekend = 0
            for league_id, league_name in [(140, "La Liga"), (141, "Segunda")]:
                response = await client.get(
                    f"{BASE_URL}/fixtures",
                    headers=headers,
                    params={
                        "league": league_id, 
                        "season": current_season,
                        "from": weekend_from,
                        "to": weekend_to
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get("response", [])
                    print(f"  {league_name}: {len(matches)} matches")
                    total_weekend += len(matches)
            
            print(f"  TOTAL: {total_weekend} matches")
            if total_weekend >= 14:
                print(f"  ✅ This weekend works for Quiniela!")
                return True
        
        print("\n❌ No suitable weekends found for Quiniela in next 4 weeks")
        return False

if __name__ == "__main__":
    if not API_KEY:
        print("❌ No API_FOOTBALL_KEY found")
        exit(1)
    
    result = asyncio.run(test_quiniela_data())
    if result:
        print("\n🎯 CONCLUSION: API-Football CAN provide Quiniela data")
    else:
        print("\n⚠️  CONCLUSION: API-Football might not have current Quiniela data")