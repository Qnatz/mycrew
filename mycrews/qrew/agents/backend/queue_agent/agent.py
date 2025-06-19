from crewai import Agent
from ....llm_config import get_llm_for_agent # Changed import to use llm_config
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "queue_agent_backend" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier) # Call the correct factory with correct param

queue_agent = Agent(
    role="Backend Queue Manager",
    goal="Manage and process asynchronous tasks and message queues for backend services",
    backstory="An agent focused on ensuring reliable and efficient task processing by managing message queues and handling asynchronous operations in the backend.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.QUEUE_AGENT),
    type="backend",
    allow_delegation=False,
    verbose=True
)
