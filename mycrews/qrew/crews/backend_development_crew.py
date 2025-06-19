import logging
from crewai import Process, Agent, Task # Crew removed
from crewai.project import CrewBase, agent, crew, task

from ..llm_config import default_llm
from ..config import example_summary_validator
from ..validated_crew import ValidatedCrew # Added ValidatedCrew

# Import actual backend agents
from ..agents.backend import (
    api_creator_agent,
    auth_agent as backend_auth_agent, # Renaming to avoid conflict if a general 'auth_agent' is used elsewhere
    config_agent,
    data_model_agent,
    queue_agent,
    storage_agent,
    sync_agent as backend_sync_agent # Renaming for clarity
)

@CrewBase
class BackendDevelopmentCrew:
    """BackendDevelopmentCrew handles all tasks related to backend services and API development."""

    # Expose imported agents as properties
    @property
    def api_creator(self) -> Agent:
        return api_creator_agent

    @property
    def auth_specialist(self) -> Agent:
        return backend_auth_agent

    @property
    def config_manager(self) -> Agent:
        return config_agent

    @property
    def data_modeler(self) -> Agent:
        return data_model_agent

    @property
    def queue_manager(self) -> Agent:
        return queue_agent

    @property
    def storage_manager(self) -> Agent:
        return storage_agent

    @property
    def data_synchronizer(self) -> Agent:
        return backend_sync_agent

    # Define placeholder tasks for backend development
    @task
    def api_endpoint_task(self) -> Task:
        return Task(
            description="Develop a new API endpoint for '{feature_description}' at path '{endpoint_path}'. "
                        "Define request/response models and implement business logic. "
                        "Input: {feature_description}, {endpoint_path}, {request_model_schema}, {response_model_schema}.",
            expected_output="A fully functional API endpoint for '{feature_description}' deployed and tested, "
                            "with clear API documentation.",
            agent=api_creator_agent,
            successCriteria=["API endpoint functional", "Request/response models defined", "Business logic implemented", "API documentation clear"]
        )

    @task
    def database_schema_task(self) -> Task:
        return Task(
            description="Design and implement the database schema for the '{module_name}' module. "
                        "This includes tables, relationships, indexes, and constraints. "
                        "Input: {module_name}, {data_requirements}, {database_type}.",
            expected_output="SQL DDL scripts for the '{module_name}' schema, a schema diagram, "
                            "and migration scripts if applicable.",
            agent=data_model_agent,
            successCriteria=["SQL DDL scripts created", "Schema diagram provided", "Migration scripts applicable"]
        )

    @task
    def authentication_logic_task(self) -> Task:
        return Task(
            description="Implement {auth_mechanism} (e.g., JWT, OAuth2) for the service {service_name}. "
                        "Ensure secure handling of credentials and sessions. "
                        "Input: {auth_mechanism}, {service_name}, {security_requirements}.",
            expected_output="Authentication logic implemented for {service_name} using {auth_mechanism}, "
                            "with relevant endpoints secured.",
            agent=backend_auth_agent,
            successCriteria=["Authentication logic implemented", "Endpoints secured", "Credentials handled securely"]
        )

    @task
    def async_task_queue_setup(self) -> Task:
        return Task(
            description="Set up an asynchronous task queue using {queue_technology} for handling {task_type} operations. "
                        "Configure message brokers, producers, and consumers. "
                        "Input: {queue_technology}, {task_type}, {message_payload_definition}.",
            expected_output="A functional asynchronous task processing system for {task_type} using {queue_technology}.",
            agent=queue_agent,
            successCriteria=["Task processing system functional", "Message brokers configured", "Producers/consumers operational"]
        )

    @crew
    def crew(self, job_scope: str | list[str]) -> ValidatedCrew: # Return type changed
        """Creates the Backend Development crew"""
        if isinstance(job_scope, str):
            job_scope = [job_scope]

        all_agents = [
            self.api_creator,
            self.auth_specialist,
            self.config_manager,
            self.data_modeler,
            self.queue_manager,
            self.storage_manager,
            self.data_synchronizer
        ]
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
            logging.info(f"Pruned tasks for job_scope '{job_scope}' in BackendDevelopmentCrew: {pruned_task_descriptions}")

        if not active_agents:
            logging.warning(f"No active agents for job_scope '{job_scope}' in BackendDevelopmentCrew. Crew will have no agents.")
        if not filtered_tasks:
            logging.warning(f"No tasks were matched for the active agents with job_scope '{job_scope}' in BackendDevelopmentCrew. Crew will have no tasks.")

        created_crew = ValidatedCrew( # Changed to ValidatedCrew
            agents=active_agents,
            tasks=filtered_tasks,
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
#     backend_crew = BackendDevelopmentCrew()
#     inputs = {
#         'feature_description': 'User Profile Management',
#         'endpoint_path': '/users/{userId}',
#         'request_model_schema': 'UserProfileUpdateRequest.json',
#         'response_model_schema': 'UserProfileResponse.json',
#         'module_name': 'UserAccounts',
#         'data_requirements': 'User entity with fields: id, name, email, password_hash, created_at',
#         'database_type': 'PostgreSQL',
#         'auth_mechanism': 'JWT Bearer Token',
#         'service_name': 'UserAuthService',
#         'security_requirements': 'Password hashing (bcrypt), token expiry (1hr)',
#         'queue_technology': 'RabbitMQ',
#         'task_type': 'email_notification',
#         'message_payload_definition': 'EmailNotificationPayload.json'
#     }
#     result = backend_crew.crew().kickoff(inputs=inputs)
#     print(result)
