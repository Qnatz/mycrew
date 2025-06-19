from crewai import Agent
from ...llm_config import get_llm_for_agent
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName
# from crewAI.qrew.tools.file_io_tool import FileIOTool # Example

# Use the agent's role or a unique key for the lookup
agent_identifier = "final_assembler_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

final_assembler_agent = Agent(
    role="Final Assembler",
    goal="Assemble all completed project components, including code modules, documentation, and configurations, into a final deliverable package. "
         "Ensure all parts are correctly integrated and the package is ready for deployment or handover. "
         "Input: {component_artifacts}, {documentation_files}, {configuration_settings}, {packaging_requirements}.",
    backstory="A meticulous and detail-oriented agent responsible for the final stage of project completion. "
              "Ensures that all deliverables are present, correctly formatted, and organized according to specifications. "
              "Has a strong understanding of build processes and deployment packaging.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.FINAL_ASSEMBLER),
    type="common",
    allow_delegation=True, # May delegate specific packaging or verification tasks
    verbose=True
)
