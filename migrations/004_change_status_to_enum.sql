-- migrations/004_change_status_to_enum.sql

-- 1. Create the ENUM type
CREATE TYPE report_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

-- 2. Alter the table to use the ENUM
-- We need to map existing lowercase values to uppercase before changing the type
ALTER TABLE report_requests 
    ALTER COLUMN status TYPE report_status 
    USING (UPPER(status)::report_status);

-- 3. Set default to 'PENDING'
ALTER TABLE report_requests 
    ALTER COLUMN status SET DEFAULT 'PENDING';
