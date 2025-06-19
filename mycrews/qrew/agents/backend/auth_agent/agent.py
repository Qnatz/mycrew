from crewai import Agent
from ....llm_config import get_llm_for_agent # Changed import to use llm_config
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "auth_agent_backend" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier) # Call the correct factory with correct param

auth_agent = Agent(
    role="Backend Authentication Agent",
    goal="Implement and manage authentication and authorization logic for backend services",
    backstory="A security-focused agent responsible for safeguarding backend systems by implementing and enforcing authentication and authorization policies.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.AUTH_AGENT),
    type="backend",
    allow_delegation=False,
    verbose=True
)
