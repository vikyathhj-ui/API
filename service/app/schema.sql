-- Database schema. Safe to run repeatedly (IF NOT EXISTS), so the API applies it on start-up.
-- Privacy by design: we store WHO called WHAT and WHEN (for quotas and billing),
-- never the invoice contents.

CREATE TABLE IF NOT EXISTS customers (
    id          BIGSERIAL PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    name        TEXT,
    plan        TEXT NOT NULL DEFAULT 'free',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS api_keys (
    id           BIGSERIAL PRIMARY KEY,
    customer_id  BIGINT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    key_hash     TEXT NOT NULL UNIQUE,     -- SHA-256 of the key; the key itself is never stored
    key_prefix   TEXT NOT NULL,            -- first characters, to recognise a key in lists
    label        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS usage_events (
    id           BIGSERIAL PRIMARY KEY,
    customer_id  BIGINT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    api_key_id   BIGINT REFERENCES api_keys(id) ON DELETE SET NULL,
    endpoint     TEXT NOT NULL,
    status       INTEGER NOT NULL,
    billable     BOOLEAN NOT NULL,
    duration_ms  INTEGER NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS usage_events_customer_month
    ON usage_events (customer_id, created_at) WHERE billable;
