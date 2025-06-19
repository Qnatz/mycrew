from crewai import Agent
from ....utils.llm_factory import get_llm # Corrected relative import path
# Removed: from ....tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "api_creator_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm(agent_identifier=agent_identifier) # Call the factory

api_creator_agent = Agent(
    role="Backend API Creator",
    goal="Design, develop, and maintain robust and scalable backend APIs",
    backstory="A skilled backend developer specializing in API creation, ensuring seamless data exchange and application functionality."
              " This developer frequently consults the project's knowledge base to adhere to established API design guidelines, leverage existing interface definitions, and ensure new APIs integrate smoothly with the overall system architecture."
              " If the knowledge base does not provide the specific information you need after a reasonable attempt, you should then rely on your general backend development knowledge and best practices to design and develop the API."
              " If you are still blocked due to lack of critical information, clearly state what information is missing.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.API_CREATOR),
    knowledge_sources=[], # Added as per instruction
    type="backend",
    allow_delegation=False,
    verbose=True
)
