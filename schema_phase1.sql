-- schema_phase1.sql - SOLO FASE 1

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

-- Assignments (asignaciones de usuarios)
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    variant_assignments JSONB NOT NULL,  -- {"element1": "variant2", ...}
    context JSONB DEFAULT '{}',
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    converted_at TIMESTAMPTZ,
    conversion_value DECIMAL(10,2) DEFAULT 0,
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

-- Índices
CREATE INDEX idx_experiments_user ON experiments(user_id);
CREATE INDEX idx_elements_experiment ON experiment_elements(experiment_id);
CREATE INDEX idx_variants_element ON element_variants(element_id);
CREATE INDEX idx_assignments_experiment ON assignments(experiment_id);
CREATE INDEX idx_assignments_user ON assignments(user_id);
CREATE INDEX idx_installations_user ON platform_installations(user_id);
CREATE INDEX idx_installations_token ON platform_installations(installation_token);

-- Triggers
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

-- RLS (Row Level Security)
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE element_variants ENABLE ROW LEVEL SECURITY;

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

-- Añadir a schema_phase1.sql

CREATE TABLE traffic_exclusion_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Método de exclusión
    rule_type VARCHAR(20) NOT NULL,  -- 'ip', 'cookie', 'email', 'url_param'
    
    -- Valor del filtro
    rule_value TEXT NOT NULL,
    
    -- Metadata
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_rule_type CHECK (rule_type IN ('ip', 'cookie', 'email', 'url_param', 'user_agent'))
);

CREATE INDEX idx_exclusion_rules_user ON traffic_exclusion_rules(user_id);
CREATE INDEX idx_exclusion_rules_type ON traffic_exclusion_rules(rule_type);

-- Tabla para sesiones excluidas (para analytics)
CREATE TABLE excluded_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    user_identifier VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    exclusion_reason TEXT,  -- "IP: 192.168.1.1", "Cookie: samplit_internal=true"
    excluded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_excluded_sessions_experiment ON excluded_sessions(experiment_id);

-- Añadir al final de schema_phase1.sql

-- ============================================
-- ONBOARDING TABLE
-- ============================================

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

CREATE INDEX idx_onboarding_user ON user_onboarding(user_id);
CREATE INDEX idx_onboarding_completed ON user_onboarding(completed);

-- Trigger para updated_at
CREATE TRIGGER update_onboarding_updated_at 
    BEFORE UPDATE ON user_onboarding
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

ALTER TABLE user_onboarding ENABLE ROW LEVEL SECURITY;

CREATE POLICY onboarding_user_policy ON user_onboarding
    FOR ALL USING (auth.uid()::uuid = user_id);

