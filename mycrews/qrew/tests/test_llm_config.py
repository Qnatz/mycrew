import os
import unittest
from unittest.mock import patch
from crewai import LLM # Assuming LLM is imported like this in llm_config
from mycrews.qrew.llm_config import get_llm_for_agent, MODEL_BY_AGENT

class TestLLMConfiguration(unittest.TestCase):

    def test_all_agents_use_correct_model_when_api_key_present(self):
        """Test that all agents are configured to use gemini/gemini-2.0-flash-001 when API key is set."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            for agent_identifier in MODEL_BY_AGENT.keys():
                llm_instance = get_llm_for_agent(agent_identifier)
                self.assertIsNotNone(llm_instance, f"LLM instance for {agent_identifier} should not be None when API key is present.")
                self.assertIsInstance(llm_instance, LLM, f"Instance for {agent_identifier} is not an LLM object.")
                self.assertEqual(llm_instance.model, "gemini/gemini-2.0-flash-001",
                                 f"Model for {agent_identifier} should be 'gemini/gemini-2.0-flash-001'. Found '{llm_instance.model}'")

    def test_get_llm_returns_none_when_api_key_missing(self):
        """Test that get_llm_for_agent returns None if GEMINI_API_KEY is not set."""
        # Ensure GEMINI_API_KEY is not in the environment for this test
        original_api_key_value = os.environ.pop("GEMINI_API_KEY", None)

        try:
            for agent_identifier in MODEL_BY_AGENT.keys():
                llm_instance = get_llm_for_agent(agent_identifier)
                self.assertIsNone(llm_instance,
                                  f"LLM instance for {agent_identifier} should be None when API key is missing.")
        finally:
            # Restore the original API key value if it existed
            if original_api_key_value is not None:
                os.environ["GEMINI_API_KEY"] = original_api_key_value

if __name__ == '__main__':
    unittest.main()
