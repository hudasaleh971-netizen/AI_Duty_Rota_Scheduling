-- Remove obsolete columns from the units table to match the refined data model
-- Run this in your Supabase SQL Editor

ALTER TABLE units 
  DROP COLUMN IF EXISTS department,
  DROP COLUMN IF EXISTS min_nurses_per_shift;
