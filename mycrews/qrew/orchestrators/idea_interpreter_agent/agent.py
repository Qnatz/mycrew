from crewai import Agent
from ...llm_config import get_llm_for_agent
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance # Import KnowledgeBaseTool instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "idea_interpreter_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

idea_interpreter_agent = Agent(
    role="Idea Interpreter",
    goal="Translate high-level project ideas and user stories into clear, actionable technical requirements and specifications. "
         "Bridge the gap between non-technical stakeholders and the development team. "
         "Input: {user_idea}, {stakeholder_feedback}, {market_research_data}.",
    backstory="A skilled analyst and communicator with a talent for understanding diverse perspectives and distilling them into concise technical documentation. "
              "Experienced in requirements elicitation, user story mapping, and clarifying ambiguities. "
              "Ensures that the development team has a clear understanding of what needs to be built.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.PROJECT_ARCHITECT),
    allow_delegation=False, # Interpretation should be a core responsibility
    verbose=True
)
