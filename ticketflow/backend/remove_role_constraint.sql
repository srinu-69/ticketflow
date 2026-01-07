-- Remove the CHECK constraint on user_profile.role to allow custom roles
-- This allows users to add any role they want in the admin panel

ALTER TABLE user_profile 
DROP CONSTRAINT IF EXISTS user_profile_role_check;

-- Optional: If you want to also remove department constraint
ALTER TABLE user_profile 
DROP CONSTRAINT IF EXISTS user_profile_department_check;

