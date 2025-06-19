# mycrews/qrew/tools/agenttools.py
# Description: Maps agents to their assigned tools using preconfigured groups from inbuilt_tools.

from enum import Enum
from .inbuilt_tools import (
    # Individual Tools (some might also be in groups)
    code_interpreter_tool,
    file_read_tool,
    file_write_tool,
    directory_read_tool,
    directory_search_tool,
    code_docs_search_tool,
    github_search_tool,
    txt_search_tool, # Included as per user's file content for inbuilt_tools
    pdf_search_tool,   # Included
    mdx_search_tool,   # Included
    exa_search_tool,
    website_search_tool,
    serper_dev_tool,
    # Placeholder/Wrapped Tools
    ui_converter,
    schema_generator,
    security_scanner,
    ai_code_generator,
    # RAG Tools (via getter)
    get_rag_tool, # We'll call this if a RAG tool is needed for an agent
    # Tool Groups
    file_system_tools,
    search_tools_general,
    code_search_tools,
    api_dev_tools,
    cloud_dev_tools,
    mobile_dev_tools,
    web_dev_tools,
    security_tools,
    schema_tools,
    dev_utility_tools,
    coordinator_tools,
    base_developer_tools
)

class AgentName(str, Enum):
    # Authentication Agents
    AUTH_COORDINATOR = "auth_coordinator_agent"
    OTP_VERIFIER = "otp_verifier_agent"

    # Backend Agents
    API_CREATOR = "api_creator_agent"
    AUTH_AGENT = "auth_agent"
    CONFIG_AGENT = "config_agent"
    DATA_MODEL_AGENT = "data_model_agent"
    QUEUE_AGENT = "queue_agent"
    STORAGE_AGENT_BACKEND = "storage_agent_backend"
    SYNC_AGENT_BACKEND = "sync_agent_backend"

    # Mobile Agents
    MOBILE_API_CLIENT_AGENT = "mobile_api_client_agent"
    MOBILE_STORAGE_AGENT = "mobile_storage_agent"
    MOBILE_UI_AGENT = "mobile_ui_agent"

    # Web Agents
    ASSET_MANAGER = "asset_manager_agent"
    DYNAMIC_PAGE_BUILDER = "dynamic_page_builder_agent"
    STATIC_PAGE_BUILDER = "static_page_builder_agent"

    # Dev Utilities
    CODE_WRITER = "code_writer_agent"
    DEBUGGER = "debugger_agent"
    LOGGER_AGENT = "logger_agent"
    TESTER_AGENT = "tester_agent"

    # Lead Agents
    WEB_PROJECT_COORDINATOR = "web_project_coordinator_agent"
    BACKEND_PROJECT_COORDINATOR = "backend_project_coordinator_agent"
    MOBILE_PROJECT_COORDINATOR = "mobile_project_coordinator_agent"
    DEVOPS_COORDINATOR = "devops_coordinator_agent"
    OFFLINE_COORDINATOR = "offline_coordinator_agent"

    # Orchestrators
    EXECUTION_MANAGER = "execution_manager_agent"
    TECH_VETTING_COUNCIL = "tech_vetting_council_agent"
    PROJECT_ARCHITECT = "project_architect_agent"
    FINAL_ASSEMBLER = "final_assembler_agent"

    # Special Cases
    SOFTWARE_ENGINEER = "software_engineer_agent"
    DEVOPS_AGENT = "devops_agent"

# Helper to combine tool lists and remove duplicates
def _unique_tools(*tool_lists):
    # First, flatten the list of lists and filter out any None tool lists
    combined_initial = []
    for lst in tool_lists:
        if lst:  # Ensure the list itself is not None before extending
            combined_initial.extend(lst)

    # Filter out None tool objects from the combined list
    # This is important because tools like EXASearchTool, SerperDevTool, etc.,
    # might be None if their API keys are not set.
    combined_filtered_nones = [tool for tool in combined_initial if tool is not None]

    # De-duplicate by object identity, preserving order
    unique_list = []
    seen_ids = set() # Store ids of objects already added
    for tool_obj in combined_filtered_nones:
        # It's possible a tool object might not be hashable if it doesn't implement __hash__
        # However, we are hashing id(tool_obj) which is always hashable.
        obj_id = id(tool_obj)
        if obj_id not in seen_ids:
            unique_list.append(tool_obj)
            seen_ids.add(obj_id)
    return unique_list


enhanced_tools_groupings = {
    "file_system": file_system_tools,
    "search_general": search_tools_general,
    "search_code": code_search_tools,
    "dev_utils": dev_utility_tools,
    "api": api_dev_tools,
    "cloud": cloud_dev_tools,
    "security": security_tools,
    "mobile": mobile_dev_tools,
    "web": web_dev_tools,
    "db_schema": schema_tools,
    "coordinator": coordinator_tools,
    "base_dev": base_developer_tools,
    "ai_gen": [ai_code_generator],
    "ui_convert": [ui_converter],
    # Individual tools that might be directly assigned or part of smaller, specific combos
    "code_interpreter": [code_interpreter_tool],
    "file_read": [file_read_tool],
    "file_write": [file_write_tool],
    "dir_search": [directory_search_tool],
    "dir_read": [directory_read_tool],
    "txt_search": [txt_search_tool], # Assuming txt_search_tool is a valid imported tool
    "serper": [serper_dev_tool],
    "exa": [exa_search_tool],
    "github_search": [github_search_tool], # github_search_tool is also in code_search_tools
    "code_docs_search": [code_docs_search_tool] # also in code_search_tools
}

agent_tool_map = {
    # Authentication Agents
    AgentName.AUTH_COORDINATOR: _unique_tools(enhanced_tools_groupings["api"], enhanced_tools_groupings["security"], enhanced_tools_groupings["search_code"]),
    AgentName.OTP_VERIFIER: _unique_tools(enhanced_tools_groupings["api"], enhanced_tools_groupings["mobile"], enhanced_tools_groupings["security"]),

    # Backend Agents
    AgentName.API_CREATOR: _unique_tools(enhanced_tools_groupings["api"], enhanced_tools_groupings["cloud"], enhanced_tools_groupings["db_schema"]),
    AgentName.AUTH_AGENT: _unique_tools(enhanced_tools_groupings["api"], enhanced_tools_groupings["security"], enhanced_tools_groupings["search_code"]),
    AgentName.CONFIG_AGENT: _unique_tools(enhanced_tools_groupings["cloud"], enhanced_tools_groupings["file_system"]),
    AgentName.DATA_MODEL_AGENT: _unique_tools(enhanced_tools_groupings["db_schema"], enhanced_tools_groupings["api"], enhanced_tools_groupings["search_code"]),
    AgentName.QUEUE_AGENT: _unique_tools(enhanced_tools_groupings["cloud"], enhanced_tools_groupings["api"], enhanced_tools_groupings["github_search"]),
    AgentName.STORAGE_AGENT_BACKEND: _unique_tools(enhanced_tools_groupings["cloud"], enhanced_tools_groupings["db_schema"], enhanced_tools_groupings["api"]),
    AgentName.SYNC_AGENT_BACKEND: _unique_tools(enhanced_tools_groupings["cloud"], enhanced_tools_groupings["api"], enhanced_tools_groupings["mobile"]),

    # Mobile Agents
    AgentName.MOBILE_API_CLIENT_AGENT: _unique_tools(enhanced_tools_groupings["mobile"], enhanced_tools_groupings["api"], enhanced_tools_groupings["ui_convert"]),
    AgentName.MOBILE_STORAGE_AGENT: _unique_tools(enhanced_tools_groupings["mobile"], enhanced_tools_groupings["db_schema"], enhanced_tools_groupings["security"]),
    AgentName.MOBILE_UI_AGENT: _unique_tools(enhanced_tools_groupings["ui_convert"], enhanced_tools_groupings["mobile"], enhanced_tools_groupings["github_search"]),

    # Web Agents
    AgentName.ASSET_MANAGER: _unique_tools(enhanced_tools_groupings["web"], enhanced_tools_groupings["file_system"]),
    AgentName.DYNAMIC_PAGE_BUILDER: _unique_tools(enhanced_tools_groupings["web"], enhanced_tools_groupings["ai_gen"], enhanced_tools_groupings["api"]),
    AgentName.STATIC_PAGE_BUILDER: _unique_tools(enhanced_tools_groupings["web"], enhanced_tools_groupings["ui_convert"], enhanced_tools_groupings["github_search"]),

    # Dev Utilities
    AgentName.CODE_WRITER: _unique_tools(enhanced_tools_groupings["ai_gen"], enhanced_tools_groupings["search_code"], enhanced_tools_groupings["github_search"]),
    AgentName.DEBUGGER: _unique_tools(enhanced_tools_groupings["code_interpreter"], enhanced_tools_groupings["security"], enhanced_tools_groupings["file_read"]),
    AgentName.LOGGER_AGENT: _unique_tools(enhanced_tools_groupings["file_write"], enhanced_tools_groupings["dir_search"], enhanced_tools_groupings["txt_search"]),
    AgentName.TESTER_AGENT: _unique_tools(enhanced_tools_groupings["code_interpreter"], enhanced_tools_groupings["ai_gen"], enhanced_tools_groupings["file_read"]),

    # Lead Agents
    AgentName.BACKEND_PROJECT_COORDINATOR: _unique_tools(coordinator_tools, api_dev_tools, cloud_dev_tools),
    AgentName.WEB_PROJECT_COORDINATOR: _unique_tools(coordinator_tools, api_dev_tools, web_dev_tools),
    AgentName.MOBILE_PROJECT_COORDINATOR: _unique_tools(coordinator_tools, api_dev_tools, mobile_dev_tools),
    AgentName.DEVOPS_COORDINATOR: _unique_tools(cloud_dev_tools, security_tools, enhanced_tools_groupings["github_search"]),
    AgentName.OFFLINE_COORDINATOR: _unique_tools(mobile_dev_tools, cloud_dev_tools, api_dev_tools),

    # Orchestrators
    AgentName.EXECUTION_MANAGER: _unique_tools(coordinator_tools, enhanced_tools_groupings["file_system"], [get_rag_tool('web_components')]),
    AgentName.TECH_VETTING_COUNCIL: _unique_tools(enhanced_tools_groupings["serper"], enhanced_tools_groupings["exa"], enhanced_tools_groupings["search_code"]),
    AgentName.PROJECT_ARCHITECT: _unique_tools(enhanced_tools_groupings["ai_gen"], enhanced_tools_groupings["db_schema"], enhanced_tools_groupings["cloud"]),
    AgentName.FINAL_ASSEMBLER: _unique_tools(enhanced_tools_groupings["dir_read"], enhanced_tools_groupings["file_read"], enhanced_tools_groupings["security"]),

    # Special Cases
    AgentName.SOFTWARE_ENGINEER: _unique_tools(base_developer_tools, enhanced_tools_groupings["ai_gen"]), # base_developer_tools includes ai_code_generator, set logic handles dupes
    AgentName.DEVOPS_AGENT: _unique_tools(cloud_dev_tools, security_tools, enhanced_tools_groupings["github_search"]),
}

# Example of how to add a RAG tool to an agent if needed:
# rag_project_tool = get_rag_tool("project_specific_docs") # Assuming "project_specific_docs" was a key in configure_rag_tools
# if rag_project_tool:
#   if AgentName.PROJECT_ARCHITECT in agent_tool_map:
#       agent_tool_map[AgentName.PROJECT_ARCHITECT] = _unique_tools(agent_tool_map[AgentName.PROJECT_ARCHITECT], [rag_project_tool])
#   else:
#       agent_tool_map[AgentName.PROJECT_ARCHITECT] = [rag_project_tool]

print("QREW Agent Tool Map loaded.")

def get_tools_for_agent(agent_name: AgentName) -> list:
    """Returns the list of tools assigned to the given agent name."""
    tools = agent_tool_map.get(agent_name)
    if tools is None:
        print(f"Warning: No tools explicitly mapped for agent '{agent_name.value}'. Returning empty list.")
        return []

    # Filter out any None values that might have resulted from conditional tool initializations
    actual_tools = [tool for tool in tools if tool is not None]

    # Further check: ensure all items in the list are actual tool objects
    # This is mostly a sanity check; the construction should ensure this.
    valid_tools = []
    for tool_item in actual_tools: # Iterate over the filtered list
        if hasattr(tool_item, 'run') and callable(getattr(tool_item, 'run')):
            valid_tools.append(tool_item)
        else:
            # This case should ideally not be hit if all configured tools are valid objects or None
            print(f"Warning: Item '{tool_item}' for agent '{agent_name.value}' is not a valid tool object (missing run method). Skipping.")
    return valid_tools

# Example usage:
# backend_tools = get_tools_for_agent(AgentName.API_CREATOR)
# print(f"Tools for API Creator: {[tool.name for tool in backend_tools if hasattr(tool, 'name')]}")
