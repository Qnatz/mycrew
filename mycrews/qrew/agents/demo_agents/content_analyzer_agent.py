# mycrews/qrew/agents/demo_agents/content_analyzer_agent.py
from crewai import Agent
from ....utils.llm_factory import get_llm # Relative path from demo_agents to utils

content_analyzer_agent = Agent(
    role="Content Analyzer",
    goal="Analyze and summarize text snippets accurately.",
    backstory="An expert in quickly understanding and summarizing textual content.",
    llm=get_llm("default_agent_llm"), # Use the factory
    tools=[],
    allow_delegation=False,
    verbose=True
)
