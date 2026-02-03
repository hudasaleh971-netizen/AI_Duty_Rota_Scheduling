"""
Google ADK Agents Package for AI-Assisted Form Filling

This package contains:
- Rota Filling Agent: Extracts schedule data from files
- Unit Filling Agent: Extracts unit/staff data from files
- File processing using Vertex AI Gemini
"""

from .rota_filling_agent import RotaFillingAgent
from .unit_filling_agent import UnitFillingAgent

__all__ = ["RotaFillingAgent", "UnitFillingAgent"]
