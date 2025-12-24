-- ============================================================================
-- MIGRATION V3.1: Contextual Bandits
-- ============================================================================
-- Adds contextual bandits support to V2 architecture
--
-- Integration with V2:
-- - Uses existing variant_segment_state table (Fase 1)
-- - Compatible with FeatureEngineeringService (Fase 2)
-- - Works with ClusteringServiceV2 (Fase 3)
-- - Integrates with SampleSizeCalculator (Fase 4)
--
-- New capabilities:
-- - Context-aware segment tracking
-- - Per-segment performance analytics
-- - Lift analysis
-- - Statistical significance testing
-- ============================================================================

-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 1: Context Segments Table                                          │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS context_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Segment identification
    segment_key VARCHAR(500) NOT NULL,
    -- Format: "device:mobile|source:instagram"
    -- Matches segment_key in variant_segment_state (V2 Fase 1)
    
    -- Context metadata (extracted features)
    context_features JSONB NOT NULL,
    -- Example: {"source": "instagram", "device": "mobile", "country": "US"}
    
    -- Aggregated statistics
    total_visits INT DEFAULT 0,
    total_conversions INT DEFAULT 0,
    
    -- Timestamps
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(experiment_id, segment_key)
);

CREATE INDEX idx_context_segments_experiment ON context_segments(experiment_id);
CREATE INDEX idx_context_segments_key ON context_segments(segment_key);
CREATE INDEX idx_context_segments_visits ON context_segments(total_visits DESC);
CREATE INDEX idx_context_segments_features ON context_segments USING GIN(context_features);

COMMENT ON TABLE context_segments IS 
'Context-based segments for contextual bandits. Aggregates stats per segment.';

COMMENT ON COLUMN context_segments.segment_key IS 
'Segment identifier matching variant_segment_state.segment_key from V2';

COMMENT ON COLUMN context_segments.context_features IS 
'Extracted and normalized context features (from FeatureEngineeringService V2)';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 2: Update Assignments Table (Add Context)                          │
-- └──────────────────────────────────────────────────────────────────────────┘

-- Add columns to track context for each assignment
ALTER TABLE assignments 
ADD COLUMN IF NOT EXISTS context_data JSONB,
ADD COLUMN IF NOT EXISTS segment_id UUID REFERENCES context_segments(id);

CREATE INDEX IF NOT EXISTS idx_assignments_segment ON assignments(segment_id);
CREATE INDEX IF NOT EXISTS idx_assignments_context ON assignments USING GIN(context_data);

COMMENT ON COLUMN assignments.context_data IS 
'Raw context data from user request (device, source, geo, etc)';

COMMENT ON COLUMN assignments.segment_id IS 
'Link to context_segments table for this assignment';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 3: Segment Performance View                                        │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE VIEW v_segment_performance AS
SELECT 
    cs.id as segment_id,
    cs.experiment_id,
    cs.segment_key,
    cs.context_features,
    cs.total_visits,
    cs.total_conversions,
    CASE 
        WHEN cs.total_visits > 0 
        THEN cs.total_conversions::FLOAT / cs.total_visits
        ELSE 0.0
    END as conversion_rate,
    
    -- Best variant for this segment (from variant_segment_state)
    (
        SELECT ev.name
        FROM variant_segment_state vss
        JOIN element_variants ev ON ev.id = vss.variant_id
        WHERE vss.segment_key = cs.segment_key
        ORDER BY (vss.alpha / (vss.alpha + vss.beta)) DESC NULLS LAST
        LIMIT 1
    ) as best_variant,
    
    -- Number of variants with data for this segment
    (
        SELECT COUNT(*)
        FROM variant_segment_state vss
        WHERE vss.segment_key = cs.segment_key
          AND vss.samples >= 10
    ) as variants_with_data,
    
    cs.first_seen_at,
    cs.last_seen_at
    
FROM context_segments cs
WHERE cs.total_visits >= 10;

COMMENT ON VIEW v_segment_performance IS 
'Overview of segment performance with best variant';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 4: Segment Lift Analysis View                                      │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE VIEW v_segment_lift AS
SELECT 
    cs.experiment_id,
    cs.segment_key,
    cs.context_features,
    ev.id as variant_id,
    ev.name as variant_name,
    
    -- Segment performance (from variant_segment_state)
    vss.alpha,
    vss.beta,
    vss.samples as segment_samples,
    CASE 
        WHEN vss.samples > 0
        THEN (vss.alpha - 1.0) / (vss.alpha + vss.beta - 2.0)
        ELSE 0.0
    END as segment_cr,
    
    -- Global performance (from element_variants)
    ev.total_visitors as global_samples,
    CASE 
        WHEN ev.total_visitors > 0 
        THEN ev.total_conversions::FLOAT / ev.total_visitors
        ELSE 0.0
    END as global_cr,
    
    -- Lift calculation
    CASE 
        WHEN ev.total_visitors > 0 AND ev.total_conversions > 0 AND vss.samples > 0
        THEN (
            ((vss.alpha - 1.0) / (vss.alpha + vss.beta - 2.0)) 
            - (ev.total_conversions::FLOAT / ev.total_visitors)
        ) / (ev.total_conversions::FLOAT / ev.total_visitors) * 100
        ELSE NULL
    END as lift_percent,
    
    -- Traffic
    cs.total_visits as segment_traffic
    
FROM context_segments cs
JOIN variant_segment_state vss ON vss.segment_key = cs.segment_key
JOIN element_variants ev ON ev.id = vss.variant_id
WHERE vss.samples >= 50  -- Min samples for reliable comparison
  AND ev.total_visitors >= 100  -- Min global samples
ORDER BY ABS(
    CASE 
        WHEN ev.total_visitors > 0 AND ev.total_conversions > 0 AND vss.samples > 0
        THEN (
            ((vss.alpha - 1.0) / (vss.alpha + vss.beta - 2.0)) 
            - (ev.total_conversions::FLOAT / ev.total_visitors)
        ) / (ev.total_conversions::FLOAT / ev.total_visitors)
        ELSE 0
    END
) DESC;

COMMENT ON VIEW v_segment_lift IS 
'Segment lift analysis comparing segment vs global performance';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 5: Functions for Segment Management                                │
-- └──────────────────────────────────────────────────────────────────────────┘

-- Get or create segment
CREATE OR REPLACE FUNCTION get_or_create_segment(
    p_experiment_id UUID,
    p_segment_key VARCHAR,
    p_context_features JSONB
) RETURNS UUID AS $$
DECLARE
    v_segment_id UUID;
BEGIN
    -- Try to get existing
    SELECT id INTO v_segment_id
    FROM context_segments
    WHERE experiment_id = p_experiment_id
    AND segment_key = p_segment_key;
    
    -- Create if doesn't exist
    IF v_segment_id IS NULL THEN
        INSERT INTO context_segments (
            experiment_id,
            segment_key,
            context_features,
            total_visits
        ) VALUES (
            p_experiment_id,
            p_segment_key,
            p_context_features,
            0
        )
        RETURNING id INTO v_segment_id;
    END IF;
    
    RETURN v_segment_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_or_create_segment IS 
'Get existing segment or create new one';


-- Update segment stats
CREATE OR REPLACE FUNCTION update_segment_stats(
    p_segment_id UUID,
    p_converted BOOLEAN
) RETURNS VOID AS $$
BEGIN
    UPDATE context_segments
    SET 
        total_visits = total_visits + 1,
        total_conversions = total_conversions + CASE WHEN p_converted THEN 1 ELSE 0 END,
        last_seen_at = NOW()
    WHERE id = p_segment_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_segment_stats IS 
'Update aggregated segment statistics';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 6: Materialized View for Fast Analytics                            │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_segment_analytics AS
SELECT 
    cs.experiment_id,
    e.name as experiment_name,
    cs.segment_key,
    cs.context_features,
    cs.total_visits,
    cs.total_conversions,
    cs.total_conversions::FLOAT / NULLIF(cs.total_visits, 0) as conversion_rate,
    
    -- Best variant with details
    (
        SELECT jsonb_build_object(
            'variant_id', vss.variant_id,
            'variant_name', ev.name,
            'conversion_rate', (vss.alpha - 1.0) / (vss.alpha + vss.beta - 2.0),
            'samples', vss.samples,
            'alpha', vss.alpha,
            'beta', vss.beta
        )
        FROM variant_segment_state vss
        JOIN element_variants ev ON ev.id = vss.variant_id
        WHERE vss.segment_key = cs.segment_key
        ORDER BY (vss.alpha / (vss.alpha + vss.beta)) DESC NULLS LAST
        LIMIT 1
    ) as best_variant_data,
    
    -- Number of variants
    (
        SELECT COUNT(*)
        FROM variant_segment_state vss
        WHERE vss.segment_key = cs.segment_key
          AND vss.samples >= 10
    ) as active_variants,
    
    cs.first_seen_at,
    cs.last_seen_at
    
FROM context_segments cs
JOIN experiments e ON e.id = cs.experiment_id
WHERE cs.total_visits >= 50;  -- Min threshold

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_segment_analytics_pk 
ON mv_segment_analytics(experiment_id, segment_key);

CREATE INDEX IF NOT EXISTS idx_mv_segment_analytics_cr
ON mv_segment_analytics(conversion_rate DESC NULLS LAST);

COMMENT ON MATERIALIZED VIEW mv_segment_analytics IS 
'Fast analytics view for segment performance (refresh periodically)';


-- Refresh function
CREATE OR REPLACE FUNCTION refresh_segment_analytics()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_segment_analytics;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_segment_analytics IS 
'Refresh segment analytics materialized view';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 7: Helper Functions for Analytics                                  │
-- └──────────────────────────────────────────────────────────────────────────┘

-- Get top segments by performance
CREATE OR REPLACE FUNCTION get_top_segments(
    p_experiment_id UUID,
    p_limit INT DEFAULT 10,
    p_min_samples INT DEFAULT 50
) RETURNS TABLE (
    segment_key VARCHAR,
    context_features JSONB,
    visits INT,
    conversions INT,
    conversion_rate FLOAT,
    best_variant TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sp.segment_key,
        sp.context_features,
        sp.total_visits,
        sp.total_conversions,
        sp.conversion_rate,
        sp.best_variant
    FROM v_segment_performance sp
    WHERE sp.experiment_id = p_experiment_id
      AND sp.total_visits >= p_min_samples
    ORDER BY sp.conversion_rate DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_top_segments IS 
'Get top performing segments for an experiment';


-- Get segment lift analysis
CREATE OR REPLACE FUNCTION get_segment_lifts(
    p_experiment_id UUID,
    p_min_samples INT DEFAULT 50
) RETURNS TABLE (
    segment_key VARCHAR,
    variant_name TEXT,
    segment_cr FLOAT,
    global_cr FLOAT,
    lift_percent FLOAT,
    segment_samples INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sl.segment_key,
        sl.variant_name,
        sl.segment_cr,
        sl.global_cr,
        sl.lift_percent,
        sl.segment_samples
    FROM v_segment_lift sl
    WHERE sl.experiment_id = p_experiment_id
      AND sl.segment_samples >= p_min_samples
    ORDER BY ABS(sl.lift_percent) DESC NULLS LAST
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_segment_lifts IS 
'Get segments with highest lift (positive or negative) vs global';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 8: Indexes for Performance                                         │
-- └──────────────────────────────────────────────────────────────────────────┘

-- Compound indexes for common queries
CREATE INDEX IF NOT EXISTS idx_context_segments_exp_visits 
ON context_segments(experiment_id, total_visits DESC);

CREATE INDEX IF NOT EXISTS idx_context_segments_exp_cr
ON context_segments(
    experiment_id,
    (total_conversions::FLOAT / NULLIF(total_visits, 1)) DESC NULLS LAST
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 9: Validation and Monitoring                                       │
-- └──────────────────────────────────────────────────────────────────────────┘

-- Check if contextual bandits is properly configured
CREATE OR REPLACE FUNCTION validate_contextual_setup(
    p_experiment_id UUID
) RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    message TEXT
) AS $$
BEGIN
    -- Check 1: Segments exist
    RETURN QUERY
    SELECT 
        'segments_exist'::TEXT,
        CASE 
            WHEN COUNT(*) > 0 THEN 'OK'
            ELSE 'WARNING'
        END,
        'Found ' || COUNT(*)::TEXT || ' segments'
    FROM context_segments
    WHERE experiment_id = p_experiment_id;
    
    -- Check 2: Segments have sufficient samples
    RETURN QUERY
    SELECT 
        'segments_powered'::TEXT,
        CASE 
            WHEN COUNT(*) > 0 THEN 'OK'
            ELSE 'WARNING'
        END,
        COUNT(*)::TEXT || ' segments with 100+ samples'
    FROM context_segments
    WHERE experiment_id = p_experiment_id
      AND total_visits >= 100;
    
    -- Check 3: Variant states exist
    RETURN QUERY
    SELECT 
        'variant_states_exist'::TEXT,
        CASE 
            WHEN COUNT(*) > 0 THEN 'OK'
            ELSE 'ERROR'
        END,
        'Found ' || COUNT(*)::TEXT || ' variant-segment states'
    FROM variant_segment_state vss
    WHERE EXISTS (
        SELECT 1 FROM context_segments cs
        WHERE cs.segment_key = vss.segment_key
          AND cs.experiment_id = p_experiment_id
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION validate_contextual_setup IS 
'Validate contextual bandits configuration for experiment';


-- ============================================================================
-- ROLLBACK PLAN
-- ============================================================================
/*
-- To rollback this migration:

DROP FUNCTION IF EXISTS validate_contextual_setup(UUID);
DROP FUNCTION IF EXISTS get_segment_lifts(UUID, INT);
DROP FUNCTION IF EXISTS get_top_segments(UUID, INT, INT);
DROP FUNCTION IF EXISTS refresh_segment_analytics();
DROP MATERIALIZED VIEW IF EXISTS mv_segment_analytics;
DROP FUNCTION IF EXISTS update_segment_stats(UUID, BOOLEAN);
DROP FUNCTION IF EXISTS get_or_create_segment(UUID, VARCHAR, JSONB);
DROP VIEW IF EXISTS v_segment_lift;
DROP VIEW IF EXISTS v_segment_performance;

ALTER TABLE assignments 
DROP COLUMN IF EXISTS segment_id,
DROP COLUMN IF EXISTS context_data;

DROP TABLE IF EXISTS context_segments;

-- Note: variant_segment_state from V2 is preserved (shared with clustering)
*/


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
/*
-- Verify migration
SELECT 
    tablename, 
    schemaname 
FROM pg_tables 
WHERE tablename IN ('context_segments');

-- Check indexes
SELECT 
    indexname, 
    tablename 
FROM pg_indexes 
WHERE tablename IN ('context_segments', 'assignments');

-- Check functions
SELECT 
    proname, 
    prokind 
FROM pg_proc 
WHERE proname LIKE '%segment%';
*/
