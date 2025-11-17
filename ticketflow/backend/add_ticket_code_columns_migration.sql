-- Migration script to add ticket_code columns for formatted ticket identifiers
-- Run this SQL against your database to persist the new FL####V ticket codes.

ALTER TABLE tickets
ADD COLUMN IF NOT EXISTS ticket_code VARCHAR(20) UNIQUE;

ALTER TABLE admin_tickets
ADD COLUMN IF NOT EXISTS ticket_code VARCHAR(20) UNIQUE;

-- Backfill ticket_code for existing rows using their numeric IDs
UPDATE tickets
SET ticket_code = CONCAT('FL', LPAD(id::text, 4, '0'), 'V')
WHERE ticket_code IS NULL;

UPDATE admin_tickets
SET ticket_code = CONCAT('FL', LPAD(ticket_id::text, 4, '0'), 'V')
WHERE ticket_code IS NULL;


