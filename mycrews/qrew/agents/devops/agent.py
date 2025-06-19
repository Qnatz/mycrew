from crewai import Agent
from ...llm_config import get_llm_for_agent # Changed import to use llm_config
# Removed: from ...tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "devops_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier) # Call the correct factory with correct param

devops_agent = Agent(
    role="DevOps Engineer",
    goal="Automate and streamline software development and deployment processes",
    backstory="An experienced DevOps professional focused on building and maintaining CI/CD pipelines, managing infrastructure, and ensuring system reliability.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.DEVOPS_AGENT),
    type="devops",
    allow_delegation=False,
    verbose=True
)
