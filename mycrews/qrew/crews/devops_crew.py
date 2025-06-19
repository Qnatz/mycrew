import logging
from crewai import Process, Agent, Task # Crew removed
from crewai.project import CrewBase, agent, crew, task

from ..llm_config import default_llm
from ..config import example_summary_validator
from ..validated_crew import ValidatedCrew # Added ValidatedCrew

# Import the actual devops agent
from mycrews.qrew.agents.devops import devops_agent

@CrewBase
class DevOpsCrew:
    """DevOpsCrew handles CI/CD, infrastructure, monitoring, and deployment tasks."""

    @property
    def cicd_specialist(self) -> Agent: # Naming the property for clarity within the crew
        return devops_agent

    # Define placeholder tasks for DevOps
    @task
    def ci_cd_pipeline_setup_task(self) -> Task:
        return Task(
            description="Set up a full CI/CD pipeline for the {application_name} using {ci_cd_tool}. "
                        "The pipeline must include stages for building, testing (unit, integration), and deploying to {deployment_environment}. "
                        "Input: {application_name}, {ci_cd_tool}, {repository_url}, {deployment_environment}, {build_script_path}, {test_script_path}.",
            expected_output="A functional CI/CD pipeline configuration for {application_name}. "
                            "A successful run of the pipeline deploying a sample change. "
                            "Documentation on how to trigger and monitor the pipeline.",
            agent=devops_agent,
            successCriteria=["CI/CD pipeline configured", "Successful test deployment", "Pipeline documentation created"]
        )

    @task
    def infrastructure_provisioning_task(self) -> Task:
        return Task(
            description="Provision the required infrastructure on {cloud_provider} for the {project_name} using {iac_tool} (e.g., Terraform, CloudFormation). "
                        "Infrastructure components include {list_of_components_needed}. "
                        "Input: {cloud_provider}, {project_name}, {iac_tool}, {list_of_components_needed}, {configuration_details}.",
            expected_output="Infrastructure successfully provisioned on {cloud_provider} as per specifications. "
                            "IaC scripts committed to version control. "
                            "Access details and endpoints documented.",
            agent=devops_agent,
            successCriteria=["Infrastructure provisioned", "IaC scripts versioned", "Access details documented"]
        )

    @task
    def monitoring_and_alerting_setup_task(self) -> Task:
        return Task(
            description="Implement a monitoring and alerting system for the {application_name} in the {environment} environment using {monitoring_tool}. "
                        "Set up dashboards for key metrics ({key_metrics_list}) and configure alerts for critical thresholds. "
                        "Input: {application_name}, {environment}, {monitoring_tool}, {key_metrics_list}, {alerting_channels}.",
            expected_output="Monitoring dashboards displaying real-time application metrics. "
                            "Alerting system configured and tested. "
                            "Documentation on accessing dashboards and managing alerts.",
            agent=devops_agent,
            successCriteria=["Dashboards created", "Alerts configured and tested", "Monitoring documentation provided"]
        )

    @crew
    def crew(self, job_scope: str | list[str]) -> ValidatedCrew: # Return type changed
        """Creates the DevOps crew"""
        if isinstance(job_scope, str):
            job_scope = [job_scope]

        all_agents = [self.cicd_specialist]
        active_agents = [
            agt for agt in all_agents if hasattr(agt, 'type') and (agt.type == "common" or agt.type in job_scope)
        ]

        all_tasks = self.tasks
        filtered_tasks = [
            tsk for tsk in all_tasks if tsk.agent in active_agents
        ]

        pruned_tasks = [task for task in all_tasks if task not in filtered_tasks]
        if pruned_tasks:
            pruned_task_descriptions = [task.description for task in pruned_tasks]
            logging.info(f"Pruned tasks for job_scope '{job_scope}' in DevOpsCrew: {pruned_task_descriptions}")

        if not active_agents:
            logging.warning(f"No active agents for job_scope '{job_scope}' in DevOpsCrew. Crew will have no agents.")
        if not filtered_tasks:
            logging.warning(f"No tasks were matched for the active agents with job_scope '{job_scope}' in DevOpsCrew. Crew will have no tasks.")

        created_crew = ValidatedCrew( # Changed to ValidatedCrew
            agents=active_agents, # Using the property name
            tasks=filtered_tasks, # From @task decorator
            process=Process.sequential,
            verbose=True,
            llm=default_llm
        )
        created_crew.configure_quality_gate(
            keyword_check=True,
            custom_validators=[example_summary_validator]
        )
        return created_crew

# Example usage (conceptual)
# if __name__ == '__main__':
#     devops_crew_instance = DevOpsCrew()
#     inputs = {
#         'application_name': 'QrewApp',
#         'ci_cd_tool': 'GitHub Actions',
#         'repository_url': 'git@github.com:user/qrewapp.git',
#         'deployment_environment': 'staging',
#         'build_script_path': './scripts/build.sh',
#         'test_script_path': './scripts/test.sh',
#         'cloud_provider': 'AWS',
#         'project_name': 'Qrew Platform',
#         'iac_tool': 'Terraform',
#         'list_of_components_needed': 'EC2 instances, RDS database, S3 bucket, ELB',
#         'configuration_details': 'terraform_vars.tfvars',
#         'environment': 'production',
#         'monitoring_tool': 'Prometheus & Grafana',
#         'key_metrics_list': 'CPU utilization, memory usage, request latency, error rates',
#         'alerting_channels': 'Slack, PagerDuty'
#     }
#     result = devops_crew_instance.crew().kickoff(inputs=inputs)
#     print(result)
