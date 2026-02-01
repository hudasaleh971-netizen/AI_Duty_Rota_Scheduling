# AI Duty Rota Scheduling

An intelligent nurse scheduling system that uses AI (CrewAI + Vertex AI) to generate optimized shift rosters for healthcare units.

## Overview

This system helps hospital managers create fair, balanced nurse schedules by:
- **Frontend**: React app for creating units, managing staff, and setting up rotas
- **Backend**: CrewAI agent that analyzes scheduling data and generates Timefold-compatible optimization input

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  Create Unit → Add Staff → Create Rota → Pre-fill Requests     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SUPABASE (Database)                        │
│  units table → rotas_config table                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND (CrewAI + Vertex AI)                       │
│  Fetch Data → Expert Nurse Scheduler Agent → Timefold JSON     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Timefold Optimizer (TODO)
```

---

## Project Structure

```
AI_Duty_Rota_Scheduling/
├── frontend/                    # React + TypeScript
│   ├── src/
│   │   ├── pages/              # Dashboard, CreateUnit, CreateRota
│   │   ├── components/         # Sidebar, UI components
│   │   ├── services/           # Supabase integration
│   │   └── types/              # TypeScript types
│   └── package.json
│
├── backend/                     # Python + CrewAI
│   ├── src/
│   │   ├── crew.py             # Expert scheduling agent
│   │   ├── main.py             # Entry point
│   │   └── tools/
│   │       └── supabase_tool.py # Fetches data from Supabase
│   ├── database/
│   │   ├── tables_creation.sql # Database schema
│   │   └── sample_data.sql     # Test data
│   ├── requirements.txt
│   └── .env                    # Credentials
│
└── .gitignore
```

---

## Quick Start

### 1. Database Setup (Supabase)

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run `backend/database/tables_creation.sql` in Supabase SQL Editor
3. Run `backend/database/sample_data.sql` for test data

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env  # Add your Supabase URL and key
npm run dev
```

Open http://localhost:5173

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your credentials

# Authenticate with Google Cloud
gcloud auth application-default login

# Run the scheduling agent
python -m src.main --rota-id "22222222-2222-2222-2222-222222222222"
```

---

## Configuration

### Frontend `.env`

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### Backend `.env`

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Vertex AI (Google Cloud)
VERTEX_PROJECT=your-gcp-project-id
VERTEX_LOCATION=us-central1
```

---

## Features

### Frontend

| Page | Description |
|------|-------------|
| **Dashboard** | View all units and rotas |
| **Create Unit** | Add hospital unit with staff and shift codes |
| **Create Rota** | Set scheduling period and pre-fill requests |

**Pre-Schedule Grid Features:**
- Fill shift requests (M, E, N, AL, SL, TR, DO)
- 🔒 Lock/Unlock requests (locked = hard constraint)
- Set staff target hours (contracted + owing)

### Backend (CrewAI Agent)

The scheduling expert agent:

1. **Fetches data** from Supabase (unit, staff, shift codes, requests)
2. **Analyzes deeply**:
   - Understands shift codes (M/E/N = work, AL/SL/TR = unavailable)
   - Detects implicit requirements from comments (mentorship, preferences)
   - Calculates target hours (contracted + owing)
3. **Generates Timefold JSON** with:
   - Employees (skills, availability, unavailability)
   - Shifts (ISO 8601 format for each M/E/N in date range)
   - Hard constraints (no overlaps, locked requests)
   - Soft constraints (balance hours, detected pairings)

---

## Shift Codes

| Code | Type | Hours | Description |
|------|------|-------|-------------|
| M | Work | 8 | Morning (07:00-15:00) |
| E | Work | 8 | Evening (15:00-23:00) |
| N | Work | 8 | Night (23:00-07:00) |
| DO | Off | 0 | Day Off |
| AL | Off | 8 | Annual Leave (counts toward hours) |
| SL | Off | 8 | Sick Leave (counts toward hours) |
| TR | Non-care | 8 | Training (counts toward hours) |

---

## Database Schema

### `units` table
- Staff array (id, name, position, contractedHours, comments)
- Shift codes array
- Rules (e.g., "no back-to-back night shifts")

### `rotas_config` table
- Scheduling period (start_date, end_date)
- Special requests (pre-filled shifts with isLocked flag)
- Staff target hours and owing hours

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite |
| Backend | Python 3.11+, CrewAI |
| LLM | Vertex AI (Gemini 2.0 Flash) |
| Database | Supabase (PostgreSQL) |
| Optimizer | Timefold (planned) |

---

## License

MIT
