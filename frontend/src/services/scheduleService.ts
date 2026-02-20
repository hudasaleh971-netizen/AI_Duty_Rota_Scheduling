import { supabase } from '../lib/supabaseClient';
import type { ScheduleResult } from '../types';

// Backend API URL
const API_BASE_URL = 'http://localhost:5000';

export const scheduleService = {
    /**
     * Get existing schedule from Supabase
     */
    async getScheduleByRotaId(rotaId: string): Promise<ScheduleResult | null> {
        try {
            const { data, error } = await supabase
                .from('schedule_assignments')
                .select('*')
                .eq('rota_id', rotaId);

            if (error) throw error;

            if (!data || data.length === 0) {
                return null;
            }

            // Transform DB rows back to ScheduleResult format
            const schedule = data.map((row: any) => ({
                date: row.date,
                employeeId: row.employee_id,
                employeeName: row.employee_name,
                shiftCode: row.shift_code
            }));

            // Note: DB doesn't store summary stats yet unless we added a column for it.
            // For now, we can either re-calculate on frontend or just return schedule.
            // The user wanted "pending/owning hours". Ideally we store the summary blob in rotas_config
            // or we re-calculate here. Re-calculating on frontend is safer for now.
            return {
                status: 'success',
                schedule,
                summary: undefined // Frontend can compute or we fetch from rotas_config if we saved it there
            };

        } catch (error) {
            console.error('Error fetching schedule:', error);
            return null;
        }
    },

    /**
     * Generate an optimized schedule for the given rota.
     * Calls the 3-agent CrewAI pipeline.
     */
    async generateSchedule(rotaId: string): Promise<ScheduleResult> {
        try {
            const response = await fetch(`${API_BASE_URL}/api/schedule/${rotaId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                return {
                    status: 'error',
                    error: errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
                };
            }

            const data = await response.json();

            // Handle the case where the API returns markdown-wrapped JSON
            if (data.raw_output && data.status === 'error') {
                // Try to extract JSON from markdown code block
                const jsonMatch = data.raw_output.match(/```json\n([\s\S]*?)\n```/);
                if (jsonMatch) {
                    try {
                        return JSON.parse(jsonMatch[1]);
                    } catch {
                        return data;
                    }
                }
            }

            return data;
        } catch (error) {
            console.error('Schedule API error:', error);
            return {
                status: 'error',
                error: error instanceof Error ? error.message : 'Failed to connect to backend',
            };
        }
    },

    /**
     * Parse a schedule result to extract assignments by staff and date.
     * Returns a map: staffId/name -> date -> shiftCode
     */
    parseScheduleByStaff(result: ScheduleResult): Map<string, Map<string, string>> {
        const staffSchedule = new Map<string, Map<string, string>>();

        if (result.status !== 'success' || !result.schedule) {
            return staffSchedule;
        }

        for (const assignment of result.schedule) {
            const staffKey = assignment.employeeName || assignment.employeeId || 'Unassigned';

            if (!staffSchedule.has(staffKey)) {
                staffSchedule.set(staffKey, new Map());
            }

            staffSchedule.get(staffKey)!.set(assignment.date, assignment.shiftCode);
        }

        return staffSchedule;
    },
};
