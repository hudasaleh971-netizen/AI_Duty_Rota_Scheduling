import { useState, useCallback } from "react";
import { useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";

/**
 * Copilot API service for file processing and form filling.
 * Connects to the backend Google ADK agents.
 */

const COPILOT_API_BASE = "http://localhost:5000/copilotkit";

export interface AgentResponse {
    success: boolean;
    data?: {
        extracted_data: Record<string, unknown>;
        summary: string;
        stats: Record<string, unknown>;
        suggestions: Record<string, unknown>;
    };
    message?: string;
    error?: string;
}

/**
 * Process a file using the CopilotKit agent endpoint.
 */
export async function processFile(
    file: File,
    agentType: "rota" | "unit"
): Promise<AgentResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("agent_type", agentType);

    const response = await fetch(`${COPILOT_API_BASE}/process-file`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`Failed to process file: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Custom hook to use the Rota Filling Agent.
 * 
 * Provides:
 * - processRotaFile: Function to upload and process a file
 * - suggestions: Extracted suggestions for form fields
 * - isProcessing: Loading state
 * - error: Error message if any
 */
export function useRotaAgent(rotaState: unknown, updateRotaState: (updates: Partial<unknown>) => void) {
    const [suggestions, setSuggestions] = useState<Record<string, unknown> | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Make rota state readable by the copilot
    useCopilotReadable({
        description: "Current rota configuration including dates, selected unit, and special requests",
        value: JSON.stringify(rotaState),
    });

    // Action to update rota fields
    useCopilotAction({
        name: "updateRotaField",
        description: "Update a specific field in the rota form",
        parameters: [
            {
                name: "field",
                type: "string",
                description: "The field to update (startDate, endDate, unitId, etc.)",
            },
            {
                name: "value",
                type: "string",
                description: "The value to set",
            },
        ],
        handler: async ({ field, value }: { field: string; value: string }) => {
            updateRotaState({ [field]: value });
            return `Updated ${field} to ${value}`;
        },
    });

    // Action to add a special request
    useCopilotAction({
        name: "addSpecialRequest",
        description: "Add a locked shift assignment (special request) to the rota",
        parameters: [
            {
                name: "staffId",
                type: "string",
                description: "The staff member's ID",
            },
            {
                name: "date",
                type: "string",
                description: "The date in YYYY-MM-DD format",
            },
            {
                name: "shiftCode",
                type: "string",
                description: "The shift code to assign",
            },
        ],
        handler: async ({ staffId, date, shiftCode }: { staffId: string; date: string; shiftCode: string }) => {
            // This will be connected to the actual pre-schedule update logic
            console.log("Adding special request:", { staffId, date, shiftCode });
            return `Added locked shift ${shiftCode} for ${staffId} on ${date}`;
        },
    });

    const processRotaFile = useCallback(async (file: File) => {
        setIsProcessing(true);
        setError(null);

        try {
            const response = await processFile(file, "rota");

            if (response.success && response.data) {
                setSuggestions(response.data.suggestions);
                return response.data;
            } else {
                throw new Error(response.error || "Failed to process file");
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Unknown error";
            setError(errorMessage);
            throw err;
        } finally {
            setIsProcessing(false);
        }
    }, []);

    return {
        processRotaFile,
        suggestions,
        isProcessing,
        error,
        clearError: () => setError(null),
    };
}

/**
 * Custom hook to use the Unit Filling Agent.
 * 
 * Provides:
 * - processUnitFile: Function to upload and process a file
 * - suggestions: Extracted suggestions for form fields (staff, shift codes)
 * - isProcessing: Loading state
 * - error: Error message if any
 */
export function useUnitAgent(unitState: unknown, _updateUnitState: (updates: Partial<unknown>) => void) {
    const [suggestions, setSuggestions] = useState<Record<string, unknown> | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Make unit state readable by the copilot
    useCopilotReadable({
        description: "Current unit configuration including staff members and shift codes",
        value: JSON.stringify(unitState),
    });

    // Action to add staff members
    useCopilotAction({
        name: "addStaffMember",
        description: "Add a new staff member to the unit",
        parameters: [
            {
                name: "name",
                type: "string",
                description: "Staff member's full name",
            },
            {
                name: "staffId",
                type: "string",
                description: "Staff member's ID/code",
            },
            {
                name: "position",
                type: "string",
                description: "Level 1, Level 2, or Level 3",
            },
            {
                name: "contractedHours",
                type: "number",
                description: "Monthly contracted hours",
            },
        ],
        handler: async (params: { name: string; staffId: string; position: string; contractedHours: number }) => {
            console.log("Adding staff member:", params);
            return `Added staff member ${params.name}`;
        },
    });

    // Action to add shift code
    useCopilotAction({
        name: "addShiftCode",
        description: "Add a new shift code definition",
        parameters: [
            {
                name: "code",
                type: "string",
                description: "Shift code (e.g., E, L, N)",
            },
            {
                name: "definition",
                type: "string",
                description: "Shift definition (e.g., Early, Late, Night)",
            },
            {
                name: "hours",
                type: "number",
                description: "Number of hours for this shift",
            },
        ],
        handler: async (params: { code: string; definition: string; hours: number }) => {
            console.log("Adding shift code:", params);
            return `Added shift code ${params.code}`;
        },
    });

    const processUnitFile = useCallback(async (file: File) => {
        setIsProcessing(true);
        setError(null);

        try {
            const response = await processFile(file, "unit");

            if (response.success && response.data) {
                setSuggestions(response.data.suggestions);
                return response.data;
            } else {
                throw new Error(response.error || "Failed to process file");
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Unknown error";
            setError(errorMessage);
            throw err;
        } finally {
            setIsProcessing(false);
        }
    }, []);

    return {
        processUnitFile,
        suggestions,
        isProcessing,
        error,
        clearError: () => setError(null),
    };
}
