-- ============================================================================
-- MIGRATION: Clustering V2 - Model Versioning & Monitoring
-- ============================================================================
-- Adds proper model versioning, quality tracking, and drift monitoring
-- for clustering models.
--
-- This migration supports:
-- - Multiple model versions per experiment
-- - Quality metrics tracking
-- - Drift detection history
-- - Model comparison analytics
-- ============================================================================

-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 1: Drop old table if exists (from V1)                              │
-- └──────────────────────────────────────────────────────────────────────────┘

-- Old table used pickle (security risk) and no versioning
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'clustering_models'
        AND EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'clustering_models' 
            AND column_name = 'model_binary'
        )
    ) THEN
        -- Backup old data first
        CREATE TABLE IF NOT EXISTS clustering_models_old AS 
        SELECT * FROM clustering_models;
        
        DROP TABLE clustering_models;
        
        RAISE NOTICE 'Backed up old clustering_models to clustering_models_old';
    END IF;
END $$;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 2: Create new clustering_models table with versioning              │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS clustering_models (
    -- Primary identification
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,  -- Auto-incrementing per experiment
    
    -- Model data (JSON format - NOT pickle for security)
    model_data JSONB NOT NULL,
    -- Structure: {
    --   'centroids': [[...], [...], ...],
    --   'n_clusters': int,
    --   'inertia': float,
    --   'n_iter': int,
    --   'algorithm': 'kmeans',
    --   'random_state': int
    -- }
    
    -- Model metadata
    n_clusters INTEGER NOT NULL,
    algorithm VARCHAR(50) DEFAULT 'kmeans',
    
    -- Quality metrics (from cluster_validation.py)
    quality_metrics JSONB NOT NULL,
    -- Structure: {
    --   'silhouette_score': float,
    --   'davies_bouldin_score': float,
    --   'calinski_harabasz_score': float,
    --   'inertia': float,
    --   'cluster_sizes': {...},
    --   'quality_grade': str,
    --   'is_good_quality': bool
    -- }
    
    -- Training info
    training_samples INTEGER,
    training_duration_ms INTEGER,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,  -- Currently deployed model
    deployed_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),  -- User/system that created it
    
    -- Primary key
    PRIMARY KEY (experiment_id, version),
    
    -- Indexes
    INDEX idx_clustering_models_active (experiment_id, is_active, version DESC),
    INDEX idx_clustering_models_created (created_at DESC),
    INDEX idx_clustering_models_quality ((quality_metrics->>'silhouette_score') DESC)
);

COMMENT ON TABLE clustering_models IS 
'Clustering model versions with JSON serialization (secure, portable)';

COMMENT ON COLUMN clustering_models.model_data IS 
'Model parameters in JSON (centroids, etc) - NOT pickle for security';

COMMENT ON COLUMN clustering_models.quality_metrics IS 
'Clustering quality metrics from validation';

COMMENT ON COLUMN clustering_models.is_active IS 
'Whether this version is currently deployed';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 3: Trigger for auto-incrementing version                           │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE FUNCTION set_model_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-increment version per experiment
    IF NEW.version IS NULL THEN
        SELECT COALESCE(MAX(version), 0) + 1
        INTO NEW.version
        FROM clustering_models
        WHERE experiment_id = NEW.experiment_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_model_version
    BEFORE INSERT ON clustering_models
    FOR EACH ROW
    EXECUTE FUNCTION set_model_version();

COMMENT ON FUNCTION set_model_version IS 
'Auto-increment version number per experiment';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 4: Trigger to ensure only one active model per experiment          │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE FUNCTION ensure_single_active_model()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = TRUE THEN
        -- Deactivate all other versions for this experiment
        UPDATE clustering_models
        SET is_active = FALSE
        WHERE experiment_id = NEW.experiment_id
          AND version != NEW.version;
        
        -- Set deployed_at
        NEW.deployed_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ensure_single_active_model
    BEFORE INSERT OR UPDATE OF is_active ON clustering_models
    FOR EACH ROW
    WHEN (NEW.is_active = TRUE)
    EXECUTE FUNCTION ensure_single_active_model();

COMMENT ON FUNCTION ensure_single_active_model IS 
'Ensures only one model version is active at a time per experiment';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 5: Drift detection history table                                   │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS model_drift_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Model identification
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    model_version INTEGER NOT NULL,
    
    -- Drift detection results
    drift_detected BOOLEAN NOT NULL,
    drift_score DECIMAL(5, 4) NOT NULL,
    threshold DECIMAL(5, 4) NOT NULL,
    
    -- Sample info
    sample_size INTEGER NOT NULL,
    sample_period_start TIMESTAMP NOT NULL,
    sample_period_end TIMESTAMP NOT NULL,
    
    -- Metrics
    avg_distance_new DECIMAL(10, 4),
    avg_distance_original DECIMAL(10, 4),
    
    -- Recommendation
    recommendation TEXT,
    
    -- Action taken
    action_taken VARCHAR(50),  -- 'none', 'retrained', 'alerted'
    new_model_version INTEGER,  -- If retrained
    
    -- Timestamps
    checked_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_drift_history_experiment (experiment_id, checked_at DESC),
    INDEX idx_drift_history_drift (drift_detected, checked_at DESC),
    
    -- Foreign key
    FOREIGN KEY (experiment_id, model_version) 
        REFERENCES clustering_models(experiment_id, version)
        ON DELETE CASCADE
);

COMMENT ON TABLE model_drift_history IS 
'History of drift detection checks for monitoring model degradation';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 6: Model comparison view                                           │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE VIEW model_comparison AS
SELECT 
    cm.experiment_id,
    e.name as experiment_name,
    cm.version,
    cm.n_clusters,
    cm.is_active,
    
    -- Quality metrics (extracted from JSONB)
    (cm.quality_metrics->>'silhouette_score')::decimal as silhouette_score,
    (cm.quality_metrics->>'davies_bouldin_score')::decimal as davies_bouldin_score,
    (cm.quality_metrics->>'calinski_harabasz_score')::decimal as calinski_harabasz_score,
    (cm.quality_metrics->>'quality_grade')::text as quality_grade,
    (cm.quality_metrics->>'is_good_quality')::boolean as is_good_quality,
    
    -- Training info
    cm.training_samples,
    cm.training_duration_ms,
    
    -- Deployment info
    cm.deployed_at,
    EXTRACT(EPOCH FROM (NOW() - cm.deployed_at))/86400 as days_deployed,
    
    -- Recent drift (last check)
    (
        SELECT drift_score
        FROM model_drift_history
        WHERE experiment_id = cm.experiment_id
          AND model_version = cm.version
        ORDER BY checked_at DESC
        LIMIT 1
    ) as last_drift_score,
    
    cm.created_at

FROM clustering_models cm
JOIN experiments e ON cm.experiment_id = e.id
ORDER BY cm.experiment_id, cm.version DESC;

COMMENT ON VIEW model_comparison IS 
'Easy comparison of model versions with key metrics';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 7: Helper functions for querying                                   │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE FUNCTION get_active_model(p_experiment_id UUID)
RETURNS TABLE (
    version INTEGER,
    model_data JSONB,
    quality_metrics JSONB,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.version,
        cm.model_data,
        cm.quality_metrics,
        cm.created_at
    FROM clustering_models cm
    WHERE cm.experiment_id = p_experiment_id
      AND cm.is_active = TRUE
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_active_model IS 
'Get currently active model for an experiment';


CREATE OR REPLACE FUNCTION get_model_history(p_experiment_id UUID)
RETURNS TABLE (
    version INTEGER,
    n_clusters INTEGER,
    silhouette_score DECIMAL,
    is_active BOOLEAN,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.version,
        cm.n_clusters,
        (cm.quality_metrics->>'silhouette_score')::decimal,
        cm.is_active,
        cm.created_at
    FROM clustering_models cm
    WHERE cm.experiment_id = p_experiment_id
    ORDER BY cm.version DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_model_history IS 
'Get version history for an experiment';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 8: Cleanup old versions function                                   │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE FUNCTION cleanup_old_model_versions(
    p_experiment_id UUID,
    p_keep_last INTEGER DEFAULT 5
) RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    -- Keep active model + last N versions
    DELETE FROM clustering_models
    WHERE experiment_id = p_experiment_id
      AND is_active = FALSE
      AND version NOT IN (
          SELECT version
          FROM clustering_models
          WHERE experiment_id = p_experiment_id
          ORDER BY version DESC
          LIMIT p_keep_last
      );
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_model_versions IS 
'Delete old model versions, keeping last N plus active';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 9: Migration from old table (if exists)                            │
-- └──────────────────────────────────────────────────────────────────────────┘

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'clustering_models_old'
    ) THEN
        -- Try to migrate data (best effort)
        -- Old format was different, so this is partial migration
        
        INSERT INTO clustering_models (
            experiment_id,
            version,
            model_data,
            n_clusters,
            quality_metrics,
            created_at
        )
        SELECT 
            experiment_id,
            1 as version,  -- All old models become version 1
            jsonb_build_object(
                'centroids', '[]'::jsonb,  -- Can't reconstruct from pickle
                'algorithm', 'kmeans_legacy'
            ),
            n_clusters,
            jsonb_build_object(
                'silhouette_score', 0.0,
                'quality_grade', 'unknown',
                'note', 'Migrated from V1'
            ),
            created_at
        FROM clustering_models_old
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Migrated % models from old table', (SELECT COUNT(*) FROM clustering_models_old);
    END IF;
END $$;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 10: Sample queries for testing                                     │
-- └──────────────────────────────────────────────────────────────────────────┘

-- List all models with quality
/*
SELECT 
    experiment_id,
    version,
    n_clusters,
    quality_metrics->>'silhouette_score' as silhouette,
    quality_metrics->>'quality_grade' as grade,
    is_active,
    created_at
FROM clustering_models
ORDER BY experiment_id, version DESC;
*/

-- Get active model for experiment
/*
SELECT * FROM get_active_model('YOUR_EXPERIMENT_ID');
*/

-- Check drift history
/*
SELECT 
    checked_at,
    drift_detected,
    drift_score,
    recommendation
FROM model_drift_history
WHERE experiment_id = 'YOUR_EXPERIMENT_ID'
ORDER BY checked_at DESC
LIMIT 10;
*/

-- Compare model versions
/*
SELECT * FROM model_comparison
WHERE experiment_id = 'YOUR_EXPERIMENT_ID';
*/


-- ============================================================================
-- ROLLBACK PLAN
-- ============================================================================
/*
-- To rollback this migration:

DROP VIEW IF EXISTS model_comparison;
DROP FUNCTION IF EXISTS cleanup_old_model_versions(UUID, INTEGER);
DROP FUNCTION IF EXISTS get_model_history(UUID);
DROP FUNCTION IF EXISTS get_active_model(UUID);
DROP TABLE IF EXISTS model_drift_history;
DROP TRIGGER IF EXISTS trigger_ensure_single_active_model ON clustering_models;
DROP FUNCTION IF EXISTS ensure_single_active_model();
DROP TRIGGER IF EXISTS trigger_set_model_version ON clustering_models;
DROP FUNCTION IF EXISTS set_model_version();
DROP TABLE IF EXISTS clustering_models;

-- Restore old table if needed
-- ALTER TABLE clustering_models_old RENAME TO clustering_models;
*/
