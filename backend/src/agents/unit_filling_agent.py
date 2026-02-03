"""
Unit Filling Agent using Google ADK

This agent helps users fill the Create Unit form by:
1. Processing uploaded files (Excel, Word, PDF) containing staff or unit data
2. Extracting staff information (names, IDs, positions, hours)
3. Extracting shift code definitions
4. Providing suggestions for form fields
"""

from typing import Any

from .file_processor import extract_unit_data


# =============================================================================
# Tool Definitions for the Unit Agent
# =============================================================================

def process_unit_file(file_content: bytes, file_name: str) -> dict[str, Any]:
    """
    Process an uploaded file to extract unit/staff information.
    
    Args:
        file_content: The raw bytes of the uploaded file
        file_name: Original filename (e.g., "staff_list.xlsx")
        
    Returns:
        Extracted unit data including staff list and shift codes
    """
    return extract_unit_data(file_content, file_name)


def format_staff_list(extracted_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Format extracted staff data for the unit form.
    
    Args:
        extracted_data: Data extracted from the file
        
    Returns:
        List of staff members in the format expected by the frontend
    """
    staff_list = []
    for staff in extracted_data.get("staff", []):
        staff_list.append({
            "name": staff.get("name", ""),
            "staffId": staff.get("staffId", ""),
            "position": _normalize_position(staff.get("position", "Level 1")),
            "type": _normalize_staff_type(staff.get("type", "Direct Care")),
            "contractedHours": staff.get("contractedHours") or 160,
            "comments": staff.get("comments", "")
        })
    return staff_list


def format_shift_codes(extracted_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Format extracted shift codes for the unit form.
    
    Args:
        extracted_data: Data extracted from the file
        
    Returns:
        List of shift codes in the format expected by the frontend
    """
    shift_codes = []
    for code in extracted_data.get("shiftCodes", []):
        shift_codes.append({
            "code": code.get("code", "").upper(),
            "definition": code.get("definition", ""),
            "description": code.get("description", ""),
            "hours": code.get("hours") or 8,
            "type": _normalize_staff_type(code.get("type", "Direct Care")),
            "remarks": code.get("remarks", "")
        })
    return shift_codes


def _normalize_position(position: str) -> str:
    """Normalize position to match frontend options."""
    position_lower = position.lower()
    if "3" in position_lower or "senior" in position_lower:
        return "Level 3"
    elif "2" in position_lower or "mid" in position_lower:
        return "Level 2"
    else:
        return "Level 1"


def _normalize_staff_type(staff_type: str) -> str:
    """Normalize staff type to match frontend options."""
    if "non" in staff_type.lower() or "indirect" in staff_type.lower():
        return "Non-Direct Care"
    return "Direct Care"


# =============================================================================
# Agent Definition
# =============================================================================

class UnitFillingAgent:
    """
    Agent for filling unit configuration forms using Vertex AI Gemini.
    
    This agent can:
    - Process uploaded staff lists (Excel, Word, PDF)
    - Extract staff information (names, IDs, positions, hours)
    - Extract shift code definitions from policy documents
    - Help users complete the unit configuration form
    """
    
    def __init__(self):
        self.name = "unit_filling_agent"
        self.model = "gemini-2.0-flash"
        self._extracted_data: dict[str, Any] | None = None
    
    @property
    def system_instruction(self) -> str:
        return """You are a helpful assistant that helps users fill out unit configuration forms for staff scheduling.

Your capabilities:
1. Process uploaded files (Excel, Word, PDF) containing staff lists or shift definitions
2. Extract staff information: names, IDs, positions, contracted hours
3. Extract shift code definitions from policy documents
4. Suggest how to fill in form fields based on extracted data

When a user uploads a file:
1. Analyze the file to extract staff and shift code information
2. Summarize what you found (number of staff, shift codes, etc.)
3. Offer to help populate the staff table or shift code table

Staff positions should be: Level 1, Level 2, or Level 3
Staff types should be: Direct Care or Non-Direct Care

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
        self._extracted_data = extract_unit_data(file_content, file_name)
        
        # Generate summary response
        summary = self._extracted_data.get("summary", "File processed")
        staff_count = len(self._extracted_data.get("staff", []))
        shift_codes_count = len(self._extracted_data.get("shiftCodes", []))
        unit_info = self._extracted_data.get("unitInfo", {})
        
        response = {
            "extracted_data": self._extracted_data,
            "summary": summary,
            "stats": {
                "staff_found": staff_count,
                "shift_codes_found": shift_codes_count,
                "unit_name": unit_info.get("name"),
                "department": unit_info.get("department")
            },
            "suggestions": {
                "unit_info": unit_info,
                "staff": format_staff_list(self._extracted_data),
                "shift_codes": format_shift_codes(self._extracted_data)
            }
        }
        
        return response
