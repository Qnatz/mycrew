import unittest
import os
import shutil
import numpy as np

# Assuming the tool paths are correctly discoverable from the test execution context
from mycrews.qrew.tools.knowledge_base_tool import KnowledgeBaseTool

# Define a test-specific path for the ONNX ObjectBox store
TEST_DB_PATH = "test_db_onnx_kb_tool"

# Helper to get an embedder instance (KnowledgeBaseTool itself for its _embed_text)
# This ensures we use the same ONNX model and tokenizer as the tool.
# Paths for ONNX model/tokenizer are taken from KnowledgeBaseTool defaults.
embedder_tool_for_tests = None

def get_embedder_for_tests():
    global embedder_tool_for_tests
    if embedder_tool_for_tests is None:
        try:
            embedder_tool_for_tests = KnowledgeBaseTool() # Uses default model paths
            if not embedder_tool_for_tests.embedding_session or not embedder_tool_for_tests.tokenizer:
                raise RuntimeError("Failed to initialize ONNX model/tokenizer in embedder_tool_for_tests.")
        except Exception as e:
            print(f"CRITICAL TEST SETUP ERROR: Could not initialize KnowledgeBaseTool for embedding: {e}")
            raise RuntimeError(f"CRITICAL TEST SETUP ERROR: Could not initialize KnowledgeBaseTool for embedding: {e}")
    return embedder_tool_for_tests

class TestKnowledgeBaseToolWithONNX(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up for all tests in this class."""
        if os.path.exists(TEST_DB_PATH):
            ONNXObjectBoxMemory.remove_store_files(TEST_DB_PATH)

        # The constructor of ONNXObjectBoxMemory creates the directory.
        cls.memory = ONNXObjectBoxMemory(store_path=TEST_DB_PATH) # Changed from store_path_override

        try:
            embedder = get_embedder_for_tests()
        except RuntimeError as e:
            cls.embedder_failed = True
            print(f"Skipping data population due to embedder failure: {e}")
            return
        cls.embedder_failed = False

        cls.sample_data = [
            ("CrewAI Agent", "CrewAI is a framework for orchestrating role-playing, autonomous AI agents."),
            ("ObjectBox DB", "ObjectBox is an embedded database for mobile and IoT devices, known for its speed."),
            ("Paris Capital", "The capital of France is Paris, a major European city."),
            ("Python Language", "Python is a versatile and popular high-level programming language.")
        ]

        for title, text in cls.sample_data:
            embedding = embedder._embed_text(text)
            if embedding is not None:
                cls.memory.add_knowledge(text, embedding)
            else:
                print(f"Warning: Failed to generate embedding for '{text}' during test setup.")

        cls.kb_tool = KnowledgeBaseTool(memory_instance=cls.memory)
        if not cls.kb_tool.embedding_session or not cls.kb_tool.tokenizer:
            print("Warning: KnowledgeBaseTool under test failed to load ONNX models.")


    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in this class."""
        if hasattr(cls, 'memory') and cls.memory:
             ONNXObjectBoxMemory.close_store_instance(TEST_DB_PATH)
        if os.path.exists(TEST_DB_PATH): # Attempt cleanup again just in case
            ONNXObjectBoxMemory.remove_store_files(TEST_DB_PATH)

    def setUp(self):
        if hasattr(TestKnowledgeBaseToolWithONNX, 'embedder_failed') and TestKnowledgeBaseToolWithONNX.embedder_failed:
            self.skipTest("Skipping test due to ONNX embedder initialization failure in setUpClass.")
        if not self.kb_tool.embedding_session or not self.kb_tool.tokenizer:
            self.skipTest("Skipping test due to ONNX model/tokenizer load failure in kb_tool.")


    def test_query_crewai_concept(self):
        """Test querying for CrewAI concept."""
        question = "What is CrewAI?"
        response = self.kb_tool._run(question)
        self.assertIn("CrewAI is a framework", response)
        self.assertNotIn("No relevant information", response)

        """Test querying for ObjectBox information."""
        question = "Tell me about ObjectBox."
        response = self.kb_tool._run(question)
        self.assertIn("ObjectBox is an embedded database", response)
        self.assertNotIn("No relevant information", response)

    def test_query_paris_fact(self):
        """Test querying for Paris fact."""
        question = "Which European city is known as the capital of France?"
        response = self.kb_tool._run(question)
        self.assertIn("capital of France is Paris", response)
        self.assertNotIn("No relevant information", response)

    def test_query_python_details(self):
        """Test querying for Python language details."""
        question = "Describe Python programming."
        response = self.kb_tool._run(question)
        self.assertIn("Python is a versatile", response)
        self.assertNotIn("No relevant information", response)

    def test_query_non_existent_data(self):
        """Test querying for data that does not exist."""
        question = "What is the airspeed velocity of an unladen swallow in Andromeda?"
        response = self.kb_tool._run(question)
        self.assertTrue("No relevant information found" in response or "Embedding generation failed" in response)

    def test_query_with_dict_input_and_max_context(self):
        """Test querying using dictionary input with max_context."""
        question_dict = {
            "question": "Tell me about programming languages and frameworks",
            "max_context": 1
        }
        response = self.kb_tool._run(question_dict)
        self.assertTrue("Python" in response or "CrewAI" in response)


    def test_llm_interaction_if_provided(self):
        """Test that LLM is called if provided and context is found."""
        class MockLLM:
            def __init__(self):
                self.generated_prompt = None
            def generate(self, prompt):
                self.generated_prompt = prompt
                return "LLM processed the answer based on context."
            def invoke(self, prompt): return self.generate(prompt)
            def chat(self, prompt): return self.generate(prompt)

        mock_llm = MockLLM()
        question_dict = {
            "question": "What is CrewAI?",
            "llm": mock_llm
        }
        response = self.kb_tool._run(question_dict)
        self.assertEqual(response, "LLM processed the answer based on context.")
        self.assertIsNotNone(mock_llm.generated_prompt)
        self.assertIn("CrewAI is a framework", mock_llm.generated_prompt)
        self.assertIn("What is CrewAI?", mock_llm.generated_prompt)

    def test_llm_not_called_if_no_context(self):
        """Test that LLM is NOT called if no context is found."""
        class MockLLM:
            def __init__(self):
                self.called = False
            def generate(self, prompt):
                self.called = True
                return "LLM should not have been called."
            def invoke(self, prompt): return self.generate(prompt)
            def chat(self, prompt): return self.generate(prompt)

        mock_llm = MockLLM()
        question_dict = {
            "question": "AGI history in the 15th century",
            "llm": mock_llm
        }
        response = self.kb_tool._run(question_dict)
        self.assertFalse(mock_llm.called)
        self.assertIn("No relevant information found", response)


if __name__ == '__main__':
    unittest.main()
