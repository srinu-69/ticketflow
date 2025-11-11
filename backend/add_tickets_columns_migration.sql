-- Migration script to add tickets_issued and tickets_resolved columns to users_management table
-- Run this script on your existing database to add the new columns

-- Add tickets_issued column with default value 0
ALTER TABLE users_management 
ADD COLUMN IF NOT EXISTS tickets_issued INTEGER NOT NULL DEFAULT 0;

-- Add tickets_resolved column with default value 0
ALTER TABLE users_management 
ADD COLUMN IF NOT EXISTS tickets_resolved INTEGER NOT NULL DEFAULT 0;

-- Update existing records to have 0 for both columns (if needed)
UPDATE users_management 
SET tickets_issued = 0 
WHERE tickets_issued IS NULL;

UPDATE users_management 
SET tickets_resolved = 0 
WHERE tickets_resolved IS NULL;

-- Verify the columns were added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users_management' 
AND column_name IN ('tickets_issued', 'tickets_resolved');

