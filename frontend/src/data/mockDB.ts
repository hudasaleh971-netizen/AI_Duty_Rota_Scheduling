// ============================================================
// MOCK DATABASE - Sample data for development
// ============================================================

import type { UnitState, RotaState, RotaListItem } from '../types';

// Default shift codes used in healthcare
export const defaultShiftCodes = [
    { code: 'M', definition: 'Morning', description: 'Day shift 7:00 AM - 3:00 PM', hours: 8, type: 'Direct Care' as const, remarks: 'Standard day shift' },
    { code: 'E', definition: 'Evening', description: 'Afternoon shift 3:00 PM - 11:00 PM', hours: 8, type: 'Direct Care' as const, remarks: 'Standard evening shift' },
    { code: 'N', definition: 'Night', description: 'Night shift 7:00 PM - 7:00 AM', hours: 12, type: 'Direct Care' as const, remarks: 'Extended night coverage' },
    { code: 'DO', definition: 'Day Off', description: 'Rest day', hours: 0, type: '-' as const, remarks: 'Mandatory after 6 working days' },
    { code: 'AL', definition: 'Annual Leave', description: 'Approved leave', hours: 0, type: '-' as const, remarks: 'Planned time off' },
    { code: 'SL', definition: 'Sick Leave', description: 'Medical leave', hours: 0, type: '-' as const, remarks: 'Unplanned absence' },
    { code: 'CL', definition: 'Compensatory Leave', description: 'Time-off in lieu', hours: 0, type: '-' as const, remarks: 'For extra hours worked' },
    { code: 'TR', definition: 'Training', description: 'Development day', hours: 0, type: 'Non-Direct Care' as const, remarks: 'Courses, certifications' },
    { code: 'AD', definition: 'Administrative', description: 'Meetings, documentation', hours: 8, type: 'Non-Direct Care' as const, remarks: 'Non-clinical duties' },
];

// Sample units
export const mockUnits: UnitState[] = [
    {
        id: 'unit-001',
        unitInfo: {
            name: 'ICU - Floor 3',
            department: 'Critical Care',
            manager: 'Dr. Sarah Ahmed',
            minNursesPerShift: 4,
            rules: 'At least 2 Level 3 nurses per shift. Maximum 3 consecutive night shifts.',
        },
        staff: [
            { id: 'staff-001', name: 'Sarah Ahmed, RN', staffId: 'N12345', position: 'Level 3', type: 'Direct Care', contractedHours: 160, comments: 'Unit manager, preceptor' },
            { id: 'staff-002', name: 'James Wilson, RN', staffId: 'N12346', position: 'Level 2', type: 'Direct Care', contractedHours: 160, comments: '' },
            { id: 'staff-003', name: 'Maria Santos, RN', staffId: 'N12347', position: 'Level 2', type: 'Direct Care', contractedHours: 120, comments: 'Part-time' },
            { id: 'staff-004', name: 'Ahmed Hassan, RN', staffId: 'N12348', position: 'Level 1', type: 'Direct Care', contractedHours: 160, comments: 'New graduate' },
            { id: 'staff-005', name: 'Emily Chen, RN', staffId: 'N12349', position: 'Level 3', type: 'Direct Care', contractedHours: 160, comments: 'CCRN certified' },
            { id: 'staff-006', name: 'David Brown, NA', staffId: 'N12350', position: 'Level 1', type: 'Non-Direct Care', contractedHours: 160, comments: 'Nursing assistant' },
        ],
        shiftCodes: defaultShiftCodes,
        createdAt: '2026-01-15T08:00:00Z',
        updatedAt: '2026-01-28T14:30:00Z',
    },
    {
        id: 'unit-002',
        unitInfo: {
            name: 'Emergency Department',
            department: 'Emergency Medicine',
            manager: 'Dr. Michael Torres',
            minNursesPerShift: 6,
            rules: 'Trauma-certified nurse required at all times. Float pool staff welcome.',
        },
        staff: [
            { id: 'staff-010', name: 'Lisa Park, RN', staffId: 'N22001', position: 'Level 3', type: 'Direct Care', contractedHours: 160, comments: 'Trauma certified' },
            { id: 'staff-011', name: 'Robert Kim, RN', staffId: 'N22002', position: 'Level 2', type: 'Direct Care', contractedHours: 160, comments: '' },
            { id: 'staff-012', name: 'Anna Volkov, RN', staffId: 'N22003', position: 'Level 2', type: 'Direct Care', contractedHours: 160, comments: '' },
            { id: 'staff-013', name: 'Carlos Rivera, RN', staffId: 'N22004', position: 'Level 1', type: 'Direct Care', contractedHours: 160, comments: '' },
        ],
        shiftCodes: defaultShiftCodes,
        createdAt: '2026-01-10T09:00:00Z',
        updatedAt: '2026-01-25T16:45:00Z',
    },
    {
        id: 'unit-003',
        unitInfo: {
            name: 'Cardiac Care Unit',
            department: 'Cardiology',
            manager: 'Dr. Jennifer Lee',
            minNursesPerShift: 3,
            rules: 'ACLS certification required for all staff.',
        },
        staff: [
            { id: 'staff-020', name: 'Thomas Wright, RN', staffId: 'N33001', position: 'Level 3', type: 'Direct Care', contractedHours: 160, comments: 'ACLS instructor' },
            { id: 'staff-021', name: 'Rachel Green, RN', staffId: 'N33002', position: 'Level 2', type: 'Direct Care', contractedHours: 160, comments: '' },
            { id: 'staff-022', name: 'Kevin Patel, RN', staffId: 'N33003', position: 'Level 1', type: 'Direct Care', contractedHours: 160, comments: '' },
        ],
        shiftCodes: defaultShiftCodes,
        createdAt: '2026-01-20T10:00:00Z',
        updatedAt: '2026-01-30T11:20:00Z',
    },
];

// Sample rotas
export const mockRotas: RotaState[] = [
    {
        id: 'rota-001',
        metadata: {
            unitId: 'unit-001',
            unitName: 'ICU - Floor 3',
            startDate: '2026-02-01',
            endDate: '2026-02-28',
        },
        specialRequests: [
            { staffId: 'staff-002', date: '2026-02-14', shiftCode: 'AL', isLocked: true },
            { staffId: 'staff-003', date: '2026-02-10', shiftCode: 'TR', isLocked: false },
        ],
        comments: "February schedule with Valentine's Day coverage considerations.",
        createdAt: '2026-01-28T09:00:00Z',
        updatedAt: '2026-01-30T15:30:00Z',
    },
    {
        id: 'rota-002',
        metadata: {
            unitId: 'unit-002',
            unitName: 'Emergency Department',
            startDate: '2026-02-01',
            endDate: '2026-02-28',
        },
        specialRequests: [],
        comments: 'Standard February rotation.',
        createdAt: '2026-01-25T11:00:00Z',
        updatedAt: '2026-01-29T10:00:00Z',
    },
];

// Get rota list items for dashboard
export const getRotaListItems = (): RotaListItem[] => {
    return mockRotas.map((rota) => ({
        id: rota.id,
        unitName: rota.metadata.unitName,
        startDate: rota.metadata.startDate,
        endDate: rota.metadata.endDate,
        lastModified: rota.updatedAt,
    }));
};

// Get all units (for dropdown selection)
export const getUnits = (): UnitState[] => {
    return mockUnits;
};

// Get unit by ID
export const getUnitById = (id: string): UnitState | undefined => {
    return mockUnits.find((unit) => unit.id === id);
};

// Get rota by ID
export const getRotaById = (id: string): RotaState | undefined => {
    return mockRotas.find((rota) => rota.id === id);
};

// Simulate saving a unit (returns the saved unit)
export const saveUnit = (unit: UnitState): UnitState => {
    console.log('Saving unit:', unit);
    return { ...unit, updatedAt: new Date().toISOString() };
};

// Simulate saving a rota (returns the saved rota)
export const saveRota = (rota: RotaState): RotaState => {
    console.log('Saving rota:', rota);
    return { ...rota, updatedAt: new Date().toISOString() };
};
