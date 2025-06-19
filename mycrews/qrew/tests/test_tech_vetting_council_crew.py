import unittest
from mycrews.qrew.orchestrators.tech_stack_committee.crews.tech_vetting_council_crew import TechVettingCouncilCrew

class TestTechVettingCouncilCrew(unittest.TestCase):

    def test_tech_vetting_council_crew_instantiation_and_kickoff(self):
        """Test TechVettingCouncilCrew instantiation and kickoff."""
        try:
            crew_instance = TechVettingCouncilCrew()
        except Exception as e:
            self.fail(f"TechVettingCouncilCrew instantiation failed: {e}")

        inputs = {
            'technology_or_architecture': 'Adoption of Microfrontend Architecture',
            'evaluation_criteria': 'Scalability, Team Autonomy, Deployment Independence, Performance Overhead',
            'project_goals': 'Improve frontend development velocity and enable independent team deployments for Project Phoenix.',
            'current_tech_stack': 'Monolithic React Frontend, Java Spring Boot Backend',
            'proposed_item': 'New JavaScript library "MagicUtil.js" for state management.',
            'constraints_list': 'Budget for new tools: $0. Must comply with existing security policy XYZ. Must be compatible with IE11 (hypothetical).',
            'vetted_item_name': 'Microfrontend Architecture for Project Phoenix',
            'council_decision_summary': 'Approved with conditions: Pilot on one module, review performance after 3 months.',
            'supporting_documents_links': 'link_to_evaluation_report.md, link_to_compliance_report.md',
            'documentation_template': 'company_decision_record_template.docx'
        }

        try:
            result = crew_instance.crew().kickoff(inputs=inputs)
            self.assertIsNotNone(result, "Kickoff returned None.")
        except Exception as e:
            self.fail(f"TechVettingCouncilCrew kickoff failed: {e}")

if __name__ == '__main__':
    unittest.main()
