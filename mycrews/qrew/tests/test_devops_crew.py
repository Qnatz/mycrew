import unittest
from mycrews.qrew.crews.devops_crew import DevOpsCrew

class TestDevOpsCrew(unittest.TestCase):

    def test_devops_crew_instantiation_and_kickoff(self):
        """Test DevOpsCrew instantiation and kickoff."""
        try:
            crew_instance = DevOpsCrew()
        except Exception as e:
            self.fail(f"DevOpsCrew instantiation failed: {e}")

        inputs = {
            'application_name': 'QrewPlatformAPI',
            'ci_cd_tool': 'GitLab CI',
            'repository_url': 'https://gitlab.com/example/qrewplatformapi.git',
            'deployment_environment': 'staging',
            'build_script_path': 'scripts/build.sh',
            'test_script_path': 'scripts/run_tests.sh',
            'cloud_provider': 'AWS',
            'project_name': 'QrewMainInfrastructure',
            'iac_tool': 'Terraform',
            'list_of_components_needed': 'VPC, EC2 instances, RDS, S3 bucket',
            'configuration_details': 'staging.tfvars',
            'environment': 'staging', # For monitoring task
            'monitoring_tool': 'Datadog',
            'key_metrics_list': 'request_count, error_rate, cpu_load, db_connections',
            'alerting_channels': 'slack_channel_ops, email_group_devops'
        }

        try:
            result = crew_instance.crew().kickoff(inputs=inputs)
            self.assertIsNotNone(result, "Kickoff returned None.")
        except Exception as e:
            self.fail(f"DevOpsCrew kickoff failed: {e}")

if __name__ == '__main__':
    unittest.main()
