ALTER TABLE report_requests
ADD COLUMN IF NOT EXISTS user_prompt TEXT NOT NULL DEFAULT '';

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_report_requests_status_created
ON report_requests(status, created_at ASC)
WHERE status = 'pending';

-- Update existing records (if any) with a default prompt
UPDATE report_requests
SET user_prompt = CONCAT('Generate scouting report for team ', team_id, ' in ', time_window)
WHERE user_prompt = '';