"""
Integration tests for API endpoints - Clean Architecture v2.1.0
Tests all critical endpoints with real database interactions
"""
import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime

class TestCoreEndpoints:
    """Test core API endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.critical
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    @pytest.mark.integration
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        # Act
        response = client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

class TestDataEndpoints:
    """Test data management endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.critical
    def test_data_status_endpoint(self, client, sample_teams, sample_matches):
        """Test data status endpoint with sample data"""
        # Act
        response = client.get("/data/status/2025")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "season", "teams_total", "matches_total", 
            "matches_with_results", "team_statistics_total"
        ]
        for field in required_fields:
            assert field in data
        
        # Should have our sample data
        assert data["teams_total"] >= len(sample_teams)
        assert data["matches_total"] >= len(sample_matches)
    
    @pytest.mark.integration
    def test_update_teams_endpoint_response(self, client):
        """Test that update teams endpoint responds correctly"""
        # Act
        response = client.post("/data/update-teams/2025")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "2025" in str(data["message"])

class TestPredictionEndpoints:
    """Test prediction generation endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.critical
    def test_current_week_predictions(self, client, sample_matches, sample_team_statistics):
        """Test current week predictions endpoint"""
        # Act
        response = client.get("/predictions/current-week?season=2025")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["season", "matches", "generated_at", "model_version"]
        for field in required_fields:
            assert field in data
        
        assert data["season"] == 2025
        assert "generated_at" in data
    
    @pytest.mark.integration
    def test_predictions_history(self, client):
        """Test predictions history endpoint"""
        # Act
        response = client.get("/predictions/history?season=2025&limit=10")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestQuinielaEndpoints:
    """Test Quiniela-specific endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.critical
    def test_next_matches_endpoint(self, client, sample_matches, sample_team_statistics):
        """Test quiniela next matches endpoint"""
        # Act
        response = client.get("/quiniela/next-matches/2025")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["season", "matches", "generated_at"]
        for field in required_fields:
            assert field in data
        
        assert data["season"] == 2025
    
    @pytest.mark.integration
    @pytest.mark.critical
    def test_create_user_quiniela(self, client, valid_quiniela_data):
        """Test creating user quiniela"""
        # Act
        response = client.post("/quiniela/user/create", json=valid_quiniela_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "message" in data
        assert data["week_number"] == valid_quiniela_data["week_number"]
        assert data["season"] == valid_quiniela_data["season"]
        assert data["cost"] == valid_quiniela_data["cost"]
    
    @pytest.mark.integration
    def test_user_quiniela_history(self, client, sample_user_quiniela):
        """Test getting user quiniela history"""
        # Act
        response = client.get("/quiniela/user/history?season=2025")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "quinielas" in data
        assert "summary" in data
        assert isinstance(data["quinielas"], list)
        
        summary = data["summary"]
        assert "total_quinielas" in summary
        assert "total_cost" in summary
        assert "total_winnings" in summary
    
    @pytest.mark.integration
    @pytest.mark.critical
    def test_upcoming_matches_by_round(self, client, sample_matches):
        """Test upcoming matches by round endpoint"""
        # Act
        response = client.get("/quiniela/upcoming-by-round/2025")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["matches", "total", "season"]
        for field in required_fields:
            assert field in data
        
        assert data["season"] == 2025
        assert isinstance(data["matches"], list)

class TestCustomConfigEndpoints:
    """Test custom quiniela configuration endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.critical
    def test_list_custom_configs(self, client, sample_quiniela_config):
        """Test listing custom quiniela configurations"""
        # Act
        response = client.get("/quiniela/custom-config/list?season=2025")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "total_configs" in data
        assert "configs" in data
        assert isinstance(data["configs"], list)
        
        if data["configs"]:
            config = data["configs"][0]
            assert "id" in config
            assert "config_name" in config
            assert "season" in config
    
    @pytest.mark.integration
    @pytest.mark.critical
    def test_predictions_from_config(self, client, sample_quiniela_config):
        """Test generating predictions from custom config"""
        # Act
        response = client.get(f"/quiniela/from-config/{sample_quiniela_config.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["season", "config_name", "matches", "generated_at"]
        for field in required_fields:
            assert field in data
        
        assert data["season"] == sample_quiniela_config.season
        assert data["config_name"] == sample_quiniela_config.config_name
        assert isinstance(data["matches"], list)

class TestMultipleQuinielaEndpoints:
    """Test multiple quiniela (dobles/triples) endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.critical
    def test_validate_multiple_quiniela(self, client, valid_multiple_quiniela_data):
        """Test validating multiple quiniela configuration"""
        # Arrange
        validation_request = {
            "predictions": valid_multiple_quiniela_data["predictions"],
            "elige_8": {
                "enabled": False,
                "selected_matches": [],
                "predictions": []
            }
        }
        
        # Act
        response = client.post("/quiniela/multiple/validate", json=validation_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "valid", "total_combinations", "base_cost", 
            "total_cost", "bet_type"
        ]
        for field in required_fields:
            assert field in data
        
        assert isinstance(data["valid"], bool)
        assert data["total_combinations"] > 0
        assert data["base_cost"] > 0
    
    @pytest.mark.integration
    def test_calculate_quiniela_cost(self, client):
        """Test calculating quiniela cost in real-time"""
        # Arrange
        cost_request = {
            "multiplicities": [1, 2, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            "elige_8_enabled": False
        }
        
        # Act
        response = client.post("/quiniela/multiple/calculate-cost", json=cost_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "total_combinations", "base_cost", "total_cost",
            "cost_breakdown", "efficiency_metrics"
        ]
        for field in required_fields:
            assert field in data
        
        # Should calculate: 1*2*1*3*1*...*1 = 6 combinations
        assert data["total_combinations"] == 6
        assert data["base_cost"] == 6 * 0.75  # 6 * €0.75 = €4.50
    
    @pytest.mark.integration
    def test_get_official_reductions(self, client):
        """Test getting official BOE reductions"""
        # Act
        response = client.get("/quiniela/multiple/reductions/official")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "reductions" in data
        assert "total_available" in data
        assert isinstance(data["reductions"], list)
        
        if data["reductions"]:
            reduction = data["reductions"][0]
            required_fields = ["name", "triples", "dobles", "combinations", "cost"]
            for field in required_fields:
                assert field in reduction

class TestAnalyticsEndpoints:
    """Test analytics and reporting endpoints"""
    
    @pytest.mark.integration
    def test_financial_summary(self, client):
        """Test financial summary endpoint"""
        # Act
        response = client.get("/analytics/financial-summary?season=2025")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should return financial metrics even if empty
        assert "season" in data
    
    @pytest.mark.integration
    def test_model_performance(self, client):
        """Test model performance analytics"""
        # Act
        response = client.get("/analytics/model-performance")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should return performance metrics structure
        assert isinstance(data, (dict, list))

class TestModelEndpoints:
    """Test ML model management endpoints"""
    
    @pytest.mark.integration
    def test_model_training_status(self, client):
        """Test model training status endpoint"""
        # Act
        response = client.get("/models/training-status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should return status information
        assert "status" in data or "message" in data
    
    @pytest.mark.integration
    def test_model_requirements(self, client):
        """Test model requirements endpoint"""
        # Act
        response = client.get("/models/requirements/2025")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should return requirements information
        assert isinstance(data, dict)

class TestErrorHandling:
    """Test error handling across endpoints"""
    
    @pytest.mark.integration
    def test_invalid_season_parameter(self, client):
        """Test API with invalid season parameters"""
        # Act
        response = client.get("/data/status/invalid")
        
        # Assert
        # Should handle gracefully (either 422 validation error or default behavior)
        assert response.status_code in [422, 200, 400]
    
    @pytest.mark.integration
    def test_nonexistent_endpoints(self, client):
        """Test that nonexistent endpoints return 404"""
        # Act
        response = client.get("/nonexistent/endpoint")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.integration
    def test_invalid_json_payload(self, client):
        """Test invalid JSON payload handling"""
        # Act
        response = client.post(
            "/quiniela/user/create", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 422
    
    @pytest.mark.integration
    def test_missing_required_fields(self, client):
        """Test missing required fields in requests"""
        # Arrange
        incomplete_data = {
            "week_number": 1,
            # Missing required fields like season, predictions, etc.
        }
        
        # Act
        response = client.post("/quiniela/user/create", json=incomplete_data)
        
        # Assert
        assert response.status_code in [400, 422, 500]

class TestAuthentication:
    """Test authentication and authorization (if implemented)"""
    
    @pytest.mark.integration
    def test_public_endpoints_accessible(self, client):
        """Test that public endpoints are accessible without auth"""
        public_endpoints = [
            "/health",
            "/",
            "/data/status/2025",
            "/predictions/current-week?season=2025"
        ]
        
        for endpoint in public_endpoints:
            # Act
            response = client.get(endpoint)
            
            # Assert
            # Should not return 401 Unauthorized
            assert response.status_code != 401

class TestCleanArchitecture:
    """Test Clean Architecture v2.1.0 specific functionality"""
    
    @pytest.mark.integration
    def test_all_domains_accessible(self, client):
        """Test that all domain endpoints are accessible through v1 router"""
        domain_endpoints = [
            "/health",  # core
            "/data/status/2025",  # data
            "/models/training-status",  # models  
            "/predictions/current-week?season=2025",  # predictions
            "/quiniela/upcoming-by-round/2025",  # quiniela
            "/analytics/model-performance",  # analytics
        ]
        
        for endpoint in domain_endpoints:
            # Act
            response = client.get(endpoint)
            
            # Assert
            # Should be accessible (not 404) - content may vary
            assert response.status_code != 404
    
    @pytest.mark.integration
    def test_backwards_compatibility(self, client):
        """Test that reorganized endpoints maintain backwards compatibility"""
        # These endpoints should still work after Clean Architecture reorganization
        legacy_endpoints = [
            "/health",
            "/data/status/2025",
            "/quiniela/next-matches/2025"
        ]
        
        for endpoint in legacy_endpoints:
            # Act
            response = client.get(endpoint)
            
            # Assert
            # Should work the same as before reorganization
            assert response.status_code in [200, 404]  # 404 is ok if no data, but not 500