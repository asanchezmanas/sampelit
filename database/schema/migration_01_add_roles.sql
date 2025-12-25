-- Migration: Add role to users
-- Date: 2025-12-25

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'client';

-- Constrain values
ALTER TABLE users 
ADD CONSTRAINT valid_role CHECK (role IN ('client', 'admin', 'editor'));

-- Create index for faster role lookups
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Set initial admin (optional, for safety we don't hardcode emails here, 
-- user should update their role directly in DB or via seed script)
