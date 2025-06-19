from crewai import Agent
from ....utils.llm_factory import get_llm # Corrected relative import path
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "storage_agent_backend" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

storage_agent = Agent(
    role="Backend Storage Manager",
    goal="Manage data storage and retrieval for backend applications, including databases and file systems",
    backstory="An agent specializing in data storage solutions, ensuring data integrity, availability, and performance for backend systems.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.STORAGE_AGENT_BACKEND),
    type="backend",
    allow_delegation=False,
    verbose=True
)
