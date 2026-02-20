// ============================================================
// TYPE DEFINITIONS - CopilotKit-Ready State Schemas
// ============================================================

// Staff member in a unit
export type Staff = {
    id: string;
    name: string;
    staffId: string;
    position: string;     // Free text field
    isDirectCare: boolean; // True = Direct Care, False = Non-Direct
    contractedHours: number;
    comments: string;
};

// Previous owing hours per staff member (specific to each rota)
export type StaffOwingHours = {
    [staffId: string]: number;
};

// Shift code definition
export type ShiftCode = {
    code: string;
    definition: string;
    description: string;
    hours: number;
    isDirectCare: boolean; // True = Direct Care, False = Non-Direct (e.g. Admin, Training)
    remarks: string;
};

// Unit information
export type UnitInfo = {
    name: string;
    manager: string;
    rules: string;
};

// Complete Unit State - Single Source of Truth
export type UnitState = {
    id: string;
    unitInfo: UnitInfo;
    staff: Staff[];
    shiftCodes: ShiftCode[];
    createdAt: string;
    updatedAt: string;
};

// Special request for a specific staff member on a specific date
export type SpecialRequest = {
    staffId: string;
    date: string;
    shiftCode: string;
    isLocked: boolean;
};

// Scheduling rule for the suggested rules section
export type SchedulingRule = {
    key: string;    // snake_case identifier, e.g. "min_rest_between_duties"
    name: string;   // display name for UI
    description: string;
    parameterLabel: string;
    parameterSuffix: string;
    defaultValue: string;
    currentValue: string;
    isActive: boolean;
    isLocked: boolean;
};

// Minimized rule format for Supabase persistence (only active rules are stored)
// Uses descriptive snake_case names so the agent can read them directly
export type SavedRule = {
    rule: string;   // e.g. "min_rest_between_duties"
    value: string;
    locked: boolean;
};

// Rota metadata
export type RotaMetadata = {
    unitId: string;
    unitName: string;
    startDate: string;
    endDate: string;
};

// Complete Rota State - Single Source of Truth
export type RotaState = {
    id: string;
    metadata: RotaMetadata;
    staffOwingHours: StaffOwingHours;  // INPUT: Balance from previous month
    staffTargetHours: StaffOwingHours; // OUTPUT: Calculated goal for this month
    specialRequests: SpecialRequest[];
    rules: SchedulingRule[];           // Full rules (in-memory, for UI)
    savedRules: SavedRule[];           // Minimized rules from DB (active only)
    comments: string;
    createdAt: string;
    updatedAt: string;
};

// Rota list item for dashboard display
export type RotaListItem = {
    id: string;
    unitName: string;
    startDate: string;
    endDate: string;
    lastModified: string;
};

// Helper type for creating new staff
export const createEmptyStaff = (): Staff => ({
    id: crypto.randomUUID(),
    name: '',
    staffId: '',
    position: 'Standard Nurse',
    isDirectCare: true,
    contractedHours: 160,
    comments: '',
});

// Helper type for creating new shift code
export const createEmptyShiftCode = (): ShiftCode => ({
    code: '',
    definition: '',
    description: '',
    hours: 8,
    isDirectCare: true,
    remarks: '',
});

// Helper for creating new unit state
export const createEmptyUnitState = (): UnitState => ({
    id: crypto.randomUUID(),
    unitInfo: {
        name: '',
        manager: '',
        rules: '',
    },
    staff: [],
    shiftCodes: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
});

// Helper for creating new rota state
export const createEmptyRotaState = (): RotaState => ({
    id: crypto.randomUUID(),
    metadata: {
        unitId: '',
        unitName: '',
        startDate: '',
        endDate: '',
    },
    staffOwingHours: {},
    staffTargetHours: {},
    specialRequests: [],
    rules: [],
    savedRules: [],
    comments: '',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
});

// ============================================================
// SCHEDULE RESULT TYPES - From Backend API
// ============================================================

// Single shift assignment from AI optimization
export type ScheduleAssignment = {
    date: string;
    employeeId: string | null;
    employeeName: string | null;
    shiftCode: string;
};

// Detailed hours structure
export type EmployeeHoursDetail = {
    total: number;
    target?: number;
    balance?: number;
};

// Summary statistics
export type ScheduleSummary = {
    totalShifts: number;
    assignedShifts: number;
    unassignedShifts: number;
    employeeHours: { [name: string]: number | EmployeeHoursDetail };
};

// Full schedule result from API
export type ScheduleResult = {
    status: 'success' | 'error';
    score?: string | null;
    schedule?: ScheduleAssignment[];
    summary?: ScheduleSummary;
    error?: string;
    details?: string;
    raw_output?: string;
};
