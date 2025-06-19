from crewai import Agent
from ...llm_config import get_llm_for_agent # Path relative to mycrews/qrew/orchestrators/software_engineer_agent/agent.py
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

agent_identifier = "software_engineer_agent"
specific_llm = get_llm_for_agent(agent_identifier)

software_engineer_agent = Agent(
    role="Software Engineer",
    goal="To meticulously design, develop, and implement software components and systems based on detailed architectural plans and technical specifications. "
         "This includes creating database schemas, defining API contracts, structuring UI components, and writing robust code.",
    backstory="A versatile and highly skilled software engineer with a broad understanding of different technologies and programming paradigms. "
              "Adept at translating architectural blueprints into functional and efficient code, with a strong focus on quality, maintainability, and scalability. "
              "Comfortable working across the full stack and on various aspects of software development, from backend logic to frontend interfaces.",
    llm=specific_llm,
    tools=get_tools_for_agent(AgentName.SOFTWARE_ENGINEER),
    allow_delegation=False,
    verbose=True
)

# Example of how to import (for comments or other files):
# from mycrews.qrew.orchestrators.software_engineer_agent.agent import software_engineer_agent
