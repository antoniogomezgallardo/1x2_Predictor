#!/usr/bin/env python3
"""
Tests de integración para el sistema de Quiniela Predictor
Incluye tests para API, base de datos, y flujos completos
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database.models import Base, Team, Match
from backend.app.main import app
from backend.app.database.database import get_db
import os

# Test database URL
TEST_DATABASE_URL = "postgresql://quiniela_user:quiniela_password@localhost:5432/quiniela_predictor_test"

@pytest.fixture
def test_db():
    """Create test database session"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Create test client"""
    return AsyncClient(app=app, base_url="http://test")

class TestAPIEndpoints:
    """Test all API endpoints for basic functionality"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        
    @pytest.mark.asyncio
    async def test_data_status_endpoint(self, client):
        """Test data status endpoint"""
        response = await client.get("/data/status/2024")
        assert response.status_code == 200
        data = response.json()
        required_fields = [
            "season", "teams_total", "matches_total", 
            "matches_with_results", "team_statistics_total"
        ]
        for field in required_fields:
            assert field in data
            
    @pytest.mark.asyncio
    async def test_update_teams_endpoint_response(self, client):
        """Test that update teams endpoint responds correctly"""
        response = await client.post("/data/update-teams/2024")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "2024" in data["message"]
        
    @pytest.mark.asyncio
    async def test_quiniela_next_matches_endpoint(self, client):
        """Test quiniela next matches endpoint"""
        response = await client.get("/quiniela/next-matches/2024")
        assert response.status_code == 200
        data = response.json()
        required_fields = ["season", "matches", "generated_at"]
        for field in required_fields:
            assert field in data

class TestDatabaseOperations:
    """Test database operations and models"""
    
    def test_team_creation(self, test_db):
        """Test creating teams in database"""
        team = Team(
            api_id=123,
            name="Test Team",
            short_name="TT",
            league_id=140,
            founded=2000
        )
        test_db.add(team)
        test_db.commit()
        
        retrieved_team = test_db.query(Team).filter_by(api_id=123).first()
        assert retrieved_team is not None
        assert retrieved_team.name == "Test Team"
        assert retrieved_team.league_id == 140
        
    def test_match_creation(self, test_db):
        """Test creating matches in database"""
        # First create teams
        home_team = Team(api_id=1, name="Home Team", league_id=140)
        away_team = Team(api_id=2, name="Away Team", league_id=140) 
        test_db.add_all([home_team, away_team])
        test_db.commit()
        
        # Create match
        match = Match(
            api_id=999,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            league_id=140,
            season=2024,
            round="Regular Season - 1"
        )
        test_db.add(match)
        test_db.commit()
        
        retrieved_match = test_db.query(Match).filter_by(api_id=999).first()
        assert retrieved_match is not None
        assert retrieved_match.season == 2024

class TestQuinielaLogic:
    """Test Quiniela-specific business logic"""
    
    @pytest.mark.asyncio
    async def test_season_validation_logic(self, client):
        """Test that season validation works correctly"""
        # Test future season
        response = await client.post("/data/update-teams/2030")
        assert response.status_code == 200
        data = response.json()
        # Should return warning about future season
        assert ("not started" in data.get("message", "").lower() or 
                "warning" in data or 
                "recommendation" in data)
        
    def test_quiniela_match_count_validation(self, test_db):
        """Test that we can validate proper Quiniela match counts"""
        # Create 15 matches (typical Quiniela)
        teams = []
        for i in range(30):  # 30 teams to have enough for 15 matches
            team = Team(api_id=i+1, name=f"Team {i+1}", league_id=140)
            teams.append(team)
        test_db.add_all(teams)
        test_db.commit()
        
        matches = []
        for i in range(15):
            match = Match(
                api_id=i+1,
                home_team_id=teams[i*2].id,
                away_team_id=teams[i*2+1].id,
                league_id=140,
                season=2024,
                round="Regular Season - 1"
            )
            matches.append(match)
        test_db.add_all(matches)
        test_db.commit()
        
        match_count = test_db.query(Match).filter_by(season=2024).count()
        assert match_count == 15
        assert match_count >= 14  # Minimum for Quiniela

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_invalid_season_parameter(self, client):
        """Test API with invalid season parameters"""
        response = await client.get("/data/status/invalid")
        # Should handle gracefully (either 422 or default behavior)
        assert response.status_code in [422, 200]
        
    @pytest.mark.asyncio 
    async def test_nonexistent_endpoints(self, client):
        """Test that nonexistent endpoints return 404"""
        response = await client.get("/nonexistent/endpoint")
        assert response.status_code == 404

class TestAPIFootballIntegration:
    """Test API-Football integration with mocking"""
    
    def test_api_key_configuration(self):
        """Test that API key is configured"""
        from backend.app.config.settings import settings
        assert settings.api_football_key is not None
        assert len(settings.api_football_key) > 0
        
    def test_league_ids_configuration(self):
        """Test that Spanish league IDs are correct"""
        from backend.app.config.settings import settings
        assert settings.la_liga_id == 140
        assert settings.segunda_division_id == 141

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_api_integration.py -v
    pytest.main([__file__, "-v"])