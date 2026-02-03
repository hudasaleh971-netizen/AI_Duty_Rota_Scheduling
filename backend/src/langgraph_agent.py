"""
LangGraph Agent for CopilotKit Integration

This module creates a LangGraph-based chat agent that integrates with CopilotKit.
It provides file processing capabilities for rota and unit forms through tools.
"""

import base64
from typing import Any, Literal
from typing_extensions import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from copilotkit import CopilotKitState

from src.agents import RotaFillingAgent, UnitFillingAgent


# =============================================================================
# Initialize Agents
# =============================================================================

rota_agent = RotaFillingAgent()
unit_agent = UnitFillingAgent()


# =============================================================================
# Agent State
# =============================================================================

class AssistantState(CopilotKitState):
    """State for the form filling assistant agent."""
    # Inherits 'messages' and 'copilotkit' from CopilotKitState
    pass


# =============================================================================
# Tool Definitions
# =============================================================================

@tool
async def process_rota_file(file_content_base64: str, file_name: str) -> dict[str, Any]:
    """
    Process an uploaded rota/schedule file to extract dates, staff assignments, and special requests.
    
    Use this tool when a user uploads a file for creating a new duty rota.
    The file can be Excel (.xlsx), Word (.docx), or PDF format.
    
    Args:
        file_content_base64: Base64 encoded content of the uploaded file
        file_name: Original filename with extension (e.g., 'schedule.xlsx')
    
    Returns:
        Extracted rota data including dates, assignments, and suggestions
    """
    try:
        decoded_content = base64.b64decode(file_content_base64)
        result = await rota_agent.process_file_and_respond(
            file_content=decoded_content,
            file_name=file_name
        )
        return {
            "success": True,
            "data": result,
            "message": result.get("summary", "File processed successfully")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
async def process_unit_file(file_content_base64: str, file_name: str) -> dict[str, Any]:
    """
    Process an uploaded unit configuration file to extract staff details and shift codes.
    
    Use this tool when a user uploads a file for setting up a unit configuration.
    The file can be Excel (.xlsx), Word (.docx), or PDF format.
    
    Args:
        file_content_base64: Base64 encoded content of the uploaded file
        file_name: Original filename with extension (e.g., 'staff_list.xlsx')
    
    Returns:
        Extracted unit data including staff list and shift codes
    """
    try:
        decoded_content = base64.b64decode(file_content_base64)
        result = await unit_agent.process_file_and_respond(
            file_content=decoded_content,
            file_name=file_name
        )
        return {
            "success": True,
            "data": result,
            "message": result.get("summary", "File processed successfully")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# All tools available to the agent
TOOLS = [process_rota_file, process_unit_file]


# =============================================================================
# Graph Nodes
# =============================================================================

SYSTEM_PROMPT = """You are a helpful AI assistant for the Duty Rota Scheduling application.
You help users fill out forms by:
1. Processing uploaded files (Excel, Word, PDF) containing schedule or staff data
2. Extracting relevant information like dates, staff assignments, and special requests
3. Suggesting how to fill form fields based on the extracted data

When a user wants to create a rota schedule:
- Ask them to upload their schedule file
- Use the process_rota_file tool to extract data
- Summarize what you found and offer to help fill the form

When a user wants to configure a unit:
- Ask them to upload their staff list or policy document
- Use the process_unit_file tool to extract data
- Summarize the staff and shift codes found

Be concise, helpful, and focus on extracting accurate data from files.
"""


async def chat_node(state: AssistantState, config: RunnableConfig) -> dict:
    """Main chat node that processes user messages and generates responses."""
    
    # Initialize the model
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7
    )
    
    # Get CopilotKit actions/tools if available
    copilotkit_actions = state.get("copilotkit", {}).get("actions", [])
    all_tools = TOOLS + copilotkit_actions
    
    # Bind tools to model
    model_with_tools = model.bind_tools(all_tools)
    
    # Prepare messages with system prompt
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    
    # Generate response
    response = await model_with_tools.ainvoke(messages, config)
    
    return {"messages": [response]}


async def tool_node(state: AssistantState, config: RunnableConfig) -> dict:
    """Execute tool calls from the model."""
    
    last_message = state["messages"][-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"messages": []}
    
    results = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Find and execute the tool
        tool_result = None
        for t in TOOLS:
            if t.name == tool_name:
                tool_result = await t.ainvoke(tool_args)
                break
        
        if tool_result is None:
            tool_result = {"error": f"Tool {tool_name} not found"}
        
        # Create tool message
        from langchain_core.messages import ToolMessage
        results.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            )
        )
    
    return {"messages": results}


def should_continue(state: AssistantState) -> Literal["tools", "end"]:
    """Determine if we should continue to tool execution or end."""
    
    last_message = state["messages"][-1]
    
    # Check if the model wants to call a tool
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return "end"


# =============================================================================
# Build Graph
# =============================================================================

def create_graph():
    """Create the LangGraph graph for the assistant."""
    
    workflow = StateGraph(AssistantState)
    
    # Add nodes
    workflow.add_node("chat", chat_node)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("chat")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "chat",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # After tools, go back to chat for response
    workflow.add_edge("tools", "chat")
    
    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# Create the compiled graph
graph = create_graph()
