from crewai import Agent
from ...llm_config import get_llm_for_agent
# Removed: from mycrews.qrew.tools.knowledge_base_tool import knowledge_base_tool_instance
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName
# from crewAI.qrew.crews.offline_support_crew import OfflineSupportCrew

# Use the agent's role or a unique key for the lookup
agent_identifier = "offline_support_coordinator_agent" # Matching the key in MODEL_BY_AGENT
specific_llm = get_llm_for_agent(agent_identifier)

offline_support_coordinator_agent = Agent(
    role="Offline Support Coordinator",
    goal="Lead and manage the OfflineSupportCrew to implement robust offline capabilities in applications, "
         "including local data storage, data synchronization, and seamless online/offline transitions. "
         "Input: {application_name}, {offline_requirements}, {data_sync_rules}, {target_platforms}.",
    backstory="An experienced technical lead specializing in offline-first application architecture. "
              "Understands the challenges of data consistency, local storage limitations, and network variability. "
              "Guides teams to build applications that provide a reliable user experience, even without an internet connection.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.OFFLINE_COORDINATOR),
    allow_delegation=True, # Can delegate tasks to OfflineSupportCrew
    verbose=True
    # tools=[...] # Tools for testing offline behavior, database management
)
