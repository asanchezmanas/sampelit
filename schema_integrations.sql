-- schema_integrations.sql
-- ============================================
-- Schema Updates para Integraciones
-- ============================================

-- OAuth States (temporal storage para OAuth flow)
CREATE TABLE IF NOT EXISTS oauth_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    state_token VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    shop_domain VARCHAR(255),  -- Para Shopify
    return_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Auto-delete después de 10 minutos
    CONSTRAINT expired_check CHECK (created_at > NOW() - INTERVAL '10 minutes')
);

CREATE INDEX idx_oauth_states_token ON oauth_states(state_token);
CREATE INDEX idx_oauth_states_user ON oauth_states(user_id);
CREATE INDEX idx_oauth_states_created ON oauth_states(created_at);

-- Función para limpiar estados expirados
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_states()
RETURNS void AS $$
BEGIN
    DELETE FROM oauth_states 
    WHERE created_at < NOW() - INTERVAL '10 minutes';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Updates a platform_installations
-- ============================================

-- Agregar columna para metadata adicional si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'platform_installations' 
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE platform_installations 
        ADD COLUMN metadata JSONB DEFAULT '{}';
    END IF;
END $$;

-- Índice para búsquedas en metadata
CREATE INDEX IF NOT EXISTS idx_installations_metadata 
ON platform_installations USING gin(metadata);

-- ============================================
-- Webhook Registry
-- ============================================

-- Tabla para trackear webhooks registrados
CREATE TABLE IF NOT EXISTS integration_webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id UUID NOT NULL REFERENCES platform_installations(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    webhook_id VARCHAR(255) NOT NULL,  -- ID del webhook en la plataforma externa
    topic VARCHAR(100) NOT NULL,  -- Tipo de evento
    url TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    last_triggered TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(installation_id, webhook_id)
);

CREATE INDEX idx_webhooks_installation ON integration_webhooks(installation_id);
CREATE INDEX idx_webhooks_platform ON integration_webhooks(platform);
CREATE INDEX idx_webhooks_status ON integration_webhooks(status);

-- ============================================
-- Integration Events Log
-- ============================================

-- Log de eventos de integraciones (para debugging)
CREATE TABLE IF NOT EXISTS integration_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id UUID REFERENCES platform_installations(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(20) NOT NULL,  -- 'oauth', 'sync', 'webhook', 'error'
    message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_integration_events_installation ON integration_events(installation_id);
CREATE INDEX idx_integration_events_type ON integration_events(event_type);
CREATE INDEX idx_integration_events_category ON integration_events(event_category);
CREATE INDEX idx_integration_events_created ON integration_events(created_at DESC);

-- Función helper para loggear eventos
CREATE OR REPLACE FUNCTION log_integration_event(
    p_installation_id UUID,
    p_event_type VARCHAR,
    p_category VARCHAR,
    p_message TEXT,
    p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    INSERT INTO integration_events (
        installation_id, event_type, event_category, message, metadata
    ) VALUES (
        p_installation_id, p_event_type, p_category, p_message, p_metadata
    ) RETURNING id INTO v_event_id;
    
    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Cleanup Job (opcional, para cron)
-- ============================================

-- Función para limpiar eventos viejos (retener solo últimos 30 días)
CREATE OR REPLACE FUNCTION cleanup_old_integration_events()
RETURNS void AS $$
BEGIN
    DELETE FROM integration_events 
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Vistas útiles
-- ============================================

-- Vista: Integraciones activas con stats
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
    COUNT(DISTINCT iw.id) as webhook_count,
    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'active') as active_experiments,
    pi.metadata
FROM platform_installations pi
LEFT JOIN integration_webhooks iw ON pi.id = iw.installation_id AND iw.status = 'active'
LEFT JOIN experiments e ON e.user_id = pi.user_id AND e.url LIKE '%' || pi.site_url || '%'
WHERE pi.status = 'active'
GROUP BY pi.id;

-- Vista: Últimos eventos por instalación
CREATE OR REPLACE VIEW v_recent_integration_events AS
SELECT 
    ie.*,
    pi.platform,
    pi.site_name
FROM integration_events ie
JOIN platform_installations pi ON ie.installation_id = pi.id
WHERE ie.created_at > NOW() - INTERVAL '7 days'
ORDER BY ie.created_at DESC;

-- ============================================
-- Grants (si usas RLS)
-- ============================================

ALTER TABLE oauth_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY oauth_states_user_policy ON oauth_states
    FOR ALL USING (auth.uid()::uuid = user_id);

CREATE POLICY webhooks_user_policy ON integration_webhooks
    FOR ALL USING (
        installation_id IN (
            SELECT id FROM platform_installations WHERE user_id = auth.uid()::uuid
        )
    );

CREATE POLICY events_user_policy ON integration_events
    FOR ALL USING (
        installation_id IN (
            SELECT id FROM platform_installations WHERE user_id = auth.uid()::uuid
        )
    );

-- ============================================
-- Comentarios
-- ============================================

COMMENT ON TABLE oauth_states IS 'Temporary storage for OAuth flow state tokens (auto-expires after 10 minutes)';
COMMENT ON TABLE integration_webhooks IS 'Registry of webhooks registered with external platforms';
COMMENT ON TABLE integration_events IS 'Log of integration events for debugging and auditing';

COMMENT ON FUNCTION log_integration_event IS 'Helper function to log integration events';
COMMENT ON FUNCTION cleanup_expired_oauth_states IS 'Cleanup function for expired OAuth states (run via cron)';
COMMENT ON FUNCTION cleanup_old_integration_events IS 'Cleanup function for old event logs (run via cron)';
