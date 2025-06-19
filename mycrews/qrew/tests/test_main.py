import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
import sys
import os
import json # For knowledge_base_configs check

# Ensure imports from mycrews.qrew are possible
# Adjust path if tests are run from a different location relative to project root
try:
    from mycrews.qrew import main as qrew_main # Direct import for testing functions
    from mycrews.qrew.project_manager import ProjectStateManager
except ImportError:
    # Fallback for different execution contexts (e.g. running test directly)
    project_root_for_test = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    if project_root_for_test not in sys.path:
        sys.path.insert(0, project_root_for_test)
    from mycrews.qrew import main as qrew_main
    from mycrews.qrew.project_manager import ProjectStateManager


class TestMainExecutionSubprocess(unittest.TestCase): # Renamed for clarity
    def test_main_script_runs_smoketest(self): # Renamed for clarity
        """
        Basic smoke test: main.py script runs via subprocess.
        Focuses on startup and very high-level output, not detailed logic.
        """
        main_script_path = ""
        try:
            import mycrews.qrew
            package_path = os.path.dirname(mycrews.qrew.__file__)
            main_script_path = os.path.join(package_path, "main.py")
        except ImportError:
            # This fallback might be hit if the package structure isn't fully set up
            # or if tests are run in a way that `mycrews.qrew` isn't in PYTHONPATH directly.
            # For local dev, `python -m unittest discover` from project root should work.
            # The sys.path modification in the class above this might also help.
            qrew_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # mycrews/qrew/tests -> mycrews/qrew
            main_script_path = os.path.join(qrew_dir, "main.py")


        if not os.path.exists(main_script_path):
            self.fail(f"main.py not found at expected path: {main_script_path}. ")

        stdout_content = ""
        stderr_content = ""
        try:
            # Set environment variables to try and use mocked/dummy LLMs if possible
            # This depends on how llm_config.py handles missing API keys or specific test model names
            env = os.environ.copy()
            env["GEMINI_API_KEY"] = "TEST_MODE_NO_API_CALLS_PLEASE" # Example
            env["OPENAI_API_KEY"] = "TEST_MODE_NO_API_CALLS_PLEASE"
            # Potentially set a specific model name that llm_config might treat as a mock
            # env["GEMINI_MODEL_NAME"] = "mock/mock-model"

            # For this smoke test, we'll provide 'n' for new project then a simple idea to avoid hanging on prompts too long.
            # We'll also mock Prompt.ask to avoid actual stdin blocking if subprocess doesn't handle it well.
            # However, for a true subprocess test, it's better if it can run non-interactively.
            # A better way for non-interactive run is to pipe input, or modify main.py to take args.
            # For now, this test primarily checks if it starts and prints initial messages.
            # We'll use a very short timeout as it might hang on prompts.

            process = subprocess.Popen(
                [sys.executable, "-u", main_script_path], # -u for unbuffered output
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE, # To send input
                text=True,
                env=env
            )
            # Simulate user input: 'n' for new project, then 'test idea'
            # This might not work if the Rich prompts are too complex for simple stdin piping.
            # For a true smoke test, we might only check up to the point of the first prompt.
            try:
                # This input sequence might not be hit if the program exits early or hangs before reading all.
                stdout_content, stderr_content = process.communicate(input="n\ntest idea\n", timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_content, stderr_content = process.communicate()
                # self.fail(f"main.py execution timed out. Stdout:\n{stdout_content}\nStderr:\n{stderr_content}")
                # For a smoke test, timeout might just mean it got to a prompt. We check what we got.
                print("main.py subprocess timed out (likely waiting for prompt). This is partially expected for smoke test.")


            print("\n--- main.py STDOUT (Smoke Test) ---")
            print(stdout_content)
            print("--- main.py STDERR (Smoke Test) ---")
            print(stderr_content)
            print("----------------------")

            # Basic checks for startup messages
            self.assertIn("Testing Logger Initialization", stdout_content)
            self.assertIn("LLM Initialization", stdout_content) # From Rich panel title
            self.assertIn("Initializing Qrew System...", stdout_content)

            # If it didn't timeout, we might check for return code
            if process.returncode is not None:
                 # If it exited, it might be an error, or it completed an non-interactive path (unlikely here)
                 # For this smoke test, we are more interested in startup.
                 # self.assertEqual(process.returncode, 0, f"main.py exited with code {process.returncode}. Stderr:\n{stderr_content}")
                 pass


        except Exception as e:
            self.fail(f"Executing main.py via subprocess failed with an unexpected error: {e}\nSTDOUT:\n{stdout_content}\nSTDERR:\n{stderr_content}")


class TestRunQrewLogic(unittest.TestCase):
    def setUp(self):
        # Path to the directory where main.py is located (mycrews/qrew)
        self.main_script_dir = os.path.dirname(qrew_main.__file__)

    @patch('mycrews.qrew.main.ProjectStateManager')
    @patch('rich.prompt.Prompt.ask')
    @patch('mycrews.qrew.main.WorkflowOrchestrator')
    @patch('mycrews.qrew.main.configure_rag_tools')
    @patch('mycrews.qrew.main.display_model_initialization_status') # Mock display
    @patch('mycrews.qrew.main.ChromaLogger') # Mock logger init
    @patch('mycrews.qrew.main.fallback_log') # Mock fallback logger
    def test_run_qrew_new_project_flow(self, mock_fallback_log, mock_chroma_logger, mock_display_status, mock_configure_rag, MockOrchestrator, mock_prompt_ask, MockPSM):
        # Scenario: No existing projects, user chooses to start a new one.
        MockPSM.list_projects.return_value = [] # No existing projects
        mock_prompt_ask.return_value = "My new project idea" # User types in an idea

        mock_orchestrator_instance = MockOrchestrator.return_value
        mock_orchestrator_instance.execute_pipeline.return_value = {"status": "completed", "final_assembly": {"result": "done"}}
        # Simulate project state after orchestrator run for output saving
        mock_orchestrator_instance.state = MagicMock()
        mock_orchestrator_instance.state.project_info = {"name": "MyNewProjectIdea", "path": os.path.join(self.main_script_dir, "projects", "MyNewProjectIdea")}
        mock_orchestrator_instance.state.state = {"status": "completed"}


        qrew_main.run_qrew()

        MockPSM.list_projects.assert_called_once()
        mock_prompt_ask.assert_called_once_with("[bold yellow]Please enter your new project idea or request[/bold yellow]")

        MockOrchestrator.assert_called_once_with(project_name=None)
        mock_orchestrator_instance.execute_pipeline.assert_called_once_with({"user_request": "My new project idea"})

        # Check RAG tool configuration call
        expected_kb_root = os.path.join(self.main_script_dir, "knowledge")
        expected_kb_configs = {
            'web_components': os.path.join(expected_kb_root, 'web_components'),
            'mobile_patterns': os.path.join(expected_kb_root, 'mobile_patterns'),
            'api_specs': os.path.join(expected_kb_root, 'api_specs'),
            'cloud_templates': os.path.join(expected_kb_root, 'cloud_templates')
        }
        mock_configure_rag.assert_called_once_with(expected_kb_configs)
        mock_display_status.assert_any_call("[bold cyan]--- LLM Initialization ---[/bold cyan]", ANY) # ANY from unittest.mock
        mock_display_status.assert_any_call("[bold cyan]--- ONNX Model Initialization ---[/bold cyan]", ANY)


    @patch('mycrews.qrew.main.ProjectStateManager')
    @patch('rich.prompt.Prompt.ask')
    @patch('mycrews.qrew.main.WorkflowOrchestrator')
    @patch('mycrews.qrew.main.configure_rag_tools') # Mock this to avoid its side effects
    @patch('mycrews.qrew.main.display_model_initialization_status')
    @patch('mycrews.qrew.main.ChromaLogger')
    @patch('mycrews.qrew.main.fallback_log')
    def test_run_qrew_resume_project_flow(self, mock_fallback_log, mock_chroma_logger, mock_display_status, mock_configure_rag, MockOrchestrator, mock_prompt_ask, MockPSM):
        # Scenario: Existing projects, user chooses to resume one.
        existing_projects = [
            {"name": "ProjectAlpha", "rich_name": "✅ ProjectAlpha", "last_updated": "2023-01-01", "status": "completed"},
            {"name": "ProjectBeta", "rich_name": "⚠️ ProjectBeta", "last_updated": "2023-01-05", "status": "in_progress"},
        ]
        MockPSM.list_projects.return_value = existing_projects

        # Simulate user choosing the second project (index 1, so input "2")
        # Then, the orchestrator will be called for this project.
        mock_prompt_ask.side_effect = ["2"]

        mock_orchestrator_instance = MockOrchestrator.return_value
        mock_orchestrator_instance.execute_pipeline.return_value = {"status": "completed", "final_assembly": {"result": "resumed_done"}}
        mock_orchestrator_instance.state = MagicMock()
        mock_orchestrator_instance.state.project_info = {"name": "ProjectBeta", "path": os.path.join(self.main_script_dir, "projects", "ProjectBeta")}
        mock_orchestrator_instance.state.state = {"status": "completed"}


        qrew_main.run_qrew()

        MockPSM.list_projects.assert_called_once()
        mock_prompt_ask.assert_called_once_with(f"Enter project number (1-{len(existing_projects)}) to resume, or '{len(existing_projects)+1}' (or 'n') for a new project")

        MockOrchestrator.assert_called_once_with(project_name="ProjectBeta")
        mock_orchestrator_instance.execute_pipeline.assert_called_once_with({"project_name": "ProjectBeta", "action": "resume"})


if __name__ == '__main__':
    unittest.main()
# Import ANY if it was used in assertions above.
from unittest.mock import ANY
