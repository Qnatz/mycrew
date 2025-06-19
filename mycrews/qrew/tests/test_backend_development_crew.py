import unittest
from crewai import Agent, Task # Added Agent and Task
from mycrews.qrew.crews.backend_development_crew import BackendDevelopmentCrew

class TestBackendDevelopmentCrew(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        self.crew_instance = BackendDevelopmentCrew()
        self.expected_roles_backend_crew = {
            "Backend API Creator",
            "Backend Authentication Agent",
            "Backend Configuration Manager",
            "Backend Data Modeler",
            "Backend Queue Manager",
            "Backend Storage Manager",
            "Backend Data Synchronizer"
        }
        self.total_defined_tasks_backend_crew = 4 # Based on current BackendDevelopmentCrew tasks

    def _get_agent_roles(self, agents_list: list[Agent]) -> set[str]:
        """Helper to get a set of roles from a list of Agent objects."""
        return {agent.role for agent in agents_list}

    def test_backend_dev_crew_instantiation_and_kickoff(self):
        """Test BackendDevelopmentCrew instantiation and kickoff with 'backend' scope."""
        inputs = {
            'feature_description': 'Order Processing Service',
            'endpoint_path': '/api/orders',
            'request_model_schema': 'OrderRequest.json',
            'response_model_schema': 'OrderResponse.json',
            'module_name': 'OrdersModule',
            'data_requirements': 'Order table, OrderItems table, Customer reference',
            'database_type': 'PostgreSQL',
            'auth_mechanism': 'OAuth 2.0 Client Credentials',
            'service_name': 'OrderService',
            'security_requirements': 'Input validation, role-based access',
            'queue_technology': 'Kafka',
            'task_type': 'OrderFulfilmentNotification',
            'message_payload_definition': 'OrderNotification.json'
            # Add any other inputs your crew's tasks might expect
        }
        try:
            # Ensure kickoff is tested with a scope that activates the crew
            pruned_crew = self.crew_instance.crew(job_scope="backend")
            result = pruned_crew.kickoff(inputs=inputs)
            self.assertIsNotNone(result, "Kickoff returned None.")
        except Exception as e:
            self.fail(f"BackendDevelopmentCrew kickoff failed: {e}")

    def test_job_scope_backend(self):
        """Test crew pruning for 'backend' job_scope."""
        pruned_crew = self.crew_instance.crew(job_scope="backend")
        active_roles = self._get_agent_roles(pruned_crew.agents)

        self.assertEqual(active_roles, self.expected_roles_backend_crew,
                         f"Expected roles {self.expected_roles_backend_crew}, got {active_roles}")

        self.assertEqual(len(pruned_crew.tasks), self.total_defined_tasks_backend_crew,
                         f"Expected {self.total_defined_tasks_backend_crew} tasks, got {len(pruned_crew.tasks)}")

        for task in pruned_crew.tasks:
            self.assertIn(task.agent.role, active_roles,
                          f"Task '{task.description}' agent role '{task.agent.role}' not in active roles.")

    def test_job_scope_other_scope(self):
        """Test crew pruning with an unrelated job_scope (e.g., 'web')."""
        pruned_crew = self.crew_instance.crew(job_scope="web") # "web" is not a type handled by BackendDevelopmentCrew agents
        active_roles = self._get_agent_roles(pruned_crew.agents)

        self.assertEqual(len(active_roles), 0, f"Expected no active agents, got {active_roles}")
        self.assertEqual(len(pruned_crew.tasks), 0, f"Expected no tasks, got {len(pruned_crew.tasks)}")


if __name__ == '__main__':
    unittest.main()
