from crewai import Agent
from ....llm_config import get_llm_for_agent # Changed import to use llm_config
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "config_agent_backend" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier) # Call the correct factory with correct param

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
