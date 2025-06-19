from crewai import Agent
from ...llm_config import get_llm_for_agent # Point to the main llm_config.py
# Removed: from ....tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "auth_coordinator_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier) # Use correct param name

auth_coordinator_agent = Agent(
    role="Authentication Coordinator",
    goal="Manage user authentication and authorization processes",
    backstory="An experienced agent responsible for overseeing all aspects of user authentication and authorization, ensuring secure and efficient access control.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.AUTH_COORDINATOR),
    type="auth",
    allow_delegation=False,
    verbose=True
)
