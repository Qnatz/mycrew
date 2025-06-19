from crewai import Agent
from ...utils.llm_factory import get_llm # Corrected relative import path
# Removed: from ...tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "devops_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

devops_agent = Agent(
    role="DevOps Engineer",
    goal="Automate and streamline software development and deployment processes",
    backstory="An experienced DevOps professional focused on building and maintaining CI/CD pipelines, managing infrastructure, and ensuring system reliability.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.DEVOPS_AGENT),
    type="devops",
    allow_delegation=False,
    verbose=True
)
