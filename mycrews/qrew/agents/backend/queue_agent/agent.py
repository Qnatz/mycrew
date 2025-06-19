from crewai import Agent
from ....utils.llm_factory import get_llm # Corrected relative import path
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "queue_agent_backend" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

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
