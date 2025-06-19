from crewai import Agent
from ....llm_config import get_llm_for_agent
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "local_storage_agent_offline" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

local_storage_agent = Agent(
    role="Local Storage Manager",
    goal="Manage local data storage for offline application functionality",
    backstory="An agent specializing in local data persistence, enabling applications to function effectively even without an internet connection.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.MOBILE_STORAGE_AGENT),
    type="offline",
    allow_delegation=False,
    verbose=True
)
