#!/usr/bin/env python3
import asyncio
import httpx
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

async def test_quiniela_simple():
    headers = {
        "X-RapidAPI-Host": "v3.football.api-sports.io",
        "X-RapidAPI-Key": API_KEY
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Testing Quiniela data availability...")
        
        # Test upcoming matches in next 7 days
        today = datetime.now()
        next_week = today + timedelta(days=7)
        
        date_from = today.strftime("%Y-%m-%d")
        date_to = next_week.strftime("%Y-%m-%d")
        
        print(f"Checking matches from {date_from} to {date_to}")
        
        # Test different seasons
        for season in [2024, 2025]:
            print(f"\n--- Season {season} ---")
            
            # La Liga upcoming
            response = await client.get(
                f"{BASE_URL}/fixtures",
                headers=headers,
                params={
                    "league": 140, 
                    "season": season,
                    "from": date_from,
                    "to": date_to
                }
            )
            
            laliga_count = 0
            if response.status_code == 200:
                data = response.json()
                laliga_count = len(data.get("response", []))
                print(f"La Liga matches: {laliga_count}")
                
                # Show first match if available
                matches = data.get("response", [])
                if matches:
                    first = matches[0]
                    home = first['teams']['home']['name']
                    away = first['teams']['away']['name']
                    date = first['fixture']['date']
                    print(f"  Example: {home} vs {away} on {date}")
            
            # Segunda Division upcoming
            response = await client.get(
                f"{BASE_URL}/fixtures",
                headers=headers,
                params={
                    "league": 141, 
                    "season": season,
                    "from": date_from,
                    "to": date_to
                }
            )
            
            segunda_count = 0
            if response.status_code == 200:
                data = response.json()
                segunda_count = len(data.get("response", []))
                print(f"Segunda Division matches: {segunda_count}")
            
            total = laliga_count + segunda_count
            print(f"TOTAL: {total} matches")
            
            if total >= 14:
                print(f"SUCCESS: Season {season} has enough matches for Quiniela!")
                return season
            else:
                print(f"Season {season}: Not enough matches ({total} < 14)")
        
        print("\nNo suitable season found with upcoming matches")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_quiniela_simple())
    if result:
        print(f"\nCONCLUSION: Season {result} can provide Quiniela data")
    else:
        print("\nCONCLUSION: No current Quiniela data available")