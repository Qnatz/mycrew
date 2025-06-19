from crewai import Agent
from ....utils.llm_factory import get_llm # Corrected relative import path
# Removed: from ....tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "tester_agent_devutils" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

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
