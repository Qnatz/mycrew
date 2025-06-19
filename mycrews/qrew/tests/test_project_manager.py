import unittest
import json
from pathlib import Path
import shutil
from datetime import datetime, timezone
import os # For path manipulation if needed, though pathlib is preferred

# Module to be tested
from mycrews.qrew.project_manager import ProjectStateManager
# Import the module itself for monkeypatching global variables like PROJECTS_ROOT
import mycrews.qrew.project_manager as pm_module

class TestProjectStateManagerListProjects(unittest.TestCase):

    def setUp(self):
        """Set up a temporary projects root directory for testing."""
        self.temp_projects_root_path = Path("temp_test_projects_dir_list")
        self.temp_projects_root_path.mkdir(parents=True, exist_ok=True)

        # Monkeypatch the PROJECTS_ROOT used by ProjectStateManager
        self.original_projects_root = pm_module.PROJECTS_ROOT
        pm_module.PROJECTS_ROOT = self.temp_projects_root_path

    def tearDown(self):
        """Clean up by restoring original PROJECTS_ROOT and removing the temporary directory."""
        pm_module.PROJECTS_ROOT = self.original_projects_root
        if self.temp_projects_root_path.exists():
            shutil.rmtree(self.temp_projects_root_path)

    def _create_project_dir(self, dir_name: str, state_content: dict = None, make_corrupt: bool = False):
        """Helper method to create a project directory with an optional state.json file."""
        project_dir = self.temp_projects_root_path / dir_name
        project_dir.mkdir(parents=True, exist_ok=True)
        if state_content is not None:
            state_file = project_dir / "state.json"
            if make_corrupt:
                state_file.write_text("{corrupt_json_data,,")
            else:
                state_file.write_text(json.dumps(state_content))
        return project_dir

    def test_list_projects_empty(self):
        """Test listing projects when the projects root directory is empty."""
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 0)

    def test_list_project_completed(self):
        """Test listing a single completed project."""
        timestamp_str = "2023-01-01T10:00:00Z"
        self._create_project_dir("proj_completed", {
            "status": "completed",
            "project_name": "Test Project Completed",
            "updated_at": timestamp_str
        })
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        self.assertEqual(proj["name"], "Test Project Completed")
        self.assertEqual(proj["status"], "completed")
        self.assertTrue(proj["rich_name"].startswith("✅"))
        # Check if the formatted timestamp is present
        # datetime.fromisoformat handles 'Z' correctly as UTC
        dt_obj = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        # Format might vary slightly based on local system's strftime for %Z if timezone is not UTC.
        # The implementation uses .strip() for strftime("%Y-%m-%d %H:%M:%S %Z").strip()
        # For UTC, %Z might be empty or "UTC".
        expected_time_str_part = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
        self.assertIn(expected_time_str_part, proj["last_updated"])
        self.assertEqual(proj["key"], "proj_completed")

    def test_list_project_failed(self):
        """Test listing a single failed project with an error message."""
        self._create_project_dir("proj_failed", {
            "status": "failed",
            "project_name": "Test Project Failed",
            "error_summary": [{"success": False, "message": "It broke"}]
        })
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        self.assertEqual(proj["status"], "failed")
        self.assertTrue(proj["rich_name"].startswith("❌"))
        self.assertEqual(proj["error_message"], "It broke")

    def test_list_project_in_progress(self):
        """Test listing a project that is in_progress."""
        self._create_project_dir("proj_inprogress", {
            "status": "in_progress",
            "project_name": "In Progress Project"
        })
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        self.assertEqual(proj["status"], "in_progress")
        # As per current list_projects, "in_progress" does not get a special prefix
        self.assertFalse(proj["rich_name"].startswith("✅"))
        self.assertFalse(proj["rich_name"].startswith("❌"))
        self.assertFalse(proj["rich_name"].startswith("⚠️"))
        self.assertEqual(proj["name"], "In Progress Project")


    def test_list_project_missing_state_json(self):
        """Test listing a project where state.json is missing."""
        self._create_project_dir("proj_missing_state") # No state_content
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        self.assertEqual(proj["status"], "Error - State file missing")
        self.assertTrue(proj["rich_name"].startswith("⚠️"))
        self.assertEqual(proj["name"], "Proj Missing State") # Name derived from dir name

    def test_list_project_corrupt_state_json(self):
        """Test listing a project with a corrupt state.json file."""
        self._create_project_dir("proj_corrupt_state", make_corrupt=True, state_content={"project_name": "Corrupt"})
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        self.assertEqual(proj["status"], "Error - State file corrupted")
        self.assertTrue(proj["rich_name"].startswith("⚠️"))
        self.assertEqual(proj["name"], "Proj Corrupt State") # Name derived from dir name

    def test_list_projects_sorting(self):
        """Test the sorting order of listed projects."""
        self._create_project_dir("proj_c_completed", {"status": "completed", "project_name": "C Completed"})
        self._create_project_dir("proj_a_failed", {"status": "failed", "project_name": "A Failed"})
        self._create_project_dir("proj_e_error_missing", {"project_name": "E Error Missing"}) # No state file
        self._create_project_dir("proj_b_inprogress", {"status": "in_progress", "project_name": "B In Progress"})
        self._create_project_dir("proj_d_unknown", {"status": "unknown", "project_name": "D Unknown"})


        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 5)
        # Expected order: Failed, Errors, Completed, Unknown, Others (like in_progress)
        self.assertEqual(projects[0]["name"], "A Failed")           # status: failed (sort key 0)
        self.assertEqual(projects[1]["name"], "E Error Missing")    # status: Error - State file missing (sort key 1)
        self.assertEqual(projects[2]["name"], "C Completed")        # status: completed (sort key 2)
        self.assertEqual(projects[3]["name"], "D Unknown")          # status: unknown (sort key 3)
        self.assertEqual(projects[4]["name"], "B In Progress")      # status: in_progress (sort key 4)

    def test_project_name_from_state_vs_dirname(self):
        """Test that project name from state.json is preferred over directory name."""
        self._create_project_dir("project_slug_123", {
            "project_name": "My Actual Project Name",
            "status": "testing"
        })
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        self.assertEqual(proj["name"], "My Actual Project Name")
        self.assertEqual(proj["key"], "project_slug_123")

    def test_ignore_files_in_projects_root(self):
        """Test that files in PROJECTS_ROOT (not directories) are ignored."""
        # Create a file directly in the temp projects root
        (self.temp_projects_root_path / "some_file.txt").write_text("hello")

        self._create_project_dir("real_project", {
            "status": "completed",
            "project_name": "Real Project"
        })

        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "Real Project")

    def test_last_updated_fallback_to_created_at(self):
        """Test that last_updated falls back to created_at if updated_at is missing."""
        timestamp_created_str = "2023-02-01T12:00:00Z"
        self._create_project_dir("proj_created_only", {
            "status": "in_progress",
            "project_name": "Created Only Test",
            "created_at": timestamp_created_str
            # "updated_at" is missing
        })
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        dt_obj = datetime.fromisoformat(timestamp_created_str.replace("Z", "+00:00"))
        expected_time_str_part = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
        self.assertIn(expected_time_str_part, proj["last_updated"])

    def test_error_message_extraction_for_failed_project(self):
        """Test detailed error message extraction for failed projects."""
        error_summary = [
            {"stage": "stage1", "success": True, "message": "Completed stage1"},
            {"stage": "stage2", "success": False, "message": "Failed at stage2"},
            {"stage": "stage3", "success": True, "message": "This should not be reached"}
        ]
        self._create_project_dir("proj_complex_fail", {
            "status": "failed",
            "project_name": "Complex Fail Case",
            "error_summary": error_summary
        })
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        self.assertEqual(proj["error_message"], "Failed at stage2")

    def test_error_message_empty_summary_for_failed_project(self):
        """Test failed project with empty error_summary list."""
        self._create_project_dir("proj_empty_summary_fail", {
            "status": "failed",
            "project_name": "Empty Summary Fail",
            "error_summary": []
        })
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        self.assertEqual(proj["error_message"], "Failed, error summary not available or empty.")

    def test_error_message_no_failure_in_summary_for_failed_project(self):
        """Test failed project where error_summary has no explicit failure messages."""
        self._create_project_dir("proj_no_failure_msg_fail", {
            "status": "failed",
            "project_name": "No Failure Message Fail",
            "error_summary": [{"success": True, "message": "All good here"}]
        })
        projects = ProjectStateManager.list_projects()
        self.assertEqual(len(projects), 1)
        proj = projects[0]
        self.assertEqual(proj["error_message"], "Failed, but no specific error message recorded in summary.")


from unittest.mock import patch, MagicMock
# ChromaLogger import might be needed if we were to directly interact with a real test instance,
# but for mocking, it's not strictly necessary to import here unless type hinting or instanceof checks were used.
# from mycrews.qrew.tools.chroma_logger import ChromaLogger

class TestProjectStateManagerInstance(unittest.TestCase):

    def setUp(self):
        """Set up temporary directories and patch ProjectStateManager's dependencies."""
        self.temp_test_base_dir = Path("temp_psm_instance_tests")
        self.temp_test_base_dir.mkdir(parents=True, exist_ok=True)

        self.temp_projects_root_path = self.temp_test_base_dir / "projects_root"
        self.temp_projects_root_path.mkdir(parents=True, exist_ok=True)

        # This path is for a ChromaLogger instance we might manage directly in tests,
        # NOT for the one inside ProjectStateManager unless we specifically configure PSM to use it.
        # For now, we'll mock the PSM's internal ChromaLogger.
        self.temp_chroma_db_path = self.temp_test_base_dir / "test_chroma_psm"
        self.temp_chroma_db_path.mkdir(parents=True, exist_ok=True)

        self.temp_projects_index_file = self.temp_test_base_dir / "temp_projects_index.json"

        # Monkeypatch global paths in the project_manager module (pm_module)
        self.original_projects_root = pm_module.PROJECTS_ROOT
        pm_module.PROJECTS_ROOT = self.temp_projects_root_path

        self.original_projects_index = pm_module.PROJECTS_INDEX
        pm_module.PROJECTS_INDEX = self.temp_projects_index_file

        # If ProjectStateManager directly instantiated ChromaLogger without allowing path override,
        # we'd have to either live with its default path or patch 'chromadb.PersistentClient'
        # or the 'ChromaLogger' class itself within the scope of pm_module.
        # For this subtask, we will mock methods on the psm.chroma_logger instance.

    def tearDown(self):
        """Clean up temporary directories and restore original paths."""
        pm_module.PROJECTS_ROOT = self.original_projects_root
        pm_module.PROJECTS_INDEX = self.original_projects_index

        if self.temp_test_base_dir.exists():
            shutil.rmtree(self.temp_test_base_dir)

        # If we had a self.chroma_logger = ChromaLogger(...) instance for direct use, clear it.
        # e.g., if hasattr(self, 'chroma_logger_instance_for_direct_use'):
        #     self.chroma_logger_instance_for_direct_use.clear_logs() # Assuming such a method

    @patch(f'{pm_module.__name__}.ChromaLogger') # Patch ChromaLogger in the project_manager module
    def test_save_state_writes_to_json_and_calls_chroma(self, MockChromaLogger):
        """Test that save_state writes to state.json and calls chroma_logger.save_project_state."""
        mock_chroma_instance = MagicMock()
        MockChromaLogger.return_value = mock_chroma_instance

        psm = ProjectStateManager("test_project_save", config={"enable_db_logging": True})

        # Ensure the internal chroma_logger is the mocked one
        self.assertEqual(psm.chroma_logger, mock_chroma_instance)

        psm.state["new_key"] = "new_value"
        psm.state["current_stage"] = "test_stage" # Example state data
        psm.save_state()

        # 1. Assert state.json was written correctly
        expected_state_file_path = self.temp_projects_root_path / psm.project_info["id"] / "state.json"
        self.assertTrue(expected_state_file_path.exists())
        with open(expected_state_file_path, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["new_key"], "new_value")
        self.assertEqual(saved_data["current_stage"], "test_stage")

        # 2. Assert chroma_logger.save_project_state was called
        mock_chroma_instance.save_project_state.assert_called_once_with(
            psm.project_info["name"],
            psm.state
        )

    @patch(f'{pm_module.__name__}.ChromaLogger')
    def test_load_state_from_chroma_if_json_missing(self, MockChromaLogger):
        """Test loading state from ChromaDB if state.json is missing."""
        mock_chroma_instance = MagicMock()
        MockChromaLogger.return_value = mock_chroma_instance

        project_name = "test_project_load_chroma"
        expected_state_from_chroma = {
            "project_name": project_name,
            "current_stage": "from_chroma",
            "some_data": "chroma_value",
            "error_summary": [], # Ensure error_summary is part of the state
            "completed_stages": ["initial_setup_chroma"],
            "artifacts": {"initial_setup_chroma": {"detail": "Loaded from Chroma"}}
        }

        # Configure the mock get_project_state to return our test state
        mock_chroma_instance.get_project_state.return_value = expected_state_from_chroma

        # Initialize ProjectStateManager. state.json will not exist for this new project.
        # __init__ calls load_state().
        psm = ProjectStateManager(project_name, config={"enable_db_logging": True})

        # Assert that get_project_state was called
        mock_chroma_instance.get_project_state.assert_called_once_with(project_name)

        # Assert that the state was loaded from the mocked ChromaDB output
        self.assertEqual(psm.state["current_stage"], "from_chroma")
        self.assertEqual(psm.state["some_data"], "chroma_value")
        self.assertEqual(psm.state["completed_stages"], ["initial_setup_chroma"])
        # Check if error_summary was correctly initialized/rehydrated (should be empty from expected_state)
        self.assertEqual(len(psm.error_summary.records), 0)


    @patch(f'{pm_module.__name__}.ChromaLogger')
    def test_load_state_initializes_if_json_and_chroma_missing(self, MockChromaLogger):
        """Test that an initial state is created if both JSON and Chroma state are missing."""
        mock_chroma_instance = MagicMock()
        MockChromaLogger.return_value = mock_chroma_instance

        project_name = "test_project_load_initial"

        # Configure mock get_project_state to return None (no state in Chroma)
        mock_chroma_instance.get_project_state.return_value = None

        psm = ProjectStateManager(project_name, config={"enable_db_logging": True})

        mock_chroma_instance.get_project_state.assert_called_once_with(project_name)

        # Assert that the state is the initial state
        self.assertEqual(psm.state["project_name"], project_name)
        self.assertEqual(psm.state["current_stage"], "initialized")
        self.assertEqual(len(psm.state["completed_stages"]), 0)
        self.assertTrue("created_at" in psm.state)


    @patch(f'{pm_module.__name__}.ChromaLogger')
    def test_fail_stage_logs_to_chroma(self, MockChromaLogger):
        """Test that fail_stage calls chroma_logger.log when DB logging is enabled."""
        mock_chroma_instance = MagicMock()
        MockChromaLogger.return_value = mock_chroma_instance

        psm = ProjectStateManager("test_project_fail_log", config={"enable_db_logging": True})

        self.assertEqual(psm.chroma_logger, mock_chroma_instance)

        test_stage_name = "test_stage_failure"
        test_error_message = "A dummy error occurred"

        # Call fail_stage
        psm.fail_stage(test_stage_name, test_error_message, exception_obj=ValueError("Test Exception"))

        # Assert that chroma_logger.log was called
        # We expect it to be called once.
        mock_chroma_instance.log.assert_called_once()

        # Verify the arguments of the call
        # The first argument to assert_called_once_with is *args, the second is **kwargs
        # We need to capture the actual call arguments to inspect them more easily
        args, kwargs = mock_chroma_instance.log.call_args

        # args[0] is 'content', args[1] is 'stage', args[2] is 'log_type', args[3] is 'metadata'
        # In the implementation, these are passed as keyword arguments.
        self.assertIn(test_error_message, kwargs.get("content", "")) # Check if error message is part of the logged content
        self.assertEqual(kwargs.get("stage"), test_stage_name)
        self.assertEqual(kwargs.get("log_type"), "error")

        metadata_arg = kwargs.get("metadata", {})
        self.assertEqual(metadata_arg.get("stage"), test_stage_name)
        self.assertEqual(metadata_arg.get("error_message"), test_error_message)
        self.assertEqual(metadata_arg.get("exception_type"), "ValueError")
        self.assertTrue("stack_trace" in metadata_arg)


if __name__ == '__main__':
    unittest.main()
