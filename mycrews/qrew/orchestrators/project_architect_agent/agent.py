from crewai import Agent
from ...llm_config import get_llm_for_agent
from ...tools.custom_agent_tools import CustomDelegateWorkTool, CustomAskQuestionTool
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName
# from crewAI.qrew.tools.file_io_tool import FileIOTool # Example if tools are ready

# Use the agent's role or a unique key for the lookup
agent_identifier = "project_architect_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

# Instantiate custom tools
custom_delegate_tool = CustomDelegateWorkTool()
custom_ask_question_tool = CustomAskQuestionTool()

# Example: If FileIOTool or other tools are also needed by this agent
# from ....tools.file_io_tool import FileIOTool # Make sure this path is correct if used
# file_io_tool = FileIOTool()
# agent_tools = [custom_delegate_tool, custom_ask_question_tool, file_io_tool]

# Get tools from centralized mapping
mapped_tools = get_tools_for_agent(AgentName.PROJECT_ARCHITECT)

# Combine with essential custom tools, ensuring custom tools are prioritized
# and duplicates (by reference or unique name) are handled.
essential_custom_tools = [custom_delegate_tool, custom_ask_question_tool]
final_tools = list(essential_custom_tools) # Start with custom tools

# Add tools from the map, avoiding duplicates if they were already in essential_custom_tools (e.g. by name if applicable)
# Simple by-reference check here for now:
for tool in mapped_tools:
    is_already_added = False
    for existing_tool in final_tools:
        if tool is existing_tool: # Check by reference
            is_already_added = True
            break
        # Optionally, if tools have a .name attribute that's unique:
        # if hasattr(tool, 'name') and hasattr(existing_tool, 'name') and tool.name == existing_tool.name:
        #     is_already_added = True
        #     break
    if not is_already_added:
        final_tools.append(tool)

project_architect_agent = Agent(
    role="Project Architect",
    goal="Design a robust and scalable software architecture based on project requirements, constraints, and technical vision, "
         "all detailed in the task description. Ensure the architecture aligns with best practices.",
    backstory="A seasoned software architect with extensive experience in designing complex systems across various domains. "
              "Known for creating elegant, maintainable, and future-proof architectures. "
              "Possesses deep knowledge of design patterns, system integration, and technology stacks.",
    llm=specific_llm, # Assign the fetched LLM
    tools=final_tools, # Use the combined list
    allow_delegation=True, # This will be used by defining sub-tasks, not by the agent itself using a tool.
    verbose=True
)
