import unittest
from mycrews.qrew.crews.web_development_crew import WebDevelopmentCrew

class TestWebDevelopmentCrew(unittest.TestCase):

    def test_web_dev_crew_instantiation_and_kickoff(self):
        """Test WebDevelopmentCrew instantiation and kickoff."""
        try:
            crew_instance = WebDevelopmentCrew()
        except Exception as e:
            self.fail(f"WebDevelopmentCrew instantiation failed: {e}")

        inputs = {
            'page_topic': 'Contact Us',
            'required_elements': 'Address, Map, Contact Form',
            'design_specifications': 'company_style_guide.pdf',
            'feature_name': 'User Login',
            'feature_details': 'Standard email/password login, OAuth option',
            'api_endpoint': '/api/auth/login',
            'ui_mockups': 'login_screen_mockup.fig',
            'section_name': 'Global',
            'asset_paths': ['/css/theme.css', '/img/logo.png']
        }

        try:
            result = crew_instance.crew().kickoff(inputs=inputs)
            self.assertIsNotNone(result, "Kickoff returned None.")
        except Exception as e:
            self.fail(f"WebDevelopmentCrew kickoff failed: {e}")

if __name__ == '__main__':
    unittest.main()
