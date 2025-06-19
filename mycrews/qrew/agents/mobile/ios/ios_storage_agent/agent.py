from crewai import Agent
from .....llm_config import get_llm_for_agent # Changed import to use llm_config
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "ios_storage_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier) # Call the correct factory with correct param

ios_storage_agent = Agent(
    role="iOS Storage Manager",
    goal="Manage data storage and retrieval for iOS applications, including local databases and file systems",
    backstory="An agent specializing in iOS data storage solutions, ensuring data persistence, integrity, and performance on mobile devices.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.MOBILE_STORAGE_AGENT),
    allow_delegation=False,
    verbose=True,
    metadata={"type": "ios"}
)
