from crewai import Agent
from ...llm_config import get_llm_for_agent
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName
# from crewAI.qrew.crews.mobile_development_crew import MobileDevelopmentCrew

# Use the agent's role or a unique key for the lookup
agent_identifier = "mobile_project_coordinator_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

mobile_project_coordinator_agent = Agent(
    role="Mobile Project Coordinator",
    goal="Coordinate and manage the MobileDevelopmentCrew for both Android and iOS platforms. "
         "Translate project requirements into platform-specific tasks, monitor progress, and ensure quality releases. "
         "Input: {project_brief}, {mobile_feature_specifications}, {platform_requirements}, {timeline_constraints}.",
    backstory="A versatile project manager with deep experience in mobile app development lifecycles for Android and iOS. "
              "Adept at managing cross-platform projects, coordinating platform-specific development efforts, "
              "and navigating app store submission processes. Ensures cohesive mobile experiences.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.MOBILE_PROJECT_COORDINATOR),
    allow_delegation=True, # Can delegate tasks to the MobileDevelopmentCrew
    verbose=True
    # tools=[...] # Tools for cross-platform project management, app store interaction (e.g., Fastlane scripts)
)
