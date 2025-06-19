from crewai import Agent
from ...llm_config import get_llm_for_agent
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName
# from crewAI.qrew.crews.devops_crew import DevOpsCrew

# Use the agent's role or a unique key for the lookup
agent_identifier = "devops_and_integration_coordinator_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

devops_and_integration_coordinator_agent = Agent(
    role="DevOps and Integration Coordinator",
    goal="Streamline and manage DevOps processes, including CI/CD, infrastructure, and monitoring, through the DevOpsCrew. "
         "Additionally, coordinate the integration of different services and components across the project. "
         "Input: {project_name}, {devops_requirements}, {integration_points_list}, {release_schedule}.",
    backstory="A seasoned engineer with strong experience in both DevOps practices and system integration. "
              "Expert in automating software delivery pipelines, managing cloud infrastructure, and ensuring seamless interaction "
              "between various microservices and application components. Bridges the gap between development and operations.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.DEVOPS_COORDINATOR),
    allow_delegation=True, # Can delegate tasks to DevOpsCrew or other relevant agents
    verbose=True
    # tools=[...] # Tools for CI/CD management, infrastructure monitoring, API contract testing
)
