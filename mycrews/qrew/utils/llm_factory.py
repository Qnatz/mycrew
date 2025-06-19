# mycrews/qrew/utils/llm_factory.py
from typing import Optional

# Assuming crewai.LLM is the correct type. If it's different, this should be adjusted.
# e.g., from langchain_core.language_models import BaseLanguageModel as LLM_TYPE
# For now, using crewai.LLM based on its usage in llm_config.py
from crewai import LLM as CrewLLMType # Alias to avoid confusion if LLM is also a var name

# Import the function from the existing llm_config.py
# The path is relative from mycrews/qrew/utils/ to mycrews/qrew/
from ..llm_config import get_llm_for_agent as get_llm_for_agent_from_config

# Default agent identifier to use if no specific one is provided to the factory.
# This aligns with how llm_config.py fetches a default.
DEFAULT_FACTORY_AGENT_ID = "default_agent_llm"

def get_llm(
    agent_identifier: Optional[str] = None,
    max_tokens_override: Optional[int] = None,
    temperature_override: Optional[float] = None
) -> Optional[CrewLLMType]:
    """
    Factory function to get a configured LLM instance for agents.
    It leverages the existing llm_config.py module for model selection and configuration.

    Args:
        agent_identifier: Optional. The specific identifier for the agent
                          (e.g., 'code_writer_agent'). If None, uses a default
                          identifier ('default_agent_llm') to fetch a generic agent LLM.
        max_tokens_override: Optional. If provided, this value is intended to
                             override the max_tokens setting from llm_config.py.
                             (Note: Current implementation primarily logs a warning
                             as direct override post-selection is complex with llm_config.py's
                             current structure. Relies on llm_config.py for actual settings.)
        temperature_override: Optional. Similar to max_tokens_override for temperature.
                              (Note: Same limitation as max_tokens_override.)

    Returns:
        A crewai.LLM instance as configured by llm_config.py, or None if unavailable.
    """
    target_agent_id = agent_identifier if agent_identifier is not None else DEFAULT_FACTORY_AGENT_ID

    if max_tokens_override is not None or temperature_override is not None:
        # This warning is important as the current factory doesn't enforce these overrides
        # over the complex logic in llm_config.py.
        print(
            f"[LLMFactory] INFO: max_tokens_override ({max_tokens_override}) or "
            f"temperature_override ({temperature_override}) was provided. "
            f"However, the factory currently relies on llm_config.py for detailed "
            f"model configuration based on agent_identifier ('{target_agent_id}'). "
            f"These overrides are not applied in this version."
        )
        # Future TODO: If overrides are essential, this factory would need to:
        # 1. Fetch a base model name (e.g., the first from the agent's list in llm_config).
        # 2. Create a new LLM instance using that model name but with the overridden params.
        # This would bypass some of the fallback logic in get_llm_for_agent_from_config.

    # Call the existing function from llm_config.py
    llm_instance = get_llm_for_agent_from_config(target_agent_id)

    # The llm_instance returned by get_llm_for_agent_from_config is already configured.
    # Modifying its attributes (like llm_instance.max_tokens) post-initialization
    # is generally not how these LLM objects are designed to be used (they often
    # take config at __init__).
    # Thus, the factory, for now, acts as a centralized access point and pass-through
    # to the sophisticated logic in llm_config.py.

    return llm_instance

# Example of how an agent might use this factory:
# from mycrews.qrew.utils.llm_factory import get_llm
#
# class MyAgent:
#     def __init__(self, agent_id: str):
#         self.llm = get_llm(agent_identifier=agent_id)
#         if not self.llm:
#             raise ValueError(f"Could not initialize LLM for agent {agent_id}")
#
# my_specific_agent_llm = get_llm("code_writer_agent")
# default_agent_llm = get_llm() # Uses "default_agent_llm"
