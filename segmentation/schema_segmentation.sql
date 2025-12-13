-- schema_segmentation.sql
-- Añadir soporte para segmentación y clustering

-- ============================================
-- SEGMENTATION CONFIG (per experiment)
-- ============================================

CREATE TABLE experiment_segmentation_config (
    experiment_id UUID PRIMARY KEY REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Mode: 'disabled', 'manual', 'auto'
    mode VARCHAR(20) DEFAULT 'disabled',
    
    -- Manual segmentation
    segment_by TEXT[], -- ['source', 'device']
    min_samples_per_segment INTEGER DEFAULT 100,
    
    -- Auto clustering
    auto_clustering_enabled BOOLEAN DEFAULT false,
    n_clusters INTEGER,  -- NULL = auto-determine
    clustering_algorithm VARCHAR(50) DEFAULT 'kmeans',
    last_clustering_at TIMESTAMPTZ,
    
    -- Auto-activation settings
    auto_activation_enabled BOOLEAN DEFAULT false,
    auto_activation_threshold INTEGER DEFAULT 1000, -- visitors/day
    
    -- Feature preferences
    user_preferences JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_mode CHECK (mode IN ('disabled', 'manual', 'auto'))
);

CREATE INDEX idx_segmentation_config_experiment ON experiment_segmentation_config(experiment_id);
CREATE INDEX idx_segmentation_config_mode ON experiment_segmentation_config(mode);

-- ============================================
-- SEGMENTS (discovered or configured)
-- ============================================

CREATE TABLE experiment_segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    segment_key VARCHAR(255) NOT NULL, -- 'source:instagram' o 'cluster_0'
    segment_type VARCHAR(20) NOT NULL, -- 'manual' o 'auto'
    
    -- Segment characteristics (for display)
    display_name VARCHAR(255),
    description TEXT,
    characteristics JSONB DEFAULT '{}'::jsonb, -- {"source": "instagram", "device": "mobile"}
    
    -- Performance
    total_allocations INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(10,6) DEFAULT 0,
    
    -- Auto-clustering data
    cluster_centroid JSONB, -- For K-means
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(experiment_id, segment_key),
    CONSTRAINT valid_segment_type CHECK (segment_type IN ('manual', 'auto'))
);

CREATE INDEX idx_segments_experiment ON experiment_segments(experiment_id);
CREATE INDEX idx_segments_key ON experiment_segments(experiment_id, segment_key);
CREATE INDEX idx_segments_type ON experiment_segments(segment_type);

-- ============================================
-- SEGMENTED VARIANTS (Thompson per segment)
-- ============================================

ALTER TABLE element_variants 
ADD COLUMN segment_key VARCHAR(255) DEFAULT 'default';

-- Drop old unique constraint
ALTER TABLE element_variants 
DROP CONSTRAINT IF EXISTS element_variants_element_id_variant_order_key;

-- Add new unique constraint including segment
ALTER TABLE element_variants 
ADD CONSTRAINT unique_variant_per_segment 
UNIQUE(element_id, variant_order, segment_key);

-- Index for fast lookups
CREATE INDEX idx_variants_segment ON element_variants(element_id, segment_key);

-- ============================================
-- ASSIGNMENTS - Track segment
-- ============================================

ALTER TABLE assignments
ADD COLUMN segment_key VARCHAR(255) DEFAULT 'default';

CREATE INDEX idx_assignments_segment ON assignments(experiment_id, segment_key);

-- ============================================
-- TRAFFIC STATS (for eligibility detection)
-- ============================================

CREATE TABLE experiment_traffic_stats (
    experiment_id UUID PRIMARY KEY REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Daily stats (updated hourly)
    visitors_last_24h INTEGER DEFAULT 0,
    visitors_last_7d INTEGER DEFAULT 0,
    avg_daily_visitors DECIMAL(10,2) DEFAULT 0,
    
    -- Segment distribution
    segment_distribution JSONB DEFAULT '{}'::jsonb,
    
    -- Eligibility
    is_eligible_for_segmentation BOOLEAN DEFAULT false,
    is_eligible_for_clustering BOOLEAN DEFAULT false,
    
    last_calculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_traffic_stats_eligible ON experiment_traffic_stats(is_eligible_for_segmentation, is_eligible_for_clustering);

-- ============================================
-- CLUSTERING MODELS (for auto-clustering)
-- ============================================

CREATE TABLE clustering_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Model metadata
    algorithm VARCHAR(50) NOT NULL, -- 'kmeans', 'dbscan', etc
    n_clusters INTEGER NOT NULL,
    feature_names TEXT[] NOT NULL,
    
    -- Model artifacts (serialized)
    model_data BYTEA NOT NULL, -- Pickled scikit-learn model
    scaler_data BYTEA, -- Feature scaler if used
    
    -- Performance
    inertia DECIMAL(10,4),
    silhouette_score DECIMAL(5,4),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    trained_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_clustering_models_experiment ON clustering_models(experiment_id);
CREATE INDEX idx_clustering_models_active ON clustering_models(experiment_id, is_active) WHERE is_active = true;

-- ============================================
-- SEGMENTATION RECOMMENDATIONS
-- ============================================

CREATE TABLE segmentation_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    recommendation_type VARCHAR(50) NOT NULL, -- 'enable_segmentation', 'add_segment', 'enable_clustering'
    
    -- Recommendation details
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    expected_lift DECIMAL(5,2), -- Expected % improvement
    confidence DECIMAL(5,4), -- 0-1 confidence score
    
    -- Action
    suggested_config JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'accepted', 'dismissed'
    dismissed_reason TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'accepted', 'dismissed'))
);

CREATE INDEX idx_recommendations_experiment ON segmentation_recommendations(experiment_id);
CREATE INDEX idx_recommendations_status ON segmentation_recommendations(status) WHERE status = 'pending';

-- ============================================
-- TRIGGERS
-- ============================================

CREATE TRIGGER update_segmentation_config_updated_at 
    BEFORE UPDATE ON experiment_segmentation_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_segments_updated_at 
    BEFORE UPDATE ON experiment_segments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_traffic_stats_updated_at 
    BEFORE UPDATE ON experiment_traffic_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- FUNCTIONS
-- ============================================

-- Update traffic stats (called by cron/scheduler)
CREATE OR REPLACE FUNCTION update_experiment_traffic_stats(exp_id UUID)
RETURNS void AS $$
DECLARE
    visitors_24h INTEGER;
    visitors_7d INTEGER;
    avg_daily DECIMAL(10,2);
    eligible_seg BOOLEAN;
    eligible_clust BOOLEAN;
BEGIN
    -- Count visitors last 24h
    SELECT COUNT(DISTINCT user_id)
    INTO visitors_24h
    FROM assignments
    WHERE experiment_id = exp_id
      AND assigned_at >= NOW() - INTERVAL '24 hours';
    
    -- Count visitors last 7d
    SELECT COUNT(DISTINCT user_id)
    INTO visitors_7d
    FROM assignments
    WHERE experiment_id = exp_id
      AND assigned_at >= NOW() - INTERVAL '7 days';
    
    -- Calculate average
    avg_daily := visitors_7d / 7.0;
    
    -- Determine eligibility
    eligible_seg := avg_daily >= 1000;  -- 1K/day for segmentation
    eligible_clust := avg_daily >= 10000; -- 10K/day for clustering
    
    -- Upsert stats
    INSERT INTO experiment_traffic_stats (
        experiment_id, 
        visitors_last_24h, 
        visitors_last_7d, 
        avg_daily_visitors,
        is_eligible_for_segmentation,
        is_eligible_for_clustering,
        last_calculated_at
    ) VALUES (
        exp_id, 
        visitors_24h, 
        visitors_7d, 
        avg_daily,
        eligible_seg,
        eligible_clust,
        NOW()
    )
    ON CONFLICT (experiment_id) DO UPDATE SET
        visitors_last_24h = EXCLUDED.visitors_last_24h,
        visitors_last_7d = EXCLUDED.visitors_last_7d,
        avg_daily_visitors = EXCLUDED.avg_daily_visitors,
        is_eligible_for_segmentation = EXCLUDED.is_eligible_for_segmentation,
        is_eligible_for_clustering = EXCLUDED.is_eligible_for_clustering,
        last_calculated_at = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Get segment performance
CREATE OR REPLACE FUNCTION get_segment_performance(exp_id UUID, seg_key VARCHAR)
RETURNS TABLE (
    segment_key VARCHAR(255),
    allocations INTEGER,
    conversions INTEGER,
    conversion_rate DECIMAL(10,6)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.segment_key,
        COUNT(*)::INTEGER as allocations,
        COUNT(*) FILTER (WHERE a.converted_at IS NOT NULL)::INTEGER as conversions,
        CASE 
            WHEN COUNT(*) > 0 
            THEN COUNT(*) FILTER (WHERE a.converted_at IS NOT NULL)::DECIMAL / COUNT(*)::DECIMAL
            ELSE 0
        END as conversion_rate
    FROM assignments a
    WHERE a.experiment_id = exp_id
      AND a.segment_key = seg_key
    GROUP BY a.segment_key;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VIEWS
-- ============================================

-- View: Segmentation overview per experiment
CREATE VIEW experiment_segmentation_overview AS
SELECT 
    e.id as experiment_id,
    e.name as experiment_name,
    e.status,
    esc.mode as segmentation_mode,
    esc.auto_activation_enabled,
    ets.avg_daily_visitors,
    ets.is_eligible_for_segmentation,
    ets.is_eligible_for_clustering,
    COUNT(DISTINCT es.id) as segment_count,
    COALESCE(SUM(es.total_allocations), 0) as total_allocations,
    COUNT(DISTINCT sr.id) FILTER (WHERE sr.status = 'pending') as pending_recommendations
FROM experiments e
LEFT JOIN experiment_segmentation_config esc ON e.id = esc.experiment_id
LEFT JOIN experiment_traffic_stats ets ON e.id = ets.experiment_id
LEFT JOIN experiment_segments es ON e.id = es.experiment_id
LEFT JOIN segmentation_recommendations sr ON e.id = sr.experiment_id
GROUP BY e.id, e.name, e.status, esc.mode, esc.auto_activation_enabled, 
         ets.avg_daily_visitors, ets.is_eligible_for_segmentation, ets.is_eligible_for_clustering;

-- ============================================
-- SEED DEFAULT CONFIGS (for existing experiments)
-- ============================================

INSERT INTO experiment_segmentation_config (experiment_id, mode)
SELECT id, 'disabled'
FROM experiments
ON CONFLICT (experiment_id) DO NOTHING;

INSERT INTO experiment_traffic_stats (experiment_id)
SELECT id
FROM experiments
ON CONFLICT (experiment_id) DO NOTHING;
