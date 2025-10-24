-- Email events table for tracking Resend webhook events
CREATE TABLE IF NOT EXISTS email_events (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email        text NOT NULL,
    event_type   text NOT NULL,           -- delivered, bounced, complained, opened, clicked, etc.
    provider_id  text,                    -- Resend email id
    subject      text,
    payload      jsonb NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS email_events_email_idx ON email_events(email);
CREATE INDEX IF NOT EXISTS email_events_type_idx ON email_events(event_type);
CREATE INDEX IF NOT EXISTS email_events_created_idx ON email_events(created_at);

-- Digest runs table for tracking weekly digest execution
CREATE TABLE IF NOT EXISTS digest_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    sent integer NOT NULL DEFAULT 0,
    errors integer NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS digest_runs_started_idx ON digest_runs(started_at DESC);
