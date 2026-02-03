import { useState, useRef, useCallback } from "react";
import { CopilotSidebar as CopilotSidebarUI } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

interface AICopilotSidebarProps {
    agentType: "rota" | "unit";
    onFileProcessed?: (data: unknown) => void;
    onSuggestionsReceived?: (suggestions: unknown) => void;
}

/**
 * AI Copilot Sidebar component that provides:
 * - Chat interface with the AI agent
 * - File upload capability for extracting data
 * - Suggestions for form filling
 */
export function AICopilotSidebar({
    agentType,
    onFileProcessed,
    onSuggestionsReceived
}: AICopilotSidebarProps) {
    const [isUploading, setIsUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [lastUploadResult, setLastUploadResult] = useState<unknown>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setUploadError(null);

        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("agent_type", agentType);

            const response = await fetch("http://localhost:5000/copilotkit/process-file", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();

            if (result.success) {
                setLastUploadResult(result.data);
                onFileProcessed?.(result.data);
                onSuggestionsReceived?.(result.data?.suggestions);
            } else {
                setUploadError(result.error || "Failed to process file");
            }
        } catch (err) {
            setUploadError(err instanceof Error ? err.message : "Upload failed");
        } finally {
            setIsUploading(false);
            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    }, [agentType, onFileProcessed, onSuggestionsReceived]);

    const triggerFileUpload = () => {
        fileInputRef.current?.click();
    };

    const labels = agentType === "rota"
        ? {
            title: "Rota Assistant",
            placeholder: "Ask me to help fill your rota form...",
            uploadButton: "Upload Schedule File",
            uploadHint: "Upload Excel, Word, or PDF files",
        }
        : {
            title: "Unit Assistant",
            placeholder: "Ask me to help configure your unit...",
            uploadButton: "Upload Staff List",
            uploadHint: "Upload Excel, Word, or PDF files",
        };

    return (
        <>
            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.docx,.doc,.pdf,.csv"
                onChange={handleFileUpload}
                style={{ display: "none" }}
            />

            {/* CopilotKit Sidebar */}
            <CopilotSidebarUI
                labels={{
                    title: labels.title,
                    initial: `👋 Hi! I can help you ${agentType === "rota" ? "fill out your rota" : "configure your unit"}.\n\nUpload a file or ask me questions!`,
                    placeholder: labels.placeholder,
                }}
                icons={{
                    // Custom icons can be added here
                }}
                defaultOpen={true}
                clickOutsideToClose={false}
            >
                {/* Custom header with file upload */}
                <div className="copilot-file-upload">
                    <button
                        onClick={triggerFileUpload}
                        disabled={isUploading}
                        className="copilot-upload-btn"
                    >
                        {isUploading ? "⏳ Processing..." : `📁 ${labels.uploadButton}`}
                    </button>
                    <p className="copilot-upload-hint">{labels.uploadHint}</p>

                    {uploadError && (
                        <div className="copilot-error">
                            ❌ {uploadError}
                            <button onClick={() => setUploadError(null)}>×</button>
                        </div>
                    )}

                    {lastUploadResult && (
                        <div className="copilot-success">
                            ✅ File processed! Check suggestions below.
                        </div>
                    )}
                </div>
            </CopilotSidebarUI>

            {/* Styles */}
            <style>{`
        .copilot-file-upload {
          padding: 12px;
          border-bottom: 1px solid #e2e8f0;
          background: #f8fafc;
        }
        
        .copilot-upload-btn {
          width: 100%;
          padding: 10px 16px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .copilot-upload-btn:hover:not(:disabled) {
          background: linear-gradient(135deg, #4f46e5, #7c3aed);
          transform: translateY(-1px);
        }
        
        .copilot-upload-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .copilot-upload-hint {
          font-size: 12px;
          color: #64748b;
          text-align: center;
          margin-top: 6px;
          margin-bottom: 0;
        }
        
        .copilot-error {
          margin-top: 8px;
          padding: 8px 12px;
          background: #fef2f2;
          color: #dc2626;
          border-radius: 6px;
          font-size: 13px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .copilot-error button {
          background: none;
          border: none;
          color: #dc2626;
          cursor: pointer;
          font-size: 16px;
        }
        
        .copilot-success {
          margin-top: 8px;
          padding: 8px 12px;
          background: #f0fdf4;
          color: #16a34a;
          border-radius: 6px;
          font-size: 13px;
        }
      `}</style>
        </>
    );
}
