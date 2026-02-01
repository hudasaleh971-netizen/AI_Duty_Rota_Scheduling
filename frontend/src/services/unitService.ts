import { supabase } from '../lib/supabaseClient';
import type { UnitState, Staff, ShiftCode } from '../types';

// Database row type (snake_case)
type UnitRow = {
    id: string;
    name: string;
    department: string | null;
    manager: string | null;
    min_nurses_per_shift: number;
    rules: string | null;
    staff: Staff[];
    shift_codes: ShiftCode[];
    created_at: string;
    updated_at: string;
};

// Transform DB row to UnitState
const rowToUnitState = (row: UnitRow): UnitState => ({
    id: row.id,
    unitInfo: {
        name: row.name,
        department: row.department || '',
        manager: row.manager || '',
        minNursesPerShift: row.min_nurses_per_shift,
        rules: row.rules || '',
    },
    staff: row.staff || [],
    shiftCodes: row.shift_codes || [],
    createdAt: row.created_at,
    updatedAt: row.updated_at,
});

// Transform UnitState to DB payload
const unitStateToPayload = (state: UnitState) => ({
    name: state.unitInfo.name,
    department: state.unitInfo.department || null,
    manager: state.unitInfo.manager || null,
    min_nurses_per_shift: state.unitInfo.minNursesPerShift,
    rules: state.unitInfo.rules || null,
    staff: state.staff,
    shift_codes: state.shiftCodes,
    updated_at: new Date().toISOString(),
});

export const unitService = {
    // Get all units
    async getUnits(): Promise<UnitState[]> {
        const { data, error } = await supabase
            .from('units')
            .select('*')
            .order('updated_at', { ascending: false });

        if (error) throw error;
        return (data || []).map(rowToUnitState);
    },

    // Get single unit by ID
    async getUnitById(id: string): Promise<UnitState | null> {
        const { data, error } = await supabase
            .from('units')
            .select('*')
            .eq('id', id)
            .single();

        if (error) {
            if (error.code === 'PGRST116') return null; // Not found
            throw error;
        }
        return rowToUnitState(data);
    },

    // Save (upsert) a unit
    async saveUnit(state: UnitState): Promise<UnitState> {
        const payload = unitStateToPayload(state);

        // Check if this is an update or insert
        const isUpdate = state.id && !state.id.startsWith('temp-');

        const { data, error } = await supabase
            .from('units')
            .upsert(isUpdate ? { id: state.id, ...payload } : payload)
            .select()
            .single();

        if (error) throw error;
        return rowToUnitState(data);
    },

    // Delete a unit
    async deleteUnit(id: string): Promise<void> {
        const { error } = await supabase
            .from('units')
            .delete()
            .eq('id', id);

        if (error) throw error;
    },
};

// Default shift codes (moved from mockDB)
export const defaultShiftCodes: ShiftCode[] = [
    { code: 'M', definition: 'Morning', description: 'Day shift 7:00 AM - 3:00 PM', hours: 8, type: 'Direct Care', remarks: 'Standard day shift' },
    { code: 'E', definition: 'Evening', description: 'Afternoon shift 3:00 PM - 11:00 PM', hours: 8, type: 'Direct Care', remarks: 'Standard evening shift' },
    { code: 'N', definition: 'Night', description: 'Night shift 7:00 PM - 7:00 AM', hours: 12, type: 'Direct Care', remarks: 'Extended night coverage' },
    { code: 'DO', definition: 'Day Off', description: 'Rest day', hours: 0, type: '-', remarks: 'Mandatory after 6 working days' },
    { code: 'AL', definition: 'Annual Leave', description: 'Approved leave', hours: 0, type: '-', remarks: 'Planned time off' },
    { code: 'SL', definition: 'Sick Leave', description: 'Medical leave', hours: 0, type: '-', remarks: 'Unplanned absence' },
    { code: 'CL', definition: 'Compensatory Leave', description: 'Time-off in lieu', hours: 0, type: '-', remarks: 'For extra hours worked' },
    { code: 'TR', definition: 'Training', description: 'Development day', hours: 0, type: 'Non-Direct Care', remarks: 'Courses, certifications' },
    { code: 'AD', definition: 'Administrative', description: 'Meetings, documentation', hours: 8, type: 'Non-Direct Care', remarks: 'Non-clinical duties' },
];
