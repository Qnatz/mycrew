import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import sys
import json

project_root_for_test = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if project_root_for_test not in sys.path:
    sys.path.insert(0, project_root_for_test)

from mycrews.qrew.workflows.tech_vetting_flow import run_tech_vetting_workflow
# We will be mocking the crew and its agents, so direct imports of them might not be needed here,
# unless we need their instances for type checking or specific properties.
# from mycrews.qrew.orchestrators.tech_stack_committee.crews.tech_vetting_council_crew import TechVettingCouncilCrew

class TestTechVettingFlow(unittest.TestCase):

    @patch('mycrews.qrew.workflows.tech_vetting_flow.Crew') # Patch the Crew class used in the flow
    @patch('mycrews.qrew.workflows.tech_vetting_flow.TechVettingCouncilCrew') # Patch the CrewBase provider
    def test_run_tech_vetting_workflow_success(self, MockTechVettingCouncilCrewProvider, MockCrew):
        # Mock the crew provider to return instances with mocked agents
        mock_council_instance = MockTechVettingCouncilCrewProvider.return_value
        mock_council_instance.stack_advisor = MagicMock(name="StackAdvisorAgent")
        mock_council_instance.constraint_checker = MagicMock(name="ConstraintCheckerAgent")
        mock_council_instance.doc_writer = MagicMock(name="DocWriterAgent")

        # Mock the Crew instance that will be created and its kickoff method
        mock_crew_instance = MockCrew.return_value
        mock_kickoff_output = {
            "recommended_tech_stack": {"frontend": "React", "backend": "Python"},
            "architectural_guidelines_markdown": "Follow MVC, use microservices.",
            "vetting_report_markdown": "Tech vetting completed. React and Python chosen."
        }
        # Simulate kickoff returning a string that needs JSON parsing (as per one path in the flow)
        # or directly a dict if the last agent's tool/output is a dict.
        # Let's assume the last task's output (recommendation_task by doc_writer) is a raw JSON string.

        # To simulate the most complex path in run_tech_vetting_workflow's output handling,
        # we make kickoff return None, but ensure the last task has the raw JSON string.
        mock_crew_instance.kickoff.return_value = None

        # The flow tries to access mock_crew_instance.tasks[-1].output.raw
        # So, we need to set this up.
        mock_last_task = MagicMock()
        mock_last_task.output = MagicMock()
        mock_last_task.output.raw = json.dumps(mock_kickoff_output)

        # The tasks are added to the crew instance. We need to make it accessible.
        # The Crew class stores tasks in self.tasks.
        # When Crew() is called in the flow, it's given a list of tasks.
        # We can capture this list via the tasks argument to MockCrew constructor.

        # Store the tasks list when Crew is initialized
        tasks_passed_to_crew = []
        def capture_tasks(*args, **kwargs):
            nonlocal tasks_passed_to_crew
            tasks_passed_to_crew = kwargs.get('tasks', [])
            # Now that we have the tasks, we can set the last one's output
            if tasks_passed_to_crew:
                tasks_passed_to_crew[-1].output = MagicMock()
                tasks_passed_to_crew[-1].output.raw = json.dumps(mock_kickoff_output)
            return mock_crew_instance # Return the original mock_crew_instance

        MockCrew.side_effect = capture_tasks


        inputs = {
            "refined_brief": "A detailed project brief for a new social media platform.",
            "project_name": "SocialNet",
            # "requirements_document_markdown": "Some initial requirements..." # Optional
        }

        result = run_tech_vetting_workflow(inputs)

        # Assertions
        MockTechVettingCouncilCrewProvider.assert_called_once()
        MockCrew.assert_called_once() # Crew was instantiated with agents and tasks

        # Check tasks were created and passed to Crew
        self.assertEqual(len(tasks_passed_to_crew), 4) # 4 tasks defined in the flow

        # Check descriptions of tasks (optional, but good for verifying dynamic content)
        self.assertIn("Analyze the refined project brief for 'SocialNet'", tasks_passed_to_crew[0].description)
        self.assertEqual(tasks_passed_to_crew[0].agent, mock_council_instance.stack_advisor)

        self.assertIn("research and propose suitable technology options", tasks_passed_to_crew[1].description)
        self.assertEqual(tasks_passed_to_crew[1].agent, mock_council_instance.stack_advisor)

        self.assertIn("Evaluate the proposed technology options", tasks_passed_to_crew[2].description)
        self.assertEqual(tasks_passed_to_crew[2].agent, mock_council_instance.constraint_checker)

        self.assertIn("Consolidate the findings for project 'SocialNet'", tasks_passed_to_crew[3].description)
        self.assertEqual(tasks_passed_to_crew[3].agent, mock_council_instance.doc_writer)
        self.assertEqual(tasks_passed_to_crew[3].expected_output, "A JSON object containing: "
                        "'recommended_tech_stack': (dict, e.g., {'frontend': 'React', 'backend': 'Node.js', 'database': 'PostgreSQL'}), "
                        "'architectural_guidelines_markdown': (string, markdown format, outlining high-level guidelines and best practices), "
                        "and 'vetting_report_markdown': (string, markdown format, summarizing the entire vetting process, options considered, rationale for choices, and any identified risks or open questions).")

        mock_crew_instance.kickoff.assert_called_once()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["recommended_tech_stack"], mock_kickoff_output["recommended_tech_stack"])
        self.assertEqual(result["architectural_guidelines_markdown"], mock_kickoff_output["architectural_guidelines_markdown"])
        self.assertEqual(result["vetting_report_markdown"], mock_kickoff_output["vetting_report_markdown"])

    def test_run_tech_vetting_workflow_no_brief(self):
        inputs = {"project_name": "TestNoBrief"}
        result = run_tech_vetting_workflow(inputs)
        self.assertEqual(result["status"], "error")
        self.assertIn("Refined brief is required", result["message"])

    @patch('mycrews.qrew.workflows.tech_vetting_flow.Crew')
    @patch('mycrews.qrew.workflows.tech_vetting_flow.TechVettingCouncilCrew')
    def test_run_tech_vetting_workflow_crew_fails(self, MockTechVettingCouncilCrewProvider, MockCrew):
        mock_council_instance = MockTechVettingCouncilCrewProvider.return_value # Dummy instance
        mock_crew_instance = MockCrew.return_value
        mock_crew_instance.kickoff.return_value = None # Simulate crew failure (no output)
        # And also ensure last_task.output.raw is not set or not parseable if kickoff is None
        # In this case, the logic path taken is the one where `vetting_results` is None.

        inputs = {"refined_brief": "A brief.", "project_name": "TestCrewFail"}
        result = run_tech_vetting_workflow(inputs)

        self.assertEqual(result["status"], "error")
        self.assertIn("Tech Vetting Crew execution failed.", result["message"])
        self.assertTrue(result["vetting_report_markdown"].startswith("# Tech Vetting Failed"))

    @patch('mycrews.qrew.workflows.tech_vetting_flow.Crew')
    @patch('mycrews.qrew.workflows.tech_vetting_flow.TechVettingCouncilCrew')
    def test_run_tech_vetting_workflow_bad_json_output(self, MockTechVettingCouncilCrewProvider, MockCrew):
        mock_council_instance = MockTechVettingCouncilCrewProvider.return_value
        mock_crew_instance = MockCrew.return_value

        # Simulate kickoff returning a non-JSON string when one is expected from last task
        tasks_passed_to_crew = []
        def capture_tasks_bad_json(*args, **kwargs):
            nonlocal tasks_passed_to_crew
            tasks_passed_to_crew = kwargs.get('tasks', [])
            if tasks_passed_to_crew:
                tasks_passed_to_crew[-1].output = MagicMock()
                tasks_passed_to_crew[-1].output.raw = "This is not JSON" # Bad output
            return mock_crew_instance

        MockCrew.side_effect = capture_tasks_bad_json
        mock_crew_instance.kickoff.return_value = None # To trigger the last_task.output.raw path

        inputs = {"refined_brief": "A brief.", "project_name": "TestBadJSON"}
        result = run_tech_vetting_workflow(inputs)

        self.assertEqual(result["status"], "partial_success")
        self.assertIn("last task output parsing failed", result["message"])
        self.assertIn("Raw output of last task", result["vetting_report_markdown"])
        self.assertIn("This is not JSON", result["vetting_report_markdown"])
        self.assertEqual(result["raw_output"], "This is not JSON")


if __name__ == '__main__':
    unittest.main()
