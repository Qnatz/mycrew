from crewai import Agent
from ....llm_config import get_llm_for_agent
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "sync_agent_offline" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

offline_sync_agent = Agent(
    role="Offline Data Synchronizer",
    goal="Manage data synchronization between local storage and remote servers when an internet connection is available",
    backstory="An agent dedicated to ensuring data consistency between offline local storage and online backend systems by managing data synchronization processes.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.MOBILE_API_CLIENT_AGENT),
    type="offline",
    allow_delegation=False,
    verbose=True
)
