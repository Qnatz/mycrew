import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Add project root for imports
project_root_for_test = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root_for_test not in sys.path:
    sys.path.insert(0, project_root_for_test)

from mycrews.qrew.workflows.orchestrator import WorkflowOrchestrator
from mycrews.qrew.project_manager import ProjectStateManager

class TestWorkflowOrchestratorLogic(unittest.TestCase):

    @patch('mycrews.qrew.workflows.orchestrator.ProjectStateManager')
    @patch('mycrews.qrew.workflows.orchestrator.run_idea_to_architecture_workflow', return_value={"arch_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_tech_vetting_workflow', return_value={"tech_vetting_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_crew_lead_workflow', return_value={"crew_lead_output": "done"}) # Mock other stages
    @patch('mycrews.qrew.workflows.orchestrator.run_subagent_execution_workflow', return_value={"subagent_exec_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_final_assembly_workflow', return_value={"final_output": "done"})
    def test_execute_pipeline_tech_vetting_path(self,
                                                mock_final_assembly, mock_subagent_exec, mock_crew_lead,
                                                mock_tech_vetting, mock_architecture, MockPSM):

        # Mock ProjectStateManager instance and its methods
        mock_psm_instance = MockPSM.return_value
        mock_psm_instance.state = {"status": "new"} # Simulate a new project state initially
        mock_psm_instance.is_completed.return_value = False
        mock_psm_instance.get_artifacts.return_value = {} # No existing artifacts initially

        orchestrator = WorkflowOrchestrator() # Test with orchestrator determining project name

        # Mock taskmaster workflow part of the orchestrator
        mock_taskmaster_output = {
            "project_name": "TestProjectTechVetting",
            "refined_brief": "Brief for tech vetting path.",
            "is_new_project": True,
            "recommended_next_stage": "tech_vetting"
        }
        orchestrator.run_taskmaster_workflow = MagicMock(return_value=mock_taskmaster_output)

        initial_inputs = {"user_request": "test request for tech vetting"}
        orchestrator.execute_pipeline(initial_inputs)

        # Check that ProjectStateManager was initialized with the project name from taskmaster
        MockPSM.assert_called_with("TestProjectTechVetting")

        # Check that taskmaster was called (implicitly via execute_pipeline's internal logic)
        orchestrator.run_taskmaster_workflow.assert_called_once_with(initial_inputs)
        mock_psm_instance.complete_stage.assert_any_call("taskmaster", artifacts=mock_taskmaster_output)

        # Check that tech_vetting workflow was called
        mock_tech_vetting.assert_called_once()
        # Inputs to tech_vetting should include taskmaster outputs
        args_tech_vetting, _ = mock_tech_vetting.call_args
        self.assertIn("taskmaster", args_tech_vetting[0])
        self.assertEqual(args_tech_vetting[0]["taskmaster"]["project_name"], "TestProjectTechVetting")
        mock_psm_instance.complete_stage.assert_any_call("tech_vetting", artifacts={"tech_vetting_output": "done"})

        # Check that architecture workflow was called
        mock_architecture.assert_called_once()
        args_architecture, _ = mock_architecture.call_args
        self.assertIn("taskmaster", args_architecture[0])
        self.assertIn("tech_vetting", args_architecture[0]) # Ensure tech_vetting artifacts are passed
        self.assertEqual(args_architecture[0]["tech_vetting"]["tech_vetting_output"], "done")
        mock_psm_instance.complete_stage.assert_any_call("architecture", artifacts={"arch_output": "done"})

        # Check other stages were called
        mock_crew_lead.assert_called_once()
        mock_subagent_exec.assert_called_once()
        mock_final_assembly.assert_called_once()


    @patch('mycrews.qrew.workflows.orchestrator.ProjectStateManager')
    @patch('mycrews.qrew.workflows.orchestrator.run_idea_to_architecture_workflow', return_value={"arch_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_tech_vetting_workflow', return_value={"tech_vetting_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_crew_lead_workflow', return_value={"crew_lead_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_subagent_execution_workflow', return_value={"subagent_exec_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_final_assembly_workflow', return_value={"final_output": "done"})
    def test_execute_pipeline_direct_to_architecture_path(self,
                                                        mock_final_assembly, mock_subagent_exec, mock_crew_lead,
                                                        mock_tech_vetting, mock_architecture, MockPSM):

        mock_psm_instance = MockPSM.return_value
        mock_psm_instance.state = {"status": "new"}
        mock_psm_instance.is_completed.return_value = False
        mock_psm_instance.get_artifacts.return_value = {}

        orchestrator = WorkflowOrchestrator()

        mock_taskmaster_output = {
            "project_name": "TestProjectArchitecture",
            "refined_brief": "Brief for direct architecture path.",
            "is_new_project": True,
            "recommended_next_stage": "architecture"
        }
        orchestrator.run_taskmaster_workflow = MagicMock(return_value=mock_taskmaster_output)

        initial_inputs = {"user_request": "test request for architecture"}
        orchestrator.execute_pipeline(initial_inputs)

        MockPSM.assert_called_with("TestProjectArchitecture")
        orchestrator.run_taskmaster_workflow.assert_called_once_with(initial_inputs)
        mock_psm_instance.complete_stage.assert_any_call("taskmaster", artifacts=mock_taskmaster_output)

        # Check that tech_vetting workflow was NOT called
        mock_tech_vetting.assert_not_called()

        # Check that architecture workflow was called
        mock_architecture.assert_called_once()
        args_architecture, _ = mock_architecture.call_args
        self.assertIn("taskmaster", args_architecture[0])
        self.assertNotIn("tech_vetting", args_architecture[0]) # Ensure tech_vetting artifacts are NOT passed
        mock_psm_instance.complete_stage.assert_any_call("architecture", artifacts={"arch_output": "done"})

        mock_crew_lead.assert_called_once()
        mock_subagent_exec.assert_called_once()
        mock_final_assembly.assert_called_once()

    @patch('mycrews.qrew.workflows.orchestrator.ProjectStateManager')
    @patch('mycrews.qrew.workflows.orchestrator.run_idea_to_architecture_workflow', return_value={"arch_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_tech_vetting_workflow', return_value={"tech_vetting_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_crew_lead_workflow', return_value={"crew_lead_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_subagent_execution_workflow', return_value={"subagent_exec_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.run_final_assembly_workflow', return_value={"final_output": "done"})
    @patch('mycrews.qrew.workflows.orchestrator.RichProjectReporter') # Mock the reporter
    def test_execute_pipeline_full_completion_and_finalization(self,
                                                                MockRichProjectReporter,
                                                                mock_final_assembly,
                                                                mock_subagent_exec,
                                                                mock_crew_lead,
                                                                mock_tech_vetting,
                                                                mock_architecture,
                                                                MockPSM):

        mock_psm_instance = MockPSM.return_value
        mock_psm_instance.state = {"status": "in_progress"} # Start as in_progress

        # Simulate stage completion tracking
        _completed_stages_for_test = set()

        def mock_is_completed_side_effect(stage_name):
            return stage_name in _completed_stages_for_test

        def mock_complete_stage_side_effect(stage_name, artifacts=None):
            _completed_stages_for_test.add(stage_name)
            # Simulate the actual state update for 'status' upon finalization
            if stage_name == "project_finalization":
                mock_psm_instance.state["status"] = "completed"


        mock_psm_instance.is_completed.side_effect = mock_is_completed_side_effect
        mock_psm_instance.complete_stage.side_effect = mock_complete_stage_side_effect
        # Ensure finalize_project can be called and we can check its call
        mock_psm_instance.finalize_project = MagicMock(side_effect=lambda: mock_complete_stage_side_effect("project_finalization"))


        mock_psm_instance.get_artifacts.return_value = {}

        orchestrator = WorkflowOrchestrator()

        mock_taskmaster_output = {
            "project_name": "TestProjectFinalize",
            "refined_brief": "Brief for finalization test.",
            "is_new_project": True,
            "recommended_next_stage": "architecture" # Skip tech_vetting for this test's focus
        }
        orchestrator.run_taskmaster_workflow = MagicMock(return_value=mock_taskmaster_output)

        initial_inputs = {"user_request": "test request for finalization"}
        orchestrator.execute_pipeline(initial_inputs)

        # Assertions
        orchestrator.run_taskmaster_workflow.assert_called_once()
        mock_architecture.assert_called_once()
        mock_crew_lead.assert_called_once()
        mock_subagent_exec.assert_called_once()
        mock_final_assembly.assert_called_once()

        # Verify all stages in ALL_PIPELINE_STAGES (excluding tech_vetting in this path, and project_finalization which is special)
        # were attempted to be completed.
        # The complete_stage mock will add them to _completed_stages_for_test
        expected_stages_run_in_loop = ["taskmaster", "architecture", "crew_assignment", "subagent_execution", "final_assembly"]
        for stage in expected_stages_run_in_loop:
            self.assertIn(stage, _completed_stages_for_test)

        # Verify that finalize_project was called
        mock_psm_instance.finalize_project.assert_called_once()

        # Verify that "project_finalization" was marked as complete via the finalize_project call
        self.assertIn("project_finalization", _completed_stages_for_test)

        # Verify is_completed was called for all stages in ALL_PIPELINE_STAGES during the final check
        # This is a bit tricky because is_completed is also called in the main loop.
        # We are interested in the calls that happen *after* the loop, inside the all(...) check.
        # For simplicity, we can check if it was called for 'project_finalization' as that's only in the final check.
        is_completed_calls = [call_args[0][0] for call_args in mock_psm_instance.is_completed.call_args_list]
        # Ensure all stages from the canonical list were checked
        for stage_name_in_all_stages in WorkflowOrchestrator.ALL_PIPELINE_STAGES:
            self.assertIn(stage_name_in_all_stages, is_completed_calls)

        # Verify RichProjectReporter was called
        MockRichProjectReporter.assert_called_once_with(mock_psm_instance.state)
        reporter_instance = MockRichProjectReporter.return_value
        reporter_instance.print_report.assert_called_once()


if __name__ == '__main__':
    unittest.main()
