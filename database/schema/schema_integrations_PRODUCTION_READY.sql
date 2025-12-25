-- schema_integrations_PRODUCTION_READY.sql
-- PRODUCTION READY - Integraciones WordPress, Shopify, etc
-- Versión: 1.0
-- Fecha: 13 Diciembre 2025
-- REQUISITO: Ejecutar DESPUÉS de schema_phase1_PRODUCTION.sql

-- ============================================
-- TABLA: OAUTH_STATES
-- ============================================

CREATE TABLE IF NOT EXISTS oauth_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    state_token VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    shop_domain VARCHAR(255),  -- Para Shopify
    return_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- (El cleanup se maneja vía función cleanup_expired_oauth_states)
    CONSTRAINT valid_platform CHECK (platform IN ('wordpress', 'shopify', 'woocommerce', 'magento'))
);

-- Índices para oauth_states
CREATE INDEX idx_oauth_states_token ON oauth_states(state_token);
CREATE INDEX idx_oauth_states_user ON oauth_states(user_id);
CREATE INDEX idx_oauth_states_created ON oauth_states(created_at);

-- Función para limpiar estados expirados (ejecutar con cron)
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_states()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM oauth_states 
    WHERE created_at < NOW() - INTERVAL '10 minutes';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_oauth_states IS 'Cleanup expired OAuth states (run via cron every 10 minutes)';

-- ============================================
-- TABLA: INTEGRATION_WEBHOOKS
-- ============================================

CREATE TABLE IF NOT EXISTS integration_webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id UUID NOT NULL REFERENCES platform_installations(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    webhook_id VARCHAR(255) NOT NULL,  -- ID del webhook en la plataforma externa
    topic VARCHAR(100) NOT NULL,  -- Tipo de evento (orders/create, posts/update, etc)
    url TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    last_triggered TIMESTAMPTZ,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(installation_id, webhook_id),
    CONSTRAINT valid_platform CHECK (platform IN ('wordpress', 'shopify', 'woocommerce', 'magento')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'error', 'deleted'))
);

-- Índices para integration_webhooks
CREATE INDEX idx_webhooks_installation ON integration_webhooks(installation_id);
CREATE INDEX idx_webhooks_platform ON integration_webhooks(platform);
CREATE INDEX idx_webhooks_status ON integration_webhooks(status);
CREATE INDEX idx_webhooks_topic ON integration_webhooks(topic);

-- Índice para cleanup de webhooks con errores
CREATE INDEX idx_webhooks_errors ON integration_webhooks(error_count, last_triggered) 
    WHERE status = 'error';

-- ============================================
-- TABLA: INTEGRATION_EVENTS
-- ============================================

CREATE TABLE IF NOT EXISTS integration_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id UUID REFERENCES platform_installations(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(20) NOT NULL,  -- 'oauth', 'sync', 'webhook', 'error', 'api'
    severity VARCHAR(10) DEFAULT 'info',  -- 'info', 'warning', 'error', 'critical'
    message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_category CHECK (event_category IN ('oauth', 'sync', 'webhook', 'error', 'api', 'install')),
    CONSTRAINT valid_severity CHECK (severity IN ('info', 'warning', 'error', 'critical'))
);

-- Índices para integration_events
CREATE INDEX idx_integration_events_installation ON integration_events(installation_id);
CREATE INDEX idx_integration_events_type ON integration_events(event_type);
CREATE INDEX idx_integration_events_category ON integration_events(event_category);
CREATE INDEX idx_integration_events_severity ON integration_events(severity);
CREATE INDEX idx_integration_events_created ON integration_events(created_at DESC);

-- Índice compuesto para queries de debugging
CREATE INDEX idx_integration_events_debug ON integration_events(installation_id, severity, created_at DESC)
    WHERE severity IN ('error', 'critical');

-- Índice para metadata (JSONB)
CREATE INDEX idx_integration_events_metadata ON integration_events USING gin(metadata);

-- Función helper para loggear eventos
CREATE OR REPLACE FUNCTION log_integration_event(
    p_installation_id UUID,
    p_event_type VARCHAR,
    p_category VARCHAR,
    p_message TEXT,
    p_severity VARCHAR DEFAULT 'info',
    p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    INSERT INTO integration_events (
        installation_id, 
        event_type, 
        event_category, 
        severity,
        message, 
        metadata
    ) VALUES (
        p_installation_id, 
        p_event_type, 
        p_category, 
        p_severity,
        p_message, 
        p_metadata
    ) RETURNING id INTO v_event_id;
    
    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_integration_event IS 'Helper function to log integration events with severity';

-- Función para limpiar eventos viejos (retener solo últimos 30 días)
CREATE OR REPLACE FUNCTION cleanup_old_integration_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM integration_events 
    WHERE created_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_integration_events IS 'Cleanup old integration events (run daily via cron)';

-- ============================================
-- TABLA: INTEGRATION_API_CALLS
-- ============================================

-- Track API calls para rate limiting y monitoring
CREATE TABLE IF NOT EXISTS integration_api_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id UUID REFERENCES platform_installations(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_method CHECK (method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'))
);

-- Índices para integration_api_calls
CREATE INDEX idx_api_calls_installation ON integration_api_calls(installation_id);
CREATE INDEX idx_api_calls_platform ON integration_api_calls(platform);
CREATE INDEX idx_api_calls_created ON integration_api_calls(created_at DESC);
CREATE INDEX idx_api_calls_status ON integration_api_calls(status_code);

-- Índice para rate limiting (Optimizado para queries recientes)
CREATE INDEX idx_api_calls_rate_limit ON integration_api_calls(installation_id, created_at DESC);

-- Función para limpiar llamadas API viejas (retener solo últimos 7 días)
CREATE OR REPLACE FUNCTION cleanup_old_api_calls()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM integration_api_calls 
    WHERE created_at < NOW() - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_api_calls IS 'Cleanup old API calls (run daily via cron)';

-- ============================================
-- TABLA: PLATFORM_SYNC_JOBS
-- ============================================

-- Para trackear sync jobs de productos, posts, etc
CREATE TABLE IF NOT EXISTS platform_sync_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id UUID NOT NULL REFERENCES platform_installations(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,  -- 'products', 'posts', 'orders', 'full_sync'
    status VARCHAR(20) DEFAULT 'pending',
    
    -- Progress tracking
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Índices para platform_sync_jobs
CREATE INDEX idx_sync_jobs_installation ON platform_sync_jobs(installation_id);
CREATE INDEX idx_sync_jobs_status ON platform_sync_jobs(status);
CREATE INDEX idx_sync_jobs_type ON platform_sync_jobs(job_type);
CREATE INDEX idx_sync_jobs_created ON platform_sync_jobs(created_at DESC);

-- Índice para jobs activos
CREATE INDEX idx_sync_jobs_active ON platform_sync_jobs(installation_id, status)
    WHERE status IN ('pending', 'running');

-- ============================================
-- VISTAS ÚTILES
-- ============================================

-- Vista: Integraciones activas con estadísticas
CREATE OR REPLACE VIEW v_active_integrations AS
SELECT 
    pi.id,
    pi.user_id,
    pi.platform,
    pi.installation_method,
    pi.site_name,
    pi.site_url,
    pi.status,
    pi.verified_at,
    pi.last_activity,
    pi.created_at,
    
    -- Webhook stats
    COUNT(DISTINCT iw.id) FILTER (WHERE iw.status = 'active') as active_webhook_count,
    COUNT(DISTINCT iw.id) FILTER (WHERE iw.status = 'error') as error_webhook_count,
    
    -- Event stats (últimas 24h)
    COUNT(DISTINCT ie.id) FILTER (
        WHERE ie.created_at > NOW() - INTERVAL '24 hours'
    ) as events_24h,
    COUNT(DISTINCT ie.id) FILTER (
        WHERE ie.created_at > NOW() - INTERVAL '24 hours' 
        AND ie.severity IN ('error', 'critical')
    ) as errors_24h,
    
    -- Sync job stats
    COUNT(DISTINCT sj.id) FILTER (
        WHERE sj.status = 'running'
    ) as running_sync_jobs,
    
    pi.metadata
FROM platform_installations pi
LEFT JOIN integration_webhooks iw ON pi.id = iw.installation_id
LEFT JOIN integration_events ie ON pi.id = ie.installation_id
LEFT JOIN platform_sync_jobs sj ON pi.id = sj.installation_id
WHERE pi.status = 'active'
GROUP BY pi.id;

-- Vista: Últimos eventos por instalación (últimos 7 días)
CREATE OR REPLACE VIEW v_recent_integration_events AS
SELECT 
    ie.id,
    ie.installation_id,
    ie.event_type,
    ie.event_category,
    ie.severity,
    ie.message,
    ie.metadata,
    ie.created_at,
    pi.platform,
    pi.site_name,
    pi.site_url
FROM integration_events ie
JOIN platform_installations pi ON ie.installation_id = pi.id
WHERE ie.created_at > NOW() - INTERVAL '7 days'
ORDER BY ie.created_at DESC;

-- Vista: Health check de integraciones
CREATE OR REPLACE VIEW v_integration_health AS
SELECT 
    pi.id as installation_id,
    pi.platform,
    pi.site_name,
    pi.status,
    
    -- Health score (0-100)
    CASE
        WHEN pi.status != 'active' THEN 0
        WHEN error_count_24h > 10 THEN 25
        WHEN error_count_24h > 5 THEN 50
        WHEN error_count_24h > 0 THEN 75
        ELSE 100
    END as health_score,
    
    -- Metrics
    COALESCE(webhook_count, 0) as webhook_count,
    COALESCE(error_count_24h, 0) as error_count_24h,
    COALESCE(api_calls_1h, 0) as api_calls_last_hour,
    
    pi.last_activity,
    pi.verified_at
FROM platform_installations pi
LEFT JOIN (
    SELECT installation_id, COUNT(*) as webhook_count
    FROM integration_webhooks
    WHERE status = 'active'
    GROUP BY installation_id
) w ON pi.id = w.installation_id
LEFT JOIN (
    SELECT installation_id, COUNT(*) as error_count_24h
    FROM integration_events
    WHERE severity IN ('error', 'critical')
    AND created_at > NOW() - INTERVAL '24 hours'
    GROUP BY installation_id
) e ON pi.id = e.installation_id
LEFT JOIN (
    SELECT installation_id, COUNT(*) as api_calls_1h
    FROM integration_api_calls
    WHERE created_at > NOW() - INTERVAL '1 hour'
    GROUP BY installation_id
) a ON pi.id = a.installation_id;

-- ============================================
-- TRIGGERS
-- ============================================

CREATE TRIGGER update_webhooks_updated_at 
    BEFORE UPDATE ON integration_webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sync_jobs_updated_at 
    BEFORE UPDATE ON platform_sync_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

ALTER TABLE oauth_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_api_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_sync_jobs ENABLE ROW LEVEL SECURITY;

-- Políticas para oauth_states
CREATE POLICY oauth_states_user_policy ON oauth_states
    FOR ALL USING (auth.uid()::uuid = user_id);

-- Políticas para integration_webhooks
CREATE POLICY webhooks_user_policy ON integration_webhooks
    FOR ALL USING (
        installation_id IN (
            SELECT id FROM platform_installations WHERE user_id = auth.uid()::uuid
        )
    );

-- Políticas para integration_events
CREATE POLICY events_user_policy ON integration_events
    FOR ALL USING (
        installation_id IN (
            SELECT id FROM platform_installations WHERE user_id = auth.uid()::uuid
        )
    );

-- Políticas para integration_api_calls
CREATE POLICY api_calls_user_policy ON integration_api_calls
    FOR SELECT USING (
        installation_id IN (
            SELECT id FROM platform_installations WHERE user_id = auth.uid()::uuid
        )
    );

-- Políticas para platform_sync_jobs
CREATE POLICY sync_jobs_user_policy ON platform_sync_jobs
    FOR ALL USING (
        installation_id IN (
            SELECT id FROM platform_installations WHERE user_id = auth.uid()::uuid
        )
    );

-- ============================================
-- FUNCIONES ADICIONALES
-- ============================================

-- Función para obtener health score de una instalación
CREATE OR REPLACE FUNCTION get_installation_health(install_id UUID)
RETURNS INTEGER AS $$
DECLARE
    health_score INTEGER;
BEGIN
    SELECT 
        CASE
            WHEN pi.status != 'active' THEN 0
            WHEN error_count > 10 THEN 25
            WHEN error_count > 5 THEN 50
            WHEN error_count > 0 THEN 75
            ELSE 100
        END INTO health_score
    FROM platform_installations pi
    LEFT JOIN (
        SELECT installation_id, COUNT(*) as error_count
        FROM integration_events
        WHERE severity IN ('error', 'critical')
        AND created_at > NOW() - INTERVAL '24 hours'
        GROUP BY installation_id
    ) e ON pi.id = e.installation_id
    WHERE pi.id = install_id;
    
    RETURN COALESCE(health_score, 0);
END;
$$ LANGUAGE plpgsql;

-- Función para marcar última actividad de instalación
CREATE OR REPLACE FUNCTION mark_installation_activity(install_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE platform_installations
    SET last_activity = NOW()
    WHERE id = install_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- COMENTARIOS
-- ============================================

COMMENT ON TABLE oauth_states IS 'Temporary storage for OAuth flow state tokens (auto-expires after 10 minutes)';
COMMENT ON TABLE integration_webhooks IS 'Registry of webhooks registered with external platforms';
COMMENT ON TABLE integration_events IS 'Log of integration events for debugging and auditing';
COMMENT ON TABLE integration_api_calls IS 'Track API calls for rate limiting and monitoring';
COMMENT ON TABLE platform_sync_jobs IS 'Track sync jobs for products, posts, orders, etc';

COMMENT ON VIEW v_active_integrations IS 'Active integrations with statistics';
COMMENT ON VIEW v_recent_integration_events IS 'Recent integration events (last 7 days)';
COMMENT ON VIEW v_integration_health IS 'Health check dashboard for integrations';

-- ============================================
-- CRON JOBS (Configurar en servidor)
-- ============================================

-- Ejemplo de configuración de cron jobs (fuera de SQL):
-- # Limpiar OAuth states expirados (cada 10 minutos)
-- */10 * * * * psql -h localhost -U postgres -d samplit -c "SELECT cleanup_expired_oauth_states();"
-- (Nota: El formato */10 indica frecuencia en cron)

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Schema Integraciones creado exitosamente';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tablas creadas:';
    RAISE NOTICE '- oauth_states (OAuth flow)';
    RAISE NOTICE '- integration_webhooks (Webhook registry)';
    RAISE NOTICE '- integration_events (Event logging)';
    RAISE NOTICE '- integration_api_calls (API monitoring)';
    RAISE NOTICE '- platform_sync_jobs (Sync tracking)';
    RAISE NOTICE '';
    RAISE NOTICE 'Vistas creadas:';
    RAISE NOTICE '- v_active_integrations';
    RAISE NOTICE '- v_recent_integration_events';
    RAISE NOTICE '- v_integration_health';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  IMPORTANTE: Configurar cron jobs para cleanup';
    RAISE NOTICE '';
END $$;
