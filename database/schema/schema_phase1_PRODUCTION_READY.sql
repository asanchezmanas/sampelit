-- schema_phase1_PRODUCTION_READY.sql
-- ✅ PRODUCTION READY - Optimizado para Samplit A/B Testing
-- Versión: 1.0
-- Fecha: 13 Diciembre 2025

-- ============================================
-- EXTENSIONES
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- TABLA: USERS
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created ON users(created_at DESC);

-- ============================================
-- TABLA: EXPERIMENTS
-- ============================================

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
    
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived')),
    CONSTRAINT valid_traffic_allocation CHECK (traffic_allocation > 0 AND traffic_allocation <= 1.0)
);

-- ✅ ÍNDICES CRÍTICOS PARA EXPERIMENTS
CREATE INDEX idx_experiments_user ON experiments(user_id);
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_user_status ON experiments(user_id, status);
CREATE INDEX idx_experiments_created ON experiments(created_at DESC);

-- ✅ ÍNDICE COMPUESTO para tracker (query más común)
CREATE INDEX idx_experiments_active_lookup ON experiments(user_id, status, url) 
    WHERE status = 'active';

-- ============================================
-- TABLA: EXPERIMENT_ELEMENTS
-- ============================================

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
    
    UNIQUE(experiment_id, element_order),
    CONSTRAINT valid_selector_type CHECK (selector_type IN ('css', 'xpath', 'id', 'class'))
);

-- Índices para experiment_elements
CREATE INDEX idx_elements_experiment ON experiment_elements(experiment_id);
CREATE INDEX idx_elements_experiment_order ON experiment_elements(experiment_id, element_order);

-- ============================================
-- TABLA: ELEMENT_VARIANTS (CRÍTICA)
-- ============================================

CREATE TABLE element_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    element_id UUID NOT NULL REFERENCES experiment_elements(id) ON DELETE CASCADE,
    variant_order INTEGER NOT NULL DEFAULT 0,
    name VARCHAR(255),
    content JSONB NOT NULL,
    
    -- ✅ MÉTRICAS PÚBLICAS
    total_allocations INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(10,6) DEFAULT 0,
    
    -- ✅ CRÍTICO: Estado cifrado de Thompson Sampling (BYTEA)
    algorithm_state BYTEA,
    state_version INTEGER DEFAULT 1,
    
    -- Flags
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(element_id, variant_order),
    CONSTRAINT positive_allocations CHECK (total_allocations >= 0),
    CONSTRAINT positive_conversions CHECK (total_conversions >= 0),
    CONSTRAINT conversions_le_allocations CHECK (total_conversions <= total_allocations)
);

-- ✅ ÍNDICES CRÍTICOS PARA ELEMENT_VARIANTS
CREATE INDEX idx_variants_element ON element_variants(element_id);
CREATE INDEX idx_variants_element_order ON element_variants(element_id, variant_order);

-- ✅ ÍNDICE CRÍTICO para optimization queries
CREATE INDEX idx_variants_active ON element_variants(element_id, is_active) 
    WHERE is_active = TRUE;

-- ✅ ÍNDICE para analytics
CREATE INDEX idx_variants_metrics ON element_variants(total_allocations, total_conversions);

-- ============================================
-- VIEW: VARIANTS (Backward Compatibility)
-- ============================================

-- Esta VIEW permite usar "variants" en el código mientras
-- la tabla real es "element_variants"
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
    ev.is_active,
    ev.state_version,
    ev.created_at,
    ev.updated_at
FROM element_variants ev
JOIN experiment_elements ee ON ev.element_id = ee.id;

-- ============================================
-- TABLA: ASSIGNMENTS (MUY CRÍTICA PARA PERFORMANCE)
-- ============================================

CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    
    -- Para experimentos simples (1 elemento)
    variant_id UUID REFERENCES element_variants(id) ON DELETE SET NULL,
    
    -- Para experimentos multi-elemento
    variant_assignments JSONB,  -- {"element1": "variant2", ...}
    
    session_id VARCHAR(255),
    context JSONB DEFAULT '{}',
    
    -- Timestamps
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    converted_at TIMESTAMPTZ,
    
    -- Conversion data
    conversion_value DECIMAL(10,2) DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    
    -- ✅ CONSTRAINT ÚNICO para prevenir duplicados
    UNIQUE(experiment_id, user_id)
);

-- ✅ ÍNDICES CRÍTICOS PARA ASSIGNMENTS (Performance crítica del tracker)
-- Índice principal para lookup de asignaciones
CREATE UNIQUE INDEX idx_assignments_lookup ON assignments(experiment_id, user_id);

-- Índice para user_id (búsquedas por usuario)
CREATE INDEX idx_assignments_user ON assignments(user_id);

-- Índice para conversiones (analytics)
CREATE INDEX idx_assignments_converted ON assignments(experiment_id, converted_at) 
    WHERE converted_at IS NOT NULL;

-- Índice para timeline queries
CREATE INDEX idx_assignments_assigned_at ON assignments(assigned_at DESC);

-- Índice para variant (analytics por variante)
CREATE INDEX idx_assignments_variant ON assignments(variant_id) 
    WHERE variant_id IS NOT NULL;

-- ============================================
-- TABLA: PLATFORM_INSTALLATIONS
-- ============================================

CREATE TABLE platform_installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    installation_method VARCHAR(50) NOT NULL,
    site_url VARCHAR(500) NOT NULL,
    site_name VARCHAR(255),
    
    -- Tokens
    installation_token VARCHAR(255) UNIQUE NOT NULL,
    api_token VARCHAR(255) UNIQUE NOT NULL,
    
    status VARCHAR(20) DEFAULT 'pending',
    verified_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ,
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_platform CHECK (platform IN ('manual', 'wordpress', 'shopify', 'woocommerce', 'magento')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'active', 'inactive', 'error'))
);

-- Índices para platform_installations
CREATE INDEX idx_installations_user ON platform_installations(user_id);
CREATE INDEX idx_installations_token ON platform_installations(installation_token);
CREATE INDEX idx_installations_api_token ON platform_installations(api_token);
CREATE INDEX idx_installations_status ON platform_installations(status);
CREATE INDEX idx_installations_platform ON platform_installations(platform);

-- ✅ ÍNDICE para metadata (GIN index para JSONB)
CREATE INDEX idx_installations_metadata ON platform_installations USING gin(metadata);

-- ============================================
-- TABLA: TRAFFIC_EXCLUSION_RULES
-- ============================================

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

-- Índices para traffic_exclusion_rules
CREATE INDEX idx_exclusion_rules_user ON traffic_exclusion_rules(user_id);
CREATE INDEX idx_exclusion_rules_type ON traffic_exclusion_rules(rule_type);
CREATE INDEX idx_exclusion_rules_enabled ON traffic_exclusion_rules(user_id, enabled) 
    WHERE enabled = true;

-- ============================================
-- TABLA: EXCLUDED_SESSIONS
-- ============================================

CREATE TABLE excluded_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    user_identifier VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    exclusion_reason TEXT,
    excluded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para excluded_sessions
CREATE INDEX idx_excluded_sessions_experiment ON excluded_sessions(experiment_id);
CREATE INDEX idx_excluded_sessions_user ON excluded_sessions(user_identifier);
CREATE INDEX idx_excluded_sessions_date ON excluded_sessions(excluded_at DESC);

-- ============================================
-- TABLA: USER_ONBOARDING
-- ============================================

CREATE TABLE user_onboarding (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    completed BOOLEAN DEFAULT false,
    current_step VARCHAR(50) DEFAULT 'welcome',
    installation_verified BOOLEAN DEFAULT false,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_step CHECK (current_step IN ('welcome', 'install', 'verify', 'create_experiment', 'complete'))
);

-- Índices para user_onboarding
CREATE INDEX idx_onboarding_completed ON user_onboarding(completed);

-- ============================================
-- TABLA: SUBSCRIPTIONS
-- ============================================

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) DEFAULT 'free',
    status VARCHAR(20) DEFAULT 'active',
    
    -- Stripe
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT false,
    canceled_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_plan CHECK (plan IN ('free', 'starter', 'professional', 'enterprise')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'past_due', 'canceled', 'incomplete'))
);

-- Índices para subscriptions
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_plan ON subscriptions(plan);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);

-- ============================================
-- TRIGGERS PARA UPDATE TIMESTAMPS
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiments_updated_at 
    BEFORE UPDATE ON experiments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_variants_updated_at 
    BEFORE UPDATE ON element_variants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_installations_updated_at 
    BEFORE UPDATE ON platform_installations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exclusion_rules_updated_at 
    BEFORE UPDATE ON traffic_exclusion_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_onboarding_updated_at 
    BEFORE UPDATE ON user_onboarding
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at 
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE element_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_installations ENABLE ROW LEVEL SECURITY;
ALTER TABLE traffic_exclusion_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_onboarding ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Políticas para users (solo pueden ver/editar su propio registro)
CREATE POLICY users_self_policy ON users
    FOR ALL USING (auth.uid()::uuid = id);

-- Políticas para experiments
CREATE POLICY experiments_user_policy ON experiments
    FOR ALL USING (auth.uid()::uuid = user_id);

-- Políticas para experiment_elements
CREATE POLICY elements_user_policy ON experiment_elements
    FOR ALL USING (
        experiment_id IN (SELECT id FROM experiments WHERE user_id = auth.uid()::uuid)
    );

-- Políticas para element_variants
CREATE POLICY variants_user_policy ON element_variants
    FOR ALL USING (
        element_id IN (
            SELECT ee.id FROM experiment_elements ee
            JOIN experiments e ON ee.experiment_id = e.id
            WHERE e.user_id = auth.uid()::uuid
        )
    );

-- Políticas para assignments (usuarios pueden ver sus propias asignaciones)
CREATE POLICY assignments_user_policy ON assignments
    FOR SELECT USING (
        experiment_id IN (SELECT id FROM experiments WHERE user_id = auth.uid()::uuid)
    );

-- Políticas para platform_installations
CREATE POLICY installations_user_policy ON platform_installations
    FOR ALL USING (auth.uid()::uuid = user_id);

-- Políticas para traffic_exclusion_rules
CREATE POLICY exclusion_rules_user_policy ON traffic_exclusion_rules
    FOR ALL USING (auth.uid()::uuid = user_id);

-- Políticas para user_onboarding
CREATE POLICY onboarding_user_policy ON user_onboarding
    FOR ALL USING (auth.uid()::uuid = user_id);

-- Políticas para subscriptions
CREATE POLICY subscriptions_user_policy ON subscriptions
    FOR ALL USING (auth.uid()::uuid = user_id);

-- ============================================
-- FUNCIONES HELPER
-- ============================================

-- Función para obtener estadísticas de experimento
CREATE OR REPLACE FUNCTION get_experiment_stats(exp_id UUID)
RETURNS TABLE (
    total_users BIGINT,
    total_conversions BIGINT,
    conversion_rate DECIMAL,
    variant_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(ev.total_allocations), 0) as total_users,
        COALESCE(SUM(ev.total_conversions), 0) as total_conversions,
        CASE 
            WHEN COALESCE(SUM(ev.total_allocations), 0) > 0 
            THEN COALESCE(SUM(ev.total_conversions), 0)::DECIMAL / 
                 COALESCE(SUM(ev.total_allocations), 1)::DECIMAL
            ELSE 0
        END as conversion_rate,
        COUNT(DISTINCT ev.id)::INTEGER as variant_count
    FROM element_variants ev
    JOIN experiment_elements ee ON ev.element_id = ee.id
    WHERE ee.experiment_id = exp_id AND ev.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Función para verificar si un experimento está listo para iniciar
CREATE OR REPLACE FUNCTION is_experiment_ready(exp_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    variant_count INTEGER;
    element_count INTEGER;
BEGIN
    -- Verificar que tenga al menos 1 elemento
    SELECT COUNT(*) INTO element_count
    FROM experiment_elements
    WHERE experiment_id = exp_id;
    
    IF element_count = 0 THEN
        RETURN FALSE;
    END IF;
    
    -- Verificar que cada elemento tenga al menos 2 variantes activas
    SELECT MIN(variant_count) INTO variant_count
    FROM (
        SELECT COUNT(*) as variant_count
        FROM element_variants ev
        JOIN experiment_elements ee ON ev.element_id = ee.id
        WHERE ee.experiment_id = exp_id AND ev.is_active = TRUE
        GROUP BY ee.id
    ) counts;
    
    RETURN variant_count >= 2;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VISTAS ÚTILES
-- ============================================

-- Vista: Experimentos activos con estadísticas
CREATE VIEW v_active_experiments AS
SELECT 
    e.id,
    e.user_id,
    e.name,
    e.description,
    e.status,
    e.url,
    e.created_at,
    e.started_at,
    (SELECT COUNT(*) FROM experiment_elements ee WHERE ee.experiment_id = e.id) as element_count,
    (SELECT COUNT(*) FROM element_variants ev 
     JOIN experiment_elements ee ON ev.element_id = ee.id 
     WHERE ee.experiment_id = e.id AND ev.is_active = TRUE) as variant_count,
    (SELECT COALESCE(SUM(total_allocations), 0) FROM element_variants ev 
     JOIN experiment_elements ee ON ev.element_id = ee.id 
     WHERE ee.experiment_id = e.id) as total_allocations,
    (SELECT COALESCE(SUM(total_conversions), 0) FROM element_variants ev 
     JOIN experiment_elements ee ON ev.element_id = ee.id 
     WHERE ee.experiment_id = e.id) as total_conversions
FROM experiments e
WHERE e.status = 'active';

-- ============================================
-- COMENTARIOS EN TABLAS
-- ============================================

COMMENT ON TABLE users IS 'Users of the Samplit platform';
COMMENT ON TABLE experiments IS 'A/B test experiments';
COMMENT ON TABLE experiment_elements IS 'Elements being tested in multi-element experiments';
COMMENT ON TABLE element_variants IS 'Variants for each element with encrypted Thompson Sampling state';
COMMENT ON TABLE assignments IS 'User assignments to variants';
COMMENT ON TABLE platform_installations IS 'Platform installations (WordPress, Shopify, manual snippet)';
COMMENT ON TABLE traffic_exclusion_rules IS 'Rules to exclude traffic from experiments (internal IPs, etc)';
COMMENT ON TABLE excluded_sessions IS 'Log of excluded sessions for analytics';
COMMENT ON TABLE user_onboarding IS 'User onboarding progress';
COMMENT ON TABLE subscriptions IS 'User subscription and billing information';

COMMENT ON COLUMN element_variants.algorithm_state IS '🔒 ENCRYPTED Thompson Sampling state (BYTEA) - Never expose in API';
COMMENT ON COLUMN element_variants.total_allocations IS 'Public metric: total users assigned to this variant';
COMMENT ON COLUMN element_variants.total_conversions IS 'Public metric: total conversions for this variant';
COMMENT ON COLUMN element_variants.conversion_rate IS 'Public metric: observed conversion rate';

-- ============================================
-- ✅ VERIFICACIÓN FINAL
-- ============================================

-- Verificar que algorithm_state es BYTEA
DO $$
DECLARE
    col_type text;
BEGIN
    SELECT data_type INTO col_type
    FROM information_schema.columns
    WHERE table_name = 'element_variants' AND column_name = 'algorithm_state';
    
    IF col_type != 'bytea' THEN
        RAISE EXCEPTION 'ERROR: algorithm_state debe ser BYTEA, pero es %', col_type;
    END IF;
    
    RAISE NOTICE '✅ algorithm_state correctamente configurado como BYTEA';
END $$;

-- Verificar índices críticos
DO $$
BEGIN
    -- Verificar idx_assignments_lookup
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'assignments' AND indexname = 'idx_assignments_lookup'
    ) THEN
        RAISE EXCEPTION 'ERROR: Falta índice crítico idx_assignments_lookup';
    END IF;
    
    -- Verificar idx_variants_active
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'element_variants' AND indexname = 'idx_variants_active'
    ) THEN
        RAISE EXCEPTION 'ERROR: Falta índice crítico idx_variants_active';
    END IF;
    
    RAISE NOTICE '✅ Todos los índices críticos presentes';
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE '✅ Schema Phase 1 creado exitosamente';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Próximos pasos:';
    RAISE NOTICE '1. Ejecutar schema_integrations.sql';
    RAISE NOTICE '2. Configurar variables de entorno';
    RAISE NOTICE '3. Inicializar aplicación';
    RAISE NOTICE '';
END $$;
