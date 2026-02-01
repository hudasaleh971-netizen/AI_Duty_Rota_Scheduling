-- ============================================================
-- SAMPLE DATA FOR TESTING
-- Run this in Supabase SQL Editor after creating the tables
-- ============================================================

-- Sample Unit: ICU Ward A with 4 nurses
INSERT INTO units (id, name, department, manager, min_nurses_per_shift, rules, staff, shift_codes)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  'ICU Ward A',
  'Intensive Care',
  'Dr. Sarah Ahmed',
  2,
  ' No back-to-back night shifts. Maximum 5 consecutive work days.',
  '[
    {"id": "s1", "name": "Fatima Hassan", "staffId": "N001", "position": "Level 2", "type": "Direct Care", "contractedHours": 160, "comments": "Senior nurse, can train others, currently Omar Khalid Prosepter"},
    {"id": "s2", "name": "Ahmed Ali", "staffId": "N002", "position": "Level 1", "type": "Direct Care", "contractedHours": 160, "comments": ""},
    {"id": "s3", "name": "Huda Mohammed", "staffId": "N003", "position": "Level 3", "type": "Direct Care", "contractedHours": 120, "comments": "Part-time, prefers morning shifts"},
    {"id": "s4", "name": "Omar Khalid", "staffId": "N004", "position": "Level 1", "type": "Direct Care", "contractedHours": 160, "comments": "New hire, still in training"}
  ]'::jsonb,
  '[
    {"code": "M", "definition": "Morning Shift", "description": "07:00-15:00", "hours": 8, "type": "Direct Care", "remarks": ""},
    {"code": "E", "definition": "Evening Shift", "description": "15:00-23:00", "hours": 8, "type": "Direct Care", "remarks": ""},
    {"code": "N", "definition": "Night Shift", "description": "23:00-07:00", "hours": 8, "type": "Direct Care", "remarks": "Night differential pay"},
    {"code": "DO", "definition": "Day Off", "description": "Scheduled day off", "hours": 0, "type": "-", "remarks": ""},
    {"code": "AL", "definition": "Annual Leave", "description": "Approved vacation", "hours": 8, "type": "-", "remarks": "Locked"},
    {"code": "SL", "definition": "Sick Leave", "description": "Medical absence", "hours": 8, "type": "-", "remarks": ""},
    {"code": "TR", "definition": "Training", "description": "Professional development", "hours": 8, "type": "Non-Direct Care", "remarks": ""}
  ]'::jsonb
)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  staff = EXCLUDED.staff,
  shift_codes = EXCLUDED.shift_codes,
  updated_at = NOW();

-- Sample Rota Config: February 2026
INSERT INTO rotas_config (id, unit_id, unit_name, start_date, end_date, staff_owing_hours, staff_target_hours, special_requests, comments)
VALUES (
  '22222222-2222-2222-2222-222222222222',
  '11111111-1111-1111-1111-111111111111',
  'ICU Ward A',
  '2026-02-01',
  '2026-02-28',
  '{"s1": -12, "s2": 0, "s3": 4, "s4": -8}'::jsonb,
  '{"s1": 148, "s2": 160, "s3": 124, "s4": 152}'::jsonb,
  '[
    {"staffId": "s1", "date": "2026-02-14", "shiftCode": "AL", "isLocked": true},
    {"staffId": "s1", "date": "2026-02-15", "shiftCode": "AL", "isLocked": true},
    {"staffId": "s3", "date": "2026-02-10", "shiftCode": "DO", "isLocked": true},
    {"staffId": "s2", "date": "2026-02-20", "shiftCode": "TR", "isLocked": true}
  ]'::jsonb,
  'February 2026 schedule. Note: Fatima on leave 14-15th for family event.'
)
ON CONFLICT (id) DO UPDATE SET
  staff_owing_hours = EXCLUDED.staff_owing_hours,
  staff_target_hours = EXCLUDED.staff_target_hours,
  special_requests = EXCLUDED.special_requests,
  updated_at = NOW();

-- Verification query
SELECT 
  r.id as rota_id,
  r.unit_name,
  r.start_date,
  r.end_date,
  jsonb_array_length(u.staff) as staff_count,
  jsonb_array_length(u.shift_codes) as shift_code_count,
  jsonb_array_length(r.special_requests) as locked_requests
FROM rotas_config r
JOIN units u ON r.unit_id = u.id
WHERE r.id = '22222222-2222-2222-2222-222222222222';
