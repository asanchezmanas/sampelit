-- migrations/010_contextual_segments.sql

-- ============================================
-- Contextual Bandits Schema
-- ============================================

-- 1. Segment definitions
CREATE TABLE context_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Segment identification
    segment_key VARCHAR(500) NOT NULL,
    -- Format: "source:instagram|device:mobile"
    
    -- Segment metadata
    context_features JSONB NOT NULL,
    -- Example: {"source": "instagram", "device": "mobile"}
    
    -- Statistics
    total_visits INT DEFAULT 0,
    total_conversions INT DEFAULT 0,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(experiment_id, segment_key)
);

CREATE INDEX idx_context_segments_experiment ON context_segments(experiment_id);
CREATE INDEX idx_context_segments_key ON context_segments(segment_key);
CREATE INDEX idx_context_segments_visits ON context_segments(total_visits DESC);

-- 2. Variant performance per segment
CREATE TABLE variant_segment_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- References
    variant_id UUID NOT NULL REFERENCES element_variants(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES context_segments(id) ON DELETE CASCADE,
    
    -- Thompson Sampling state for this segment
    alpha FLOAT NOT NULL DEFAULT 1.0,
    beta FLOAT NOT NULL DEFAULT 1.0,
    samples INT DEFAULT 0,
    
    -- Performance metrics
    conversions INT DEFAULT 0,
    conversion_rate FLOAT,
    
    -- Confidence metrics
    credible_interval_lower FLOAT,
    credible_interval_upper FLOAT,
    
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(variant_id, segment_id)
);

CREATE INDEX idx_variant_segment_variant ON variant_segment_performance(variant_id);
CREATE INDEX idx_variant_segment_segment ON variant_segment_performance(segment_id);
CREATE INDEX idx_variant_segment_cr ON variant_segment_performance(conversion_rate DESC NULLS LAST);

-- 3. Assignment tracking with context
ALTER TABLE assignments 
ADD COLUMN context_data JSONB,
ADD COLUMN segment_id UUID REFERENCES context_segments(id);

CREATE INDEX idx_assignments_segment ON assignments(segment_id);
CREATE INDEX idx_assignments_context_data ON assignments USING GIN(context_data);

-- 4. Segment performance summary view
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
    END as overall_conversion_rate,
    
    -- Best variant for this segment
    (
        SELECT ev.name
        FROM variant_segment_performance vsp
        JOIN element_variants ev ON ev.id = vsp.variant_id
        WHERE vsp.segment_id = cs.id
        ORDER BY vsp.conversion_rate DESC NULLS LAST
        LIMIT 1
    ) as best_variant,
    
    -- Variant count
    (
        SELECT COUNT(*)
        FROM variant_segment_performance vsp
        WHERE vsp.segment_id = cs.id
    ) as variant_count,
    
    cs.first_seen_at,
    cs.last_seen_at
FROM context_segments cs;

-- 5. Segment lift analysis view
-- Shows which segments perform differently from global
CREATE OR REPLACE VIEW v_segment_lift AS
SELECT 
    cs.segment_key,
    cs.context_features,
    ev.name as variant_name,
    
    -- Segment performance
    vsp.conversion_rate as segment_cr,
    vsp.samples as segment_samples,
    
    -- Global performance
    CASE 
        WHEN ev.total_visitors > 0 
        THEN ev.total_conversions::FLOAT / ev.total_visitors
        ELSE 0.0
    END as global_cr,
    
    -- Lift calculation
    CASE 
        WHEN ev.total_visitors > 0 AND ev.total_conversions > 0
        THEN (vsp.conversion_rate - (ev.total_conversions::FLOAT / ev.total_visitors)) 
             / (ev.total_conversions::FLOAT / ev.total_visitors) * 100
        ELSE NULL
    END as lift_percent,
    
    cs.total_visits as segment_traffic
    
FROM context_segments cs
JOIN variant_segment_performance vsp ON vsp.segment_id = cs.id
JOIN element_variants ev ON ev.id = vsp.variant_id
WHERE vsp.samples >= 50  -- Min samples for reliable comparison
ORDER BY ABS(
    CASE 
        WHEN ev.total_visitors > 0 AND ev.total_conversions > 0
        THEN (vsp.conversion_rate - (ev.total_conversions::FLOAT / ev.total_visitors)) 
             / (ev.total_conversions::FLOAT / ev.total_visitors)
        ELSE 0
    END
) DESC;

-- 6. Functions

-- Function to get or create segment
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
            context_features
        ) VALUES (
            p_experiment_id,
            p_segment_key,
            p_context_features
        )
        RETURNING id INTO v_segment_id;
    END IF;
    
    RETURN v_segment_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update segment stats
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

-- Function to update variant-segment performance
CREATE OR REPLACE FUNCTION update_variant_segment_performance(
    p_variant_id UUID,
    p_segment_id UUID,
    p_reward FLOAT
) RETURNS VOID AS $$
DECLARE
    v_alpha FLOAT;
    v_beta FLOAT;
    v_samples INT;
BEGIN
    -- Get current state or initialize
    SELECT alpha, beta, samples
    INTO v_alpha, v_beta, v_samples
    FROM variant_segment_performance
    WHERE variant_id = p_variant_id
    AND segment_id = p_segment_id;
    
    IF v_alpha IS NULL THEN
        -- Initialize new segment for variant
        v_alpha := 1.0;
        v_beta := 1.0;
        v_samples := 0;
    END IF;
    
    -- Bayesian update
    v_alpha := v_alpha + p_reward;
    v_beta := v_beta + (1.0 - p_reward);
    v_samples := v_samples + 1;
    
    -- Upsert
    INSERT INTO variant_segment_performance (
        variant_id,
        segment_id,
        alpha,
        beta,
        samples,
        conversions,
        conversion_rate,
        updated_at
    ) VALUES (
        p_variant_id,
        p_segment_id,
        v_alpha,
        v_beta,
        v_samples,
        CASE WHEN p_reward > 0 THEN 1 ELSE 0 END,
        (v_alpha - 1.0) / (v_alpha + v_beta - 2.0),
        NOW()
    )
    ON CONFLICT (variant_id, segment_id)
    DO UPDATE SET
        alpha = v_alpha,
        beta = v_beta,
        samples = v_samples,
        conversions = variant_segment_performance.conversions + CASE WHEN p_reward > 0 THEN 1 ELSE 0 END,
        conversion_rate = (v_alpha - 1.0) / (v_alpha + v_beta - 2.0),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- 7. Trigger to auto-calculate credible intervals
CREATE OR REPLACE FUNCTION calculate_credible_intervals()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate 95% credible interval using Beta distribution
    -- Using approximation: mean ± 1.96 * std_dev
    
    DECLARE
        v_mean FLOAT;
        v_std FLOAT;
    BEGIN
        v_mean := NEW.alpha / (NEW.alpha + NEW.beta);
        v_std := SQRT(
            (NEW.alpha * NEW.beta) / 
            (POWER(NEW.alpha + NEW.beta, 2) * (NEW.alpha + NEW.beta + 1))
        );
        
        NEW.credible_interval_lower := GREATEST(0.0, v_mean - 1.96 * v_std);
        NEW.credible_interval_upper := LEAST(1.0, v_mean + 1.96 * v_std);
        
        RETURN NEW;
    END;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_credible_intervals
BEFORE INSERT OR UPDATE ON variant_segment_performance
FOR EACH ROW
EXECUTE FUNCTION calculate_credible_intervals();

-- 8. Indexes for performance
CREATE INDEX idx_variant_segment_performance_updated 
ON variant_segment_performance(updated_at DESC);

-- 9. Materialized view for fast segment analytics
CREATE MATERIALIZED VIEW mv_segment_analytics AS
SELECT 
    cs.experiment_id,
    e.name as experiment_name,
    cs.segment_key,
    cs.context_features,
    cs.total_visits,
    cs.total_conversions,
    cs.total_conversions::FLOAT / NULLIF(cs.total_visits, 0) as conversion_rate,
    
    -- Best performing variant
    (
        SELECT jsonb_build_object(
            'variant_name', ev.name,
            'conversion_rate', vsp.conversion_rate,
            'samples', vsp.samples,
            'confidence_lower', vsp.credible_interval_lower,
            'confidence_upper', vsp.credible_interval_upper
        )
        FROM variant_segment_performance vsp
        JOIN element_variants ev ON ev.id = vsp.variant_id
        WHERE vsp.segment_id = cs.id
        ORDER BY vsp.conversion_rate DESC NULLS LAST
        LIMIT 1
    ) as best_variant_data,
    
    cs.first_seen_at,
    cs.last_seen_at
    
FROM context_segments cs
JOIN experiments e ON e.id = cs.experiment_id
WHERE cs.total_visits >= 50;  -- Min threshold

CREATE UNIQUE INDEX idx_mv_segment_analytics_pk 
ON mv_segment_analytics(experiment_id, segment_key);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_segment_analytics()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_segment_analytics;
END;
$$ LANGUAGE plpgsql;
