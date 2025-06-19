import unittest
from mycrews.qrew.orchestrators.idea_interpreter_agent.agent import idea_interpreter_agent
from crewai import Agent # To check instance type
from crewai.tools import BaseTool # BaseTool for custom tools is from crewai.tools
from crewai.llm import LLM as CrewAILLM # To check the LLM instance type

class TestIdeaInterpreterAgent(unittest.TestCase):

    def test_agent_initialization_and_llm(self):
        """Test that the IdeaInterpreterAgent is initialized correctly with its LLM and tools."""

        # Check if the agent is an instance of crewai.Agent
        self.assertIsInstance(idea_interpreter_agent, Agent,
                              "Agent should be an instance of crewai.Agent")

        # Check the agent's role
        self.assertEqual(idea_interpreter_agent.role, "Idea Interpreter",
                         "Agent role is not set correctly")

        # Check if the LLM is configured
        self.assertIsNotNone(idea_interpreter_agent.llm,
                             "Agent LLM should be configured")

        # Check if the LLM is an instance of CrewAI's LLM wrapper
        self.assertIsInstance(idea_interpreter_agent.llm, CrewAILLM,
                              "Agent LLM should be an instance of crewai.llm.LLM")

        # Check if tools are configured
        self.assertTrue(len(idea_interpreter_agent.tools) > 0,
                        "Agent should have tools configured")

        # Check if the first tool is the KnowledgeBaseTool
        # This assumes KnowledgeBaseTool is the only or first tool.
        # We also need to ensure we're checking an instance of the correct base class for tools.
        # crewai_tools.tools.base_tool.BaseTool is a good general check.
        self.assertIsInstance(idea_interpreter_agent.tools[0], BaseTool,
                              "First tool should be an instance of BaseTool")
        self.assertEqual(idea_interpreter_agent.tools[0].name, "Knowledge Base Query Tool",
                         "KnowledgeBaseTool not found or not named correctly as the first tool")

if __name__ == '__main__':
    unittest.main()
