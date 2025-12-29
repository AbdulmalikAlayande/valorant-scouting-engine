-- migrations/001_initial_schema.sql

-- Job queue
CREATE TABLE report_requests (
    id SERIAL PRIMARY KEY,
    team_id VARCHAR(255) NOT NULL,
    team_name VARCHAR(255),
    time_window VARCHAR(50) DEFAULT 'LAST_3_MONTHS',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Raw match data (Python writes)
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    series_id VARCHAR(255) UNIQUE NOT NULL,
    team_id VARCHAR(255) NOT NULL,
    team_name VARCHAR(255),
    opponent_id VARCHAR(255),
    opponent_name VARCHAR(255),
    map_name VARCHAR(100),
    won BOOLEAN,
    kills INT,
    deaths INT,
    assists INT,
    played_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

    -- Analysis results (Python writes, Java reads)
CREATE TABLE scouting_reports (
    id SERIAL PRIMARY KEY,
    report_request_id INT UNIQUE REFERENCES report_requests(id),
    team_id VARCHAR(255) NOT NULL,
    team_name VARCHAR(255),

    -- Overview stats
    total_matches INT,
    total_games INT,
    win_rate DECIMAL(5,2),
    current_streak INT,

    -- Detailed analysis (JSONB for flexibility)
    top_agents JSONB,           -- [{"agent": "Jett", "pick_rate": 0.80}]
    map_performance JSONB,       -- {"Ascent": {"wins": 4, "losses": 1}}
    player_stats JSONB,          -- [{"player": "TenZ", "kd": 1.45}]
    actionable_insights JSONB,   -- ["Ban Ascent", "Target TenZ early"]

    time_window VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_matches_team_id ON matches(team_id);
CREATE INDEX idx_matches_played_at ON matches(played_at DESC);
CREATE INDEX idx_report_requests_status ON report_requests(status);
CREATE INDEX idx_scouting_reports_team_id ON scouting_reports(team_id);