-- Add digest preferences to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS opt_in_digest BOOLEAN NOT NULL DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS last_digest_sent_at TIMESTAMP WITH TIME ZONE NULL;

-- Create digest_log table for idempotent tracking
CREATE TABLE IF NOT EXISTS digest_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('sent', 'skipped', 'error')),
    error_message TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, period_start, period_end)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_digest_log_user_id ON digest_log(user_id);
CREATE INDEX IF NOT EXISTS idx_digest_log_status ON digest_log(status);
CREATE INDEX IF NOT EXISTS idx_digest_log_period ON digest_log(period_start, period_end);

COMMENT ON TABLE digest_log IS 'Tracks weekly digest sends with idempotency guarantees';
COMMENT ON COLUMN users.opt_in_digest IS 'User preference for receiving weekly digest emails';
COMMENT ON COLUMN users.last_digest_sent_at IS 'Timestamp of last successfully sent digest';
