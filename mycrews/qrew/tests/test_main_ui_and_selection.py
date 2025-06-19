import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json
import sys

# Add project root to sys.path to allow imports like mycrews.qrew.main
# This is often needed if tests are run from a different working directory
project_root_for_test = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')) # Corrected path
if project_root_for_test not in sys.path:
    sys.path.insert(0, project_root_for_test)

# Now import the module to be tested
# Assuming main.py is in mycrews/qrew/
from mycrews.qrew import main as qrew_main
from mycrews.qrew.project_manager import ProjectStateManager # Needed for mocking its instances
from mycrews.qrew.workflows.orchestrator import WorkflowOrchestrator # Needed for mocking
from rich.panel import Panel
from rich.text import Text


class TestDisplayModelStatus(unittest.TestCase):
    @patch('mycrews.qrew.main.console.print')
    def test_display_model_initialization_status_empty(self, mock_console_print):
        title = "[bold cyan]--- Test Empty ---[/bold cyan]"
        qrew_main.display_model_initialization_status(title, [])

        mock_console_print.assert_called_once()
        args, _ = mock_console_print.call_args
        self.assertIsInstance(args[0], Panel)
        panel_instance = args[0]
        # For Rich titles, the Text object itself is the title, not a plain string.
        self.assertIsInstance(panel_instance.title, Text)
        self.assertEqual(panel_instance.title.plain, "--- Test Empty ---") # Check plain text of title
        self.assertIsInstance(panel_instance.renderable, Text)
        self.assertEqual(panel_instance.renderable.plain, "No models to display status for in this category.")
        self.assertTrue(any(span.style == "italic yellow" for span in panel_instance.renderable.spans))

    @patch('mycrews.qrew.main.console.print')
    def test_display_model_initialization_status_single_success(self, mock_console_print):
        title_text = "[bold cyan]--- Test Success ---[/bold cyan]"
        # Test with model key instead of agent identifier
        qrew_main.display_model_initialization_status(title_text, [("gemini/gemini-1.0-pro", True)])

        mock_console_print.assert_called_once()
        panel_instance = mock_console_print.call_args[0][0]
        self.assertEqual(panel_instance.title.plain, "--- Test Success ---")
        self.assertIsInstance(panel_instance.renderable, Text)
        self.assertEqual(panel_instance.renderable.plain, "gemini/gemini-1.0-pro: ✅") # Changed to ✅
        # Check for bright_green style
        self.assertTrue(any(span.style == "bright_green" for span in panel_instance.renderable.spans if panel_instance.renderable.plain[span.start:span.end] == "✅")) # Changed to ✅

    @patch('mycrews.qrew.main.console.print')
    def test_display_model_initialization_status_single_failure(self, mock_console_print):
        title_text = "[bold cyan]--- Test Failure ---[/bold cyan]"
        # Test with model key
        qrew_main.display_model_initialization_status(title_text, [("ollama/mistral", False)])

        mock_console_print.assert_called_once()
        panel_instance = mock_console_print.call_args[0][0]
        self.assertEqual(panel_instance.title.plain, "--- Test Failure ---")
        self.assertIsInstance(panel_instance.renderable, Text)
        self.assertEqual(panel_instance.renderable.plain, "ollama/mistral: ❌")
        # Check for bright_red style
        self.assertTrue(any(span.style == "bright_red" for span in panel_instance.renderable.spans if panel_instance.renderable.plain[span.start:span.end] == "❌"))

    @patch('mycrews.qrew.main.console.print')
    def test_display_model_initialization_status_multiple_unique_keys(self, mock_console_print):
        title_text = "[bold cyan]--- Test Multiple Unique Keys ---[/bold cyan]"
        statuses = [("gemini/gemini-1.5-flash", True), ("ollama/mistral", False), ("anthropic/claude-2", True)]
        qrew_main.display_model_initialization_status(title_text, statuses)

        mock_console_print.assert_called_once()
        panel_instance = mock_console_print.call_args[0][0]
        self.assertEqual(panel_instance.title.plain, "--- Test Multiple Unique Keys ---")
        self.assertIsInstance(panel_instance.renderable, Text)

        # Output is sorted by model key
        expected_plain_text = "anthropic/claude-2: ✅\ngemini/gemini-1.5-flash: ✅\nollama/mistral: ❌" # Changed to ✅
        self.assertEqual(panel_instance.renderable.plain, expected_plain_text)

        self.assertTrue(any(span.style == "bright_green" for span in panel_instance.renderable.spans if "✅" in panel_instance.renderable.plain[span.start:span.end])) # Changed to ✅
        self.assertTrue(any(span.style == "bright_red" for span in panel_instance.renderable.spans if "❌" in panel_instance.renderable.plain[span.start:span.end]))

    @patch('mycrews.qrew.main.console.print')
    def test_display_model_aggregation_success_overrides_failure(self, mock_console_print):
        title_text = "[bold cyan]--- Test Aggregation Success ---[/bold cyan]"
        statuses = [
            ("gemini/gemini-1.5-pro", False),
            ("gemini/gemini-1.5-pro", True),
            ("gemini/gemini-1.5-pro", False)
        ]
        qrew_main.display_model_initialization_status(title_text, statuses)
        panel_instance = mock_console_print.call_args[0][0]
        self.assertEqual(panel_instance.renderable.plain, "gemini/gemini-1.5-pro: ✅") # Changed to ✅
        self.assertTrue(any(span.style == "bright_green" for span in panel_instance.renderable.spans if "✅" in panel_instance.renderable.plain[span.start:span.end])) # Changed to ✅

    @patch('mycrews.qrew.main.console.print')
    def test_display_model_aggregation_all_failures(self, mock_console_print):
        title_text = "[bold cyan]--- Test Aggregation Failure ---[/bold cyan]"
        statuses = [
            ("ollama/llama2", False),
            ("ollama/llama2", False)
        ]
        qrew_main.display_model_initialization_status(title_text, statuses)
        panel_instance = mock_console_print.call_args[0][0]
        self.assertEqual(panel_instance.renderable.plain, "ollama/llama2: ❌")
        self.assertTrue(any(span.style == "bright_red" for span in panel_instance.renderable.spans if "❌" in panel_instance.renderable.plain[span.start:span.end]))

    @patch('mycrews.qrew.main.console.print')
    def test_display_model_with_none_key(self, mock_console_print):
        title_text = "[bold cyan]--- Test None Key ---[/bold cyan]"
        statuses = [(None, False), ("gemini/gemini-valid", True)]
        qrew_main.display_model_initialization_status(title_text, statuses)
        panel_instance = mock_console_print.call_args[0][0]
        # Output is sorted, "N/A" comes after "gemini/gemini-valid" if None is stringified late,
        # or before if None is handled as "N/A" early and then sorted.
        # The current implementation stringifies None to "N/A" within the loop before sorting.
        expected_text_parts = ["N/A: ❌", "gemini/gemini-valid: ✅"] # Changed to ✅
        # Check if both parts are present, order might vary based on how None is sorted against strings
        self.assertIn(expected_text_parts[0], panel_instance.renderable.plain)
        self.assertIn(expected_text_parts[1], panel_instance.renderable.plain)

        self.assertTrue(any(span.style == "bright_red" for span in panel_instance.renderable.spans if "❌" in panel_instance.renderable.plain[span.start:span.end]))
        self.assertTrue(any(span.style == "bright_green" for span in panel_instance.renderable.spans if "✅" in panel_instance.renderable.plain[span.start:span.end])) # Changed to ✅

    @patch('mycrews.qrew.main.console.print')
    def test_display_model_initialization_status_mixed_keys_and_aggregation(self, mock_console_print):
        title_text = "[bold cyan]--- Test Mixed Aggregation ---[/bold cyan]"
        statuses = [
            ("gemini/gemini-flash", True),
            ("ollama/mistral", False),
            ("gemini/gemini-flash", False), # Should still be success for gemini-flash
            ("ollama/zephyr", True),
            ("ollama/mistral", False) # Should remain failure for mistral
        ]
        qrew_main.display_model_initialization_status(title_text, statuses)

        mock_console_print.assert_called_once()
        panel_instance = mock_console_print.call_args[0][0]
        self.assertEqual(panel_instance.title.plain, "--- Test Mixed Aggregation ---")
        self.assertIsInstance(panel_instance.renderable, Text)

        # Expected output is sorted by model key
        expected_plain_text = "gemini/gemini-flash: ✅\nollama/mistral: ❌\nollama/zephyr: ✅" # Changed to ✅
        self.assertEqual(panel_instance.renderable.plain, expected_plain_text)

        # Verify styles
        text_renderable = panel_instance.renderable
        flash_span = next(s for s in text_renderable.spans if text_renderable.plain[s.start:s.end] == "✅" and "gemini/gemini-flash" in text_renderable.plain[0:s.start]) # Changed to ✅
        mistral_span = next(s for s in text_renderable.spans if text_renderable.plain[s.start:s.end] == "❌" and "ollama/mistral" in text_renderable.plain[0:s.start])
        zephyr_span = next(s for s in text_renderable.spans if text_renderable.plain[s.start:s.end] == "✅" and "ollama/zephyr" in text_renderable.plain[0:s.start]) # Changed to ✅

        self.assertEqual(flash_span.style, "bright_green")
        self.assertEqual(mistral_span.style, "bright_red")
        self.assertEqual(zephyr_span.style, "bright_green")


class TestListAvailableProjects(unittest.TestCase):
    # Path to the projects directory, relative to where qrew_main is.
    # qrew_main.project_root should resolve to the /app directory in the sandbox.
    # So, projects_dir_path_base should be 'mycrews/qrew/projects' relative to /app
    # We need to mock os.path.join to correctly use qrew_main.project_root

    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_list_projects_basic(self, mock_path_exists, mock_open_file, mock_listdir, mock_isdir):
        # Simulate the projects directory existing
        mock_isdir.side_effect = lambda path: path.endswith(os.path.join("mycrews", "qrew", "projects")) or \
                                             path.endswith("project_alpha_123") or \
                                             path.endswith("project_beta_456")

        mock_listdir.return_value = ['project_alpha_123', 'project_beta_456', 'not_a_project_file.txt']

        # Mock os.path.exists for state.json files
        def path_exists_side_effect(path):
            if "project_alpha_123" in path and path.endswith("state.json"):
                return True
            if "project_beta_456" in path and path.endswith("state.json"):
                return True
            return False
        mock_path_exists.side_effect = path_exists_side_effect

        # Mock open for reading state.json
        # Project Alpha: state.json with project_name
        # Project Beta: state.json without project_name (should fallback to folder name)
        def open_side_effect(path, mode='r'):
            if "project_alpha_123" in path and path.endswith("state.json"):
                return mock_open(read_data=json.dumps({"project_name": "Alpha Project From State"})).return_value
            elif "project_beta_456" in path and path.endswith("state.json"):
                 # Malformed JSON or missing key
                return mock_open(read_data=json.dumps({"other_key": "some_value"})).return_value
            return mock_open(read_data="").return_value # Default for other files
        mock_open_file.side_effect = open_side_effect

        # We need to ensure qrew_main.project_root is set correctly for the test environment
        # or mock how list_available_projects constructs its path.
        # For simplicity, let's assume qrew_main.project_root is accessible and correct.
        # qrew_main.project_root is defined in main.py as:
        # project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        # In the test, __file__ is different. So we might need to patch project_root in qrew_main
        with patch('mycrews.qrew.main.project_root', project_root_for_test):
            projects = qrew_main.list_available_projects()

        self.assertIn("Alpha Project From State", projects)
        self.assertIn("project_beta_456", projects) # Fallback to folder name
        self.assertNotIn("not_a_project_file.txt", projects)
        self.assertEqual(len(projects), 2)

    @patch('os.path.isdir')
    def test_list_projects_no_project_dir(self, mock_isdir):
        mock_isdir.return_value = False # Simulate projects directory not existing
        with patch('mycrews.qrew.main.project_root', project_root_for_test):
            projects = qrew_main.list_available_projects()
        self.assertEqual(projects, [])

    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('os.path.exists') # To simulate no state.json files
    def test_list_projects_no_state_files(self, mock_path_exists, mock_listdir, mock_isdir):
        mock_isdir.side_effect = lambda path: path.endswith(os.path.join("mycrews", "qrew", "projects")) or \
                                             path.endswith("project_gamma_789")
        mock_listdir.return_value = ['project_gamma_789']
        mock_path_exists.return_value = False # No state.json files exist

        with patch('mycrews.qrew.main.project_root', project_root_for_test):
            projects = qrew_main.list_available_projects()

        self.assertIn("project_gamma_789", projects) # Fallback to folder name
        self.assertEqual(len(projects), 1)


class TestRunQrewInteraction(unittest.TestCase):

    def setUp(self):
        # Common patchers, start them here if they are used across multiple test methods
        # self.patcher_orchestrator = patch('mycrews.qrew.main.WorkflowOrchestrator')
        # self.MockOrchestrator = self.patcher_orchestrator.start()
        # self.mock_orchestrator_instance = self.MockOrchestrator.return_value
        # self.mock_orchestrator_instance.execute_pipeline = MagicMock(return_value={"status": "simulated_success"})
        pass

    def tearDown(self):
        # unittest.mock.patch.stopall() # Stops all patchers started with start()
        pass

    @patch('mycrews.qrew.main.console.print') # Patched for Rich
    @patch('rich.prompt.Prompt.ask') # Patched for Rich
    @patch('mycrews.qrew.main.list_available_projects')
    @patch('mycrews.qrew.main.WorkflowOrchestrator')
    @patch('mycrews.qrew.main.ProjectStateManager')
    def test_run_qrew_new_idea_input(self, MockProjectStateManager, MockWorkflowOrchestrator, mock_list_projects, mock_prompt_ask, mock_console_print):
        mock_list_projects.return_value = []
        mock_prompt_ask.return_value = "Create a new amazing app"

        # Mock the orchestrator instance and its execute_pipeline method
        mock_orchestrator_instance = MockWorkflowOrchestrator.return_value
        mock_orchestrator_instance.execute_pipeline.return_value = {"status": "simulated_run_complete"}

        # Mock llm_initialization_statuses from llm_config, assuming it's imported by main
        with patch.dict(qrew_main.sys.modules, {'mycrews.qrew.llm_config': MagicMock(llm_initialization_statuses=[])}):
             qrew_main.run_qrew()

        MockProjectStateManager.assert_not_called()

        MockWorkflowOrchestrator.assert_called_once_with(project_name=None)

        pipeline_inputs_received = mock_orchestrator_instance.execute_pipeline.call_args[0][0]
        self.assertEqual(pipeline_inputs_received.get("user_request"), "Create a new amazing app")
        self.assertIsNone(pipeline_inputs_received.get("project_name"))
        self.assertIn("project_goal", pipeline_inputs_received)

        # Check that the Taskmaster panel was printed
        taskmaster_panel_printed = False
        new_idea_message_printed = False
        for call in mock_console_print.call_args_list:
            args = call[0]
            if args and isinstance(args[0], Panel):
                if "Taskmaster Initialization" in args[0].title.plain:
                    taskmaster_panel_printed = True
                    self.assertIn("No existing projects found.", args[0].renderable.plain)
            elif args and isinstance(args[0], Text):
                if "Processing as a new project idea: 'Create a new amazing app'" in args[0].plain:
                    new_idea_message_printed = True

        self.assertTrue(taskmaster_panel_printed, "Taskmaster initialization panel was not printed.")
        self.assertTrue(new_idea_message_printed, "New idea processing message was not printed.")


    @patch('mycrews.qrew.main.console.print') # Patched for Rich
    @patch('rich.prompt.Prompt.ask') # Patched for Rich
    @patch('mycrews.qrew.main.list_available_projects')
    @patch('mycrews.qrew.main.WorkflowOrchestrator')
    @patch('mycrews.qrew.main.ProjectStateManager')
    def test_run_qrew_existing_project_selection(self, MockProjectStateManager, MockWorkflowOrchestrator, mock_list_projects, mock_prompt_ask, mock_console_print):
        mock_list_projects.return_value = ['project_alpha', 'project_beta']
        mock_prompt_ask.return_value = "1"

        # Configure the mock ProjectStateManager instance
        mock_state_manager_instance = MockProjectStateManager.return_value
        mock_state_manager_instance.state = {
            "project_name": "project_alpha",
            "status": "in-progress",
            "artifacts": {
                "taskmaster": {"refined_brief": "Original idea for alpha"}
            },
            "project_goal": "Goal for alpha"
        }

        mock_orchestrator_instance = MockWorkflowOrchestrator.return_value
        mock_orchestrator_instance.execute_pipeline.return_value = {"status": "simulated_run_complete"}

        with patch.dict(qrew_main.sys.modules, {'mycrews.qrew.llm_config': MagicMock(llm_initialization_statuses=[])}):
            qrew_main.run_qrew()

        MockProjectStateManager.assert_called_once_with('project_alpha')
        MockWorkflowOrchestrator.assert_called_once_with(project_name='project_alpha')

        pipeline_inputs_received = mock_orchestrator_instance.execute_pipeline.call_args[0][0]
        self.assertEqual(pipeline_inputs_received.get("project_name"), "project_alpha")
        self.assertEqual(pipeline_inputs_received.get("user_request"), "Original idea for alpha")
        self.assertEqual(pipeline_inputs_received.get("project_goal"), "Goal for alpha")
        self.assertEqual(pipeline_inputs_received.get("is_new_project"), False)

        # Check Rich output for selecting project
        selected_project_message_printed = False
        for call in mock_console_print.call_args_list:
            args = call[0]
            if args and isinstance(args[0], Text):
                if "Selected existing project: 'project_alpha'" in args[0].plain:
                    selected_project_message_printed = True
                    break
        self.assertTrue(selected_project_message_printed, "Selected project message not found or not Text.")


    @patch('mycrews.qrew.main.console.print') # Patched for Rich
    @patch('rich.prompt.Prompt.ask') # Patched for Rich
    @patch('mycrews.qrew.main.list_available_projects')
    @patch('mycrews.qrew.main.WorkflowOrchestrator')
    @patch('mycrews.qrew.main.ProjectStateManager')
    def test_run_qrew_select_completed_project(self, MockProjectStateManager, MockWorkflowOrchestrator, mock_list_projects, mock_prompt_ask, mock_console_print):
        mock_list_projects.return_value = ['completed_project']
        mock_prompt_ask.return_value = "1"

        mock_state_manager_instance = MockProjectStateManager.return_value
        mock_state_manager_instance.state = {
            "project_name": "completed_project",
            "status": "completed"
        }

        mock_orchestrator_instance = MockWorkflowOrchestrator.return_value

        with patch.dict(qrew_main.sys.modules, {'mycrews.qrew.llm_config': MagicMock(llm_initialization_statuses=[])}):
            qrew_main.run_qrew()

        MockProjectStateManager.assert_called_once_with('completed_project')

        # Assert that a Panel about completion was printed
        completion_panel_printed = False
        for call in mock_console_print.call_args_list:
            args = call[0]
            if args and isinstance(args[0], Panel):
                if "Project Completed" in args[0].title.plain and \
                   "Project 'completed_project' is already marked as completed" in args[0].renderable.plain:
                    completion_panel_printed = True
                    break
        self.assertTrue(completion_panel_printed, "Completion panel was not printed as expected.")

        mock_orchestrator_instance.execute_pipeline.assert_not_called()
        MockWorkflowOrchestrator.assert_called_once_with(project_name='completed_project')


    @patch('mycrews.qrew.main.console.print') # Patched for Rich
    @patch('rich.prompt.Prompt.ask') # Patched for Rich
    @patch('mycrews.qrew.main.list_available_projects')
    @patch('mycrews.qrew.main.WorkflowOrchestrator')
    @patch('mycrews.qrew.main.ProjectStateManager')
    def test_run_qrew_invalid_project_number_treats_as_new(self, MockProjectStateManager, MockWorkflowOrchestrator, mock_list_projects, mock_prompt_ask, mock_console_print):
        mock_list_projects.return_value = ['project_one']
        mock_prompt_ask.return_value = "99"

        mock_orchestrator_instance = MockWorkflowOrchestrator.return_value
        mock_orchestrator_instance.execute_pipeline.return_value = {"status": "simulated_run_complete"}

        with patch.dict(qrew_main.sys.modules, {'mycrews.qrew.llm_config': MagicMock(llm_initialization_statuses=[])}):
            qrew_main.run_qrew()

        MockProjectStateManager.assert_not_called()

        MockWorkflowOrchestrator.assert_called_once_with(project_name=None)

        pipeline_inputs_received = mock_orchestrator_instance.execute_pipeline.call_args[0][0]
        self.assertEqual(pipeline_inputs_received.get("user_request"), "99")
        self.assertIsNone(pipeline_inputs_received.get("project_name"))

        # Check for "Invalid selection" message
        invalid_selection_message_printed = False
        for call in mock_console_print.call_args_list:
            args = call[0]
            if args and isinstance(args[0], Text):
                if "Invalid selection '99'. Treating input as a new idea." in args[0].plain:
                    invalid_selection_message_printed = True
                    break
        self.assertTrue(invalid_selection_message_printed, "Invalid selection message not printed.")


if __name__ == '__main__':
    unittest.main()
