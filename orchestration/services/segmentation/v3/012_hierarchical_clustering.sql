-- ============================================================================
-- MIGRATION V3.2: Hierarchical Clustering
-- ============================================================================
-- Adds hierarchical segment relationships for cascade allocation
--
-- New capabilities:
-- - Multi-level segment hierarchy
-- - Parent-child relationships
-- - Cascade allocation with fallback
-- - Tree navigation and analytics
-- ============================================================================

-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 1: Segment Hierarchy Table                                         │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS segment_hierarchy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Node identification
    segment_id UUID NOT NULL REFERENCES context_segments(id) ON DELETE CASCADE,
    parent_segment_id UUID REFERENCES context_segments(id) ON DELETE CASCADE,
    
    -- Hierarchy metadata
    level INT NOT NULL,  -- 0=root, 1=country, 2=device, etc.
    depth INT NOT NULL,  -- Distance from root
    is_leaf BOOLEAN DEFAULT FALSE,
    
    -- Tree navigation (for efficiency)
    path TEXT[],  -- Array of segment_keys from root to this node
    -- Example: ['global', 'country:US', 'device:mobile']
    
    -- Performance at this level
    samples_at_level INT DEFAULT 0,
    conversions_at_level INT DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(segment_id)
);

CREATE INDEX idx_segment_hierarchy_experiment ON segment_hierarchy(experiment_id);
CREATE INDEX idx_segment_hierarchy_parent ON segment_hierarchy(parent_segment_id);
CREATE INDEX idx_segment_hierarchy_level ON segment_hierarchy(level);
CREATE INDEX idx_segment_hierarchy_path ON segment_hierarchy USING GIN(path);

COMMENT ON TABLE segment_hierarchy IS 
'Multi-level segment hierarchy for cascade allocation';

COMMENT ON COLUMN segment_hierarchy.path IS 
'Path from root to this node for efficient navigation';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 2: Hierarchy Configuration Table                                   │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS hierarchy_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Configuration
    hierarchy_levels TEXT[] NOT NULL,
    -- Example: ['country', 'device', 'source']
    
    min_samples_per_level INT[] NOT NULL,
    -- Example: [1000, 500, 200]
    
    max_depth INT DEFAULT 3,
    prune_ineffective BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    tree_built_at TIMESTAMPTZ,
    total_nodes INT DEFAULT 0,
    leaf_nodes INT DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(experiment_id)
);

COMMENT ON TABLE hierarchy_config IS 
'Configuration for hierarchical clustering per experiment';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 3: Cascade Allocation Tracking                                     │
-- └──────────────────────────────────────────────────────────────────────────┘

-- Add columns to assignments to track cascade behavior
ALTER TABLE assignments 
ADD COLUMN IF NOT EXISTS target_segment_id UUID REFERENCES context_segments(id),
ADD COLUMN IF NOT EXISTS used_segment_id UUID REFERENCES context_segments(id),
ADD COLUMN IF NOT EXISTS cascade_depth INT DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_assignments_target_segment ON assignments(target_segment_id);
CREATE INDEX IF NOT EXISTS idx_assignments_used_segment ON assignments(used_segment_id);

COMMENT ON COLUMN assignments.target_segment_id IS 
'Most specific segment for this context';

COMMENT ON COLUMN assignments.used_segment_id IS 
'Actual segment used (may be parent if cascaded)';

COMMENT ON COLUMN assignments.cascade_depth IS 
'Number of levels cascaded up (0 = no cascade)';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 4: Hierarchy Navigation Functions                                  │
-- └──────────────────────────────────────────────────────────────────────────┘

-- Get children of a segment
CREATE OR REPLACE FUNCTION get_segment_children(
    p_segment_id UUID
) RETURNS TABLE (
    child_id UUID,
    child_segment_key TEXT,
    child_level INT,
    child_samples INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sh.segment_id as child_id,
        cs.segment_key as child_segment_key,
        sh.level as child_level,
        cs.total_visits as child_samples
    FROM segment_hierarchy sh
    JOIN context_segments cs ON cs.id = sh.segment_id
    WHERE sh.parent_segment_id = p_segment_id
    ORDER BY cs.total_visits DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_segment_children IS 
'Get child segments of a parent segment';


-- Get ancestors of a segment (cascade path)
CREATE OR REPLACE FUNCTION get_segment_ancestors(
    p_segment_id UUID
) RETURNS TABLE (
    ancestor_id UUID,
    ancestor_segment_key TEXT,
    ancestor_level INT,
    distance INT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE ancestors AS (
        -- Base case: the segment itself
        SELECT 
            sh.segment_id,
            sh.parent_segment_id,
            sh.level,
            0 as distance
        FROM segment_hierarchy sh
        WHERE sh.segment_id = p_segment_id
        
        UNION ALL
        
        -- Recursive case: parent segments
        SELECT 
            sh.segment_id,
            sh.parent_segment_id,
            sh.level,
            a.distance + 1
        FROM segment_hierarchy sh
        JOIN ancestors a ON a.parent_segment_id = sh.segment_id
    )
    SELECT 
        a.segment_id as ancestor_id,
        cs.segment_key as ancestor_segment_key,
        a.level as ancestor_level,
        a.distance
    FROM ancestors a
    JOIN context_segments cs ON cs.id = a.segment_id
    ORDER BY a.distance;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_segment_ancestors IS 
'Get ancestor segments (cascade path) from specific to root';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 5: Cascade Analytics Views                                         │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE VIEW v_cascade_stats AS
SELECT 
    e.id as experiment_id,
    e.name as experiment_name,
    
    -- Level usage
    sh.level,
    COUNT(DISTINCT a.id) as allocations,
    
    -- Cascade behavior
    AVG(a.cascade_depth)::FLOAT as avg_cascade_depth,
    SUM(CASE WHEN a.cascade_depth > 0 THEN 1 ELSE 0 END) as cascaded_allocations,
    
    -- Performance
    AVG(CASE WHEN a.converted THEN 1.0 ELSE 0.0 END)::FLOAT as conversion_rate
    
FROM experiments e
JOIN segment_hierarchy sh ON sh.experiment_id = e.id
JOIN assignments a ON a.used_segment_id = sh.segment_id
GROUP BY e.id, e.name, sh.level
ORDER BY e.id, sh.level;

COMMENT ON VIEW v_cascade_stats IS 
'Statistics about cascade allocation behavior per level';


CREATE OR REPLACE VIEW v_hierarchy_performance AS
SELECT 
    sh.experiment_id,
    sh.level,
    sh.segment_id,
    cs.segment_key,
    cs.total_visits,
    cs.total_conversions,
    cs.total_conversions::FLOAT / NULLIF(cs.total_visits, 0) as conversion_rate,
    
    -- Parent comparison
    parent_cs.segment_key as parent_segment_key,
    parent_cs.total_conversions::FLOAT / NULLIF(parent_cs.total_visits, 0) as parent_conversion_rate,
    
    -- Lift vs parent
    CASE 
        WHEN parent_cs.total_visits > 0 AND parent_cs.total_conversions > 0
        THEN (
            (cs.total_conversions::FLOAT / NULLIF(cs.total_visits, 0))
            - (parent_cs.total_conversions::FLOAT / parent_cs.total_visits)
        ) / (parent_cs.total_conversions::FLOAT / parent_cs.total_visits) * 100
        ELSE NULL
    END as lift_vs_parent
    
FROM segment_hierarchy sh
JOIN context_segments cs ON cs.id = sh.segment_id
LEFT JOIN context_segments parent_cs ON parent_cs.id = sh.parent_segment_id
WHERE cs.total_visits >= 50
ORDER BY sh.experiment_id, sh.level, lift_vs_parent DESC NULLS LAST;

COMMENT ON VIEW v_hierarchy_performance IS 
'Performance comparison of segments vs their parents';


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ STEP 6: Helper Functions                                                │
-- └──────────────────────────────────────────────────────────────────────────┘

-- Build hierarchy for experiment
CREATE OR REPLACE FUNCTION build_segment_hierarchy(
    p_experiment_id UUID,
    p_hierarchy_levels TEXT[],
    p_min_samples_per_level INT[]
) RETURNS INT AS $$
DECLARE
    v_nodes_created INT := 0;
BEGIN
    -- Clear existing hierarchy
    DELETE FROM segment_hierarchy WHERE experiment_id = p_experiment_id;
    
    -- Create root node (global)
    INSERT INTO segment_hierarchy (
        experiment_id,
        segment_id,
        parent_segment_id,
        level,
        depth,
        is_leaf,
        path
    )
    SELECT 
        p_experiment_id,
        cs.id,
        NULL,
        0,
        0,
        FALSE,
        ARRAY['global']
    FROM context_segments cs
    WHERE cs.experiment_id = p_experiment_id
      AND cs.segment_key = 'global';
    
    v_nodes_created := v_nodes_created + 1;
    
    -- Build subsequent levels
    -- (Complex logic - would typically be done in application code)
    -- This is a simplified version
    
    -- Save config
    INSERT INTO hierarchy_config (
        experiment_id,
        hierarchy_levels,
        min_samples_per_level,
        tree_built_at,
        total_nodes
    ) VALUES (
        p_experiment_id,
        p_hierarchy_levels,
        p_min_samples_per_level,
        NOW(),
        v_nodes_created
    )
    ON CONFLICT (experiment_id)
    DO UPDATE SET
        hierarchy_levels = p_hierarchy_levels,
        min_samples_per_level = p_min_samples_per_level,
        tree_built_at = NOW(),
        total_nodes = v_nodes_created,
        updated_at = NOW();
    
    RETURN v_nodes_created;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION build_segment_hierarchy IS 
'Build segment hierarchy tree (simplified - use application code for full build)';


-- ============================================================================
-- ROLLBACK PLAN
-- ============================================================================
/*
-- To rollback this migration:

DROP FUNCTION IF EXISTS build_segment_hierarchy(UUID, TEXT[], INT[]);
DROP VIEW IF EXISTS v_hierarchy_performance;
DROP VIEW IF EXISTS v_cascade_stats;
DROP FUNCTION IF EXISTS get_segment_ancestors(UUID);
DROP FUNCTION IF EXISTS get_segment_children(UUID);

ALTER TABLE assignments 
DROP COLUMN IF EXISTS cascade_depth,
DROP COLUMN IF EXISTS used_segment_id,
DROP COLUMN IF EXISTS target_segment_id;

DROP TABLE IF EXISTS hierarchy_config;
DROP TABLE IF EXISTS segment_hierarchy;
*/


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
/*
-- Verify hierarchy table
SELECT COUNT(*) FROM segment_hierarchy;

-- View hierarchy for experiment
SELECT 
    level,
    cs.segment_key,
    sh.depth,
    sh.is_leaf,
    sh.path
FROM segment_hierarchy sh
JOIN context_segments cs ON cs.id = sh.segment_id
WHERE sh.experiment_id = 'YOUR_EXPERIMENT_ID'
ORDER BY level, sh.path;

-- View cascade stats
SELECT * FROM v_cascade_stats
WHERE experiment_id = 'YOUR_EXPERIMENT_ID';
*/
