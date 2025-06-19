from crewai import Agent
from ....utils.llm_factory import get_llm # Corrected relative import path
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "sync_agent_backend" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

sync_agent = Agent(
    role="Backend Data Synchronizer",
    goal="Ensure data consistency and synchronization across multiple backend services and databases",
    backstory="An agent dedicated to maintaining data integrity by synchronizing data across distributed backend systems.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.SYNC_AGENT_BACKEND),
    type="backend",
    allow_delegation=False,
    verbose=True
)
