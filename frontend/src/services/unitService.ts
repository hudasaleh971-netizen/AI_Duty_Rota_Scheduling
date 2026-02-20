import { supabase } from '../lib/supabaseClient';
import type { UnitState, Staff, ShiftCode } from '../types';

// Database row type (snake_case)
type UnitRow = {
    id: string;
    name: string;
    manager: string | null;
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
        manager: row.manager || '',
        rules: row.rules || '',
    },
    // Map staff safely, handling potential old data structure if any
    staff: (row.staff || []).map((s: any) => ({
        ...s,
        // Ensure position is string
        position: s.position || 'Standard Nurse',
        // Map old 'type' enum to boolean if needed, or use existing boolean
        isDirectCare: s.isDirectCare !== undefined ? s.isDirectCare : (s.type === 'Direct Care')
    })),
    shiftCodes: (row.shift_codes || []).map((sc: any) => ({
        ...sc,
        isDirectCare: sc.isDirectCare !== undefined ? sc.isDirectCare : (sc.type === 'Direct Care')
    })),
    createdAt: row.created_at,
    updatedAt: row.updated_at,
});

// Transform UnitState to DB payload
const unitStateToPayload = (state: UnitState) => ({
    name: state.unitInfo.name,
    manager: state.unitInfo.manager || null,
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
// Default shift codes - Updated for standard nursing shifts
export const defaultShiftCodes: ShiftCode[] = [
    { code: 'D', definition: 'Day', description: 'Day shift 07:00 - 19:00', hours: 12, isDirectCare: true, remarks: 'Standard 12h day shift' },
    { code: 'N', definition: 'Night', description: 'Night shift 19:00 - 07:00', hours: 12, isDirectCare: true, remarks: 'Standard 12h night shift' },
    { code: 'O', definition: 'Off', description: 'Rest day', hours: 0, isDirectCare: false, remarks: 'Scheduled day off' },
    { code: 'AL', definition: 'Annual Leave', description: 'Approved leave', hours: 12, isDirectCare: false, remarks: 'Contributes to duty hours' },
    { code: 'SL', definition: 'Sick Leave', description: 'Medical leave', hours: 12, isDirectCare: false, remarks: 'Contributes to duty hours' },
    { code: 'PH', definition: 'Public Holiday', description: 'Public Holiday Off', hours: 12, isDirectCare: false, remarks: 'Contributes to duty hours' },
    { code: 'CL', definition: 'Compensatory Leave', description: 'Time-off in lieu', hours: 12, isDirectCare: false, remarks: 'Contributes to duty hours' },
    { code: 'TR', definition: 'Training', description: 'Training/Development', hours: 8, isDirectCare: false, remarks: 'Training day (8h)' },
    { code: 'AD', definition: 'Admin', description: 'Administrative Duties', hours: 8, isDirectCare: false, remarks: 'Non-clinical day (8h)' },
];
