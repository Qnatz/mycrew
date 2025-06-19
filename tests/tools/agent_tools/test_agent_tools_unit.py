import uuid
from unittest.mock import patch, MagicMock, call

import pytest

from crewai.agent import Agent
from crewai.crew import Crew
from crewai.task import Task
from crewai.tools.agent_tools import DelegateWorkTool, AskQuestionTool
from crewai.utilities.constants import NOT_SPECIFIED
from crewai.utilities.i18n import I18N


# Helper function to create a mock agent
def create_mock_agent(name="Test Agent", role="Test Role", goal="Test Goal", backstory="Test Backstory"):
    mock_agent = MagicMock(spec=Agent)
    mock_agent.name = name
    mock_agent.role = role
    mock_agent.goal = goal
    mock_agent.backstory = backstory
    # mock_agent.i18n = I18N() # Replaced by mocked i18n
    mock_agent.verbose = False
    mock_agent.max_rpm = None
    mock_agent._rpm_controller = None
    mock_agent._token_process = None
    mock_agent.security_config = None
    mock_agent.tools = []

    # Create a more direct mock for i18n and its slice method
    class MockI18NHelper:
        def slice(self, text_key: str) -> str:
            return "dummy_manager_request_slice_from_helper"
    mock_agent.i18n = MockI18NHelper()

    # Mock the execute_task method to return a string
    mock_agent.execute_task.return_value = "Task executed successfully by " + name
    return mock_agent


class TestAgentToolsEnhancedFeatures:
    # @pytest.fixture # mock_i18n fixture is no longer used by tools directly
    # def mock_i18n(self):
    #     return I18N()

    @pytest.fixture
    def delegatee_agent(self):
        return create_mock_agent(name="DelegateeAgent", role="Delegatee Role")

    @pytest.fixture
    def another_agent(self):
        return create_mock_agent(name="AnotherAgent", role="Another Role")

    @pytest.fixture
    def mock_agents(self, delegatee_agent, another_agent):
        return [delegatee_agent, another_agent]

    @pytest.fixture
    def mock_crew(self, mock_agents):
        crew = MagicMock(spec=Crew)
        crew.tasks = []
        crew.agents = mock_agents
        return crew

    @pytest.fixture
    def delegator_task(self, mock_crew):
        task = MagicMock(spec=Task)
        task.crew = mock_crew
        task.id = uuid.uuid4()
        return task

    @pytest.fixture
    def delegate_work_tool(self, mock_agents, delegator_task): # Removed mock_i18n from args
        # The tool will use the i18n instance from the mock_agents it's given,
        # or its own default if not overridden by agent's i18n.
        # For these agent tools, the i18n instance on the tool itself is what BaseAgentTool uses.
        # So, we need to ensure the tool instance has an i18n that can be used.
        # The BaseAgentTool has `i18n: I18N = Field(default_factory=I18N)`
        # The mock_agents passed to it are used for finding the delegatee.
        # The i18n for the Task created *inside* _execute comes from the delegatee_agent.
        # The i18n for error messages from the tool itself comes from tool.i18n.

        # Create a real I18N for the tool itself, or mock it if its methods are called directly by tool logic
        tool_i18n = I18N()
        # If tool.i18n.errors() or other methods were used directly by the tool's own logic (not the agent's),
        # those would need mocking on tool_i18n if they cause issues.
        # For now, assuming the default I18N() is fine for the tool's own i18n needs.

        tool = DelegateWorkTool(name="Delegate Work to Coworker", description="Delegates work to a coworker agent", agents=mock_agents, i18n=tool_i18n)
        tool.task = delegator_task  # Set the delegator_task on the tool
        return tool

    @pytest.fixture
    def ask_question_tool(self, mock_agents, delegator_task): # Removed mock_i18n from args
        tool_i18n = I18N()
        tool = AskQuestionTool(name="Ask Question to Coworker", description="Asks a question to a coworker agent", agents=mock_agents, i18n=tool_i18n)
        tool.task = delegator_task # Set the delegator_task on the tool
        return tool

    def test_delegate_work_with_input_interpolation(self, delegate_work_tool, delegatee_agent):
        with patch.object(delegatee_agent, 'execute_task', return_value="Executed interpolated task") as mock_execute_task:
            delegate_work_tool.run(
                task="Analyze {data_file} for {customer_name}",
                context="Standard context",
                coworker="Delegatee Role",
                inputs={"data_file": "report.pdf", "customer_name": "Acme Corp"}
            )

            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0]
            assert isinstance(called_task_arg, Task)
            assert called_task_arg.description == "Analyze report.pdf for Acme Corp"
            assert mock_execute_task.call_args[0][1] == "Standard context"


    def test_delegate_work_with_prerequisite_tasks(self, delegate_work_tool, delegatee_agent, delegator_task):
        prior_task1 = Task(description="Prior task 1 output", agent=delegatee_agent, expected_output="dummy output1")
        prior_task2 = Task(description="Prior task 2 output", agent=delegatee_agent, expected_output="dummy output2")
        task1_id = prior_task1.id
        task2_id = prior_task2.id

        delegator_task.crew.tasks = [prior_task1, prior_task2]

        with patch.object(delegatee_agent, 'execute_task', return_value="Executed with prereqs") as mock_execute_task:
            delegate_work_tool.run(
                task="Subsequent task",
                context="String context",
                coworker="Delegatee Role",
                prerequisite_task_keys=[str(task1_id), str(task2_id)]
            )

            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0]
            assert isinstance(called_task_arg, Task)
            assert called_task_arg.description == "Subsequent task"
            assert called_task_arg.context == [prior_task1, prior_task2]
            assert mock_execute_task.call_args[0][1] == "String context"

    def test_delegate_work_with_invalid_prerequisite_keys(self, delegate_work_tool, delegatee_agent, delegator_task):
        prior_task1 = Task(description="Prior task 1 output", agent=delegatee_agent, expected_output="dummy output1")
        task1_id = prior_task1.id
        delegator_task.crew.tasks = [prior_task1]

        invalid_key = str(uuid.uuid4())

        with patch('crewai.tools.agent_tools.base_agent_tools.logger.warning') as mock_logger_warning:
            with patch.object(delegatee_agent, 'execute_task', return_value="Executed with partial prereqs") as mock_execute_task:
                delegate_work_tool.run(
                    task="Task with mixed keys",
                    context="Context here",
                    coworker="Delegatee Role",
                    prerequisite_task_keys=[str(task1_id), invalid_key]
                )

                mock_execute_task.assert_called_once()
                called_task_arg = mock_execute_task.call_args[0][0]
                assert isinstance(called_task_arg, Task)
                assert called_task_arg.context == [prior_task1]
                mock_logger_warning.assert_called_with(
                    f"Prerequisite task key '{invalid_key}' not found in crew's task history. Skipping."
                )

    def test_delegate_work_fallback_behavior(self, delegate_work_tool, delegatee_agent):
        with patch.object(delegatee_agent, 'execute_task', return_value="Executed fallback task") as mock_execute_task:
            delegate_work_tool.run(
                task="Simple task",
                context="Simple context",
                coworker="Delegatee Role"
            )

            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0]
            assert isinstance(called_task_arg, Task)
            assert called_task_arg.description == "Simple task"
            assert called_task_arg.context == NOT_SPECIFIED # or None, depending on implementation detail
            assert mock_execute_task.call_args[0][1] == "Simple context"

    # Tests for AskQuestionTool
    def test_ask_question_with_input_interpolation(self, ask_question_tool, delegatee_agent):
        with patch.object(delegatee_agent, 'execute_task', return_value="Answered interpolated q") as mock_execute_task:
            ask_question_tool.run(
                question="What is the status of {feature_name} for {client}?",
                context="Checking status",
                coworker="Delegatee Role",
                inputs={"feature_name": "Login API", "client": "BigCorp"}
            )

            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0] # This is the Task object
            assert isinstance(called_task_arg, Task)
            assert called_task_arg.description == "What is the status of Login API for BigCorp?" # description is the question for AskTool
            assert mock_execute_task.call_args[0][1] == "Checking status" # This is the context_str

    def test_ask_question_with_prerequisite_tasks(self, ask_question_tool, delegatee_agent, delegator_task):
        prior_task1 = Task(description="Background info 1", agent=delegatee_agent, expected_output="dummy output1")
        prior_task2 = Task(description="Background info 2", agent=delegatee_agent, expected_output="dummy output2")
        task1_id = prior_task1.id
        task2_id = prior_task2.id

        delegator_task.crew.tasks = [prior_task1, prior_task2]

        with patch.object(delegatee_agent, 'execute_task', return_value="Answered q with prereqs") as mock_execute_task:
            ask_question_tool.run(
                question="Based on prior context, what is next?",
                context="Follow-up question",
                coworker="Delegatee Role",
                prerequisite_task_keys=[str(task1_id), str(task2_id)]
            )

            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0]
            assert isinstance(called_task_arg, Task)
            assert called_task_arg.description == "Based on prior context, what is next?"
            assert called_task_arg.context == [prior_task1, prior_task2]
            assert mock_execute_task.call_args[0][1] == "Follow-up question"

    def test_ask_question_fallback_behavior(self, ask_question_tool, delegatee_agent):
        with patch.object(delegatee_agent, 'execute_task', return_value="Executed fallback task") as mock_execute_task:
            ask_question_tool.run(
                question="Simple question",
                context="Simple context for question",
                coworker="Delegatee Role"
            )

            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0]
            assert isinstance(called_task_arg, Task)
            assert called_task_arg.description == "Simple question"
            assert called_task_arg.context == NOT_SPECIFIED
            assert mock_execute_task.call_args[0][1] == "Simple context for question"

    def test_delegate_work_no_task_on_tool(self, delegatee_agent, mock_agents): # Removed mock_i18n
        # Test case where tool.task is None (e.g. tool not properly initialized by an agent)
        tool_i18n = I18N()
        tool_no_task = DelegateWorkTool(name="Delegate Work to Coworker", description="Delegates work to a coworker agent", agents=mock_agents, i18n=tool_i18n)
        # tool_no_task.task is None by default if not set

        with patch.object(delegatee_agent, 'execute_task', return_value="Executed") as mock_execute_task:
            tool_no_task.run(
                task="Task for agent {agent_name}",
                context="Context",
                coworker="Delegatee Role",
                inputs={"agent_name": "X"},
                prerequisite_task_keys=["some_key"] # This will try to access self.task.crew.tasks
            )
            # The call to _execute should still happen
            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0]
            assert called_task_arg.description == "Task for agent X"
            # Since self.task was None, all_crew_tasks would be None, so context should be NOT_SPECIFIED
            assert called_task_arg.context == NOT_SPECIFIED
            # And no warning should be logged for missing keys if all_crew_tasks is None
            # (or a different warning if prerequisite_task_keys is present but all_crew_tasks is None,
            #  depending on exact logic - current logic passes None for all_crew_tasks, so no key lookup happens)

    def test_ask_question_no_task_on_tool(self, delegatee_agent, mock_agents): # Removed mock_i18n
        tool_i18n = I18N()
        tool_no_task = AskQuestionTool(name="Ask Question to Coworker", description="Asks a question to a coworker agent", agents=mock_agents, i18n=tool_i18n)

        with patch.object(delegatee_agent, 'execute_task', return_value="Answered") as mock_execute_task:
            tool_no_task.run(
                question="Question for {topic}?",
                context="Context for q",
                coworker="Delegatee Role",
                inputs={"topic": "Y"},
                prerequisite_task_keys=["another_key"]
            )
            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0]
            assert called_task_arg.description == "Question for Y?"
            assert called_task_arg.context == NOT_SPECIFIED

    def test_delegate_work_prereq_keys_but_no_crew_tasks(self, delegate_work_tool, delegatee_agent, delegator_task):
        # Ensure delegator_task.crew.tasks is explicitly None or empty
        delegator_task.crew.tasks = None # Or []

        with patch('crewai.tools.agent_tools.base_agent_tools.logger.warning') as mock_logger_warning:
            with patch.object(delegatee_agent, 'execute_task', return_value="Executed") as mock_execute_task:
                delegate_work_tool.run(
                    task="Task with prereqs specified but no tasks in crew",
                    context="Context",
                    coworker="Delegatee Role",
                    prerequisite_task_keys=["key1", "key2"]
                )
                mock_execute_task.assert_called_once()
                called_task_arg = mock_execute_task.call_args[0][0]
                assert called_task_arg.description == "Task with prereqs specified but no tasks in crew"
                # Context should be NOT_SPECIFIED because all_crew_tasks was None/empty
                assert called_task_arg.context == NOT_SPECIFIED
                # No warning should be logged if all_crew_tasks is None/empty, as the key lookup loop is skipped.
                # If prerequisite_task_keys is not empty and all_crew_tasks is None, no specific warning about keys not being found.
                # The current logic is: if prerequisite_task_keys and all_crew_tasks:
                # So if all_crew_tasks is None, the block is skipped.
                mock_logger_warning.assert_not_called()

    def test_delegate_work_prereq_keys_empty_list(self, delegate_work_tool, delegatee_agent, delegator_task):
        delegator_task.crew.tasks = [Task(description="A task", agent=delegatee_agent, expected_output="dummy output")]

        with patch.object(delegatee_agent, 'execute_task', return_value="Executed") as mock_execute_task:
            delegate_work_tool.run(
                task="Task with empty prereq list",
                context="Context",
                coworker="Delegatee Role",
                prerequisite_task_keys=[] # Empty list
            )
            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0]
            assert called_task_arg.description == "Task with empty prereq list"
            # Context should be NOT_SPECIFIED because prerequisite_task_keys was empty
            assert called_task_arg.context == NOT_SPECIFIED

    def test_delegate_work_inputs_empty_dict(self, delegate_work_tool, delegatee_agent):
        original_task_desc = "Task with {placeholder}"
        with patch.object(delegatee_agent, 'execute_task', return_value="Executed") as mock_execute_task:
            delegate_work_tool.run(
                task=original_task_desc,
                context="Context",
                coworker="Delegatee Role",
                inputs={} # Empty dict
            )
            mock_execute_task.assert_called_once()
            called_task_arg = mock_execute_task.call_args[0][0]
            # Description should remain un-interpolated
            assert called_task_arg.description == original_task_desc
            assert called_task_arg.context == NOT_SPECIFIED
