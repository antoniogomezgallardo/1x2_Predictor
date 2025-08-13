#!/usr/bin/env python3
"""
Script para probar directamente la API de football y verificar qué datos tenemos disponibles
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

async def test_api_football():
    """Test direct API-Football calls"""
    headers = {
        "X-RapidAPI-Host": "v3.football.api-sports.io",
        "X-RapidAPI-Key": API_KEY
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Testing API-Football data availability...")
        
        # Test 1: Check teams for La Liga 2024
        print("\n1. Testing La Liga (140) teams for 2024:")
        try:
            response = await client.get(
                f"{BASE_URL}/teams", 
                headers=headers,
                params={"league": 140, "season": 2024}
            )
            data = response.json()
            teams = data.get("response", [])
            print(f"   Found {len(teams)} teams in La Liga 2024")
            if teams:
                print(f"   Example team: {teams[0]['team']['name']}")
        except Exception as e:
            print(f"   Error: {e}")
            
        # Test 2: Check teams for Segunda División 2024  
        print("\n2. Testing Segunda División (141) teams for 2024:")
        try:
            response = await client.get(
                f"{BASE_URL}/teams", 
                headers=headers,
                params={"league": 141, "season": 2024}
            )
            data = response.json()
            teams = data.get("response", [])
            print(f"   ✅ Found {len(teams)} teams in Segunda División 2024")
            if teams:
                print(f"   📝 Example team: {teams[0]['team']['name']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        # Test 3: Check fixtures/matches for La Liga 2024
        print("\n3. Testing La Liga (140) fixtures for 2024:")
        try:
            response = await client.get(
                f"{BASE_URL}/fixtures", 
                headers=headers,
                params={"league": 140, "season": 2024}
            )
            data = response.json()
            fixtures = data.get("response", [])
            print(f"   ✅ Found {len(fixtures)} fixtures in La Liga 2024")
            if fixtures:
                match = fixtures[0]
                home_team = match['teams']['home']['name']
                away_team = match['teams']['away']['name']
                date = match['fixture']['date']
                print(f"   📝 Example match: {home_team} vs {away_team} ({date})")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        # Test 4: Check what leagues have "Quiniela" style data (14 fixtures)
        print("\n4. Testing current round fixtures for La Liga:")
        try:
            response = await client.get(
                f"{BASE_URL}/fixtures/rounds", 
                headers=headers,
                params={"league": 140, "season": 2024, "current": "true"}
            )
            data = response.json()
            current_round = data.get("response", [])
            if current_round:
                round_name = current_round[0]
                print(f"   📅 Current round: {round_name}")
                
                # Get fixtures for current round
                fixtures_response = await client.get(
                    f"{BASE_URL}/fixtures", 
                    headers=headers,
                    params={"league": 140, "season": 2024, "round": round_name}
                )
                fixtures_data = fixtures_response.json()
                round_fixtures = fixtures_data.get("response", [])
                print(f"   ⚽ Fixtures in round: {len(round_fixtures)}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        # Test 5: Test if we can get specific Quiniela-style data
        print("\n5. Testing specific round data that might be Quiniela compatible:")
        try:
            # Check recent completed rounds to see fixture count patterns
            response = await client.get(
                f"{BASE_URL}/fixtures/rounds", 
                headers=headers,
                params={"league": 140, "season": 2024}
            )
            data = response.json()
            rounds = data.get("response", [])
            
            if rounds and len(rounds) > 1:
                test_round = rounds[-2]  # Second to last round (likely completed)
                print(f"   🔍 Testing round: {test_round}")
                
                fixtures_response = await client.get(
                    f"{BASE_URL}/fixtures", 
                    headers=headers,
                    params={"league": 140, "season": 2024, "round": test_round}
                )
                fixtures_data = fixtures_response.json()
                test_fixtures = fixtures_data.get("response", [])
                
                la_liga_count = len(test_fixtures)
                print(f"   📊 La Liga fixtures in {test_round}: {la_liga_count}")
                
                # Also check Segunda División for same round
                segunda_response = await client.get(
                    f"{BASE_URL}/fixtures", 
                    headers=headers,
                    params={"league": 141, "season": 2024, "round": test_round}
                )
                segunda_data = segunda_response.json()
                segunda_fixtures = segunda_data.get("response", [])
                segunda_count = len(segunda_fixtures)
                
                print(f"   📊 Segunda División fixtures in {test_round}: {segunda_count}")
                print(f"   🎯 Total fixtures (La Liga + Segunda): {la_liga_count + segunda_count}")
                
                if la_liga_count + segunda_count >= 14:
                    print("   ✅ This could work for Quiniela (14-15 matches needed)")
                else:
                    print("   ⚠️  Might not be enough matches for full Quiniela")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ No API_FOOTBALL_KEY found in environment")
        exit(1)
    
    asyncio.run(test_api_football())