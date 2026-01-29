"""SQL queries for keystroke data operations."""

# User queries
CREATE_USER = """
    INSERT INTO users (external_id, metadata)
    VALUES ($1, $2)
    ON CONFLICT (external_id) DO UPDATE SET metadata = users.metadata || $2
    RETURNING id, external_id, created_at, metadata
"""

GET_USER_BY_EXTERNAL_ID = """
    SELECT id, external_id, created_at, metadata
    FROM users WHERE external_id = $1
"""

# Session queries
CREATE_SESSION = """
    INSERT INTO sessions (user_id, domain, metadata)
    VALUES ($1, $2, $3)
    RETURNING id, user_id, started_at, ended_at, session_hash, domain, metadata
"""

END_SESSION = """
    UPDATE sessions
    SET ended_at = NOW(), session_hash = $2
    WHERE id = $1
    RETURNING id, user_id, started_at, ended_at, session_hash, domain, metadata
"""

GET_SESSION = """
    SELECT id, user_id, started_at, ended_at, session_hash, domain, metadata
    FROM sessions WHERE id = $1
"""

# Keystroke queries
INSERT_KEYSTROKES_BATCH = """
    INSERT INTO keystrokes (time, session_id, sequence_num, event_type, key_code, key_char, client_timestamp, dwell_time, flight_time)
    SELECT * FROM unnest($1::timestamptz[], $2::uuid[], $3::int[], $4::smallint[], $5::int[], $6::char[], $7::float8[], $8::float8[], $9::float8[])
"""

GET_SESSION_KEYSTROKES = """
    SELECT time, session_id, sequence_num, event_type, key_code, key_char, client_timestamp, dwell_time, flight_time
    FROM keystrokes
    WHERE session_id = $1
    ORDER BY sequence_num ASC
"""

# Feature queries
COMPUTE_SESSION_FEATURES = """
    SELECT 
        COUNT(*) as total_keystrokes,
        EXTRACT(EPOCH FROM (MAX(time) - MIN(time))) * 1000 as duration_ms,
        AVG(dwell_time) as avg_dwell_time,
        STDDEV(dwell_time) as std_dwell_time,
        AVG(flight_time) as avg_flight_time,
        STDDEV(flight_time) as std_flight_time,
        COUNT(*) FILTER (WHERE key_code = 8) as backspace_count
    FROM keystrokes
    WHERE session_id = $1 AND event_type = 1
"""

INSERT_SESSION_FEATURES = """
    INSERT INTO session_features (
        session_id, user_id, total_keystrokes, duration_ms,
        avg_dwell_time, std_dwell_time, avg_flight_time, std_flight_time,
        avg_wpm, error_rate, pause_count, avg_pause_duration,
        digraph_features, prediction_score, is_human
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
    RETURNING id, session_id, computed_at, prediction_score, is_human
"""

GET_SESSION_FEATURES = """
    SELECT * FROM session_features WHERE session_id = $1
"""
