import unittest
from mycrews.qrew.crews.mobile_development_crew import MobileDevelopmentCrew

class TestMobileDevelopmentCrew(unittest.TestCase):

    def test_mobile_dev_crew_instantiation_and_kickoff(self):
        """Test MobileDevelopmentCrew instantiation and kickoff."""
        try:
            crew_instance = MobileDevelopmentCrew()
        except Exception as e:
            self.fail(f"MobileDevelopmentCrew instantiation failed: {e}")

        # Using Android as the sample platform for inputs
        inputs = {
            'screen_name': 'UserProfileScreen',
            'platform': 'Android',
            'design_specifications': 'android_user_profile_design.fig',
            'api_endpoint': '/api/v1/users/{id}',
            'feature_name': 'View User Profile',
            'api_documentation': 'user_api_v1.md',
            'data_entity': 'UserPreferences',
            'storage_solution': 'Room', # Android specific
            'schema_details': 'user_preferences_schema.json'
        }

        try:
            result = crew_instance.crew().kickoff(inputs=inputs)
            self.assertIsNotNone(result, "Kickoff returned None.")
        except Exception as e:
            self.fail(f"MobileDevelopmentCrew kickoff failed: {e}")

if __name__ == '__main__':
    unittest.main()
