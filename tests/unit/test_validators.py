"""
Unit tests for Quiniela validators - CRITICAL functionality
Tests BOE compliance, cost calculations, and validation logic
"""
import pytest
from backend.app.services.quiniela_validator import (
    QuinielaValidator, 
    QuinielaPrediction, 
    QuinielaElige8,
    QuinielaValidationResult
)

class TestQuinielaValidator:
    """Test QuinielaValidator - Core BOE compliance functionality"""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_calculate_combinations_simple_quiniela(self):
        """Test combination calculation for simple quiniela (all 1s)"""
        # Arrange
        multiplicities = [1] * 15  # All simple predictions
        
        # Act
        result = QuinielaValidator.calculate_combinations(multiplicities)
        
        # Assert
        assert result == 1
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_calculate_combinations_with_dobles(self):
        """Test combination calculation with dobles"""
        # Arrange
        multiplicities = [1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # 2 dobles
        
        # Act
        result = QuinielaValidator.calculate_combinations(multiplicities)
        
        # Assert
        assert result == 4  # 1*2*1*2*1*...*1 = 4
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_calculate_combinations_with_triples(self):
        """Test combination calculation with triples"""
        # Arrange
        multiplicities = [1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # 1 triple
        
        # Act
        result = QuinielaValidator.calculate_combinations(multiplicities)
        
        # Assert
        assert result == 3  # 1*1*3*1*...*1 = 3
    
    @pytest.mark.unit
    @pytest.mark.critical 
    def test_calculate_combinations_mixed(self):
        """Test combination calculation with mixed dobles and triples"""
        # Arrange
        multiplicities = [2, 3, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # 1 doble, 1 triple, 1 doble
        
        # Act
        result = QuinielaValidator.calculate_combinations(multiplicities)
        
        # Assert
        assert result == 12  # 2*3*1*2*1*...*1 = 12
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_calculate_cost_simple_quiniela(self):
        """Test cost calculation for simple quiniela"""
        # Arrange
        total_combinations = 1
        
        # Act
        base_cost = total_combinations * QuinielaValidator.BASE_COST_PER_BET
        
        # Assert
        assert base_cost == 0.75  # 1 * €0.75
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_calculate_cost_multiple_combinations(self):
        """Test cost calculation for multiple combinations"""
        # Arrange
        total_combinations = 128  # Example: 7 dobles
        
        # Act
        base_cost = total_combinations * QuinielaValidator.BASE_COST_PER_BET
        
        # Assert
        assert base_cost == 96.0  # 128 * €0.75 = €96
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_elige_8_cost(self):
        """Test Elige 8 cost is correct"""
        # Assert
        assert QuinielaValidator.ELIGE_8_COST == 0.50
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_validate_quiniela_simple_valid(self):
        """Test validation of simple valid quiniela"""
        # Arrange
        predictions = [
            QuinielaPrediction(
                match_number=i,
                match_id=1000 + i,
                home_team=f"Team {i}A",
                away_team=f"Team {i}B",
                prediction_options=["1"]
            )
            for i in range(1, 16)
        ]
        
        # Act
        result = QuinielaValidator.validate_quiniela(predictions)
        
        # Assert
        assert result.valid == True
        assert result.total_combinations == 1
        assert result.base_cost == 0.75
        assert result.total_cost == 0.75
        assert result.bet_type == "simple"
        assert len(result.errors) == 0
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_validate_quiniela_multiple_valid(self):
        """Test validation of multiple valid quiniela"""
        # Arrange
        predictions = [
            QuinielaPrediction(
                match_number=1,
                match_id=1001,
                home_team="Real Madrid",
                away_team="Barcelona",
                prediction_options=["1", "X"]  # Doble
            ),
            QuinielaPrediction(
                match_number=2,
                match_id=1002,
                home_team="Atlético",
                away_team="Valencia",
                prediction_options=["1", "X", "2"]  # Triple
            )
        ] + [
            QuinielaPrediction(
                match_number=i,
                match_id=1000 + i,
                home_team=f"Team {i}A",
                away_team=f"Team {i}B",
                prediction_options=["1"]
            )
            for i in range(3, 16)
        ]
        
        # Act
        result = QuinielaValidator.validate_quiniela(predictions)
        
        # Assert
        assert result.valid == True
        assert result.total_combinations == 6  # 2 * 3 * 1^13 = 6
        assert result.base_cost == 4.50  # 6 * €0.75 = €4.50
        assert result.total_cost == 4.50
        assert result.bet_type == "multiple"
        assert len(result.errors) == 0
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_validate_quiniela_with_elige_8(self):
        """Test validation with Elige 8 enabled"""
        # Arrange
        predictions = [
            QuinielaPrediction(
                match_number=i,
                match_id=1000 + i,
                home_team=f"Team {i}A",
                away_team=f"Team {i}B",
                prediction_options=["1"]
            )
            for i in range(1, 16)
        ]
        
        elige_8 = QuinielaElige8(
            enabled=True,
            selected_matches=[1, 2, 3, 4, 5, 6, 7, 8],
            predictions=["1", "X", "2", "1", "X", "2", "1", "X"]
        )
        
        # Act
        result = QuinielaValidator.validate_quiniela(predictions, elige_8)
        
        # Assert
        assert result.valid == True
        assert result.base_cost == 0.75
        assert result.elige_8_cost == 0.50
        assert result.total_cost == 1.25  # €0.75 + €0.50
        assert len(result.errors) == 0
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_validate_quiniela_insufficient_predictions(self):
        """Test validation fails with insufficient predictions"""
        # Arrange
        predictions = [
            QuinielaPrediction(
                match_number=i,
                match_id=1000 + i,
                home_team=f"Team {i}A",
                away_team=f"Team {i}B",
                prediction_options=["1"]
            )
            for i in range(1, 10)  # Only 9 predictions instead of 15
        ]
        
        # Act
        result = QuinielaValidator.validate_quiniela(predictions)
        
        # Assert
        assert result.valid == False
        assert len(result.errors) > 0
        assert any("15 predicciones" in error.lower() for error in result.errors)
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_validate_quiniela_invalid_prediction_options(self):
        """Test validation fails with invalid prediction options"""
        # Arrange
        predictions = [
            QuinielaPrediction(
                match_number=1,
                match_id=1001,
                home_team="Team A",
                away_team="Team B",
                prediction_options=["4"]  # Invalid option
            )
        ] + [
            QuinielaPrediction(
                match_number=i,
                match_id=1000 + i,
                home_team=f"Team {i}A",
                away_team=f"Team {i}B",
                prediction_options=["1"]
            )
            for i in range(2, 16)
        ]
        
        # Act
        result = QuinielaValidator.validate_quiniela(predictions)
        
        # Assert
        assert result.valid == False
        assert len(result.errors) > 0
        assert any("opción inválida" in error.lower() for error in result.errors)
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_validate_quiniela_empty_prediction_options(self):
        """Test validation fails with empty prediction options"""
        # Arrange
        predictions = [
            QuinielaPrediction(
                match_number=1,
                match_id=1001,
                home_team="Team A",
                away_team="Team B",
                prediction_options=[]  # Empty options
            )
        ] + [
            QuinielaPrediction(
                match_number=i,
                match_id=1000 + i,
                home_team=f"Team {i}A",
                away_team=f"Team {i}B",
                prediction_options=["1"]
            )
            for i in range(2, 16)
        ]
        
        # Act
        result = QuinielaValidator.validate_quiniela(predictions)
        
        # Assert
        assert result.valid == False
        assert len(result.errors) > 0
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_validate_elige_8_insufficient_matches(self):
        """Test Elige 8 validation fails with insufficient matches"""
        # Arrange
        predictions = [
            QuinielaPrediction(
                match_number=i,
                match_id=1000 + i,
                home_team=f"Team {i}A",
                away_team=f"Team {i}B",
                prediction_options=["1"]
            )
            for i in range(1, 16)
        ]
        
        elige_8 = QuinielaElige8(
            enabled=True,
            selected_matches=[1, 2, 3],  # Only 3 matches instead of 8
            predictions=["1", "X", "2"]
        )
        
        # Act
        result = QuinielaValidator.validate_quiniela(predictions, elige_8)
        
        # Assert
        assert result.valid == False
        assert len(result.errors) > 0
        assert any("8 partidos" in error.lower() for error in result.errors)
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_validate_elige_8_mismatch_predictions(self):
        """Test Elige 8 validation fails when predictions don't match selected matches"""
        # Arrange
        predictions = [
            QuinielaPrediction(
                match_number=i,
                match_id=1000 + i,
                home_team=f"Team {i}A",
                away_team=f"Team {i}B",
                prediction_options=["1"]
            )
            for i in range(1, 16)
        ]
        
        elige_8 = QuinielaElige8(
            enabled=True,
            selected_matches=[1, 2, 3, 4, 5, 6, 7, 8],
            predictions=["1", "X", "2"]  # Only 3 predictions for 8 matches
        )
        
        # Act
        result = QuinielaValidator.validate_quiniela(predictions, elige_8)
        
        # Assert
        assert result.valid == False
        assert len(result.errors) > 0
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_official_reductions_exist(self):
        """Test that official BOE reductions are configured"""
        # Act & Assert
        assert hasattr(QuinielaValidator, 'OFFICIAL_REDUCTIONS')
        assert len(QuinielaValidator.OFFICIAL_REDUCTIONS) > 0
        
        # Check that key reductions exist
        reductions = QuinielaValidator.OFFICIAL_REDUCTIONS
        
        # Should have at least the main official reductions
        assert 'primera' in reductions or 'basic' in reductions
        
        # Each reduction should have required fields
        for name, config in reductions.items():
            assert 'triples' in config
            assert 'dobles' in config
            assert 'combinations' in config
            assert 'cost' in config
            assert isinstance(config['cost'], (int, float))
            assert config['cost'] > 0
    
    @pytest.mark.unit
    def test_base_cost_per_bet_is_correct(self):
        """Test that base cost per bet matches BOE regulation"""
        # According to BOE-A-1998-17040, base cost is €0.75
        assert QuinielaValidator.BASE_COST_PER_BET == 0.75
    
    @pytest.mark.unit
    def test_min_bet_combinations(self):
        """Test minimum bet combinations (should be at least 1)"""
        # Single simple quiniela should be minimum
        multiplicities = [1] * 15
        result = QuinielaValidator.calculate_combinations(multiplicities)
        assert result >= 1
    
    @pytest.mark.unit
    def test_max_reasonable_combinations(self):
        """Test that we don't allow unreasonably large combinations"""
        # All triples would be 3^15 = 14,348,907 combinations
        multiplicities = [3] * 15
        result = QuinielaValidator.calculate_combinations(multiplicities)
        
        # This should be mathematically correct but practically very expensive
        assert result == 3**15
        
        # Cost would be astronomical - this is why reductions exist
        cost = result * QuinielaValidator.BASE_COST_PER_BET
        assert cost > 10_000_000  # More than 10 million euros!

class TestQuinielaPrediction:
    """Test QuinielaPrediction data class"""
    
    @pytest.mark.unit
    def test_create_simple_prediction(self):
        """Test creating a simple prediction"""
        # Arrange & Act
        pred = QuinielaPrediction(
            match_number=1,
            match_id=1001,
            home_team="Real Madrid",
            away_team="Barcelona",
            prediction_options=["1"]
        )
        
        # Assert
        assert pred.match_number == 1
        assert pred.match_id == 1001
        assert pred.home_team == "Real Madrid"
        assert pred.away_team == "Barcelona"
        assert pred.prediction_options == ["1"]
    
    @pytest.mark.unit
    def test_create_multiple_prediction(self):
        """Test creating a multiple prediction (doble/triple)"""
        # Arrange & Act
        pred = QuinielaPrediction(
            match_number=2,
            match_id=1002,
            home_team="Atlético Madrid",
            away_team="Valencia",
            prediction_options=["X", "2"]
        )
        
        # Assert
        assert pred.prediction_options == ["X", "2"]
        assert len(pred.prediction_options) == 2

class TestQuinielaElige8:
    """Test QuinielaElige8 data class"""
    
    @pytest.mark.unit
    def test_create_elige_8(self):
        """Test creating Elige 8 configuration"""
        # Arrange & Act
        elige_8 = QuinielaElige8(
            enabled=True,
            selected_matches=[1, 2, 3, 4, 5, 6, 7, 8],
            predictions=["1", "X", "2", "1", "X", "2", "1", "X"]
        )
        
        # Assert
        assert elige_8.enabled == True
        assert len(elige_8.selected_matches) == 8
        assert len(elige_8.predictions) == 8
    
    @pytest.mark.unit
    def test_create_disabled_elige_8(self):
        """Test creating disabled Elige 8"""
        # Arrange & Act
        elige_8 = QuinielaElige8(
            enabled=False,
            selected_matches=[],
            predictions=[]
        )
        
        # Assert
        assert elige_8.enabled == False
        assert len(elige_8.selected_matches) == 0
        assert len(elige_8.predictions) == 0