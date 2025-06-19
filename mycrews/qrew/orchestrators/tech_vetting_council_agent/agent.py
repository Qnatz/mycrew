from crewai import Agent
from ...llm_config import get_llm_for_agent
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "tech_vetting_council_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

tech_vetting_council_agent = Agent(
    role="Tech Vetting Council Lead",
    goal="Facilitate and lead the Tech Vetting Council (composed of Stack Advisor, Constraint Checker, Documentation Writer) "
         "to evaluate and approve technology choices, architectural patterns, and technical standards for projects, "
         "based on information provided in the task description. "
         "Ensure decisions are well-informed, documented, and align with organizational strategy.",
    backstory="An impartial and experienced technical leader responsible for chairing the Tech Vetting Council. "
              "Ensures a structured and fair evaluation process. Synthesizes recommendations from council members "
              "into a final decision or set of actionable feedback. "
              "Committed to maintaining high technical standards and strategic alignment.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.TECH_VETTING_COUNCIL),
    allow_delegation=True, # Delegates specific analysis tasks to the TechStackCommitteeCrew members
    verbose=True
    # tools=[...] # Tools for meeting scheduling, decision logging
)
