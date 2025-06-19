import logging
from crewai import Process, Agent, Task # Crew removed
from crewai.project import CrewBase, agent, crew, task

from ..llm_config import default_llm
from ..config import example_summary_validator
from ..validated_crew import ValidatedCrew # Added ValidatedCrew

# Import actual offline agents
from mycrews.qrew.agents.offline import (
    local_storage_agent,
    offline_sync_agent
)

@CrewBase
class OfflineSupportCrew:
    """OfflineSupportCrew handles tasks related to local data storage and offline data synchronization."""

    @property
    def local_store_manager(self) -> Agent:
        return local_storage_agent

    @property
    def data_synchronizer(self) -> Agent: # Renamed for clarity within crew
        return offline_sync_agent

    # Define placeholder tasks for offline support
    @task
    def local_database_setup_task(self) -> Task:
        return Task(
            description="Set up and configure a local database using {database_technology} for the {application_name} "
                        "to enable offline storage of {data_types}. "
                        "Input: {database_technology}, {application_name}, {data_types}, {schema_definition}.",
            expected_output="A functional local database configured for {application_name}. "
                            "Schema applied and basic CRUD operations tested. "
                            "Documentation for accessing the local store.",
            agent=local_storage_agent,
            successCriteria=["Local database configured", "Schema applied", "CRUD operations tested", "Documentation provided"]
        )

    @task
    def data_sync_mechanism_task(self) -> Task:
        return Task(
            description="Implement a data synchronization mechanism between the local store and the central server ({server_endpoint}) "
                        "for {data_entities_to_sync}. Handle conflict resolution using {conflict_strategy}. "
                        "Input: {server_endpoint}, {data_entities_to_sync}, {conflict_strategy}, {sync_frequency}.",
            expected_output="A robust data synchronization process. "
                            "Data is synced efficiently when online. "
                            "Conflict resolution is handled as specified. "
                            "Monitoring for sync status is in place.",
            agent=offline_sync_agent, # Using the renamed property
            successCriteria=["Data sync mechanism implemented", "Efficient online sync", "Conflict resolution handled", "Sync monitoring in place"]
        )

    @task
    def offline_data_access_logic_task(self) -> Task:
        return Task(
            description="Develop application logic to seamlessly switch between online and offline data sources for {feature_module}. "
                        "Prioritize local data when offline and sync when online. "
                        "Input: {feature_module}, {online_data_api}, {local_storage_interface}.",
            expected_output="Application logic that enables {feature_module} to function correctly in both online and offline modes, "
                            "providing a smooth user experience.",
            agent=local_storage_agent, # Local storage agent might handle the access logic or work with another dev agent
            successCriteria=["Online/offline logic implemented", "Smooth user experience achieved", "Prioritizes local data correctly"]
        )

    @crew
    def crew(self, job_scope: str | list[str]) -> ValidatedCrew: # Return type changed
        """Creates the Offline Support crew"""
        if isinstance(job_scope, str):
            job_scope = [job_scope]

        all_agents = [self.local_store_manager, self.data_synchronizer]
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
            logging.info(f"Pruned tasks for job_scope '{job_scope}' in OfflineSupportCrew: {pruned_task_descriptions}")

        if not active_agents:
            logging.warning(f"No active agents for job_scope '{job_scope}' in OfflineSupportCrew. Crew will have no agents.")
        if not filtered_tasks:
            logging.warning(f"No tasks were matched for the active agents with job_scope '{job_scope}' in OfflineSupportCrew. Crew will have no tasks.")

        created_crew = ValidatedCrew( # Changed to ValidatedCrew
            agents=active_agents,
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
#     offline_crew = OfflineSupportCrew()
#     inputs = {
#         'database_technology': 'SQLite',
#         'application_name': 'FieldReporterApp',
#         'data_types': 'reports, images, GPS coordinates',
#         'schema_definition': 'field_reporter_schema.sql',
#         'server_endpoint': 'https://api.example.com/sync',
#         'data_entities_to_sync': 'reports',
#         'conflict_strategy': 'last_write_wins',
#         'sync_frequency': 'on_app_launch_online',
#         'feature_module': 'ReportSubmissionModule',
#         'online_data_api': 'ReportApiService',
#         'local_storage_interface': 'ReportLocalRepository'
#     }
#     result = offline_crew.crew().kickoff(inputs=inputs)
#     print(result)
