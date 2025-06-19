import unittest
from mycrews.qrew.utils.llm_factory import get_llm

class TestLLMFactory(unittest.TestCase):

    def test_get_llm_import(self):
        """Test that get_llm can be imported and called."""
        try:
            # Attempt to get an LLM for a known agent type
            llm = get_llm("default")
            self.assertIsNotNone(llm, "LLM should not be None for 'default' type")
            self.assertEqual(llm, "local-onnx", "LLM for 'default' should be 'local-onnx'")
        except ImportError:
            self.fail("Failed to import get_llm from llm_factory")
        except ValueError as e:
            self.fail(f"get_llm raised ValueError unexpectedly: {e}")

    def test_get_llm_unknown_type(self):
        """Test that get_llm raises ValueError for an unknown agent type."""
        with self.assertRaises(ValueError) as context:
            get_llm("unknown_agent_type")
        self.assertTrue("No LLM defined for agent type: unknown_agent_type" in str(context.exception))

if __name__ == '__main__':
    unittest.main()
