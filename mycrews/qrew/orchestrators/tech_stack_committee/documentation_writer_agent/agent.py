from crewai import Agent
from ....llm_config import get_llm_for_agent # Corrected relative import path
# Removed: from ....tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName
# from crewAI.qrew.tools.file_io_tool import FileIOTool # Example

# Use the agent's role or a unique key for the lookup
agent_identifier = "documentation_writer_agent_tech_committee" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

documentation_writer_agent = Agent(
    role="Tech Stack Documentation Writer",
    goal="Create clear, concise, and comprehensive documentation for all approved technology stack decisions, architectural guidelines, and technical standards. "
         "Input: {approved_tech_stack}, {architectural_diagrams}, {decision_rationale}, {style_guide}.",
    backstory="A proficient technical writer specializing in documenting complex technical information for development teams. "
              "Ensures that all decisions and standards are well-understood and easily accessible. "
              "Focuses on accuracy, clarity, and maintainability of documentation.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.CODE_WRITER), # Mapped to CODE_WRITER
    type="common",
    allow_delegation=False,
    verbose=True
)
