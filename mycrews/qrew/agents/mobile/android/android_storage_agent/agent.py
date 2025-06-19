from crewai import Agent
from .....utils.llm_factory import get_llm # Corrected relative import path
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "android_storage_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

android_storage_agent = Agent(
    role="Android Storage Manager",
    goal="Manage data storage and retrieval for Android applications, including local databases and file systems",
    backstory="An agent specializing in Android data storage solutions, ensuring data persistence, integrity, and performance on mobile devices.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.MOBILE_STORAGE_AGENT),
    allow_delegation=False,
    verbose=True,
    metadata={"type": "android"}
)
