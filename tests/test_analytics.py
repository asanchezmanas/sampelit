import pytest
from orchestration.services.analytics_service import AnalyticsService

class TestAnalyticsService:
    """Analytics service unit tests"""
    
    @pytest.mark.asyncio
    async def test_analyze_experiment_basic(self):
        """Test basic experiment analysis"""
        service = AnalyticsService()
        
        variants = [
            {
                'id': 'var-1',
                'name': 'Control',
                'total_allocations': 1000,
                'total_conversions': 100
            },
            {
                'id': 'var-2',
                'name': 'Variant A',
                'total_allocations': 1000,
                'total_conversions': 120
            }
        ]
        
        result = await service.analyze_experiment('test-exp', variants)
        
        assert result['variant_count'] == 2
        assert result['total_allocations'] == 2000
        assert result['total_conversions'] == 220
        assert 'bayesian_analysis' in result
        assert 'variants' in result
    
    @pytest.mark.asyncio
    async def test_bayesian_winner_selection(self):
        """Test Bayesian analysis selects winner"""
        service = AnalyticsService()
        
        variants = [
            {
                'id': 'var-1',
                'name': 'Control',
                'total_allocations': 1000,
                'total_conversions': 50  # 5%
            },
            {
                'id': 'var-2',
                'name': 'Winner',
                'total_allocations': 1000,
                'total_conversions': 150  # 15% - clear winner
            }
        ]
        
        result = await service.analyze_experiment('test-exp', variants)
        winner = result['bayesian_analysis']['winner']
        
        assert winner['variant_name'] == 'Winner'
        assert winner['probability_best'] > 0.9  # Should be very confident
    
    @pytest.mark.asyncio
    async def test_empty_variants(self):
        """Test analysis with no variants"""
        service = AnalyticsService()
        
        result = await service.analyze_experiment('test-exp', [])
        
        assert result['variant_count'] == 0
        assert result['total_allocations'] == 0
        assert result['variants'] == []
    
    def test_confidence_interval_calculation(self):
        """Test Wilson confidence interval"""
        service = AnalyticsService()
        
        lower, upper = service._calculate_confidence_interval(
            conversions=100,
            allocations=1000,
            confidence=0.95
        )
        
        # 100/1000 = 0.1 (10%)
        assert 0 <= lower <= 0.1
        assert 0.1 <= upper <= 1
        assert lower < upper
    
    def test_confidence_interval_edge_cases(self):
        """Test confidence interval with edge cases"""
        service = AnalyticsService()
        
        # Zero allocations
        lower, upper = service._calculate_confidence_interval(0, 0)
        assert lower == 0.0
        assert upper == 0.0
        
        # Perfect conversion
        lower, upper = service._calculate_confidence_interval(100, 100)
        assert lower < 1.0
        assert upper == 1.0
    
    def test_statistical_significance(self):
        """Test significance calculation"""
        service = AnalyticsService()
        
        # Clear difference
        p_value, is_sig = service._calculate_significance(
            conversions=150,
            allocations=1000,
            baseline_cr=0.10,  # 10% baseline
            alpha=0.05
        )
        
        # 150/1000 = 15% vs 10% baseline should be significant
        assert is_sig == True
        assert p_value < 0.05
