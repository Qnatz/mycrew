from crewai import Agent
# Import the specific instance of the KnowledgeBaseTool
# Removed: from ..tools import knowledge_base_tool_instance
from ..llm_config import get_llm_for_agent
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "taskmaster_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

taskmaster_agent = Agent(
    role="TaskMaster General Coordinator",
    goal="Determine if a user request pertains to a new or existing project. If new, generate a unique and descriptive project name. "
         "Receive, interpret, and decompose high-level user requests or project goals into a structured plan. "
         "Delegate major components of this plan to appropriate orchestrator agents (like ProjectArchitect, IdeaInterpreter, ExecutionManager) "
         "or specialized Lead Agents for execution. Ensure a clear path from initial request to final delivery. "
         "Input: {user_request}, {project_goal_statement}, {priority_level}, {expected_outcome_description}.",
    backstory="The central intelligence of the Qrew system, responsible for initial request processing and strategic delegation. "
              "The TaskMaster doesn't do the work itself but ensures that the right agents and crews are "
              "mobilized to achieve the user's objectives. It maintains a high-level view of ongoing projects "
              "and ensures that new requests are properly initiated and routed.",
    tools=get_tools_for_agent(AgentName.EXECUTION_MANAGER),
    llm=specific_llm, # Assign the fetched LLM
    allow_delegation=True,
    verbose=True
)
