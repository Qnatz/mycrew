from crewai import Agent
from ....llm_config import get_llm_for_agent # Further corrected relative import path
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName
# from crewAI.qrew.tools.network_request_tool import NetworkRequestTool # Example for research

# Use the agent's role or a unique key for the lookup
agent_identifier = "stack_advisor_agent_tech_committee" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

stack_advisor_agent = Agent(
    role="Tech Stack Advisor",
    goal="Recommend the optimal technology stack (frameworks, languages, databases, tools) "
         "for a given project based on its requirements, constraints, and long-term goals, "
         "all of which are detailed in the task description.",
    backstory="An experienced technology consultant with a broad understanding of the current tech landscape, "
              "including emerging technologies and industry best practices. Adept at evaluating trade-offs "
              "between different technologies and aligning recommendations with business objectives. "
              "Provides well-researched and justified advice.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.PROJECT_ARCHITECT), # Mapped to PROJECT_ARCHITECT
    allow_delegation=False, # Core advisory role
    verbose=True
)
