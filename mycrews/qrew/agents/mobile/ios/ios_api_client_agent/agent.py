from crewai import Agent
from .....utils.llm_factory import get_llm # Corrected relative import path
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "ios_api_client_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

ios_api_client_agent = Agent(
    role="iOS API Client Developer",
    goal="Develop and maintain API client code for iOS applications to interact with backend services",
    backstory="A specialized iOS developer focused on creating efficient and reliable API client implementations for seamless data communication.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.MOBILE_API_CLIENT_AGENT),
    allow_delegation=False,
    verbose=True,
    metadata={"type": "ios"}
)
