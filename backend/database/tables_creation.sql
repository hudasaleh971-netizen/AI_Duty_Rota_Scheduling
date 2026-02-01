-- Units table (Exactly as you had it)
CREATE TABLE units (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  department TEXT,
  manager TEXT,
  min_nurses_per_shift INTEGER DEFAULT 2,
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
  comments TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);