import { supabase } from '../lib/supabaseClient';
import type { RotaState, RotaListItem, SpecialRequest, StaffOwingHours } from '../types';

// Database row type (snake_case) - matches rotas_config table
type RotaRow = {
    id: string;
    unit_id: string;
    unit_name: string | null;
    start_date: string;
    end_date: string;
    staff_owing_hours: StaffOwingHours | null;
    staff_target_hours: StaffOwingHours | null;
    special_requests: SpecialRequest[];
    comments: string | null;
    created_at: string;
    updated_at: string;
};

// Transform DB row to RotaState
const rowToRotaState = (row: RotaRow): RotaState => ({
    id: row.id,
    metadata: {
        unitId: row.unit_id,
        unitName: row.unit_name || '',
        startDate: row.start_date,
        endDate: row.end_date,
    },
    staffOwingHours: row.staff_owing_hours || {},
    staffTargetHours: row.staff_target_hours || {},
    specialRequests: row.special_requests || [],
    comments: row.comments || '',
    createdAt: row.created_at,
    updatedAt: row.updated_at,
});

// Transform RotaState to DB payload
const rotaStateToPayload = (state: RotaState) => ({
    unit_id: state.metadata.unitId,
    unit_name: state.metadata.unitName,
    start_date: state.metadata.startDate,
    end_date: state.metadata.endDate,
    staff_owing_hours: state.staffOwingHours,
    staff_target_hours: state.staffTargetHours,
    special_requests: state.specialRequests,
    comments: state.comments || null,
    updated_at: new Date().toISOString(),
});

// Transform DB row to RotaListItem (for dashboard)
const rowToListItem = (row: Pick<RotaRow, 'id' | 'unit_name' | 'start_date' | 'end_date' | 'updated_at'>): RotaListItem => ({
    id: row.id,
    unitName: row.unit_name || '',
    startDate: row.start_date,
    endDate: row.end_date,
    lastModified: row.updated_at,
});

export const rotaService = {
    // Get all rotas for dashboard list
    async getRotaListItems(): Promise<RotaListItem[]> {
        const { data, error } = await supabase
            .from('rotas_config')  // Changed table name
            .select('id, unit_name, start_date, end_date, updated_at')
            .order('updated_at', { ascending: false });

        if (error) throw error;
        return (data || []).map(rowToListItem);
    },

    // Get single rota by ID
    async getRotaById(id: string): Promise<RotaState | null> {
        const { data, error } = await supabase
            .from('rotas_config')  // Changed table name
            .select('*')
            .eq('id', id)
            .single();

        if (error) {
            if (error.code === 'PGRST116') return null; // Not found
            throw error;
        }
        return rowToRotaState(data);
    },

    // Save (upsert) a rota
    async saveRota(state: RotaState): Promise<RotaState> {
        const payload = rotaStateToPayload(state);

        // Check if this is an update or insert
        const isUpdate = state.id && !state.id.startsWith('temp-');

        const { data, error } = await supabase
            .from('rotas_config')  // Changed table name
            .upsert(isUpdate ? { id: state.id, ...payload } : payload)
            .select()
            .single();

        if (error) throw error;
        return rowToRotaState(data);
    },

    // Delete a rota
    async deleteRota(id: string): Promise<void> {
        const { error } = await supabase
            .from('rotas_config')  // Changed table name
            .delete()
            .eq('id', id);

        if (error) throw error;
    },
};
