from crewai import Agent
from ....llm_config import get_llm_for_agent # Changed import to use llm_config
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "logger_agent_devutils" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier) # Call the correct factory with correct param

logger_agent = Agent(
    role="Logger",
    goal="Implement and manage logging functionality for applications",
    backstory="An agent focused on ensuring comprehensive and effective logging to facilitate debugging, monitoring, and auditing.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.LOGGER_AGENT),
    type="common",
    allow_delegation=False,
    verbose=True
)
