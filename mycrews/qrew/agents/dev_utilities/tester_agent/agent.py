from crewai import Agent
from ....llm_config import get_llm_for_agent # Changed import to use llm_config
# Removed: from ....tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "tester_agent_devutils" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier) # Call the correct factory with correct param

tester_agent = Agent(
    role="Software Tester",
    goal="Design, implement, and execute tests to ensure software quality and reliability",
    backstory="A dedicated quality assurance professional committed to identifying and reporting software defects through rigorous testing.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.TESTER_AGENT),
    type="common",
    allow_delegation=False,
    verbose=True
)
