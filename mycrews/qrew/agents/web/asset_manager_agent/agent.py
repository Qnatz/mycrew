from crewai import Agent
from ....llm_config import get_llm_for_agent
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "asset_manager_agent_web" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

asset_manager_agent = Agent(
    role="Web Asset Manager",
    goal="Manage and optimize static assets (images, CSS, JavaScript) for web applications",
    backstory="An agent focused on efficient asset management, ensuring fast loading times and optimal performance for web applications.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.ASSET_MANAGER),
    type="web",
    allow_delegation=False,
    verbose=True
)
