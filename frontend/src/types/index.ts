// ============================================================
// TYPE DEFINITIONS - CopilotKit-Ready State Schemas
// ============================================================

// Staff member in a unit
export type Staff = {
    id: string;
    name: string;
    staffId: string;
    position: 'Level 1' | 'Level 2' | 'Level 3';
    type: 'Direct Care' | 'Non-Direct Care';
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
    type: 'Direct Care' | 'Non-Direct Care' | '-';
    remarks: string;
};

// Unit information
export type UnitInfo = {
    name: string;
    department: string;
    manager: string;
    minNursesPerShift: number;
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
    position: 'Level 1',
    type: 'Direct Care',
    contractedHours: 160,
    comments: '',
});

// Helper type for creating new shift code
export const createEmptyShiftCode = (): ShiftCode => ({
    code: '',
    definition: '',
    description: '',
    hours: 8,
    type: 'Direct Care',
    remarks: '',
});

// Helper for creating new unit state
export const createEmptyUnitState = (): UnitState => ({
    id: crypto.randomUUID(),
    unitInfo: {
        name: '',
        department: '',
        manager: '',
        minNursesPerShift: 2,
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

// Summary statistics
export type ScheduleSummary = {
    totalShifts: number;
    assignedShifts: number;
    unassignedShifts: number;
    employeeHours: { [name: string]: number };
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
