import unittest
from unittest.mock import patch, MagicMock, call, mock_open
import os
import sys
import json # For creating JSON strings

# Add project root for imports
project_root_for_test = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')) # Adjusted path
if project_root_for_test not in sys.path:
    sys.path.insert(0, project_root_for_test)

# Now import after sys.path is modified
from mycrews.qrew.workflows.orchestrator import WorkflowOrchestrator, validate_taskmaster_output
from mycrews.qrew.project_manager import ProjectStateManager
from crewai import Task # For creating mock Task objects if needed
from crewai.tasks.task_output import TaskOutput # For creating mock TaskOutput


class TestWorkflowOrchestratorLogic(unittest.TestCase):
    def setUp(self):
        # Common setup for tests, like creating an orchestrator instance
        self.orchestrator = WorkflowOrchestrator(project_name=None) # Start fresh for most tests

    @patch('mycrews.qrew.workflows.orchestrator.ProjectStateManager')
    @patch('mycrews.qrew.workflows.orchestrator.run_idea_to_architecture_workflow', return_value={"arch_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_tech_vetting_workflow', return_value={"tech_vetting_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_crew_lead_workflow', return_value={"crew_lead_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_subagent_execution_workflow', return_value={"subagent_exec_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_final_assembly_workflow', return_value={"final_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.WorkflowOrchestrator.run_persist_code_files_workflow', return_value={"persist_output": "done"}) # Mock new stage
    def test_execute_pipeline_tech_vetting_path(self,
                                                mock_persist_code, mock_final_assembly, mock_subagent_exec, mock_crew_lead,
                                                mock_tech_vetting, mock_architecture, MockPSM):
        mock_psm_instance = MockPSM.return_value
        mock_psm_instance.state = {"status": "new"}
        mock_psm_instance.is_completed.return_value = False
        mock_psm_instance.get_artifacts.return_value = {}
        mock_psm_instance.project_info = {"name": "TestProjectTechVetting", "path": "/fake/path"}


        orchestrator = WorkflowOrchestrator()
        mock_taskmaster_output = {
            "project_name": "TestProjectTechVetting",
            "refined_brief": "Brief for tech vetting path.",
            "is_new_project": True,
            "recommended_next_stage": "tech_vetting",
            "project_scope": "full-stack"
        }
        # Instead of mocking the whole run_taskmaster_workflow, we mock the Crew and Task inside it.
        # However, for this existing test, let's keep its structure and add new focused tests later.
        orchestrator.run_taskmaster_workflow = MagicMock(return_value=mock_taskmaster_output)

        initial_inputs = {"user_request": "test request for tech vetting"}
        orchestrator.execute_pipeline(initial_inputs)

        MockPSM.assert_called_with("TestProjectTechVetting")
        orchestrator.run_taskmaster_workflow.assert_called_once_with(initial_inputs)
        mock_psm_instance.complete_stage.assert_any_call("taskmaster", artifacts=mock_taskmaster_output)
        mock_tech_vetting.assert_called_once()
        mock_architecture.assert_called_once()
        mock_crew_lead.assert_called_once()
        mock_subagent_exec.assert_called_once()
        mock_final_assembly.assert_called_once()
        mock_persist_code.assert_called_once() # Assert new stage is called

    @patch('mycrews.qrew.workflows.orchestrator.ProjectStateManager')
    @patch('mycrews.qrew.workflows.orchestrator.run_idea_to_architecture_workflow', return_value={"arch_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_tech_vetting_workflow', return_value={"tech_vetting_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_crew_lead_workflow', return_value={"crew_lead_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_subagent_execution_workflow', return_value={"subagent_exec_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_final_assembly_workflow', return_value={"final_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.WorkflowOrchestrator.run_persist_code_files_workflow', return_value={"persist_output": "done"})
    def test_execute_pipeline_direct_to_architecture_path(self,
                                                        mock_persist_code, mock_final_assembly, mock_subagent_exec, mock_crew_lead,
                                                        mock_tech_vetting, mock_architecture, MockPSM):
        mock_psm_instance = MockPSM.return_value
        mock_psm_instance.state = {"status": "new"}
        mock_psm_instance.is_completed.return_value = False
        mock_psm_instance.get_artifacts.return_value = {}
        mock_psm_instance.project_info = {"name": "TestProjectArchitecture", "path": "/fake/path"}


        orchestrator = WorkflowOrchestrator()
        mock_taskmaster_output = {
            "project_name": "TestProjectArchitecture",
            "refined_brief": "Brief for direct architecture path.",
            "is_new_project": True,
            "recommended_next_stage": "architecture",
            "project_scope": "full-stack"
        }
        orchestrator.run_taskmaster_workflow = MagicMock(return_value=mock_taskmaster_output)

        initial_inputs = {"user_request": "test request for architecture"}
        orchestrator.execute_pipeline(initial_inputs)

        MockPSM.assert_called_with("TestProjectArchitecture")
        mock_tech_vetting.assert_not_called()
        mock_architecture.assert_called_once()
        mock_crew_lead.assert_called_once()
        mock_subagent_exec.assert_called_once()
        mock_final_assembly.assert_called_once()
        mock_persist_code.assert_called_once()

    @patch('mycrews.qrew.workflows.orchestrator.ProjectStateManager')
    @patch('mycrews.qrew.workflows.orchestrator.Crew')
    @patch('mycrews.qrew.workflows.orchestrator.Task') # Patch Task from crewai
    def test_run_taskmaster_workflow_success_with_guardrail(self, MockTask, MockCrew, MockPSM):
        """Test run_taskmaster_workflow successful execution including guardrail."""
        orchestrator = WorkflowOrchestrator()
        initial_inputs = {"user_request": "Create a simple web app"}

        # Mock the Task instance that will be created
        mock_task_instance = MockTask.return_value

        # This is the raw JSON string the LLM (mocked via task output) would return
        valid_json_output_str = json.dumps({
            "project_name": "WebAppProject",
            "refined_brief": "A simple web application.",
            "is_new_project": True,
            "recommended_next_stage": "architecture",
            "project_scope": "web-only"
        })
        # Simulate the TaskOutput object structure
        mock_task_instance.output = TaskOutput(raw_output=f"```json\n{valid_json_output_str}\n```")

        # Mock Crew instance and its kickoff method
        mock_crew_instance = MockCrew.return_value
        mock_crew_instance.kickoff.return_value = "Crew kickoff successful" # Actual return value doesn't matter much here

        result = orchestrator.run_taskmaster_workflow(initial_inputs)

        MockTask.assert_called_once() # Ensure Task was created
        self.assertEqual(MockTask.call_args[1]['guardrail'], validate_taskmaster_output) # Check guardrail was passed

        MockCrew.assert_called_once_with(agents=[ANY], tasks=[mock_task_instance], verbose=ANY) # ANY from unittest.mock if needed, or check specific agent
        mock_crew_instance.kickoff.assert_called_once()

        self.assertEqual(result["project_name"], "WebAppProject")
        self.assertEqual(result["project_scope"], "web-only")

    @patch('mycrews.qrew.workflows.orchestrator.Crew')
    @patch('mycrews.qrew.workflows.orchestrator.Task')
    def test_run_taskmaster_workflow_guardrail_failure(self, MockTask, MockCrew):
        """Test run_taskmaster_workflow when guardrail fails."""
        orchestrator = WorkflowOrchestrator()
        initial_inputs = {"user_request": "test"}

        mock_task_instance = MockTask.return_value
        # Simulate TaskOutput that will fail the guardrail (e.g. missing required key)
        invalid_json_output_str = json.dumps({"project_name": "Incomplete"})
        mock_task_instance.output = TaskOutput(raw_output=invalid_json_output_str)

        # Make the guardrail fail. Since kickoff calls the task execution which applies the guardrail,
        # a guardrail failure in CrewAI usually raises an exception if retries are exhausted.
        mock_crew_instance = MockCrew.return_value
        mock_crew_instance.kickoff.side_effect = Exception("Guardrail failed after retries")


        result = orchestrator.run_taskmaster_workflow(initial_inputs)

        self.assertIn("error", result.get("project_name", "")) # Or check specific error field
        self.assertTrue(result.get("taskmaster_error", "").startswith("Kickoff exception: Guardrail failed"))


    def test_validate_taskmaster_output_valid(self):
        """Test validate_taskmaster_output with valid TaskOutput."""
        valid_data = {
            "project_name": "ValidProject", "refined_brief": "Brief.",
            "is_new_project": False, "recommended_next_stage": "tech_vetting",
            "project_scope": "mobile-only"
        }
        # Test with and without markdown code block
        raw_outputs = [
            f"```json\n{json.dumps(valid_data)}\n```",
            json.dumps(valid_data)
        ]
        for raw in raw_outputs:
            mock_task_output = MagicMock(spec=TaskOutput)
            mock_task_output.raw = raw
            is_valid, data_or_msg = validate_taskmaster_output(mock_task_output)
            self.assertTrue(is_valid, f"Validation failed for raw output: {raw}")
            self.assertEqual(data_or_msg, valid_data)

    def test_validate_taskmaster_output_invalid(self):
        """Test validate_taskmaster_output with various invalid TaskOutputs."""
        invalid_scenarios = {
            "not_a_string": (TaskOutput(raw_output=123), "Guardrail input (task_output.raw) must be a string"),
            "malformed_json": (TaskOutput(raw_output="```json\n{'project_name': 'Test'}\n```"), "Output must be valid JSON."), # Single quotes
            "not_a_dict": (TaskOutput(raw_output="[1,2,3]"), "Output must be a JSON dictionary."),
            "missing_key": (TaskOutput(raw_output=json.dumps({"refined_brief": "B"})), "Missing key in output: project_name"),
            "wrong_type_project_name": (TaskOutput(raw_output=json.dumps({**json.loads(json.dumps(VALID_TASKMASTER_DICT_MINIMAL)), "project_name": 123})), "project_name must be a non-empty string."),
            "wrong_type_is_new_project": (TaskOutput(raw_output=json.dumps({**json.loads(json.dumps(VALID_TASKMASTER_DICT_MINIMAL)), "is_new_project": "true"})), "is_new_project must be a boolean."),
        }
        for test_name, (mock_task_output, expected_msg_part) in invalid_scenarios.items():
            with self.subTest(test_name=test_name):
                is_valid, data_or_msg = validate_taskmaster_output(mock_task_output)
                self.assertFalse(is_valid)
                self.assertTrue(expected_msg_part in data_or_msg, f"Expected '{expected_msg_part}' in '{data_or_msg}'")

    @patch('mycrews.qrew.workflows.orchestrator.os.makedirs')
    @patch('mycrews.qrew.workflows.orchestrator.open', new_callable=mock_open)
    def test_run_persist_code_files_workflow_success(self, mock_file_open, mock_makedirs):
        """Test successful persistence of generated code files."""
        orchestrator = WorkflowOrchestrator(project_name="TestPersist")
        # Mock ProjectStateManager directly on the instance for this test
        orchestrator.state = MagicMock(spec=ProjectStateManager)
        orchestrator.state.project_info = {"name": "TestPersist", "path": "/test/projects/TestPersist"}

        generated_files = {
            "src/main.py": "print('hello')",
            "README.md": "# Test Project"
        }
        inputs = {"final_assembly": {"generated_files": generated_files}}

        result = orchestrator.run_persist_code_files_workflow(inputs)

        self.assertEqual(result["status"], "success")
        self.assertIn("All generated files persisted successfully.", result["message"])
        self.assertEqual(len(result["files_written"]), 2)

        expected_path_main = os.path.join("/test/projects/TestPersist", "src/main.py")
        expected_path_readme = os.path.join("/test/projects/TestPersist", "README.md")

        mock_makedirs.assert_any_call(os.path.dirname(expected_path_main), exist_ok=True)
        mock_makedirs.assert_any_call(os.path.dirname(expected_path_readme), exist_ok=True)

        mock_file_open.assert_any_call(expected_path_main, "w", encoding="utf-8")
        mock_file_open.assert_any_call(expected_path_readme, "w", encoding="utf-8")

        # Check content written (simplified)
        # mock_file_open().write.assert_any_call("print('hello')") # This gets tricky with multiple calls
        # For more robust check, you might inspect call_args_list of mock_file_open().write

    @patch('mycrews.qrew.workflows.orchestrator.os.makedirs')
    @patch('mycrews.qrew.workflows.orchestrator.open', new_callable=mock_open)
    def test_run_persist_code_files_path_traversal_attempt(self, mock_file_open, mock_makedirs):
        orchestrator = WorkflowOrchestrator(project_name="TestTraversal")
        orchestrator.state = MagicMock(spec=ProjectStateManager)
        orchestrator.state.project_info = {"name": "TestTraversal", "path": "/test/projects/TestTraversal"}

        generated_files = {"../outside_project.txt": "danger"}
        inputs = {"final_assembly": {"generated_files": generated_files}}

        result = orchestrator.run_persist_code_files_workflow(inputs)

        self.assertEqual(result["status"], "partial_success") # Or "error" depending on how you want to class it
        self.assertIn("Path traversal attempt", result["errors"][0])
        mock_file_open.assert_not_called()


# Helper for valid taskmaster output, to reduce repetition in tests
VALID_TASKMASTER_DICT_MINIMAL = {
    "project_name": "ValidProject", "refined_brief": "Brief.",
    "is_new_project": False, "recommended_next_stage": "tech_vetting",
    "project_scope": "mobile-only"
}


# Keep the existing full pipeline tests but ensure they mock the new persist stage
class TestWorkflowOrchestratorPipelineFlows(unittest.TestCase): # Renamed class
    @patch('mycrews.qrew.workflows.orchestrator.ProjectStateManager')
    @patch('mycrews.qrew.workflows.orchestrator.run_idea_to_architecture_workflow', return_value={"arch_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_tech_vetting_workflow', return_value={"tech_vetting_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_crew_lead_workflow', return_value={"crew_lead_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_subagent_execution_workflow', return_value={"subagent_exec_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_final_assembly_workflow', return_value={"final_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.WorkflowOrchestrator.run_persist_code_files_workflow', return_value={"persist_output": "done"}) # Mock new stage
    @patch('mycrews.qrew.workflows.orchestrator.RichProjectReporter')
    def test_execute_pipeline_full_completion_and_finalization(self,
                                                                MockRichProjectReporter,
                                                                mock_persist_code, # Added mock for new stage
                                                                mock_final_assembly,
                                                                mock_subagent_exec,
                                                                mock_crew_lead,
                                                                mock_tech_vetting,
                                                                mock_architecture,
                                                                MockPSM):
        mock_psm_instance = MockPSM.return_value
        mock_psm_instance.state = {"status": "in_progress"}
        _completed_stages_for_test = set()
        def mock_is_completed_side_effect(stage_name): return stage_name in _completed_stages_for_test
        def mock_complete_stage_side_effect(stage_name, artifacts=None):
            _completed_stages_for_test.add(stage_name)
            if stage_name == "project_finalization": mock_psm_instance.state["status"] = "completed"

        mock_psm_instance.is_completed.side_effect = mock_is_completed_side_effect
        mock_psm_instance.complete_stage.side_effect = mock_complete_stage_side_effect
        mock_psm_instance.finalize_project = MagicMock(side_effect=lambda: mock_complete_stage_side_effect("project_finalization"))
        mock_psm_instance.get_artifacts.return_value = {}
        mock_psm_instance.project_info = {"name": "TestProjectFinalize", "path": "/fake/path"}


        orchestrator = WorkflowOrchestrator()
        mock_taskmaster_output = {
            "project_name": "TestProjectFinalize", "refined_brief": "Brief for finalization test.",
            "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "full-stack"
        }
        orchestrator.run_taskmaster_workflow = MagicMock(return_value=mock_taskmaster_output)
        initial_inputs = {"user_request": "test request for finalization"}
        orchestrator.execute_pipeline(initial_inputs)

        orchestrator.run_taskmaster_workflow.assert_called_once()
        mock_architecture.assert_called_once()
        mock_crew_lead.assert_called_once()
        mock_subagent_exec.assert_called_once()
        mock_final_assembly.assert_called_once()
        mock_persist_code.assert_called_once() # Assert new stage

        # Include "persist_generated_code" in expected stages that run in the loop
        expected_stages_run_in_loop = ["taskmaster", "architecture", "crew_assignment", "subagent_execution", "final_assembly", "persist_generated_code"]
        for stage in expected_stages_run_in_loop:
            self.assertIn(stage, _completed_stages_for_test, f"Stage {stage} was not marked as completed.")

        mock_psm_instance.finalize_project.assert_called_once()
        self.assertIn("project_finalization", _completed_stages_for_test)

        is_completed_calls = [call_args[0][0] for call_args in mock_psm_instance.is_completed.call_args_list]
        for stage_name_in_all_stages in WorkflowOrchestrator.ALL_PIPELINE_STAGES:
            self.assertIn(stage_name_in_all_stages, is_completed_calls)
        MockRichProjectReporter.assert_called_once_with(mock_psm_instance.state)
        MockRichProjectReporter.return_value.print_report.assert_called_once()


if __name__ == '__main__':
    unittest.main()
# Need to import ANY for the MockCrew assertion if used.
from unittest.mock import ANY
