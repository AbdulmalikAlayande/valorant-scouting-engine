-- ============================================================================
-- TEAMS LOOKUP TABLE
-- ============================================================================
-- Central repository for all team data from GRID API
-- Other tables reference this via foreign keys for data consistency

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    team_id VARCHAR(255) UNIQUE NOT NULL,  -- GRID API team ID
    team_name VARCHAR(255) NOT NULL,
    name_shortened VARCHAR(100),
    logo_url VARCHAR(500),
    color_primary VARCHAR(7),
    color_secondary VARCHAR(7),
    organization_name VARCHAR(255),
    rating FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- AUTO-UPDATE TIMESTAMP TRIGGER
-- ============================================================================
-- Automatically updates updated_at column when any row is modified

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER FUNCTION: GET OR CREATE TEAM FK
-- ============================================================================
-- Looks up team by GRID ID, creates if missing, returns FK
-- This makes inserts into other tables easier

CREATE OR REPLACE FUNCTION get_or_create_team_fk(
    p_team_id VARCHAR,
    p_team_name VARCHAR DEFAULT NULL
) RETURNS INT AS $$
DECLARE
    v_fk_id INT;
BEGIN
    -- Try to find an existing team
    SELECT id INTO v_fk_id FROM teams WHERE team_id = p_team_id;

    -- If not found and name provided, create it
    IF v_fk_id IS NULL AND p_team_name IS NOT NULL THEN
        INSERT INTO teams (team_id, team_name)
        VALUES (p_team_id, p_team_name)
        RETURNING id INTO v_fk_id;
    END IF;

    RETURN v_fk_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ADD FOREIGN KEYS TO EXISTING TABLES
-- ============================================================================
-- Connect existing tables to the new teams table

-- Report requests
ALTER TABLE report_requests
    ADD COLUMN IF NOT EXISTS team_fk_id INT REFERENCES teams(id) ON DELETE CASCADE;

-- Matches (team and opponent both reference teams table)
ALTER TABLE matches
    ADD COLUMN IF NOT EXISTS team_fk_id INT REFERENCES teams(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS opponent_fk_id INT REFERENCES teams(id) ON DELETE SET NULL;

-- Scouting reports
ALTER TABLE scouting_reports
    ADD COLUMN IF NOT EXISTS team_fk_id INT REFERENCES teams(id) ON DELETE CASCADE;

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Team table indexes
CREATE INDEX IF NOT EXISTS idx_teams_team_id ON teams(team_id);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(team_name);
CREATE INDEX IF NOT EXISTS idx_teams_organization ON teams(organization_name);

-- Foreign key indexes (improves JOIN performance)
CREATE INDEX IF NOT EXISTS idx_report_requests_team_fk ON report_requests(team_fk_id);
CREATE INDEX IF NOT EXISTS idx_matches_team_fk ON matches(team_fk_id);
CREATE INDEX IF NOT EXISTS idx_matches_opponent_fk ON matches(opponent_fk_id);
CREATE INDEX IF NOT EXISTS idx_scouting_reports_team_fk ON scouting_reports(team_fk_id);

-- ============================================================================
-- CONVENIENCE VIEW: TEAM SUMMARY
-- ============================================================================
-- Aggregated view for quick team stats lookup (used by Java API)

CREATE OR REPLACE VIEW team_summary AS
SELECT
    t.id,
    t.team_id,
    t.team_name,
    t.name_shortened,
    t.logo_url,
    t.color_primary,
    t.organization_name,
    t.rating,
    COUNT(DISTINCT m.id) as total_matches,
    COUNT(DISTINCT sr.id) as total_reports,
    MAX(m.played_at) as last_match_date,
    t.created_at,
    t.updated_at
FROM teams t
LEFT JOIN matches m ON t.id = m.team_fk_id
LEFT JOIN scouting_reports sr ON t.id = sr.team_fk_id
GROUP BY t.id;

-- ============================================================================
-- DOCUMENTATION COMMENTS
-- ============================================================================

COMMENT ON TABLE teams IS 'Central team lookup table synchronized with GRID API';
COMMENT ON COLUMN teams.team_id IS 'GRID API team ID (external reference, immutable)';
COMMENT ON COLUMN teams.team_name IS 'Official team name from GRID';
COMMENT ON COLUMN teams.name_shortened IS 'Abbreviated team name (e.g., TL, C9)';
COMMENT ON COLUMN teams.rating IS 'GRID team rating (updated periodically)';
COMMENT ON TRIGGER update_teams_updated_at ON teams IS 'Auto-updates timestamp on modification';
COMMENT ON FUNCTION get_or_create_team_fk IS 'Helper to insert/lookup team FK for other tables';
COMMENT ON VIEW team_summary IS 'Aggregated team data with match/report counts for API queries';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002 completed: teams table, foreign keys, and helpers added';
END $$;