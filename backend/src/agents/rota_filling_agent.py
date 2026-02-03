"""
Rota Filling Agent using Google ADK

This agent helps users fill the Create Rota form by:
1. Processing uploaded files (Excel, Word, PDF) containing schedule data
2. Extracting dates, staff assignments, and special requests
3. Providing suggestions for form fields
"""

from typing import Any

from .file_processor import extract_rota_data


# =============================================================================
# Tool Definitions for the Rota Agent
# =============================================================================

def process_rota_file(file_content: bytes, file_name: str) -> dict[str, Any]:
    """
    Process an uploaded file to extract rota/schedule information.
    
    Args:
        file_content: The raw bytes of the uploaded file
        file_name: Original filename (e.g., "schedule.xlsx")
        
    Returns:
        Extracted rota data including dates, staff assignments, and special requests
    """
    return extract_rota_data(file_content, file_name)


def suggest_date_range(extracted_data: dict[str, Any]) -> dict[str, str]:
    """
    Suggest start and end dates based on extracted data.
    
    Args:
        extracted_data: Data extracted from the file
        
    Returns:
        Suggested start_date and end_date
    """
    return {
        "start_date": extracted_data.get("startDate"),
        "end_date": extracted_data.get("endDate"),
        "confidence": "high" if extracted_data.get("startDate") else "low"
    }


def format_special_requests(extracted_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Format extracted special requests for the rota form.
    
    Args:
        extracted_data: Data extracted from the file
        
    Returns:
        List of special requests in the format expected by the frontend
    """
    requests = []
    for req in extracted_data.get("specialRequests", []):
        requests.append({
            "staffName": req.get("staffName"),
            "date": req.get("date"),
            "shiftCode": _map_request_to_shift_code(req.get("requestType", "")),
            "isLocked": True,  # Pre-filled requests should be locked
            "notes": req.get("notes", "")
        })
    return requests


def _map_request_to_shift_code(request_type: str) -> str:
    """Map request types to standard shift codes."""
    mappings = {
        "leave": "AL",
        "annual leave": "AL",
        "sick": "SL",
        "sick leave": "SL",
        "training": "TR",
        "study": "SD",
        "day off": "DO",
        "off": "O",
    }
    return mappings.get(request_type.lower(), "O")


# =============================================================================
# Agent Definition
# =============================================================================

class RotaFillingAgent:
    """
    Agent for filling rota forms using Vertex AI Gemini.
    
    This agent can:
    - Process uploaded schedule files
    - Extract and suggest date ranges
    - Identify shift assignments and special requests
    - Help users complete the pre-schedule grid
    """
    
    def __init__(self):
        self.name = "rota_filling_agent"
        self.model = "gemini-2.0-flash"
        self._extracted_data: dict[str, Any] | None = None
    
    @property
    def system_instruction(self) -> str:
        return """You are a helpful assistant that helps users fill out duty rota (schedule) forms.

Your capabilities:
1. Process uploaded files (Excel, Word, PDF) containing schedule or rota data
2. Extract key information like date ranges, staff assignments, and leave requests
3. Suggest how to fill in form fields based on extracted data
4. Answer questions about the scheduling process

When a user uploads a file:
1. Analyze the file to extract schedule information
2. Summarize what you found (date range, number of staff, special requests)
3. Offer to help fill in specific form fields

Be concise and helpful. Focus on extracting accurate data from files."""
    
    async def process_file_and_respond(
        self,
        file_content: bytes,
        file_name: str,
        user_message: str = ""
    ) -> dict[str, Any]:
        """
        Process an uploaded file and generate a response.
        
        Args:
            file_content: Raw bytes of the uploaded file
            file_name: Original filename
            user_message: Optional user message/question
            
        Returns:
            Dict containing extracted data and agent response
        """
        # Extract data from file
        self._extracted_data = extract_rota_data(file_content, file_name)
        
        # Generate summary response
        summary = self._extracted_data.get("summary", "File processed")
        staff_count = len(self._extracted_data.get("staffAssignments", []))
        requests_count = len(self._extracted_data.get("specialRequests", []))
        
        response = {
            "extracted_data": self._extracted_data,
            "summary": summary,
            "stats": {
                "staff_assignments_found": staff_count,
                "special_requests_found": requests_count,
                "start_date": self._extracted_data.get("startDate"),
                "end_date": self._extracted_data.get("endDate")
            },
            "suggestions": {
                "date_range": suggest_date_range(self._extracted_data),
                "special_requests": format_special_requests(self._extracted_data)
            }
        }
        
        return response
