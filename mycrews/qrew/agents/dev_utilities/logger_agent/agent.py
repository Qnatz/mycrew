from crewai import Agent
from ....utils.llm_factory import get_llm # Corrected relative import path
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "logger_agent_devutils" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

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
