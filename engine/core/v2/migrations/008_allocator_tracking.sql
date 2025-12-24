-- Migration 008: Allocator Tracking & Benchmarking
-- Date: 2024-12
-- Purpose: Track which algorithm is used per experiment and enable A/B testing of algorithms

-- ============================================
-- 1. Add strategy column to experiments
-- ============================================

ALTER TABLE experiments 
ADD COLUMN IF NOT EXISTS allocation_strategy VARCHAR(50) DEFAULT 'adaptive';

COMMENT ON COLUMN experiments.allocation_strategy IS 
'Algorithm used for this experiment: thompson, adaptive, epsilon_greedy, ucb, etc.';

-- Index for analytics
CREATE INDEX IF NOT EXISTS idx_experiments_strategy 
ON experiments(allocation_strategy);

-- ============================================
-- 2. Algorithm performance tracking
-- ============================================

CREATE TABLE IF NOT EXISTS algorithm_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    strategy VARCHAR(50) NOT NULL,
    
    -- Performance metrics
    total_selections BIGINT DEFAULT 0,
    total_updates BIGINT DEFAULT 0,
    avg_selection_time_ms FLOAT,
    avg_update_time_ms FLOAT,
    
    -- Results
    final_conversion_rate FLOAT,
    total_conversions BIGINT,
    total_visits BIGINT,
    
    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    
    -- Metadata
    config JSONB,
    metrics JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_algorithm_perf_experiment 
ON algorithm_performance(experiment_id);

CREATE INDEX idx_algorithm_perf_strategy 
ON algorithm_performance(strategy);

COMMENT ON TABLE algorithm_performance IS 
'Tracks performance of different allocation algorithms';

-- ============================================
-- 3. Algorithm benchmarks (A/B test algorithms)
-- ============================================

CREATE TABLE IF NOT EXISTS algorithm_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- What we're comparing
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Algorithms being compared
    strategy_a VARCHAR(50) NOT NULL,
    strategy_b VARCHAR(50) NOT NULL,
    
    -- Config for each
    config_a JSONB,
    config_b JSONB,
    
    -- Results
    winner VARCHAR(50),  -- 'strategy_a', 'strategy_b', or NULL if inconclusive
    confidence FLOAT,    -- Statistical confidence (0.0 - 1.0)
    
    -- Metrics
    strategy_a_metrics JSONB,
    strategy_b_metrics JSONB,
    
    -- Status
    status VARCHAR(50) DEFAULT 'running',  -- running, completed, stopped
    
    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_benchmarks_status 
ON algorithm_benchmarks(status);

CREATE INDEX idx_benchmarks_strategies 
ON algorithm_benchmarks(strategy_a, strategy_b);

COMMENT ON TABLE algorithm_benchmarks IS 
'A/B tests comparing different allocation algorithms';

-- ============================================
-- 4. Experiments linked to benchmarks
-- ============================================

CREATE TABLE IF NOT EXISTS benchmark_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_id UUID NOT NULL REFERENCES algorithm_benchmarks(id) ON DELETE CASCADE,
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Which strategy this experiment uses
    assigned_strategy VARCHAR(50) NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(benchmark_id, experiment_id)
);

CREATE INDEX idx_benchmark_experiments_benchmark 
ON benchmark_experiments(benchmark_id);

CREATE INDEX idx_benchmark_experiments_experiment 
ON benchmark_experiments(experiment_id);

-- ============================================
-- 5. Update trigger for algorithm_performance
-- ============================================

CREATE OR REPLACE FUNCTION update_algorithm_performance_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_algorithm_performance_updated
    BEFORE UPDATE ON algorithm_performance
    FOR EACH ROW
    EXECUTE FUNCTION update_algorithm_performance_timestamp();

-- ============================================
-- 6. Helper views
-- ============================================

-- View: Algorithm performance summary
CREATE OR REPLACE VIEW v_algorithm_performance_summary AS
SELECT 
    strategy,
    COUNT(*) as experiment_count,
    AVG(final_conversion_rate) as avg_conversion_rate,
    AVG(total_visits) as avg_visits,
    AVG(avg_selection_time_ms) as avg_latency_ms
FROM algorithm_performance
WHERE ended_at IS NOT NULL
GROUP BY strategy;

COMMENT ON VIEW v_algorithm_performance_summary IS 
'Summary of algorithm performance across all experiments';

-- ============================================
-- 7. Sample data (for development)
-- ============================================

-- Insert sample benchmark
INSERT INTO algorithm_benchmarks (
    name,
    description,
    strategy_a,
    strategy_b,
    config_a,
    config_b,
    status
) VALUES (
    'Thompson vs UCB Comparison',
    'Comparing Thompson Sampling vs UCB on low-traffic experiments',
    'thompson',
    'ucb',
    '{"alpha_prior": 1.0, "beta_prior": 1.0}',
    '{"c": 2.0, "min_samples": 30}',
    'running'
) ON CONFLICT DO NOTHING;
