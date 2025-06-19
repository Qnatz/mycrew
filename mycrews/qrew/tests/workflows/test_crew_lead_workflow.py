import unittest
import json
from unittest.mock import MagicMock, patch

# Assuming the workflow function is directly importable
from mycrews.qrew.workflows.crew_lead_workflow import run_crew_lead_workflow
from crewai.agent import Agent # Import Agent for spec

# Mock agent objects that would be imported by crew_lead_workflow
# We need to provide them with a 'role' attribute as the workflow uses it for mapping.
# Set spec to Agent to help with Pydantic validation
# and add attributes expected by BaseAgent
mock_llm = MagicMock() # Mock for the llm attribute

mock_backend_agent = MagicMock(spec=Agent)
mock_backend_agent.role = "Backend Project Coordinator"
mock_backend_agent.goal = "Coordinate backend development"
mock_backend_agent.backstory = "A mock backend coordinator"
mock_backend_agent.llm = mock_llm
mock_backend_agent.verbose = False
mock_backend_agent.allow_delegation = False
mock_backend_agent.tools = []
mock_backend_agent.max_rpm = None
mock_backend_agent._token_process = None
mock_backend_agent.security_config = None
mock_backend_agent.function_calling_llm = None
mock_backend_agent.step_callback = None

mock_web_agent = MagicMock(spec=Agent)
mock_web_agent.role = "Web Project Coordinator"
mock_web_agent.goal = "Coordinate web development"
mock_web_agent.backstory = "A mock web coordinator"
mock_web_agent.llm = mock_llm
mock_web_agent.verbose = False
mock_web_agent.allow_delegation = False
mock_web_agent.tools = []
mock_web_agent.max_rpm = None
mock_web_agent._token_process = None
mock_web_agent.security_config = None
mock_web_agent.function_calling_llm = None
mock_web_agent.step_callback = None

mock_mobile_agent = MagicMock(spec=Agent)
mock_mobile_agent.role = "Mobile Project Coordinator"
mock_mobile_agent.goal = "Coordinate mobile development"
mock_mobile_agent.backstory = "A mock mobile coordinator"
mock_mobile_agent.llm = mock_llm
mock_mobile_agent.verbose = False
mock_mobile_agent.allow_delegation = False
mock_mobile_agent.tools = []
mock_mobile_agent.max_rpm = None
mock_mobile_agent._token_process = None
mock_mobile_agent.security_config = None
mock_mobile_agent.function_calling_llm = None
mock_mobile_agent.step_callback = None

mock_devops_agent = MagicMock(spec=Agent)
mock_devops_agent.role = "DevOps and Integration Coordinator"
mock_devops_agent.goal = "Coordinate DevOps and integration"
mock_devops_agent.backstory = "A mock DevOps coordinator"
mock_devops_agent.llm = mock_llm
mock_devops_agent.verbose = False
mock_devops_agent.allow_delegation = False
mock_devops_agent.tools = []
mock_devops_agent.max_rpm = None
mock_devops_agent._token_process = None
mock_devops_agent.security_config = None
mock_devops_agent.function_calling_llm = None
mock_devops_agent.step_callback = None

# The real agents are imported in crew_lead_workflow.py from:
# from ..lead_agents.backend_project_coordinator_agent.agent import backend_project_coordinator_agent
# ... and so on. We need to patch these specific import paths.

class TestCrewLeadWorkflowScopeHandling(unittest.TestCase):

    def test_unknown_scope_excludes_mobile_plan(self):
        """
        Test that when project_scope is 'unknown', run_crew_lead_workflow
        defaults to backend and web plans, and specifically excludes mobile plan tasks.
        """
        mock_inputs = {
            "project_name": "Test Web Project",
            "taskmaster": {
                "project_scope": "unknown"  # Simulate Taskmaster being unsure
            },
            "architecture": { # Simulate some architecture summary
                "summary": "Basic web architecture with API and frontend"
            }
            # crew_assignment (this is what this workflow generates, so not an input here)
        }

        # Mock the Task and Crew execution within the workflow to avoid real LLM calls
        # The key is to control what the sub-crews (backend_planner, web_planner, etc.) return
        # The workflow itself creates Tasks and a Crew. We'll mock `crew.kickoff()`.

        mock_crew_instance = MagicMock()

        # Define what kickoff returns based on which agents were active.
        # For an 'unknown' scope, we expect backend, web, and devops tasks.
        # Each task_output should be a JSON string as expected by the workflow.

        # Plan for backend (simulating output of backend_project_coordinator_agent)
        backend_plan_output = json.dumps({"tasks": ["Backend Task 1", "Backend Task 2"]})
        # Plan for web (simulating output of web_project_coordinator_agent)
        frontend_plan_output = json.dumps({"tasks": ["Frontend Task 1", "Frontend Task 2"]})
        # Plan for devops (simulating output of devops_and_integration_coordinator_agent)
        devops_plan_output = json.dumps({"tasks": ["DevOps Task 1"]})

        # Configure the .execute_task.return_value for the class-level mock agents
        # These are the agent instances that will be used by the Tasks within the workflow.
        mock_backend_agent.execute_task.return_value = backend_plan_output
        mock_web_agent.execute_task.return_value = frontend_plan_output
        mock_devops_agent.execute_task.return_value = devops_plan_output
        # mock_mobile_agent.execute_task should not be called, so no need to set it.

        # These are the objects that the workflow's result processing loop will iterate over,
        # representing the output of each agent's "planning" task.
        mock_backend_task_output_obj = MagicMock()
        mock_backend_task_output_obj.raw = backend_plan_output # The string output

        mock_frontend_task_output_obj = MagicMock()
        mock_frontend_task_output_obj.raw = frontend_plan_output # The string output

        mock_devops_task_output_obj = MagicMock()
        mock_devops_task_output_obj.raw = devops_plan_output # The string output

        # For "unknown" scope, tasks processed by workflow are: backend, web, devops.
        # The order in tasks_output should match this.
        simulated_kickoff_tasks_output = [
            mock_backend_task_output_obj,
            mock_frontend_task_output_obj,
            mock_devops_task_output_obj
        ]
        # Configure mock_crew_instance.kickoff() to return an object
        # that has a .tasks_output attribute, which is our simulated list.
        mock_crew_instance.kickoff.return_value = MagicMock(tasks_output=simulated_kickoff_tasks_output)

        # Patch Crew where it's imported in the workflow module.
        # Patch the agents as well.
        with patch('mycrews.qrew.workflows.crew_lead_workflow.Crew', return_value=mock_crew_instance) as mock_crew_class_for_assert, \
             patch('mycrews.qrew.workflows.crew_lead_workflow.backend_project_coordinator_agent', mock_backend_agent) as mock_backend_dispatch, \
             patch('mycrews.qrew.workflows.crew_lead_workflow.web_project_coordinator_agent', mock_web_agent) as mock_web_dispatch, \
             patch('mycrews.qrew.workflows.crew_lead_workflow.mobile_project_coordinator_agent', mock_mobile_agent) as mock_mobile_dispatch, \
             patch('mycrews.qrew.workflows.crew_lead_workflow.devops_and_integration_coordinator_agent', mock_devops_agent) as mock_devops_dispatch:

            # The run_crew_lead_workflow will now use the mock_crew_instance when it calls Crew(...).
            # Then it calls crew.kickoff(), which will return our mock_crew_instance.kickoff.return_value.
            # The workflow then processes .tasks_output from that.
            # The agent's .execute_task methods are not directly called by this setup if kickoff is fully mocked.
            # However, we set them up earlier in case a less direct mock of kickoff was used.
            # Given the current mock of kickoff, the .execute_task settings on agents are not strictly necessary
            # for *this specific way* of mocking kickoff's output, but are good practice if kickoff mocking changes.
            result_plans = run_crew_lead_workflow(mock_inputs)

        # Assertions
        self.assertIn("backend_plan", result_plans)
        self.assertTrue(len(result_plans["backend_plan"].get("tasks", [])) > 0, "Backend plan should have tasks.")

        self.assertIn("frontend_plan", result_plans)
        self.assertTrue(len(result_plans["frontend_plan"].get("tasks", [])) > 0, "Frontend plan should have tasks.")

        self.assertIn("mobile_plan", result_plans)
        self.assertEqual(len(result_plans["mobile_plan"].get("tasks", [])), 0,
                         f"Mobile plan should be empty for 'unknown' scope. Got: {result_plans['mobile_plan']}")

        self.assertIn("deployment_plan", result_plans)
        self.assertTrue(len(result_plans["deployment_plan"].get("tasks", [])) > 0, "Deployment plan should have tasks if other tasks exist.")

        # Verify that the Crew was formed with the correct agents (no mobile agent)
        # The agents passed to Crew() constructor in the workflow:
        # For "unknown" scope (now web+backend default): backend, web, devops
        expected_agents_for_crew = {mock_backend_agent, mock_web_agent, mock_devops_agent}

        # Check the arguments Crew was called with using the mock for the Crew class itself.
        if mock_crew_class_for_assert.call_args:
            called_agents = set(mock_crew_class_for_assert.call_args.kwargs.get('agents', []))
            self.assertEqual(expected_agents_for_crew, called_agents,
                             f"Crew should have been formed with backend, web, and devops agents. Called with: {called_agents}")
        else:
            self.fail("Crew constructor was not called.")

if __name__ == '__main__':
    unittest.main()
