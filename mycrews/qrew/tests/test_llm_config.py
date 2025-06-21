import os
import unittest
from unittest.mock import patch, MagicMock
from crewai import LLM
# Import items from the refactored llm_config
from mycrews.qrew.llm_config import (
    get_llm_for_agent,
    MODEL_BY_AGENT,
    llm_initialization_statuses, # To check status updates
    get_api_key_for_model,
    CFG_OPENAI_GPT4O_DEFAULT, # Example OpenAI config
    CFG_OPENAI_GPT4O_DETERMINISTIC, # Added missing import
    CFG_GEMINI_1_5_FLASH_DEFAULT # Example Gemini config
)

# Helper to reset global status list for each test
def reset_llm_init_statuses():
    llm_initialization_statuses.clear()

class TestLLMConfiguration(unittest.TestCase):

    def setUp(self):
        reset_llm_init_statuses()
        # Keep a copy of the original environment to restore after each test
        self.original_environ = os.environ.copy()

    def tearDown(self):
        # Restore environment variables
        os.environ.clear()
        os.environ.update(self.original_environ)
        reset_llm_init_statuses()

    @patch('mycrews.qrew.llm_config.LLM') # Patch the LLM class used in llm_config
    def test_get_llm_for_configured_agents_with_api_keys(self, MockLLM):
        """
        Test that get_llm_for_agent returns a correctly configured LLM
        for agents defined in MODEL_BY_AGENT when their respective API keys are present.
        """
        # Configure the MockLLM to store passed args
        mock_llm_instances = []
        def side_effect_llm(*args, **kwargs):
            instance = MagicMock(spec=LLM)
            instance.model = kwargs.get('model')
            instance.api_key = kwargs.get('api_key')
            # Store other relevant params if needed for assertion
            mock_llm_instances.append(instance)
            return instance
        MockLLM.side_effect = side_effect_llm

        # Test data: agent_id, expected_env_var, expected_api_key_value, expected_model_prefix
        test_scenarios = [
            ("idea_interpreter_agent", "GEMINI_API_KEY", "gemini_test_key", "gemini"),
            ("openai_powered_summarizer", "OPENAI_API_KEY", "openai_test_key", "gpt-4o"), # Assuming gpt-4o is primary for this
        ]

        for agent_id, env_var, api_key_val, model_prefix_check in test_scenarios:
            if agent_id not in MODEL_BY_AGENT:
                # This could happen if 'openai_powered_summarizer' isn't added to MODEL_BY_AGENT yet.
                # For now, let's assume it will be. If not, this test part for it will fail or need adjustment.
                print(f"Skipping test for {agent_id} as it's not in MODEL_BY_AGENT")
                continue

            reset_llm_init_statuses() # Reset for each agent scenario
            mock_llm_instances.clear() # Clear instances for each agent

            expected_model_config_list = MODEL_BY_AGENT[agent_id]
            self.assertTrue(len(expected_model_config_list) > 0, f"Config list for {agent_id} is empty.")
            expected_primary_model_str = expected_model_config_list[0]["model"]

            with patch.dict(os.environ, {env_var: api_key_val}, clear=True): # clear=True ensures only this key is set
                llm_instance = get_llm_for_agent(agent_id)

                self.assertIsNotNone(llm_instance, f"LLM for {agent_id} should be created with {env_var}.")
                self.assertEqual(MockLLM.call_count, 1) # Ensure LLM was called once for this success path

                # Check the instance returned by get_llm_for_agent
                self.assertEqual(llm_instance.model, expected_primary_model_str)
                self.assertEqual(llm_instance.api_key, api_key_val) # Check if correct API key was used by the mock

                # Check initialization status
                self.assertTrue(any(status[0].startswith(expected_primary_model_str) and status[1] for status in llm_initialization_statuses),
                                f"Success status for {expected_primary_model_str} for agent {agent_id} not found.")
            MockLLM.reset_mock() # Reset mock for next iteration

    @patch('mycrews.qrew.llm_config.LLM')
    def test_get_llm_api_key_missing(self, MockLLM):
        """Test that get_llm_for_agent returns None and logs status if relevant API key is missing."""
        # Scenario 1: Gemini model, GEMINI_API_KEY missing
        agent_id_gemini = "idea_interpreter_agent" # Assumes this uses a Gemini model first
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None) # Ensure no interference

        llm_instance_gemini = get_llm_for_agent(agent_id_gemini)
        self.assertIsNone(llm_instance_gemini, f"LLM for {agent_id_gemini} should be None when GEMINI_API_KEY is missing.")
        self.assertTrue(any("API_KEY_MISSING_FOR_MODEL_gemini" in status[0] and not status[1] for status in llm_initialization_statuses),
                        "Missing Gemini API key status not logged correctly.")
        MockLLM.assert_not_called() # LLM constructor should not be called if key is missing for all models in list

        reset_llm_init_statuses()
        MockLLM.reset_mock()

        # Scenario 2: OpenAI model, OPENAI_API_KEY missing
        agent_id_openai = "openai_powered_summarizer"

        original_openai_summarizer_config = MODEL_BY_AGENT.get(agent_id_openai)
        # For this specific test, ensure the agent only attempts to use OpenAI models
        MODEL_BY_AGENT[agent_id_openai] = [CFG_OPENAI_GPT4O_DETERMINISTIC]

        os.environ.pop("OPENAI_API_KEY", None)
        os.environ["GEMINI_API_KEY"] = "dummy_gemini_key" # Gemini key present, but OpenAI key missing

        llm_instance_openai = get_llm_for_agent(agent_id_openai)

        # Restore original config for other tests
        if original_openai_summarizer_config is not None:
            MODEL_BY_AGENT[agent_id_openai] = original_openai_summarizer_config
        elif agent_id_openai in MODEL_BY_AGENT: # If it was added just for this test scenario (unlikely given current setup)
            del MODEL_BY_AGENT[agent_id_openai]

        self.assertIsNone(llm_instance_openai, f"LLM for {agent_id_openai} should be None when OPENAI_API_KEY is missing and no fallback is intended for this test.")
        # Check if the status log indicates a missing key for an OpenAI model
        self.assertTrue(any("API_KEY_MISSING_FOR_MODEL_gpt" in status[0] and not status[1] for status in llm_initialization_statuses),
                        "Missing OpenAI API key status not logged correctly for summarizer.")
        MockLLM.assert_not_called()

    @patch('mycrews.qrew.llm_config.LLM')
    def test_get_llm_uses_default_agent_llm_on_missing_agent_config(self, MockLLM):
        """Test fallback to default_agent_llm if a specific agent config is missing."""
        MockLLM.return_value = MagicMock(spec=LLM, model=MODEL_BY_AGENT["default_agent_llm"][0]["model"])

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key", "OPENAI_API_KEY": "test_key_openai"}, clear=True):
            llm_instance = get_llm_for_agent("non_existent_agent")
            self.assertIsNotNone(llm_instance)
            # Check if it used the first model from the "default_agent_llm" list
            expected_model = MODEL_BY_AGENT["default_agent_llm"][0]["model"]
            self.assertEqual(llm_instance.model, expected_model)
            # Check llm_initialization_statuses for the default model
            self.assertTrue(any(status[0].startswith(expected_model) and status[1] for status in llm_initialization_statuses))

    @patch('mycrews.qrew.llm_config.LLM')
    def test_get_llm_fallback_within_model_list(self, MockLLM):
        """Test that get_llm_for_agent tries the next model in the list if the first fails."""
        agent_id = "test_fallback_agent"
        MODEL_BY_AGENT[agent_id] = [
            {"model": "gemini/fail-model", "temperature": 0.1}, # This will fail
            CFG_GEMINI_1_5_FLASH_DEFAULT # This should succeed
        ]

        # Mock LLM: first call raises exception, second call succeeds
        mock_success_llm = MagicMock(spec=LLM, model=CFG_GEMINI_1_5_FLASH_DEFAULT["model"])
        MockLLM.side_effect = [Exception("Failed to init fail-model"), mock_success_llm]

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            llm_instance = get_llm_for_agent(agent_id)
            self.assertIsNotNone(llm_instance)
            self.assertEqual(llm_instance.model, CFG_GEMINI_1_5_FLASH_DEFAULT["model"])
            self.assertEqual(MockLLM.call_count, 2) # Called for fail-model and then for success-model

            # Check statuses
            self.assertTrue(any("gemini/fail-model (init_exception" in status[0] and not status[1] for status in llm_initialization_statuses))
            self.assertTrue(any(status[0].startswith(CFG_GEMINI_1_5_FLASH_DEFAULT["model"]) and status[1] for status in llm_initialization_statuses))

        del MODEL_BY_AGENT[agent_id] # Clean up

    def test_get_api_key_for_model_utility(self):
        """Test the get_api_key_for_model utility function."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "gem_key", "OPENAI_API_KEY": "oai_key"}, clear=True):
            self.assertEqual(get_api_key_for_model("gemini/gemini-1.5-pro"), "gem_key")
            self.assertEqual(get_api_key_for_model("gpt-4o"), "oai_key")
            self.assertEqual(get_api_key_for_model("openai/gpt-3.5-turbo"), "oai_key")
            self.assertIsNone(get_api_key_for_model("anthropic/claude-2")) # Assuming ANTHROPIC_API_KEY is not set
            self.assertIsNone(get_api_key_for_model("unknown/model"))

        with patch.dict(os.environ, {}, clear=True): # No keys set
            self.assertIsNone(get_api_key_for_model("gemini/gemini-1.5-pro"))
            self.assertIsNone(get_api_key_for_model("gpt-4o"))


if __name__ == '__main__':
    unittest.main()
