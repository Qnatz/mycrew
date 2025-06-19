from crewai import Agent
from ....utils.llm_factory import get_llm # Corrected relative import path
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "config_agent_backend" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

config_agent = Agent(
    role="Backend Configuration Manager",
    goal="Manage and maintain configuration settings for backend applications and services",
    backstory="An organized agent dedicated to ensuring backend systems are correctly configured for optimal performance, security, and reliability.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.CONFIG_AGENT),
    type="backend",
    allow_delegation=False,
    verbose=True
)
