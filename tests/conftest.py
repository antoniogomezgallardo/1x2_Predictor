"""
Configuración global de pytest y fixtures reutilizables
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime, date

from backend.app.database.models import Base, Team, Match, TeamStatistics, UserQuiniela, UserQuinielaPrediction, CustomQuinielaConfig
from backend.app.main import app
from backend.app.database.database import get_db
from backend.app.services.quiniela_validator import QuinielaValidator

# Test database URL (SQLite in memory for faster tests)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture
def test_db(test_engine):
    """Create test database session with automatic rollback"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def client(test_db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(test_db):
    """Create async test client"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

# === SAMPLE DATA FIXTURES ===

@pytest.fixture
def sample_teams(test_db):
    """Create sample teams for testing"""
    teams = [
        Team(api_id=541, name="Real Madrid", short_name="RMA", league_id=140, founded=1902),
        Team(api_id=529, name="Barcelona", short_name="BAR", league_id=140, founded=1899),
        Team(api_id=530, name="Atlético Madrid", short_name="ATM", league_id=140, founded=1903),
        Team(api_id=728, name="Real Valladolid", short_name="VLL", league_id=141, founded=1928),
        Team(api_id=799, name="UD Las Palmas", short_name="LPA", league_id=141, founded=1949),
    ]
    
    for team in teams:
        test_db.add(team)
    test_db.commit()
    
    return teams

@pytest.fixture
def sample_matches(test_db, sample_teams):
    """Create sample matches for testing"""
    matches = [
        Match(
            api_id=1001,
            home_team_id=sample_teams[0].id,  # Real Madrid
            away_team_id=sample_teams[1].id,  # Barcelona
            league_id=140,
            season=2025,
            round="Regular Season - 1",
            match_date=datetime(2025, 8, 25, 21, 0)
        ),
        Match(
            api_id=1002,
            home_team_id=sample_teams[2].id,  # Atlético Madrid
            away_team_id=sample_teams[0].id,  # Real Madrid
            league_id=140,
            season=2025,
            round="Regular Season - 1",
            match_date=datetime(2025, 8, 26, 18, 30)
        ),
        Match(
            api_id=1003,
            home_team_id=sample_teams[3].id,  # Valladolid
            away_team_id=sample_teams[4].id,  # Las Palmas
            league_id=141,
            season=2025,
            round="Regular Season - 1",
            match_date=datetime(2025, 8, 24, 20, 0)
        ),
    ]
    
    for match in matches:
        test_db.add(match)
    test_db.commit()
    
    return matches

@pytest.fixture
def sample_team_statistics(test_db, sample_teams):
    """Create sample team statistics"""
    stats = [
        TeamStatistics(
            team_id=sample_teams[0].id,  # Real Madrid
            season=2025,
            matches_played=38,
            wins=26,
            draws=8,
            losses=4,
            goals_for=89,
            goals_against=34,
            points=86
        ),
        TeamStatistics(
            team_id=sample_teams[1].id,  # Barcelona
            season=2025,
            matches_played=38,
            wins=25,
            draws=7,
            losses=6,
            goals_for=85,
            goals_against=38,
            points=82
        ),
    ]
    
    for stat in stats:
        test_db.add(stat)
    test_db.commit()
    
    return stats

@pytest.fixture
def sample_quiniela_config(test_db, sample_matches):
    """Create sample custom quiniela configuration"""
    # Need at least 15 matches, so create more if needed
    match_ids = [match.id for match in sample_matches]
    
    # Add more matches if needed
    while len(match_ids) < 15:
        extra_match = Match(
            api_id=2000 + len(match_ids),
            home_team_id=sample_matches[0].home_team_id,
            away_team_id=sample_matches[0].away_team_id,
            league_id=140,
            season=2025,
            round="Regular Season - 1"
        )
        test_db.add(extra_match)
        test_db.commit()
        match_ids.append(extra_match.id)
    
    config = CustomQuinielaConfig(
        week_number=1,
        season=2025,
        config_name="Test Config",
        selected_match_ids=match_ids[:15],
        pleno_al_15_match_id=match_ids[14],
        la_liga_count=9,
        segunda_count=6,
        is_active=True,
        created_by_user=True
    )
    
    test_db.add(config)
    test_db.commit()
    
    return config

@pytest.fixture
def sample_user_quiniela(test_db):
    """Create sample user quiniela"""
    quiniela = UserQuiniela(
        week_number=1,
        season=2025,
        quiniela_date=date(2025, 8, 25),
        cost=1.50,
        pleno_al_15_home="2",
        pleno_al_15_away="1"
    )
    
    test_db.add(quiniela)
    test_db.commit()
    
    return quiniela

# === VALIDATION FIXTURES ===

@pytest.fixture
def valid_quiniela_data():
    """Valid quiniela data for testing"""
    return {
        "week_number": 1,
        "season": 2025,
        "date": "2025-08-25",
        "cost": 1.50,
        "pleno_al_15": "2-1",
        "predictions": [
            {
                "match_number": i,
                "home_team": f"Team {i}A",
                "away_team": f"Team {i}B",
                "user_prediction": "1" if i % 3 == 0 else "X" if i % 3 == 1 else "2",
                "match_date": "2025-08-25T21:00:00",
                "league": "La Liga" if i <= 9 else "Segunda División"
            }
            for i in range(1, 16)
        ]
    }

@pytest.fixture
def valid_multiple_quiniela_data():
    """Valid multiple quiniela data with dobles and triples"""
    return {
        "week_number": 1,
        "season": 2025,
        "config_name": "Test Multiple",
        "predictions": [
            {
                "match_number": 1,
                "match_id": 1001,
                "home_team": "Real Madrid",
                "away_team": "Barcelona", 
                "prediction_options": ["1"],
                "multiplicity": 1
            },
            {
                "match_number": 2,
                "match_id": 1002,
                "home_team": "Atlético Madrid",
                "away_team": "Real Madrid",
                "prediction_options": ["X", "2"],
                "multiplicity": 2
            },
            {
                "match_number": 3,
                "match_id": 1003,
                "home_team": "Valencia",
                "away_team": "Sevilla",
                "prediction_options": ["1", "X", "2"],
                "multiplicity": 3
            }
        ] + [
            {
                "match_number": i,
                "match_id": 1000 + i,
                "home_team": f"Team {i}A",
                "away_team": f"Team {i}B",
                "prediction_options": ["1"],
                "multiplicity": 1
            }
            for i in range(4, 16)
        ],
        "pleno_al_15_home": "2",
        "pleno_al_15_away": "1"
    }

# === MOCK FIXTURES ===

@pytest.fixture
def mock_api_football_response():
    """Mock API-Football response"""
    return {
        "response": [
            {
                "team": {
                    "id": 541,
                    "name": "Real Madrid",
                    "code": "RMA",
                    "country": "Spain",
                    "founded": 1902,
                    "logo": "https://media.api-sports.io/football/teams/541.png"
                },
                "venue": {
                    "id": 1456,
                    "name": "Santiago Bernabéu",
                    "capacity": 81044
                }
            }
        ]
    }

@pytest.fixture
def mock_fbref_data():
    """Mock FBRef data response"""
    return {
        "team_stats": {
            "goals": 2.1,
            "shots": 14.2,
            "xg": 1.8,
            "xa": 1.2,
            "pass_completion": 88.5
        }
    }

# === PERFORMANCE FIXTURES ===

@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
        
        @property
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return self.end_time - self.start_time
    
    return Timer()

# === EVENT LOOP FIXTURE FOR ASYNC TESTS ===

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()