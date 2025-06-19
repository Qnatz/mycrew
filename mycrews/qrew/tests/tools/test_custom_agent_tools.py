import unittest
from unittest.mock import patch, MagicMock, ANY
import uuid
from typing import Optional # Required for MockI18NHelper

# Imports from crewAI core
from crewai import Agent, Task, Crew
from crewai.utilities.constants import NOT_SPECIFIED
from crewai.utilities.i18n import I18N

# Imports from mycrews
from mycrews.qrew.tools.custom_agent_tools import CustomDelegateWorkTool, CustomAskQuestionTool

# Helper to create a mock agent as refined in previous subtask
def create_mock_agent(name="Test Agent Role"):
    mock_agent = MagicMock(spec=Agent)
    mock_agent.role = name
    mock_agent.id = uuid.uuid4()
    mock_agent.goal = "Mocked Test Goal"
    mock_agent.backstory = "Mocked Test Backstory"
    mock_agent.description = "Mocked Agent Description"
    mock_agent.expected_output = "Mocked Agent Expected Output"

    # Mock i18n object
    class MockI18NHelper:
        prompt_file: Optional[str] = None
        language: str = "en"

        def slice(self, text_key: str) -> str:
            return f"mock_slice_for_{text_key}"

        def errors(self, key: str) -> str:
            return f"mock_error_for_{key}"

    mock_agent.i18n = MockI18NHelper()

    mock_agent.execute_task = MagicMock(return_value=f"Result from {name}")

    # Standard agent attributes
    mock_agent.verbose = False
    mock_agent.max_rpm = None
    mock_agent._rpm_controller = None
    mock_agent._token_process = MagicMock()
    mock_agent.allow_delegation = True
    mock_agent.tools = []
    mock_agent.config = {}
    mock_agent.security_config = None

    return mock_agent

class TestCustomAgentTools(unittest.TestCase):

    def setUp(self):
        self.i18n_for_tool = I18N()

        self.mock_delegator_agent = create_mock_agent(name="DelegatorAgent")

        self.mock_tool_context = MagicMock()
        self.mock_tool_context.crew = MagicMock(spec=Crew)
        self.mock_tool_context.crew.i18n = self.i18n_for_tool

        self.delegatee_agent1 = create_mock_agent(name="DelegateeAgent1")
        self.delegatee_agent2 = create_mock_agent(name="DelegateeAgent2")
        self.mock_tool_context.crew.agents = [self.mock_delegator_agent, self.delegatee_agent1, self.delegatee_agent2]

        self.mock_task1 = MagicMock(spec=Task)
        self.task1_id = uuid.uuid4()
        self.mock_task1.id = self.task1_id
        self.mock_task1.description = "Mock description for task 1"
        self.mock_task1.output = MagicMock()
        self.mock_task1.output.raw = "Output from Task 1"

        self.mock_task2 = MagicMock(spec=Task)
        self.task2_id = uuid.uuid4()
        self.mock_task2.id = self.task2_id
        self.mock_task2.description = "Mock description for task 2"
        self.mock_task2.output = MagicMock()
        self.mock_task2.output.raw = "Output from Task 2"

        self.mock_tool_context.crew.tasks = [self.mock_task1, self.mock_task2]

        self.delegate_tool = CustomDelegateWorkTool()
        self.delegate_tool.context = self.mock_tool_context

        self.ask_tool = CustomAskQuestionTool()
        self.ask_tool.context = self.mock_tool_context

    @patch('mycrews.qrew.tools.custom_agent_tools.Task')
    def test_custom_delegate_work_input_interpolation(self, MockTask):
        mock_created_task_instance = MockTask.return_value

        tool_input = {
            "task": "Analyze {data_file} for {customer_name}",
            "coworker": "DelegateeAgent1",
            "context_str": "Standard context",
            "inputs": {"data_file": "report.pdf", "customer_name": "Acme Corp"}
        }
        result = self.delegate_tool.run(**tool_input)

        MockTask.assert_called_once_with(
            description="Analyze report.pdf for Acme Corp",
            agent=self.delegatee_agent1,
            expected_output=ANY,
            context=None,
            i18n=self.delegatee_agent1.i18n
        )
        self.delegatee_agent1.execute_task.assert_called_once_with(
            task=mock_created_task_instance,
            context="Standard context"
        )
        self.assertEqual(result, f"Result from DelegateeAgent1")

    @patch('mycrews.qrew.tools.custom_agent_tools.Task')
    def test_custom_delegate_work_fallback_no_special_features(self, MockTask):
        mock_created_task_instance = MockTask.return_value
        tool_input = {
            "task": "Simple delegation",
            "coworker": "DelegateeAgent1",
            "context_str": "Simple context string"
        }
        result = self.delegate_tool.run(**tool_input)

        MockTask.assert_called_once_with(
            description="Simple delegation",
            agent=self.delegatee_agent1,
            expected_output=ANY,
            context=None,
            i18n=self.delegatee_agent1.i18n
        )
        self.delegatee_agent1.execute_task.assert_called_once_with(
            task=mock_created_task_instance,
            context="Simple context string"
        )
        self.assertEqual(result, f"Result from DelegateeAgent1")

    @patch('mycrews.qrew.tools.custom_agent_tools.Task')
    def test_custom_ask_question_input_interpolation(self, MockTask):
        mock_created_task_instance = MockTask.return_value
        tool_input = {
            "question": "What is the status of {feature_name} for ticket {ticket_id}?",
            "coworker": "DelegateeAgent2",
            "inputs": {"feature_name": "AuthModule", "ticket_id": "TICKET-123"}
        }
        result = self.ask_tool.run(**tool_input)

        MockTask.assert_called_once_with(
            description="What is the status of AuthModule for ticket TICKET-123?",
            agent=self.delegatee_agent2,
            expected_output=ANY,
            context=None,
            i18n=self.delegatee_agent2.i18n
        )
        self.delegatee_agent2.execute_task.assert_called_once_with(
            task=mock_created_task_instance,
            context=None
        )
        self.assertEqual(result, f"Result from DelegateeAgent2")

    @patch('mycrews.qrew.tools.custom_agent_tools.Task') # Patch Task where it's used
    def test_custom_delegate_work_prerequisite_tasks(self, MockTask):
        mock_created_task_instance = MockTask.return_value
        tool_input = {
            "task": "Summarize findings",
            "coworker": "DelegateeAgent1",
            "context_str": "Based on prior data",
            "prerequisite_task_ids": [str(self.mock_task1.id), str(self.mock_task2.id)] # Using stringified IDs from setUp
        }
        self.delegate_tool.run(**tool_input)

        MockTask.assert_called_once_with(
            description="Summarize findings",
            agent=self.delegatee_agent1,
            expected_output=unittest.mock.ANY,
            context=[self.mock_task1, self.mock_task2], # Asserting the list of Task objects
            i18n=self.delegatee_agent1.i18n # Corrected from ANY to specific i18n
        )
        self.delegatee_agent1.execute_task.assert_called_once_with(
            task=mock_created_task_instance,
            context="Based on prior data"
        )

    @patch('mycrews.qrew.tools.custom_agent_tools.logger.warning') # Patch the logger in custom_agent_tools
    @patch('mycrews.qrew.tools.custom_agent_tools.Task')
    def test_custom_delegate_work_invalid_prerequisite_keys(self, MockTask, mock_log_warning):
        mock_created_task_instance = MockTask.return_value
        tool_input = {
            "task": "Another task",
            "coworker": "DelegateeAgent1",
            "prerequisite_task_ids": [str(self.mock_task1.id), "non_existent_id"] # Using stringified ID
        }
        self.delegate_tool.run(**tool_input)

        MockTask.assert_called_once_with(
            description="Another task",
            agent=self.delegatee_agent1,
            expected_output=unittest.mock.ANY,
            context=[self.mock_task1], # Only valid task should be in context
            i18n=self.delegatee_agent1.i18n # Corrected from ANY to specific i18n
        )
        self.delegatee_agent1.execute_task.assert_called_once_with(
            task=mock_created_task_instance,
            context=None # As no context_str was provided
        )
        mock_log_warning.assert_called_with(f"Prerequisite task ID 'non_existent_id' not found in crew's task history. Skipping.")

    @patch('mycrews.qrew.tools.custom_agent_tools.Task')
    def test_custom_ask_question_prerequisite_tasks(self, MockTask):
        mock_created_task_instance = MockTask.return_value
        tool_input = {
            "question": "Based on prior work, what is next?",
            "coworker": "DelegateeAgent2",
            "prerequisite_task_ids": [str(self.mock_task1.id)] # Using stringified ID
        }
        self.ask_tool.run(**tool_input)

        MockTask.assert_called_once_with(
            description="Based on prior work, what is next?",
            agent=self.delegatee_agent2,
            expected_output=unittest.mock.ANY,
            context=[self.mock_task1],
            i18n=self.delegatee_agent2.i18n # Corrected from ANY to specific i18n
        )
        self.delegatee_agent2.execute_task.assert_called_once_with(
            task=mock_created_task_instance,
            context=None # As no context_str was provided
        )

if __name__ == '__main__':
    unittest.main()
