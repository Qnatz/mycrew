import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import sys
import json

project_root_for_test = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if project_root_for_test not in sys.path:
    sys.path.insert(0, project_root_for_test)

from mycrews.qrew.workflows.idea_to_architecture_flow import run_idea_to_architecture_workflow, _perform_architecture_generation
# Import agents to allow patching them if they are directly used for creating Tasks
from mycrews.qrew.orchestrators.idea_interpreter_agent.agent import idea_interpreter_agent
from mycrews.qrew.orchestrators.project_architect_agent.agent import project_architect_agent

class TestIdeaToArchitectureFlow(unittest.TestCase):

    @patch('mycrews.qrew.workflows.idea_to_architecture_flow.Crew') # Patching Crew used by _perform_architecture_generation
    def test_perform_architecture_generation_with_tech_vetting_input(self, MockCrew):
        # Mock the two crew kickoff calls within _perform_architecture_generation
        mock_idea_crew_instance = MagicMock()
        mock_idea_crew_instance.kickoff.return_value = MagicMock(raw="Mocked requirements doc")

        mock_arch_crew_instance = MagicMock()
        mock_arch_crew_instance.kickoff.return_value = MagicMock(raw="Mocked architecture doc")

        # Make MockCrew return these instances sequentially
        MockCrew.side_effect = [mock_idea_crew_instance, mock_arch_crew_instance]

        # Store tasks passed to Crew for assertion
        idea_task_passed = None
        arch_task_passed = None

        def capture_tasks_idea(*args, **kwargs):
            nonlocal idea_task_passed
            idea_task_passed = kwargs.get('tasks', [None])[0]
            return mock_idea_crew_instance

        def capture_tasks_arch(*args, **kwargs):
            nonlocal arch_task_passed
            arch_task_passed = kwargs.get('tasks', [None])[0]
            return mock_arch_crew_instance

        MockCrew.side_effect = [capture_tasks_idea, capture_tasks_arch]


        inputs = {
            "project_name": "WebAppX",
            "taskmaster": {
                "refined_brief": "Build a scalable web application for X.",
            },
            "tech_vetting": {
                "vetting_report_markdown": "Vetting report details...",
                "recommended_tech_stack": {"frontend": "Vue.js", "backend": "FastAPI"},
                "architectural_guidelines_markdown": "- Use RESTful APIs.\n- Stateless services."
            },
            "stakeholder_feedback": "Needs to be fast.",
            "constraints": "Within $10k budget."
        }

        result = _perform_architecture_generation(inputs)

        self.assertEqual(MockCrew.call_count, 2) # One for idea, one for arch

        # Check idea interpretation task
        self.assertIsNotNone(idea_task_passed)
        self.assertIn("Refined Brief from Taskmaster: 'Build a scalable web application for X.'", idea_task_passed.description)
        self.assertIn("Tech Vetting Report (for context and to resolve ambiguities):\nVetting report details...", idea_task_passed.description)
        self.assertEqual(idea_task_passed.agent, idea_interpreter_agent)

        # Check project architecture task
        self.assertIsNotNone(arch_task_passed)
        self.assertIn("Technical Requirements Specification:\nMocked requirements doc", arch_task_passed.description)
        self.assertIn('A prior Tech Vetting stage has recommended the following technology stack: {"frontend": "Vue.js", "backend": "FastAPI"}', arch_task_passed.description)
        self.assertIn("You MUST base your architecture on this recommended stack.", arch_task_passed.description)
        self.assertIn("You MUST follow these architectural guidelines:\n'''\n- Use RESTful APIs.\n- Stateless services.\n'''", arch_task_passed.description)
        self.assertEqual(arch_task_passed.agent, project_architect_agent)
        self.assertIn("If a pre-vetted tech stack was provided, confirm its adoption or clearly justify any deviations.", arch_task_passed.expected_output)

        self.assertEqual(result["requirements_document_markdown"], "Mocked requirements doc")
        self.assertEqual(result["architecture_document_markdown"], "Mocked architecture doc")

    @patch('mycrews.qrew.workflows.idea_to_architecture_flow.Crew')
    def test_perform_architecture_generation_without_tech_vetting_input(self, MockCrew):
        mock_idea_crew_instance = MagicMock()
        mock_idea_crew_instance.kickoff.return_value = MagicMock(raw="Basic requirements doc")
        mock_arch_crew_instance = MagicMock()
        mock_arch_crew_instance.kickoff.return_value = MagicMock(raw="Basic architecture doc")
        MockCrew.side_effect = [mock_idea_crew_instance, mock_arch_crew_instance]

        idea_task_passed = None
        arch_task_passed = None
        def capture_tasks_idea(*args, **kwargs):
            nonlocal idea_task_passed
            idea_task_passed = kwargs.get('tasks', [None])[0]
            return mock_idea_crew_instance
        def capture_tasks_arch(*args, **kwargs):
            nonlocal arch_task_passed
            arch_task_passed = kwargs.get('tasks', [None])[0]
            return mock_arch_crew_instance
        MockCrew.side_effect = [capture_tasks_idea, capture_tasks_arch]

        inputs = {
            "project_name": "SimpleApp",
            "taskmaster": {"refined_brief": "Build a simple mobile app."},
            # No "tech_vetting" key in inputs
        }

        result = _perform_architecture_generation(inputs)

        self.assertEqual(MockCrew.call_count, 2)

        self.assertIsNotNone(idea_task_passed)
        self.assertNotIn("Tech Vetting Report", idea_task_passed.description)

        self.assertIsNotNone(arch_task_passed)
        self.assertIn("No specific tech stack was pre-determined by a vetting stage.", arch_task_passed.description)
        self.assertNotIn("A prior Tech Vetting stage has recommended", arch_task_passed.description)
        self.assertNotIn("You MUST follow these architectural guidelines", arch_task_passed.description)
        self.assertNotIn("If a pre-vetted tech stack was provided", arch_task_passed.expected_output)


    @patch('mycrews.qrew.workflows.idea_to_architecture_flow._perform_architecture_generation')
    @patch('mycrews.qrew.workflows.idea_to_architecture_flow.ProjectStateManager')
    def test_run_idea_to_architecture_workflow_new_project(self, MockPSM, mock_perform_arch):
        mock_psm_instance = MockPSM.return_value
        mock_psm_instance.is_completed.return_value = False # Not completed

        mock_generated_artifacts = {
            "requirements_document_markdown": "req_doc",
            "architecture_document_markdown": "arch_doc"
        }
        mock_perform_arch.return_value = mock_generated_artifacts

        inputs = {"project_name": "NewArchProject", "taskmaster": {"refined_brief": "brief"}}

        returned_artifacts = run_idea_to_architecture_workflow(inputs)

        MockPSM.assert_called_once_with("NewArchProject")
        mock_perform_arch.assert_called_once_with(inputs)
        self.assertEqual(returned_artifacts, mock_generated_artifacts)

    @patch('mycrews.qrew.workflows.idea_to_architecture_flow.ProjectStateManager')
    def test_run_idea_to_architecture_workflow_already_completed(self, MockPSM):
        mock_psm_instance = MockPSM.return_value
        mock_psm_instance.is_completed.return_value = True # Already completed
        mock_cached_artifacts = {"cached": "data"}
        mock_psm_instance.get_artifacts.return_value = mock_cached_artifacts

        inputs = {"project_name": "CachedArchProject"}

        # We need to ensure _perform_architecture_generation is NOT called.
        # So, we'll patch it here specifically for this test.
        with patch('mycrews.qrew.workflows.idea_to_architecture_flow._perform_architecture_generation') as mock_perform_arch_local:
            returned_artifacts = run_idea_to_architecture_workflow(inputs)
            mock_perform_arch_local.assert_not_called() # Crucial check

        MockPSM.assert_called_once_with("CachedArchProject")
        mock_psm_instance.get_artifacts.assert_called_once_with("architecture")
        self.assertEqual(returned_artifacts, mock_cached_artifacts)


if __name__ == '__main__':
    unittest.main()
