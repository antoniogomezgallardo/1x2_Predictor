#!/usr/bin/env python3
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

async def test_simple():
    # Try different header configurations
    header_configs = [
        {"X-RapidAPI-Host": "v3.football.api-sports.io", "X-RapidAPI-Key": API_KEY},
        {"X-API-Key": API_KEY},
        {"Authorization": f"Bearer {API_KEY}"},
        {"X-RapidAPI-Key": API_KEY},
    ]
    
    print(f"API Key configured: {'Yes' if API_KEY else 'No'}")
    print(f"API Key length: {len(API_KEY) if API_KEY else 0}")
    if API_KEY:
        print(f"API Key preview: {API_KEY[:10]}...{API_KEY[-5:]}")
        # Check for non-ASCII characters
        try:
            API_KEY.encode('ascii')
            print("API Key contains only ASCII characters")
        except UnicodeEncodeError:
            print("WARNING: API Key contains non-ASCII characters")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test different header configurations
            for i, headers in enumerate(header_configs):
                print(f"\n--- Testing header config {i+1}: {list(headers.keys())} ---")
                
                # Test with status endpoint first
                status_response = await client.get(
                    f"{BASE_URL}/status",
                    headers=headers
                )
                print(f"Status code: {status_response.status_code}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get("errors"):
                        print(f"Error: {status_data['errors']}")
                    else:
                        print(f"Success! Response: {status_data}")
                        
                        # If this header config works, test both Spanish leagues
                        print("\nTesting La Liga (140)...")
                        laliga_response = await client.get(
                            f"{BASE_URL}/teams",
                            headers=headers,
                            params={"league": 140, "season": 2024}
                        )
                        if laliga_response.status_code == 200:
                            laliga_data = laliga_response.json()
                            laliga_teams = laliga_data.get("response", [])
                            print(f"La Liga teams found: {len(laliga_teams)}")
                            if laliga_teams:
                                print(f"First La Liga team: {laliga_teams[0]['team']['name']}")
                        
                        print("\nTesting Segunda Division (141)...")
                        segunda_response = await client.get(
                            f"{BASE_URL}/teams",
                            headers=headers,
                            params={"league": 141, "season": 2024}
                        )
                        if segunda_response.status_code == 200:
                            segunda_data = segunda_response.json()
                            segunda_teams = segunda_data.get("response", [])
                            print(f"Segunda Division teams found: {len(segunda_teams)}")
                            if segunda_teams:
                                print(f"First Segunda team: {segunda_teams[0]['team']['name']}")
                        
                        print(f"\nTotal Spanish teams: {len(laliga_teams) + len(segunda_teams)}")
                        break  # Found working config
                else:
                    print(f"HTTP Error: {status_response.text}")
                    
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple())