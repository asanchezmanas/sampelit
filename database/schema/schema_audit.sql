-- schema_audit.sql
-- Audit System Schema
-- Version: 1.0

-- ============================================
-- TABLE: ALGORITHM_AUDIT_TRAIL
-- ============================================

CREATE TABLE IF NOT EXISTS algorithm_audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    visitor_id VARCHAR(255) NOT NULL,
    selected_variant_id UUID NOT NULL, -- References element_variants(id) but loosely to allow historical data
    assignment_id UUID, -- References assignments(id)
    
    -- Decision Context
    decision_timestamp TIMESTAMPTZ NOT NULL,
    segment_key VARCHAR(255) DEFAULT 'default',
    algorithm_version VARCHAR(50),
    context_hash VARCHAR(64), -- SHA256 of context dict
    user_agent_hash VARCHAR(64), -- SHA256 of user agent
    
    -- Conversion Data (Updated later)
    conversion_observed BOOLEAN DEFAULT FALSE,
    conversion_timestamp TIMESTAMPTZ,
    conversion_value DECIMAL(10,2),
    
    -- Integrity Chain (Blockchain-lite)
    sequence_number BIGINT NOT NULL,
    previous_hash VARCHAR(64),
    decision_hash VARCHAR(64) NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(experiment_id, sequence_number),
    UNIQUE(experiment_id, previous_hash) -- Ensures linear chain
);

-- Indices for audit trail
CREATE INDEX idx_audit_experiment ON algorithm_audit_trail(experiment_id);
CREATE INDEX idx_audit_visitor ON algorithm_audit_trail(visitor_id);
CREATE INDEX idx_audit_sequence ON algorithm_audit_trail(experiment_id, sequence_number DESC);
CREATE INDEX idx_audit_decision_time ON algorithm_audit_trail(decision_timestamp);
CREATE INDEX idx_audit_segment ON algorithm_audit_trail(segment_key);

-- ============================================
-- FUNCTION: VERIFY_AUDIT_CHAIN
-- ============================================

CREATE OR REPLACE FUNCTION verify_audit_chain(
    p_experiment_id UUID,
    p_start_sequence BIGINT DEFAULT 1,
    p_end_sequence BIGINT DEFAULT NULL
)
RETURNS TABLE (
    sequence_number BIGINT,
    is_valid BOOLEAN,
    expected_hash VARCHAR,
    actual_hash VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE chain_check AS (
        -- Anchor member: First record
        SELECT 
            t.sequence_number,
            t.decision_hash,
            t.previous_hash,
            t.visitor_id,
            t.selected_variant_id,
            t.decision_timestamp,
            true as hash_match
        FROM algorithm_audit_trail t
        WHERE t.experiment_id = p_experiment_id 
        AND t.sequence_number = p_start_sequence
        
        UNION ALL
        
        -- Recursive member: Next records
        SELECT 
            t.sequence_number,
            t.decision_hash,
            t.previous_hash,
            t.visitor_id,
            t.selected_variant_id,
            t.decision_timestamp,
            (t.previous_hash = c.decision_hash) as hash_match
        FROM algorithm_audit_trail t
        JOIN chain_check c ON t.sequence_number = c.sequence_number + 1
        WHERE t.experiment_id = p_experiment_id
        AND (p_end_sequence IS NULL OR t.sequence_number <= p_end_sequence)
    )
    SELECT 
        cc.sequence_number,
        cc.hash_match as is_valid,
        LAG(cc.decision_hash) OVER (ORDER BY cc.sequence_number) as expected_previous,
        cc.previous_hash as actual_previous
    FROM chain_check cc;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE algorithm_audit_trail IS 'Immutable log of algorithm decisions with hash chaining for integrity';
COMMENT ON FUNCTION verify_audit_chain IS 'Verifies the integrity of the audit hash chain for an experiment';

DO $$
BEGIN
    RAISE NOTICE 'Created algorithm_audit_trail table and verify_audit_chain function';
END $$;
