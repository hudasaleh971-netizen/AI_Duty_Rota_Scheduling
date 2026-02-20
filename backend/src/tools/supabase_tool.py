"""
Supabase Tool for CrewAI

Custom tool that fetches scheduling data from Supabase.
"""
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase client
_client = None

def get_client():
    global _client
    if _client is None:
        _client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    return _client


class RotaIdInput(BaseModel):
    """Input for fetching rota data."""
    rota_id: str = Field(description="The UUID of the rota configuration")


class FetchRotaDataTool(BaseTool):
    name: str = "fetch_rota_data"
    description: str = """
    Fetches all scheduling data from Supabase for a given rota_id.
    Returns the rota configuration AND the unit details (staff, shift codes).
    Use this to get all the data needed for generating CPLEX input.
    """
    args_schema: Type[BaseModel] = RotaIdInput
    
    def _run(self, rota_id: str) -> str:
        """Fetch rota and unit data from Supabase."""
        client = get_client()
        
        # Fetch rota config
        rota = client.table("rotas_config").select("*").eq("id", rota_id).single().execute()
        
        if not rota.data:
            return f"Error: Rota not found for id {rota_id}"
        
        rota_data = rota.data
        
        # Fetch unit with staff
        unit = client.table("units").select("*").eq("id", rota_data["unit_id"]).single().execute()
        
        if not unit.data:
            return f"Error: Unit not found for id {rota_data['unit_id']}"
        
        unit_data = unit.data
        
        # Combine and format the data
        result = f"""
=== ROTA CONFIGURATION ===
ID: {rota_data['id']}
Unit: {rota_data['unit_name']}
Period: {rota_data['start_date']} to {rota_data['end_date']}

Staff Target Hours (goal for this month):
{rota_data['staff_target_hours']}

Staff Owing Hours (balance from previous month):
{rota_data['staff_owing_hours']}

Special Requests (pre-filled shifts):
{rota_data['special_requests']}

Comments: {rota_data.get('comments', 'None')}

Name: {unit_data['name']}
Manager: {unit_data.get('manager', 'N/A')}

Rules:
{unit_data.get('rules', 'No specific rules')}

=== STAFF MEMBERS ===
{unit_data['staff']}

=== SHIFT CODES ===
{unit_data['shift_codes']}
"""
        return result

class SaveScheduleInput(BaseModel):
    """Input for saving schedule data."""
    rota_id: str = Field(description="The UUID of the rota configuration")
    schedule_data: dict = Field(description="The generated schedule object containing 'schedule' list")




class SaveScheduleTool(BaseTool):
    name: str = "save_schedule_to_db"
    description: str = """
    Saves the final generated schedule to the Supabase database.
    Deletes existing assignments for the rota and inserts new ones.
    """
    args_schema: Type[BaseModel] = SaveScheduleInput
    
    def _run(self, rota_id: str, schedule_data: dict) -> str:
        """Save schedule to database."""
        try:
            client = get_client()
            assignments = []
            
            # Extract the actual list
            items = schedule_data.get("schedule", [])
            
            if not items:
                return "Warning: No items to save in schedule."
            
            print(f"💾 Using SaveScheduleTool: Saving {len(items)} assignments for {rota_id}...")
            
            for item in items:
                assignments.append({
                    "rota_id": rota_id,
                    "date": item["date"],
                    "employee_id": item["employeeId"],
                    "shift_code": item["shiftCode"],
                    "employee_name": item["employeeName"]
                })
                
            # Delete existing
            client.table("schedule_assignments").delete().eq("rota_id", rota_id).execute()
            
            # Bulk insert
            client.table("schedule_assignments").insert(assignments).execute()
            
            return f"Success: Saved {len(assignments)} assignments to database."
            
        except Exception as e:
            return f"Error saving to database: {str(e)}"

# Helper function to allow direct usage without instantiating tool
def save_schedule_direct(rota_id: str, schedule_data: dict):
    tool = SaveScheduleTool()
    return tool._run(rota_id, schedule_data)
