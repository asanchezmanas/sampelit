-- migrations/011_performance_indexes.sql

-- ============================================
-- Performance-critical indexes
-- ============================================

-- 1. Assignments - hot path queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_experiment_created 
ON assignments(experiment_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_user_experiment 
ON assignments(user_identifier, experiment_id);

-- Partial index for active assignments only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_active 
ON assignments(experiment_id, variant_id) 
WHERE converted_at IS NULL;

-- 2. Conversions - frequent joins
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_assignment 
ON conversions(assignment_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_created 
ON conversions(created_at DESC);

-- 3. Variants - state lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_variants_experiment_active 
ON element_variants(experiment_id) 
WHERE is_active = true;

-- 4. Context segments - contextual bandits hot path
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_segments_lookup 
ON context_segments(experiment_id, segment_key) 
INCLUDE (id, total_visits);

-- Partial index for active segments only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_segments_active 
ON context_segments(experiment_id, segment_key) 
WHERE total_visits >= 50;

-- 5. Variant segment performance - critical for contextual
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_variant_segment_lookup 
ON variant_segment_performance(variant_id, segment_id) 
INCLUDE (alpha, beta, samples);

-- 6. Covering index for common query pattern
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_covering 
ON assignments(experiment_id, user_identifier) 
INCLUDE (variant_id, created_at);

-- ============================================
-- Analyze tables after index creation
-- ============================================

ANALYZE assignments;
ANALYZE conversions;
ANALYZE element_variants;
ANALYZE context_segments;
ANALYZE variant_segment_performance;

-- ============================================
-- Index maintenance function
-- ============================================

CREATE OR REPLACE FUNCTION reindex_critical_tables()
RETURNS void AS $$
BEGIN
    -- Reindex concurrently to avoid locking
    REINDEX TABLE CONCURRENTLY assignments;
    REINDEX TABLE CONCURRENTLY conversions;
    REINDEX TABLE CONCURRENTLY element_variants;
    REINDEX TABLE CONCURRENTLY context_segments;
    REINDEX TABLE CONCURRENTLY variant_segment_performance;
    
    -- Update statistics
    ANALYZE assignments;
    ANALYZE conversions;
    ANALYZE element_variants;
    ANALYZE context_segments;
    ANALYZE variant_segment_performance;
END;
$$ LANGUAGE plpgsql;

-- Schedule via cron: SELECT reindex_critical_tables();
