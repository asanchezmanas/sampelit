# tests/test_contextual.py

import pytest
import asyncio
from engine.core.allocators.contextual import (
    ContextualAllocator,
    ContextExtractor,
    AdaptiveContextualAllocator
)


def test_context_extractor_normalizes_source():
    """Test source normalization"""
    
    raw = {'utm_source': 'Google.com'}
    normalized = ContextExtractor.extract(raw)
    
    assert normalized['source'] == 'google'


def test_context_extractor_detects_device():
    """Test device detection from user agent"""
    
    # Mobile
    raw = {'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)'}
    normalized = ContextExtractor.extract(raw)
    assert normalized['device'] == 'mobile'
    
    # Desktop
    raw = {'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    normalized = ContextExtractor.extract(raw)
    assert normalized['device'] == 'desktop'


def test_segment_key_building():
    """Test segment key construction"""
    
    allocator = ContextualAllocator({
        'context_features': ['source', 'device']
    })
    
    context = {'source': 'instagram', 'device': 'mobile'}
    segment_key = allocator._build_segment_key(context)
    
    # Should be sorted alphabetically
    assert segment_key == 'device:mobile|source:instagram'


def test_segment_key_with_utm_params():
    """Test segment key with UTM parameters"""
    
    allocator = ContextualAllocator({
        'context_features': ['source', 'device']
    })
    
    context = {
        'utm_source': 'instagram',
        'user_agent': 'Mozilla/5.0 (iPhone)'
    }
    
    segment_key = allocator._build_segment_key(context)
    assert 'source:instagram' in segment_key
    assert 'device:mobile' in segment_key


@pytest.mark.asyncio
async def test_contextual_uses_segment_state():
    """Test that contextual allocator uses segment-specific state"""
    
    allocator = ContextualAllocator({
        'context_features': ['source'],
        'min_samples_per_segment': 50
    })
    
    options = [
        {
            'id': 'v1',
            'algorithm_state': {'alpha': 10, 'beta': 90, 'samples': 100},  # Global
            '_segments': {
                'source:instagram': {'alpha': 20, 'beta': 80, 'samples': 100}  # Segment
            }
        }
    ]
    
    context = {'source': 'instagram'}
    
    # Select
    await allocator.select(options, context)
    
    # Should use segment state
    assert options[0]['_internal_state']['alpha'] == 20
    assert options[0]['_using_segment'] is True


@pytest.mark.asyncio
async def test_contextual_falls_back_to_global():
    """Test fallback to global state when segment has insufficient data"""
    
    allocator = ContextualAllocator({
        'context_features': ['source'],
        'min_samples_per_segment': 100
    })
    
    options = [
        {
            'id': 'v1',
            'algorithm_state': {'alpha': 10, 'beta': 90, 'samples': 200},  # Global (enough)
            '_segments': {
                'source:instagram': {'alpha': 5, 'beta': 5, 'samples': 10}  # Segment (not enough)
            }
        }
    ]
    
    context = {'source': 'instagram'}
    
    # Select
    await allocator.select(options, context)
    
    # Should use global state (fallback)
    assert options[0]['_internal_state']['alpha'] == 10
    assert options[0]['_using_segment'] is False


@pytest.mark.asyncio
async def test_update_segment_state():
    """Test updating segment-specific state"""
    
    allocator = ContextualAllocator({
        'context_features': ['source']
    })
    
    variant_state = {
        'alpha': 10,
        'beta': 90,
        'samples': 100,
        '_segments': {
            'source:instagram': {'alpha': 5, 'beta': 5, 'samples': 10}
        }
    }
    
    # Update with conversion
    updated = allocator.update_segment_state(
        variant_state,
        segment_key='source:instagram',
        reward=1.0
    )
    
    # Global state updated
    assert updated['alpha'] == 11
    assert updated['samples'] == 101
    
    # Segment state updated
    segment = updated['_segments']['source:instagram']
    assert segment['alpha'] == 6
    assert segment['samples'] == 11


@pytest.mark.asyncio
async def test_creates_new_segment_on_first_update():
    """Test creating new segment on first update"""
    
    allocator = ContextualAllocator({
        'context_features': ['source']
    })
    
    variant_state = {
        'alpha': 10,
        'beta': 90,
        'samples': 100,
        '_segments': {}  # No segments yet
    }
    
    # Update for new segment
    updated = allocator.update_segment_state(
        variant_state,
        segment_key='source:facebook',
        reward=1.0
    )
    
    # Segment should be created
    assert 'source:facebook' in updated['_segments']
    assert updated['_segments']['source:facebook']['alpha'] == 2.0


def test_get_top_segments():
    """Test getting top segments by traffic"""
    
    allocator = ContextualAllocator({
        'context_features': ['source']
    })
    
    # Simulate traffic
    allocator._segment_counts = {
        'source:instagram': 1000,
        'source:google': 500,
        'source:facebook': 200,
        'source:twitter': 50
    }
    
    top = allocator.get_top_segments(n=2)
    
    assert len(top) == 2
    assert top[0] == ('source:instagram', 1000)
    assert top[1] == ('source:google', 500)


def test_performance_metrics_include_segments():
    """Test metrics include segment info"""
    
    allocator = ContextualAllocator({
        'context_features': ['source', 'device']
    })
    
    allocator._segment_counts = {
        'source:instagram|device:mobile': 100,
        'source:google|device:desktop': 50
    }
    
    metrics = allocator.get_performance_metrics()
    
    assert metrics['contextual_enabled'] is True
    assert metrics['context_features'] == ['source', 'device']
    assert metrics['total_segments'] == 2


@pytest.mark.asyncio
async def test_different_segments_select_different_variants():
    """
    Test that different segments can select different variants
    
    This is the core value proposition of contextual bandits.
    """
    
    allocator = ContextualAllocator({
        'context_features': ['source'],
        'min_samples_per_segment': 50
    })
    
    options = [
        {
            'id': 'variant_a',
            'algorithm_state': {'alpha': 10, 'beta': 90, 'samples': 100},
            '_segments': {
                'source:instagram': {'alpha': 5, 'beta': 95, 'samples': 100},  # Bad for Instagram
                'source:google': {'alpha': 50, 'beta': 50, 'samples': 100}     # Good for Google
            }
        },
        {
            'id': 'variant_b',
            'algorithm_state': {'alpha': 10, 'beta': 90, 'samples': 100},
            '_segments': {
                'source:instagram': {'alpha': 60, 'beta': 40, 'samples': 100},  # Good for Instagram
                'source:google': {'alpha': 5, 'beta': 95, 'samples': 100}       # Bad for Google
            }
        }
    ]
    
    # Instagram context
    instagram_selections = []
    for _ in range(10):
        selected = await allocator.select(options.copy(), {'source': 'instagram'})
        instagram_selections.append(selected)
    
    # Google context
    google_selections = []
    for _ in range(10):
        selected = await allocator.select(options.copy(), {'source': 'google'})
        google_selections.append(selected)
    
    # Instagram should mostly select variant_b
    instagram_b_count = instagram_selections.count('variant_b')
    assert instagram_b_count >= 7, "Instagram should favor variant_b"
    
    # Google should mostly select variant_a
    google_a_count = google_selections.count('variant_a')
    assert google_a_count >= 7, "Google should favor variant_a"
    
    print(f"Instagram selected B: {instagram_b_count}/10")
    print(f"Google selected A: {google_a_count}/10")


def test_adaptive_contextual_combines_features():
    """Test AdaptiveContextualAllocator has both features"""
    
    allocator = AdaptiveContextualAllocator({
        'context_features': ['source'],
        'exploration_bonus': 0.2
    })
    
    assert hasattr(allocator, 'context_features')
    assert hasattr(allocator, 'exploration_bonus')
    assert allocator.exploration_bonus == 0.2


@pytest.mark.asyncio
async def test_contextual_performance_improvement():
    """
    Simulation: Test that contextual improves over non-contextual
    
    Setup:
      - 2 contexts with different best variants
      - Measure regret for contextual vs non-contextual
    """
    
    # True conversion rates per context
    true_rates = {
        'source:instagram': {'v1': 0.08, 'v2': 0.18},  # v2 is better
        'source:google': {'v1': 0.15, 'v2': 0.06},     # v1 is better
    }
    
    # Non-contextual allocator
    from engine.core.allocators.bayesian import BayesianAllocator
    non_contextual = BayesianAllocator()
    
    # Contextual allocator
    contextual = ContextualAllocator({
        'context_features': ['source'],
        'min_samples_per_segment': 50
    })
    
    # Simulate
    nc_regret = await simulate_regret(non_contextual, true_rates, n_trials=500, use_context=False)
    c_regret = await simulate_regret(contextual, true_rates, n_trials=500, use_context=True)
    
    print(f"Non-contextual regret: {nc_regret:.2f}")
    print(f"Contextual regret: {c_regret:.2f}")
    print(f"Improvement: {(nc_regret - c_regret) / nc_regret * 100:.0f}%")
    
    # Contextual should have lower regret
    assert c_regret < nc_regret, "Contextual should have lower regret"


async def simulate_regret(allocator, true_rates, n_trials, use_context):
    """
    Simulate experiment and calculate regret
    
    Regret = optimal_reward - actual_reward
    """
    import random
    
    variants = [
        {'id': 'v1', '_internal_state': {'alpha': 1, 'beta': 1, 'samples': 0}, '_segments': {}},
        {'id': 'v2', '_internal_state': {'alpha': 1, 'beta': 1, 'samples': 0}, '_segments': {}}
    ]
    
    total_reward = 0
    optimal_reward = 0
    
    for _ in range(n_trials):
        # Random context
        contexts = list(true_rates.keys())
        context_key = random.choice(contexts)
        context = {'source': context_key.split(':')[1]} if use_context else {}
        
        # Select
        selected_id = await allocator.select(variants, context)
        variant = next(v for v in variants if v['id'] == selected_id)
        
        # Simulate conversion
        true_rate = true_rates[context_key][selected_id]
        converted = random.random() < true_rate
        reward = 1.0 if converted else 0.0
        
        # Update
        if hasattr(allocator, 'update_segment_state') and use_context:
            segment_key = allocator._build_segment_key(context)
            variant['_internal_state'] = allocator.update_segment_state(
                variant['_internal_state'],
                segment_key,
                reward
            )
        else:
            variant['_internal_state'] = allocator.update_state(
                variant['_internal_state'],
                reward
            )
        
        # Track
        total_reward += reward
        optimal_rate = max(true_rates[context_key].values())
        optimal_reward += optimal_rate
    
    regret = optimal_reward - total_reward
    return regret
