# Backend - 3-Agent CrewAI Pipeline

AI-powered nurse scheduling backend using CrewAI with 3 specialized agents and Timefold constraint optimization.

## 🤖 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Server (Port 5000)                   │
│  POST /api/schedule/{rota_id} → Runs 3-Agent Pipeline               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   AGENT 1   │───▶│   AGENT 2   │───▶│   AGENT 3   │
│ Data Fetch  │    │ Code Gen    │    │  Executor   │
│  Supabase   │    │  Timefold   │    │   Solver    │
│    → JSON   │    │  → Python   │    │  → Result   │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## 📁 Structure

```
backend/
├── src/
│   ├── crew.py              # 3-Agent pipeline (main)
│   ├── api.py               # FastAPI endpoints
│   ├── main.py              # CLI entry point
│   ├── config.py            # Environment config
│   ├── supabase_client.py   # Supabase singleton
│   ├── agents/
│   │   ├── data_fetcher.py  # Agent 1 helper
│   │   └── timefold_transformer.py  # Agent 2 helper
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── tools/
│       └── supabase_tool.py # FetchRotaDataTool
├── generated/               # Agent 2 output (gitignored)
│   ├── domain.py
│   ├── constraints.py
│   ├── solver.py
│   └── input_data.json
├── database/
│   ├── tables_creation.sql
│   └── sample_data.sql
├── requirements.txt
└── .env
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Vertex AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True

# Langfuse (optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

### 3. Authenticate with Google Cloud

```bash
gcloud auth application-default login
```

### 4. Run the API Server

```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 5000
```

API available at: http://localhost:5000

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/api/health` | Health check |
| POST | `/api/schedule/{rota_id}` | Generate schedule |

### Example Request

```bash
curl -X POST http://localhost:5000/api/schedule/22222222-2222-2222-2222-222222222222
```

### Example Response

```json
{
  "status": "success",
  "score": "0hard/-5soft",
  "schedule": [
    {"date": "2026-02-01", "employeeId": "s1", "employeeName": "Fatima Hassan", "shiftCode": "M"},
    {"date": "2026-02-01", "employeeId": "s2", "employeeName": "Ahmed Ali", "shiftCode": "E"}
  ],
  "summary": {
    "totalShifts": 84,
    "assignedShifts": 84,
    "unassignedShifts": 0,
    "employeeHours": {
      "Fatima Hassan": 144,
      "Ahmed Ali": 160,
      "Huda Mohammed": 120,
      "Omar Khalid": 160
    }
  }
}
```

---

## 🖥️ CLI Usage

Run the scheduling pipeline from command line:

```bash
python -m src.main --rota-id "22222222-2222-2222-2222-222222222222"
```

With output file:

```bash
python -m src.main --rota-id "22222222-2222-2222-2222-222222222222" --output schedule.json
```

---

## 🤖 Agent Details

### Agent 1: Data Interpreter

**Goal**: Fetch and analyze scheduling data from Supabase

**Expertise**:
- Shift code interpretation (M/E/N = work, AL/SL = paid absence, DO = day off)
- Hours calculation: `targetHours = contractedHours + owingHours - paidAbsenceHours`
- Implicit requirement detection (mentorship from comments)
- Rest period rules (10h between shifts, max 3 consecutive nights)

**Output**: Timefold JSON specification

---

### Agent 2: Code Generator

**Goal**: Generate Timefold Python code from JSON spec

**Files Generated**:
1. `domain.py` - Employee, Shift, ShiftSchedule classes
2. `constraints.py` - Hard/soft constraints
3. `solver.py` - Solver configuration
4. `input_data.json` - Input for solver

**Tools**: FileReadTool, FileWriterTool

---

### Agent 3: Executor

**Goal**: Execute solver and format output

**Output**: JSON for frontend with schedule array and summary

---

## 📦 Dependencies

```
crewai>=0.86.0
crewai-tools>=0.17.0
google-cloud-aiplatform>=1.38.0
supabase>=2.0.0
fastapi>=0.109.0
uvicorn>=0.27.0
timefold>=1.0.0
langfuse>=2.0.0
openinference-instrumentation-crewai>=0.1.0
python-dotenv>=1.0.0
litellm>=1.1.0
pydantic>=2.5.0
```

---

## 🔍 Debugging with Langfuse

View full agent execution traces at [cloud.langfuse.com](https://cloud.langfuse.com):

- Every agent step
- LLM calls and responses
- Tool invocations
- Token usage

---

## 📄 License

MIT
