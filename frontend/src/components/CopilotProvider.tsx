import { CopilotKit } from "@copilotkit/react-core";
import type { ReactNode } from "react";

interface CopilotProviderProps {
    children: ReactNode;
}

/**
 * CopilotKit provider wrapper for the application.
 * 
 * Configures the CopilotKit runtime to connect to our backend
 * Google ADK agents for file processing and form filling.
 */
export function CopilotProvider({ children }: CopilotProviderProps) {
    return (
        <CopilotKit
            runtimeUrl="http://localhost:5000/copilotkit"
        // Alternatively, use publicApiKey for CopilotCloud:
        // publicApiKey="your-copilot-cloud-key"
        >
            {children}
        </CopilotKit>
    );
}
