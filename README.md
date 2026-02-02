# AI Duty Rota Scheduling

An intelligent nurse scheduling system powered by a **3-Agent CrewAI Pipeline** with Vertex AI that generates optimized shift rosters using Timefold constraint optimization.

## 🎯 Overview

This system helps hospital managers create fair, balanced nurse schedules by:

- **Frontend**: React app for creating units, managing staff, pre-scheduling constraints, and viewing optimized schedules
- **Backend**: 3-Agent CrewAI pipeline that fetches data, generates Timefold Python code, and executes the solver
- **Optimization**: Timefold constraint solver for shift assignment with hard/soft constraints

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React + TypeScript)                   │
│   Dashboard → Create Unit → Create Rota → Pre-Schedule → View Schedule  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SUPABASE (PostgreSQL)                            │
│              units table ←→ rotas_config table                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI + CrewAI)                        │
│                                                                          │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│   │   AGENT 1    │───▶│   AGENT 2    │───▶│   AGENT 3    │              │
│   │Data Fetcher  │    │Code Generator│    │  Executor    │              │
│   │  Supabase→   │    │  →Timefold   │    │  →Schedule   │              │
│   │    JSON      │    │   Python     │    │    JSON      │              │
│   └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                      📅 Optimized Schedule Display
```

---

## 🤖 3-Agent Pipeline Architecture

### Agent 1: Data Interpreter
**Role**: Senior Nurse Scheduling Expert & Data Analyst

**Responsibilities**:
- Fetches scheduling data from Supabase (unit, staff, shift codes, rota config)
- Interprets shift codes (M/E/N = work, AL/SL/TR = paid absence, DO = day off)
- Calculates target hours: `targetHours = contractedHours + owingHours - paidAbsenceHours`
- Detects implicit requirements from comments (mentorship, preferences)
- Outputs standardized Timefold JSON specification

**Tools**: `FetchRotaDataTool` (Supabase integration)

### Agent 2: Code Generator
**Role**: Timefold Constraint Optimization Developer

**Responsibilities**:
- Reads Timefold skill documentation and examples
- Generates custom Python code based on JSON specification:
  - `domain.py` - Employee, Shift, ShiftSchedule classes
  - `constraints.py` - Hard/soft constraints from spec
  - `solver.py` - Solver configuration
  - `input_data.json` - Formatted input for solver

**Tools**: `FileReadTool`, `FileWriterTool`

### Agent 3: Executor
**Role**: Timefold Code Execution Specialist

**Responsibilities**:
- Reads generated Python files
- Executes the Timefold solver
- Formats output for frontend UI
- Handles errors gracefully

**Output Format**:
```json
{
  "status": "success",
  "score": "0hard/-5soft",
  "schedule": [
    {"date": "2026-02-01", "employeeId": "s1", "employeeName": "Fatima", "shiftCode": "M"},
    ...
  ],
  "summary": {
    "totalShifts": 63,
    "assignedShifts": 63,
    "employeeHours": {"Fatima Hassan": 144, "Ahmed Ali": 160}
  }
}
```

---

## 📁 Project Structure

```
AI_Duty_Rota_Scheduling/
├── frontend/                        # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx       # View all rotas, quick actions
│   │   │   ├── CreateUnit.tsx      # Add hospital unit with staff
│   │   │   ├── CreateRota.tsx      # Set schedule period, pre-fill requests
│   │   │   └── ViewSchedule.tsx    # Display optimized schedule grid
│   │   ├── components/             # UI components (Button, Sidebar, etc.)
│   │   ├── services/
│   │   │   ├── unitService.ts      # Supabase unit operations
│   │   │   ├── rotaService.ts      # Supabase rota operations
│   │   │   └── scheduleService.ts  # Backend API integration
│   │   ├── types/                  # TypeScript types
│   │   └── App.tsx                 # Routes configuration
│   └── package.json
│
├── backend/                         # Python + CrewAI + FastAPI
│   ├── src/
│   │   ├── crew.py                 # 3-Agent pipeline definition
│   │   ├── api.py                  # FastAPI endpoints
│   │   ├── main.py                 # CLI entry point
│   │   ├── config.py               # Environment configuration
│   │   ├── supabase_client.py      # Supabase client singleton
│   │   ├── agents/
│   │   │   ├── data_fetcher.py     # Agent 1 logic
│   │   │   └── timefold_transformer.py  # Agent 2 logic
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic models
│   │   └── tools/
│   │       └── supabase_tool.py    # Supabase fetch tool
│   ├── generated/                  # Generated Timefold code (gitignored)
│   │   ├── domain.py
│   │   ├── constraints.py
│   │   ├── solver.py
│   │   └── input_data.json
│   ├── database/
│   │   ├── tables_creation.sql     # Database schema
│   │   └── sample_data.sql         # Test data
│   ├── requirements.txt
│   └── .env
│
└── .gitignore
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Google Cloud account with Vertex AI enabled
- Supabase account

### 1. Database Setup (Supabase)

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run `backend/database/tables_creation.sql` in Supabase SQL Editor
3. (Optional) Run `backend/database/sample_data.sql` for test data

### 2. Frontend Setup

```bash
cd frontend
npm install

# Copy and configure environment
cp .env.example .env
# Edit .env with your Supabase URL and anon key

npm run dev
```

Frontend runs at: **http://localhost:5173**

### 3. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Authenticate with Google Cloud
gcloud auth application-default login

# Start the API server
python -m uvicorn src.api:app --host 0.0.0.0 --port 5000
```

Backend API runs at: **http://localhost:5000**

### 4. Run the Full Flow

1. **Create a Unit**: Go to Dashboard → Create New Unit → Add staff and shift codes
2. **Create a Rota**: Go to Dashboard → Create New Rota → Select unit, dates, pre-fill constraints
3. **Save & Schedule**: Click "Save & Continue to Scheduling"
4. **Generate**: On schedule page, click "🚀 Generate Optimized Schedule"
5. **View Results**: See full schedule grid with hours summary

---

## ⚙️ Configuration

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
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True

# Langfuse Tracing (optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

---

## 🎨 Frontend Features

| Page | Description |
|------|-------------|
| **Dashboard** | View all rotas, quick access to create unit/rota, view schedule buttons |
| **Create Unit** | Add hospital unit with staff members and shift code definitions |
| **Create Rota** | Set scheduling period, pre-fill known constraints (AL, TR, DO) |
| **View Schedule** | Full month grid with color-coded shifts, hours summary per staff |

### Pre-Schedule Grid Features
- Enter shift codes (M, E, N, AL, SL, TR, DO)
- 🔒 Lock/Unlock requests (locked = hard constraint for solver)
- Set previous owing hours per staff member
- Auto-calculate target hours (contracted + owing)

### Schedule View Features
- Color-coded shift cells:
  - 🟢 Morning (M) - teal
  - 🟠 Evening (E) - orange
  - 🔵 Night (N) - purple
  - 🟢 Leave (AL) - green
  - 🔴 Sick (SL) - red
  - 🟣 Training (TR) - purple
  - ⚪ Off (DO) - gray
- Hours summary per staff member
- Shift code legend reference

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and available endpoints |
| GET | `/api/health` | Health check |
| POST | `/api/schedule/{rota_id}` | Generate optimized schedule for rota |

### Example API Call
```bash
curl -X POST http://localhost:5000/api/schedule/22222222-2222-2222-2222-222222222222
```

---

## 🔤 Shift Codes

| Code | Type | Hours | Description |
|------|------|-------|-------------|
| M | Work | 8 | Morning (07:00-15:00) |
| E | Work | 8 | Evening (15:00-23:00) |
| N | Work | 8 | Night (23:00-07:00) |
| DO | Off | 0 | Day Off (unpaid) |
| O | Off | 0 | Off (unpaid) |
| PH | Off | 8 | Public Holiday |
| AL | Paid Absence | 8 | Annual Leave |
| SL | Paid Absence | 8 | Sick Leave |
| TR | Non-care | 8 | Training |

---

## 🗄️ Database Schema

### `units` table
- Unit info (name, department, manager, rules)
- Staff array (id, name, position, contractedHours, comments)
- Shift codes array (code, definition, hours, type)

### `rotas_config` table
- Scheduling period (start_date, end_date)
- Special requests (pre-filled shifts with isLocked flag)
- Staff owing hours and target hours

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite |
| Backend Framework | FastAPI, Uvicorn |
| AI Orchestration | CrewAI 0.86+ |
| LLM | Vertex AI (Gemini 2.5 Flash) |
| Observability | Langfuse (optional) |
| Database | Supabase (PostgreSQL) |
| Optimizer | Timefold |

---

## 🔍 Observability with Langfuse

The backend integrates with Langfuse for tracing agent execution:

1. Create account at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Add keys to backend `.env`
3. View traces of all agent runs, tool calls, and LLM interactions

---

## 📄 License

MIT
