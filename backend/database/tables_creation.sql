-- Units table (Exactly as you had it)
CREATE TABLE units (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  name TEXT NOT NULL,
  manager TEXT,
  rules TEXT,
  staff JSONB DEFAULT '[]'::jsonb,
  shift_codes JSONB DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rotas table (Added 'staff_target_hours' only)
CREATE TABLE rotas_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  unit_id UUID REFERENCES units(id) ON DELETE CASCADE,
  unit_name TEXT,
  start_date DATE,
  end_date DATE,
  
  -- INPUT: The balance from the previous month (e.g. {"n1": -12})
  staff_owing_hours JSONB DEFAULT '{}'::jsonb,
  
  -- OUTPUT: The calculated goal for THIS month (e.g. {"n1": 164})
  staff_target_hours JSONB DEFAULT '{}'::jsonb,  -- <--- NEW COLUMN
  
  special_requests JSONB DEFAULT '[]'::jsonb,
  
  -- Active scheduling rules with user-configured values (e.g. [{"id":"R1","value":"12","locked":true}])
  rules JSONB DEFAULT '[]'::jsonb,
  
  comments TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Schedule Assignments table (NEW)
CREATE TABLE schedule_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rota_id UUID REFERENCES rotas_config(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  employee_id TEXT NOT NULL,
  shift_code TEXT NOT NULL,
  
  -- Optional: Store cached employee data to avoid joins if staff JSON changes
  employee_name TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Ensure unique assignment per person per day
  UNIQUE(rota_id, date, employee_id)
);