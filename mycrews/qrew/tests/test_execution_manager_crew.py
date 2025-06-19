import unittest
from mycrews.qrew.orchestrators.execution_manager_agent.crews.execution_manager_crew import ExecutionManagerCrew

class TestExecutionManagerCrew(unittest.TestCase):

    def test_execution_manager_crew_instantiation_and_kickoff(self):
        """Test ExecutionManagerCrew instantiation and kickoff."""
        try:
            crew_instance = ExecutionManagerCrew()
        except Exception as e:
            self.fail(f"ExecutionManagerCrew instantiation failed: {e}")

        inputs = {
            'project_plan_url': 'link_to_project_alpha_plan.md',
            'available_lead_agents_and_crews_map': '{ "WebTeam": "WebProjectCoordinatorAgent", "BackendTeam": "BackendProjectCoordinatorAgent" }', # JSON string or dict
            'project_name': 'Project Alpha Launch',
            'key_milestones': 'Phase1_DesignComplete, Phase2_CoreFeaturesDev, Phase3_BetaRelease',
            'execution_timeline': '3_months_Q1_2024', # Simplified placeholder
            'change_request_details': 'CR_005_Add_New_Payment_Gateway.pdf',
            'impact_assessment_template': 'standard_change_impact_form.docx'
        }

        try:
            result = crew_instance.crew().kickoff(inputs=inputs)
            self.assertIsNotNone(result, "Kickoff returned None.")
        except Exception as e:
            self.fail(f"ExecutionManagerCrew kickoff failed: {e}")

if __name__ == '__main__':
    unittest.main()
