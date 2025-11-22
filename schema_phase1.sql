-- schema_phase1_optimized.sql
-- ✅ OPTIMIZED: Added performance indexes

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Experiments
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    optimization_strategy VARCHAR(50) DEFAULT 'adaptive',
    url VARCHAR(500),
    traffic_allocation DECIMAL(3,2) DEFAULT 1.0,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.95,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived'))
);

-- Experiment Elements (multi-elemento)
CREATE TABLE experiment_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    element_order INTEGER NOT NULL DEFAULT 0,
    name VARCHAR(255) NOT NULL,
    selector_type VARCHAR(20) NOT NULL,
    selector_value VARCHAR(500) NOT NULL,
    fallback_selectors JSONB DEFAULT '[]',
    element_type VARCHAR(50) NOT NULL,
    original_content JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(experiment_id, element_order)
);

-- Element Variants
CREATE TABLE element_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    element_id UUID NOT NULL REFERENCES experiment_elements(id) ON DELETE CASCADE,
    variant_order INTEGER NOT NULL DEFAULT 0,
    name VARCHAR(255),
    content JSONB NOT NULL,
    total_allocations INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(10,6) DEFAULT 0,
    algorithm_state BYTEA,  -- ⚠️ Estado cifrado de Thompson Sampling
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(element_id, variant_order)
);

-- ✅ COMPATIBILITY: Tabla "variants" para backward compatibility
-- Esta tabla mapea a element_variants para experimentos simples (1 elemento)
CREATE VIEW variants AS
SELECT 
    ev.id,
    ee.experiment_id,
    ev.name,
    ev.content,
    ev.total_allocations,
    ev.total_conversions,
    ev.conversion_rate as observed_conversion_rate,
    ev.algorithm_state,
    TRUE as is_active,
    1 as state_version,
    ev.created_at,
    ev.updated_at
FROM element_variants ev
JOIN experiment_elements ee ON ev.element_id = ee.id;

-- Assignments (asignaciones de usuarios)
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    variant_id UUID,  -- Para experimentos simples
    session_id VARCHAR(255),
    variant_assignments JSONB,  -- {"element1": "variant2", ...} para multi-elemento
    context JSONB DEFAULT '{}',
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    converted_at TIMESTAMPTZ,
    conversion_value DECIMAL(10,2) DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    UNIQUE(experiment_id, user_id)
);

-- Installations (para snippet manual)
CREATE TABLE platform_installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    installation_method VARCHAR(50) NOT NULL,
    site_url VARCHAR(500) NOT NULL,
    site_name VARCHAR(255),
    installation_token VARCHAR(255) UNIQUE NOT NULL,
    api_token VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    verified_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Traffic Exclusion Rules
CREATE TABLE traffic_exclusion_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rule_type VARCHAR(20) NOT NULL,
    rule_value TEXT NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_rule_type CHECK (rule_type IN ('ip', 'cookie', 'email', 'url_param', 'user_agent'))
);

-- Excluded Sessions (para analytics)
CREATE TABLE excluded_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    user_identifier VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    exclusion_reason TEXT,
    excluded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Onboarding
CREATE TABLE user_onboarding (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    completed BOOLEAN DEFAULT false,
    current_step VARCHAR(50) DEFAULT 'welcome',
    installation_verified BOOLEAN DEFAULT false,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_step CHECK (current_step IN ('welcome', 'install', 'verify', 'complete'))
);

-- Subscriptions (para billing)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) DEFAULT 'free',
    status VARCHAR(20) DEFAULT 'active',
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT false,
    canceled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_plan CHECK (plan IN ('free', 'starter', 'professional', 'enterprise'))
);

-- ============================================
-- ✅ ÍNDICES BÁSICOS
-- ============================================

CREATE INDEX idx_experiments_user ON experiments(user_id);
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_user_status ON experiments(user_id, status);

CREATE INDEX idx_elements_experiment ON experiment_elements(experiment_id);
CREATE INDEX idx_elements_experiment_order ON experiment_elements(experiment_id, element_order);

CREATE INDEX idx_variants_element ON element_variants(element_id);
CREATE INDEX idx_variants_element_order ON element_variants(element_id, variant_order);

CREATE INDEX idx_assignments_experiment ON assignments(experiment_id);
CREATE INDEX idx_assignments_user ON assignments(user_id);

-- ✅ NEW: Índices críticos para performance
CREATE INDEX idx_assignments_lookup ON assignments(experiment_id, user_id);
CREATE INDEX idx_assignments_converted ON assignments(converted_at) WHERE converted_at IS NOT NULL;
CREATE INDEX idx_assignments_assigned_at ON assignments(assigned_at DESC);

CREATE INDEX idx_installations_user ON platform_installations(user_id);
CREATE INDEX idx_installations_token ON platform_installations(installation_token);
CREATE INDEX idx_installations_status ON platform_installations(status);

CREATE INDEX idx_exclusion_rules_user ON traffic_exclusion_rules(user_id);
CREATE INDEX idx_exclusion_rules_type ON traffic_exclusion_rules(rule_type);
CREATE INDEX idx_exclusion_rules_enabled ON traffic_exclusion_rules(user_id, enabled) WHERE enabled = true;

CREATE INDEX idx_excluded_sessions_experiment ON excluded_sessions(experiment_id);

CREATE INDEX idx_onboarding_user ON user_onboarding(user_id);
CREATE INDEX idx_onboarding_completed ON user_onboarding(completed);

-- ✅ NEW: Índices compuestos para queries comunes del tracker
CREATE INDEX idx_experiments_active_user_url ON experiments(user_id, status, url) WHERE status = 'active';

-- ============================================
-- TRIGGERS
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_experiments_updated_at 
    BEFORE UPDATE ON experiments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_variants_updated_at 
    BEFORE UPDATE ON element_variants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_installations_updated_at 
    BEFORE UPDATE ON platform_installations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_onboarding_updated_at 
    BEFORE UPDATE ON user_onboarding
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at 
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- RLS (Row Level Security)
-- ============================================

ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE element_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_onboarding ENABLE ROW LEVEL SECURITY;

-- ✅ SIMPLIFIED: Use service_role bypass in backend, RLS only for direct client access
CREATE POLICY experiments_user_policy ON experiments
    FOR ALL USING (auth.uid()::uuid = user_id);

CREATE POLICY elements_user_policy ON experiment_elements
    FOR ALL USING (
        experiment_id IN (SELECT id FROM experiments WHERE user_id = auth.uid()::uuid)
    );

CREATE POLICY variants_user_policy ON element_variants
    FOR ALL USING (
        element_id IN (
            SELECT ee.id FROM experiment_elements ee
            JOIN experiments e ON ee.experiment_id = e.id
            WHERE e.user_id = auth.uid()::uuid
        )
    );

CREATE POLICY onboarding_user_policy ON user_onboarding
    FOR ALL USING (auth.uid()::uuid = user_id);

-- ============================================
-- ✅ HELPER FUNCTIONS
-- ============================================

-- Function to get variant by ID (compatible con código que usa "variants" table)
CREATE OR REPLACE FUNCTION get_variant_public_data(variant_uuid UUID)
RETURNS TABLE (
    id UUID,
    experiment_id UUID,
    name VARCHAR(255),
    content JSONB,
    total_allocations INTEGER,
    total_conversions INTEGER,
    observed_conversion_rate DECIMAL(10,6),
    is_active BOOLEAN,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ev.id,
        ee.experiment_id,
        ev.name,
        ev.content,
        ev.total_allocations,
        ev.total_conversions,
        ev.conversion_rate as observed_conversion_rate,
        TRUE as is_active,
        ev.created_at
    FROM element_variants ev
    JOIN experiment_elements ee ON ev.element_id = ee.id
    WHERE ev.id = variant_uuid;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SEED DATA (opcional, para testing)
-- ============================================

-- Descomentar para crear usuario de prueba
/*
INSERT INTO users (email, password_hash, name, company)
VALUES (
    'demo@samplit.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7BlBXXzW/i', -- password: demo123
    'Demo User',
    'Samplit'
);
*/

