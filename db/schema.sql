-- ============================================
-- HumanSign Database Schema
-- PostgreSQL + TimescaleDB
-- ============================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================
-- Users table
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- Sessions table (writing sessions)
-- ============================================
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    session_hash VARCHAR(64),
    domain VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- Keystrokes hypertable (TimescaleDB optimized)
-- ============================================
CREATE TABLE keystrokes (
    time TIMESTAMPTZ NOT NULL,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    sequence_num INTEGER NOT NULL,
    event_type SMALLINT NOT NULL,
    key_code INTEGER NOT NULL,
    key_char CHAR(1),
    client_timestamp DOUBLE PRECISION,
    dwell_time DOUBLE PRECISION,
    flight_time DOUBLE PRECISION,
    PRIMARY KEY (time, session_id, sequence_num)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('keystrokes', 'time', chunk_time_interval => INTERVAL '1 day');

-- ============================================
-- Session features (aggregated for ML)
-- ============================================
CREATE TABLE session_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Aggregate features
    total_keystrokes INTEGER,
    duration_ms DOUBLE PRECISION,
    avg_dwell_time DOUBLE PRECISION,
    std_dwell_time DOUBLE PRECISION,
    avg_flight_time DOUBLE PRECISION,
    std_flight_time DOUBLE PRECISION,
    avg_wpm DOUBLE PRECISION,
    error_rate DOUBLE PRECISION,
    pause_count INTEGER,
    avg_pause_duration DOUBLE PRECISION,
    
    -- Digraph features (JSON)
    digraph_features JSONB,
    
    -- Model prediction
    prediction_score DOUBLE PRECISION,
    is_human BOOLEAN,
    
    CONSTRAINT valid_score CHECK (prediction_score >= 0 AND prediction_score <= 1)
);

-- ============================================
-- Indexes
-- ============================================
CREATE INDEX idx_keystrokes_session ON keystrokes (session_id, sequence_num);
CREATE INDEX idx_sessions_user ON sessions (user_id, started_at DESC);
CREATE INDEX idx_session_features_user ON session_features (user_id, computed_at DESC);

-- ============================================
-- Compression policy (after 7 days)
-- ============================================
SELECT add_compression_policy('keystrokes', INTERVAL '7 days');
