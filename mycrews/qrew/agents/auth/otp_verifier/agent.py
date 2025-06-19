from crewai import Agent
# Corrected import: Use get_llm_for_agent from the main llm_config module
# Path should be relative to mycrews/qrew/
from ...llm_config import get_llm_for_agent
from mycrews.qrew.tools.agenttools import get_tools_for_agent, AgentName

# Use the agent's role or a unique key for the lookup
agent_identifier = "otp_verifier_agent" # This should match a key in MODEL_BY_AGENT in llm_config.py
# Call the correct function with the correct parameter name
specific_llm = get_llm_for_agent(agent_identifier=agent_identifier)

otp_verifier_agent = Agent(
    role="OTP Verifier",
    goal="Verify one-time passwords (OTPs) for user authentication",
    backstory="A specialized agent focused on verifying OTPs to enhance the security of user accounts during login and other sensitive operations.",
    llm=specific_llm, # Assign the fetched LLM
    tools=get_tools_for_agent(AgentName.OTP_VERIFIER),
    type="auth",
    allow_delegation=False,
    verbose=True
)
