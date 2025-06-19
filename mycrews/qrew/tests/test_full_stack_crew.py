import unittest
from crewai import Agent, Task # Added Agent and Task
from mycrews.qrew.crews.full_stack_crew import FullStackCrew

class TestFullStackCrew(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        self.crew_instance = FullStackCrew()
        self.expected_roles = {
            "backend_api_dev": "Backend API Creator", # Corrected based on agent definition
            "backend_data_modeler": "Backend Data Modeler", # Corrected based on agent definition
            "frontend_web_dev": "Dynamic Web Page Builder", # Corrected based on agent definition
            "general_code_writer": "Code Writer",
            "quality_assurer": "Software Tester" # Corrected based on agent definition
        }
        # Total number of tasks defined in FullStackCrew
        self.total_defined_tasks = 5


    def _get_agent_roles(self, agents_list: list[Agent]) -> set[str]:
        """Helper to get a set of roles from a list of Agent objects."""
        return {agent.role for agent in agents_list}

    def test_full_stack_crew_instantiation_and_kickoff(self):
        """Test that the FullStackCrew can be instantiated and kickoff runs with full scope."""
        # Inputs are now needed for the crew method due to job_scope
        inputs = {
            'feature_name': 'User Profile Page V2',
            'feature_requirements': 'Display user details, activity feed, and allow editing profile information.',
            'api_design_guidelines': 'RESTful, use OpenAPI spec v3.',
            'data_requirements': 'User table needs new fields: bio (TEXT), profile_picture_url (VARCHAR). Activity table for feed.',
            'current_database_schema_info': 'Link to current schema dump or ERD.',
            'ui_ux_specifications': 'Link to Figma designs for Profile Page V2.',
            'api_endpoint_details_for_feature': 'Endpoints: GET /users/{id}, PUT /users/{id}, GET /users/{id}/activity',
            'coding_task_description': 'Create a Python script to seed sample user activity data.',
            'relevant_code_files': 'user_model.py, activity_model.py',
            'test_plan_document_url': 'Link to E2E test plan for Profile Page V2.',
            'user_stories_for_feature': 'As a user, I can view my profile. As a user, I can edit my bio.'
        }
        try:
            # Using full_stack scope for kickoff test
            pruned_crew = self.crew_instance.crew(job_scope=["web", "backend"])
            result = pruned_crew.kickoff(inputs=inputs)
            self.assertIsNotNone(result, "Kickoff returned None, expected some result.")
        except Exception as e:
            self.fail(f"FullStackCrew kickoff failed: {e}")

    def test_job_scope_web_only(self):
        """Test crew pruning for 'web' job_scope."""
        pruned_crew = self.crew_instance.crew(job_scope="web")
        active_roles = self._get_agent_roles(pruned_crew.agents)

        expected_web_roles = {
            self.expected_roles["frontend_web_dev"],
            self.expected_roles["general_code_writer"],
            self.expected_roles["quality_assurer"]
        }
        self.assertEqual(active_roles, expected_web_roles, f"Expected roles {expected_web_roles}, got {active_roles}")

        self.assertNotIn(self.expected_roles["backend_api_dev"], active_roles)
        self.assertNotIn(self.expected_roles["backend_data_modeler"], active_roles)

        for task in pruned_crew.tasks:
            self.assertIn(task.agent.role, active_roles, f"Task '{task.description}' agent role '{task.agent.role}' not in active roles.")

        # Expected tasks: develop_frontend_web_task, general_coding_support_task, end_to_end_testing_task (if its agent is active)
        # Hard to assert exact number of tasks without knowing which tasks are assigned to common agents and if those common tasks are always included or contextually.
        # The check `task.agent.role in active_roles` is the primary validation.
        # For web-only, tasks for backend_api_dev and backend_data_modeler should be pruned.
        task_descriptions = {task.description for task in pruned_crew.tasks}
        self.assertNotIn(self.crew_instance.design_and_develop_api_task().description, task_descriptions)
        self.assertNotIn(self.crew_instance.develop_database_schema_task().description, task_descriptions)
        self.assertIn(self.crew_instance.develop_frontend_web_task().description, task_descriptions)


    def test_job_scope_backend_only(self):
        """Test crew pruning for 'backend' job_scope."""
        pruned_crew = self.crew_instance.crew(job_scope="backend")
        active_roles = self._get_agent_roles(pruned_crew.agents)

        expected_backend_roles = {
            self.expected_roles["backend_api_dev"],
            self.expected_roles["backend_data_modeler"],
            self.expected_roles["general_code_writer"],
            self.expected_roles["quality_assurer"]
        }
        self.assertEqual(active_roles, expected_backend_roles,  f"Expected roles {expected_backend_roles}, got {active_roles}")

        self.assertNotIn(self.expected_roles["frontend_web_dev"], active_roles)

        for task in pruned_crew.tasks:
            self.assertIn(task.agent.role, active_roles)

        task_descriptions = {task.description for task in pruned_crew.tasks}
        self.assertNotIn(self.crew_instance.develop_frontend_web_task().description, task_descriptions)
        self.assertIn(self.crew_instance.design_and_develop_api_task().description, task_descriptions)
        self.assertIn(self.crew_instance.develop_database_schema_task().description, task_descriptions)


    def test_job_scope_full_stack(self):
        """Test crew pruning for 'full-stack' (web & backend) job_scope."""
        pruned_crew = self.crew_instance.crew(job_scope=["web", "backend"])
        active_roles = self._get_agent_roles(pruned_crew.agents)

        expected_full_stack_roles = {
            self.expected_roles["backend_api_dev"],
            self.expected_roles["backend_data_modeler"],
            self.expected_roles["frontend_web_dev"],
            self.expected_roles["general_code_writer"],
            self.expected_roles["quality_assurer"]
        }
        self.assertEqual(active_roles, expected_full_stack_roles)

        self.assertEqual(len(pruned_crew.tasks), self.total_defined_tasks, "Full stack scope should include all tasks.")

        for task in pruned_crew.tasks:
            self.assertIn(task.agent.role, active_roles)

    def test_job_scope_unrelated(self):
        """Test crew pruning for an unrelated job_scope (e.g., 'mobile')."""
        pruned_crew = self.crew_instance.crew(job_scope="mobile") # "mobile" is not a type handled by FullStackCrew agents other than common
        active_roles = self._get_agent_roles(pruned_crew.agents)

        expected_common_roles_only = {
            self.expected_roles["general_code_writer"],
            self.expected_roles["quality_assurer"]
        }
        self.assertEqual(active_roles, expected_common_roles_only)

        self.assertNotIn(self.expected_roles["frontend_web_dev"], active_roles)
        self.assertNotIn(self.expected_roles["backend_api_dev"], active_roles)
        self.assertNotIn(self.expected_roles["backend_data_modeler"], active_roles)

        # Check that only tasks for common agents remain
        for task in pruned_crew.tasks:
            self.assertIn(task.agent.role, expected_common_roles_only,
                          f"Task '{task.description}' with agent role '{task.agent.role}' should not be present for unrelated scope.")

        task_descriptions = {task.description for task in pruned_crew.tasks}
        self.assertNotIn(self.crew_instance.design_and_develop_api_task().description, task_descriptions)
        self.assertNotIn(self.crew_instance.develop_database_schema_task().description, task_descriptions)
        self.assertNotIn(self.crew_instance.develop_frontend_web_task().description, task_descriptions)
        # Assuming general_coding_support_task and end_to_end_testing_task are assigned to common agents
        self.assertIn(self.crew_instance.general_coding_support_task().description, task_descriptions)
        self.assertIn(self.crew_instance.end_to_end_testing_task().description, task_descriptions)


if __name__ == '__main__':
    unittest.main()
