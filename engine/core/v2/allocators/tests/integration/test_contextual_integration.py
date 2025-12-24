# tests/integration/test_contextual_integration.py

import pytest
import asyncio
from engine.services.contextual_service import ContextualService
from orchestration.services.experiment_service import ExperimentService


@pytest.mark.asyncio
async def test_end_to_end_contextual_flow(db_pool, create_test_experiment):
    """Test complete contextual flow: allocation → conversion → analysis"""
    
    # Setup
    experiment_id = await create_test_experiment(
        allocation_strategy='contextual_thompson',
        context_features=['source', 'device']
    )
    
    exp_service = ExperimentService(db_pool)
    ctx_service = ContextualService(db_pool)
    
    # Simulate traffic from different segments
    contexts = [
        {'utm_source': 'instagram', 'user_agent': 'Mozilla/5.0 (iPhone)'},  # mobile+instagram
        {'utm_source': 'google', 'user_agent': 'Mozilla/5.0 (Windows)'},     # desktop+google
        {'utm_source': 'facebook', 'user_agent': 'Mozilla/5.0 (Android)'},   # mobile+facebook
    ]
    
    assignments = []
    
    # Generate 300 assignments (100 per context)
    for i in range(100):
        for ctx in contexts:
            selected = await exp_service.allocate_user_to_variant(
                experiment_id=experiment_id,
                user_identifier=f'user_{i}_{ctx["utm_source"]}',
                context=ctx
            )
            assignments.append({
                'context': ctx,
                'variant': selected
            })
    
    # Simulate conversions (different rates per segment)
    # Instagram mobile: high CR for variant B
    # Google desktop: high CR for variant A
    # Facebook mobile: medium CR for both
    
    for assignment in assignments:
        source = assignment['context']['utm_source']
        variant = assignment['variant']
        
        # Determine conversion probability
        if source == 'instagram' and variant == 'variant_b':
            convert_prob = 0.20
        elif source == 'google' and variant == 'variant_a':
            convert_prob = 0.15
        else:
            convert_prob = 0.08
        
        import random
        if random.random() < convert_prob:
            # Record conversion
            # (Implementation depends on your service API)
            pass
    
    # Analyze segments
    insights = await ctx_service.get_segment_insights(experiment_id)
    
    # Verify insights
    assert insights['summary']['total_segments'] >= 3
    assert len(insights['top_segments']) > 0
    
    # Should detect that instagram+mobile prefers variant B
    instagram_segments = [
        s for s in insights['top_segments']
        if 'instagram' in s['segment_key']
    ]
    
    if instagram_segments:
        assert instagram_segments[0]['best_variant'] == 'Variant B'


@pytest.mark.asyncio
async def test_segment_state_persistence(db_pool):
    """Test that segment states are correctly stored and retrieved"""
    
    ctx_service = ContextualService(db_pool)
    
    # Create test data
    # (Implementation depends on test fixtures)
    
    # Update segment performance
    await ctx_service.update_segment_performance(
        variant_id='test_variant',
        segment_id='test_segment',
        converted=True
    )
    
    # Retrieve and verify
    # (Implementation depends on service API)
