-- ============================================
-- LEADS TABLE (Email Capture)
-- ============================================
-- For waitlist signups and email sequence tracking

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core data
    email VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(50) DEFAULT 'simulator',
    variant VARCHAR(50),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'waitlist' CHECK (status IN ('waitlist', 'invited', 'active', 'churned', 'unsubscribed')),
    
    -- Email sequence tracking
    email_1_sent_at TIMESTAMP,
    email_2_sent_at TIMESTAMP,
    email_3_sent_at TIMESTAMP,
    
    -- Conversion tracking
    converted_at TIMESTAMP,
    converted_plan VARCHAR(50),
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    referrer TEXT,
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_leads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_leads_updated_at ON leads;
CREATE TRIGGER trigger_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_leads_updated_at();

-- Comments
COMMENT ON TABLE leads IS 'Email leads from simulator, landing pages, and marketing campaigns';
COMMENT ON COLUMN leads.status IS 'waitlist=pending, invited=got access, active=paying, churned=canceled, unsubscribed=opted out';
