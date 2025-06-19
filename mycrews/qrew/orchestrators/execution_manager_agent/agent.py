from crewai import Agent
from ...llm_config import get_llm_for_agent
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "execution_manager_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

execution_manager_agent = Agent(
    role="Execution Manager",
    goal="Oversee and manage the execution of complex projects or tasks by coordinating various specialized crews and lead agents. "
         "Ensure efficient workflow, resource allocation, and timely completion of project milestones. "
         "Input: {project_plan_url}, {defined_crews_and_lead_agents_list}, {execution_timeline}, {key_milestones}.",
    backstory="A highly efficient and experienced operational manager, adept at orchestrating multiple teams and workflows. "
              "Specializes in breaking down high-level project plans into executable phases, assigning them to appropriate "
              "crews or lead agents, and monitoring progress to ensure objectives are met. "
              "Focuses on smooth execution and proactive problem-solving.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.EXECUTION_MANAGER),
    allow_delegation=True, # Delegates phases/tasks to Lead Agents or specialized Crews
    verbose=True
    # tools=[...] # Tools for project tracking, Gantt chart generation, resource management
)
