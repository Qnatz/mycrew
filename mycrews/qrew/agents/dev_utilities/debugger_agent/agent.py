from crewai import Agent
from ....llm_config import get_llm_for_agent # Changed import to use llm_config
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "debugger_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier) # Call the correct factory with correct param

debugger_agent = Agent(
    role="Debugger",
    goal="Identify, analyze, and resolve bugs and issues in code",
    backstory="A meticulous troubleshooter with a keen eye for detail, adept at finding and fixing software defects.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.DEBUGGER),
    type="common",
    allow_delegation=False,
    verbose=True
)
