from crewai import Agent
from ....utils.llm_factory import get_llm # Corrected relative import path
# Removed: from mycrews.qrew.tools.knowledge_base_tool import KnowledgeBaseTool
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "data_model_agent_backend" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

data_model_agent = Agent(
    role="Backend Data Modeler",
    goal="Design and maintain data models for backend databases and applications",
    backstory="A data-centric agent specializing in creating efficient and scalable data models to support backend application requirements."
              " This modeler leverages the project's knowledge base to understand existing data structures, apply established modeling conventions, and ensure new schemas are consistent and well-integrated.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.DATA_MODEL_AGENT),
    knowledge_sources=[], # Added as per instruction
    type="backend",
    allow_delegation=False,
    verbose=True
)
