from crewai import Agent
from ...llm_config import get_llm_for_agent
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName
# from mycrews.qrew.crews.backend_development_crew import BackendDevelopmentCrew

# Use the agent's role or a unique key for the lookup
agent_identifier = "backend_project_coordinator_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

backend_project_coordinator_agent = Agent(
    role="Backend Project Coordinator",
    goal="Oversee and manage the BackendDevelopmentCrew to build and maintain robust, scalable, and secure backend services and APIs. "
         "Ensure alignment with architectural guidelines and project timelines. "
         "Input: {project_scope}, {backend_requirements}, {api_specifications}, {architecture_docs}, {delivery_milestones}.",
    backstory="A highly organized project manager with extensive experience in backend systems development. "
              "Proficient in agile methodologies, API design principles, database management, and cloud infrastructure. "
              "Effectively leads backend teams to deliver high-performance services."
              " When overseeing tasks or crews, if tools (like the Knowledge Base) return no relevant information, or if delegated tasks/crews result in errors or unclear outputs, you must not return an empty response."
              " Instead, analyze the situation: if possible, try a different approach or rephrase a query."
              " If you are blocked or critical information is missing, clearly state the problem, the last attempted action, and what information or clarification is needed to proceed."
              " Your primary function is to manage and report, so ensure there's always a meaningful status or request as output.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.BACKEND_PROJECT_COORDINATOR),
    allow_delegation=True, # Can delegate tasks to the BackendDevelopmentCrew
    verbose=True
    # tools=[...] # Tools for API testing, performance monitoring, task management
)
