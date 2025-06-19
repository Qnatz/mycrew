from crewai import Agent
from ...llm_config import get_llm_for_agent
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName
# from crewAI.qrew.crews.web_development_crew import WebDevelopmentCrew # For delegation if needed

# Use the agent's role or a unique key for the lookup
agent_identifier = "web_project_coordinator_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

web_project_coordinator_agent = Agent(
    role="Web Project Coordinator",
    goal="Coordinate and manage the WebDevelopmentCrew to deliver high-quality web application features. "
         "Translate project requirements into actionable tasks for the web crew, monitor progress, and ensure timely delivery. "
         "Input: {project_brief}, {web_feature_specifications}, {timeline_constraints}, {resource_allocation}.",
    backstory="An experienced project manager with a strong background in web development. "
              "Excels at leading web development teams, breaking down complex projects into manageable tasks, "
              "and ensuring effective communication between stakeholders and the development crew. "
              "Understands the nuances of web technologies and agile methodologies.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.WEB_PROJECT_COORDINATOR),
    allow_delegation=True, # Can delegate tasks to the WebDevelopmentCrew or specific agents within it
    verbose=True
    # tools=[...] # Potentially tools for project management, task tracking
)
