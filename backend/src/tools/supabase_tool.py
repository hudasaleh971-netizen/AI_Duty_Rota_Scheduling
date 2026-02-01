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

=== UNIT DETAILS ===
Name: {unit_data['name']}
Department: {unit_data.get('department', 'N/A')}
Manager: {unit_data.get('manager', 'N/A')}
Min Nurses Per Shift: {unit_data.get('min_nurses_per_shift', 2)}

Rules:
{unit_data.get('rules', 'No specific rules')}

=== STAFF MEMBERS ===
{unit_data['staff']}

=== SHIFT CODES ===
{unit_data['shift_codes']}
"""
        return result
