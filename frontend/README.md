# Frontend - Nurse Scheduling UI

React + TypeScript frontend for the AI Duty Rota Scheduling system.

## 🎨 Features

### Pages

| Page | Route | Description |
|------|-------|-------------|
| **Dashboard** | `/` | View all rotas, quick actions, stats |
| **Create Unit** | `/create-unit` | Add hospital unit with staff and shift codes |
| **Create Rota** | `/create-rota` | Set scheduling period, pre-fill constraints |
| **Edit Rota** | `/edit-rota/:id` | Edit existing rota configuration |
| **View Schedule** | `/schedule/:rotaId` | Display optimized schedule grid |

### Pre-Schedule Grid
- Enter known shift codes (M, E, N, AL, SL, TR, DO)
- 🔒 Lock/unlock assignments (locked = hard constraint)
- Set previous owing hours per staff
- Auto-calculate target hours

### Schedule View
- Full month grid with all staff
- Color-coded shift cells:
  - 🟢 Morning (M) - teal
  - 🟠 Evening (E) - orange
  - 🔵 Night (N) - purple
  - 🟢 Leave (AL) - green
  - ⚪ Off (DO) - gray
- Hours summary per staff
- "Generate Schedule" button to run AI

---

## 📁 Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx        # Main dashboard
│   │   ├── CreateUnit.tsx       # Unit creation
│   │   ├── CreateRota.tsx       # Rota configuration
│   │   └── ViewSchedule.tsx     # Schedule display
│   ├── components/
│   │   ├── Layout.tsx           # Main layout with sidebar
│   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   └── ui/                  # Reusable UI components
│   │       ├── Button.tsx
│   │       ├── Select.tsx
│   │       └── TextArea.tsx
│   ├── services/
│   │   ├── unitService.ts       # Supabase unit CRUD
│   │   ├── rotaService.ts       # Supabase rota CRUD
│   │   └── scheduleService.ts   # Backend API calls
│   ├── types/
│   │   └── index.ts             # All TypeScript types
│   ├── lib/
│   │   └── supabaseClient.ts    # Supabase initialization
│   ├── App.tsx                  # Routes
│   └── index.css                # Global styles
├── .env
└── package.json
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Run Development Server

```bash
npm run dev
```

Open: http://localhost:5173

---

## 🔄 User Flow

```
1. Dashboard
     │
     ├──▶ Create New Unit
     │       └── Add staff, shift codes
     │       └── Save to Supabase
     │
     ├──▶ Create New Rota
     │       └── Select unit, date range
     │       └── Pre-fill constraints (AL, TR, DO)
     │       └── Lock important assignments
     │       └── Save & Continue to Scheduling
     │            │
     │            ▼
     │       View Schedule Page
     │            └── Click "Generate Schedule"
     │            └── Wait for AI (1-2 min)
     │            └── View full schedule grid
     │
     └──▶ View Existing Rota Schedule
             └── Dashboard → "View Schedule" button
```

---

## 📊 Services

### `scheduleService.ts`

Calls the backend API to generate schedules:

```typescript
import { scheduleService } from './services/scheduleService';

// Generate schedule
const result = await scheduleService.generateSchedule(rotaId);

if (result.status === 'success') {
  console.log('Schedule:', result.schedule);
  console.log('Hours:', result.summary.employeeHours);
}
```

### `rotaService.ts`

Supabase CRUD for rotas:

```typescript
import { rotaService } from './services/rotaService';

// Get all rotas
const rotas = await rotaService.getRotaListItems();

// Get single rota
const rota = await rotaService.getRotaById(id);

// Save rota
await rotaService.saveRota(rotaState);
```

### `unitService.ts`

Supabase CRUD for units:

```typescript
import { unitService } from './services/unitService';

// Get all units
const units = await unitService.getUnits();

// Save unit
await unitService.saveUnit(unitState);
```

---

## 🎨 Styling

Uses custom CSS variables with a modern design:

- Dark navy sidebar
- Light gray backgrounds
- Teal accent color (#14b8a6)
- Coral secondary color (#f97066)
- Smooth animations and transitions

---

## 📦 Dependencies

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.21.0",
  "@supabase/supabase-js": "^2.39.0",
  "typescript": "^5.3.0",
  "vite": "^5.0.0"
}
```

---

## 🔧 Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

---

## 📄 License

MIT
