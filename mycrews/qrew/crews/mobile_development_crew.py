import logging
from crewai import Process, Agent, Task # Crew removed
from crewai.project import CrewBase, agent, crew, task

from ..llm_config import default_llm
from ..config import example_summary_validator
from ..validated_crew import ValidatedCrew # Added ValidatedCrew

# Import actual mobile agents
from mycrews.qrew.agents.mobile import (
    android_api_client_agent,
    android_storage_agent,
    android_ui_agent,
    ios_api_client_agent,
    ios_storage_agent,
    ios_ui_agent
)

@CrewBase
class MobileDevelopmentCrew:
    """MobileDevelopmentCrew handles tasks related to mobile application development for Android and iOS."""

    # Expose imported agents as properties
    @property
    def android_api_dev(self) -> Agent:
        return android_api_client_agent

    @property
    def android_storage_dev(self) -> Agent:
        return android_storage_agent

    @property
    def android_ui_dev(self) -> Agent:
        return android_ui_agent

    @property
    def ios_api_dev(self) -> Agent:
        return ios_api_client_agent

    @property
    def ios_storage_dev(self) -> Agent:
        return ios_storage_agent

    @property
    def ios_ui_dev(self) -> Agent:
        return ios_ui_agent

    # Define placeholder tasks.
    # These tasks would need to be routed to the correct agent (Android/iOS) based on input.
    # For simplicity, we'll assign one agent, but in reality, a dispatcher or conditional logic might be needed.

    @task
    def ui_development_task(self) -> Task:
        return Task(
            description="Develop the UI for the {screen_name} screen for {platform} (Android/iOS). "
                        "Implement based on {design_specifications}. "
                        "Input: {screen_name}, {platform}, {design_specifications}.",
            expected_output="UI code for {screen_name} on {platform}, matching design specifications.",
            # In a real scenario, agent assignment would be dynamic based on {platform}
            agent=android_ui_agent, # Placeholder assignment
            successCriteria=["UI code implemented", "Matches design specifications", "Platform guidelines followed"]
        )

    @task
    def api_integration_task(self) -> Task:
        return Task(
            description="Integrate backend API {api_endpoint} for the feature {feature_name} on {platform}. "
                        "Handle data fetching, posting, and error management. "
                        "Input: {api_endpoint}, {feature_name}, {platform}, {api_documentation}.",
            expected_output="Functional API integration for {feature_name} on {platform}.",
            agent=android_api_client_agent, # Placeholder assignment
            successCriteria=["API integrated", "Data fetched/posted correctly", "Error handling implemented"]
        )

    @task
    def local_storage_task(self) -> Task:
        return Task(
            description="Implement local data storage for {data_entity} on {platform} using {storage_solution} (e.g., Room, CoreData, SQLite). "
                        "Input: {data_entity}, {platform}, {storage_solution}, {schema_details}.",
            expected_output="Local storage implementation for {data_entity} on {platform}.",
            agent=android_storage_agent, # Placeholder assignment
            successCriteria=["Local storage implemented", "Data saved/retrieved correctly", "Schema matches requirements"]
        )

    @crew
    def crew(self, job_scope: str | list[str]) -> ValidatedCrew: # Return type changed
        """Creates the Mobile Development crew"""
        if isinstance(job_scope, str):
            job_scope = [job_scope]

        all_agents = [
            self.android_api_dev, self.android_storage_dev, self.android_ui_dev,
            self.ios_api_dev, self.ios_storage_dev, self.ios_ui_dev
        ]

        active_agents_set = set()
        is_general_mobile_scope = "mobile-only" in job_scope

        for agt in all_agents:
            agent_type_from_meta = None
            if hasattr(agt, 'metadata') and isinstance(agt.metadata, dict):
                agent_type_from_meta = agt.metadata.get("type")

            if agent_type_from_meta:
                if agent_type_from_meta == "common": # Assuming "common" would also be in metadata if used
                    active_agents_set.add(agt)
                elif is_general_mobile_scope and agent_type_from_meta in ["mobile", "android", "ios"]:
                    active_agents_set.add(agt)
                elif not is_general_mobile_scope and agent_type_from_meta in job_scope:
                    active_agents_set.add(agt)

        active_agents = list(active_agents_set)

        all_tasks = self.tasks
        filtered_tasks = [
            tsk for tsk in all_tasks if tsk.agent in active_agents
        ]

        pruned_tasks = [task for task in all_tasks if task not in filtered_tasks]
        if pruned_tasks:
            pruned_task_descriptions = [task.description[:50] + '...' for task in pruned_tasks]
            logging.info(f"Pruned tasks for job_scope '{job_scope}' in MobileDevelopmentCrew: {pruned_task_descriptions}")

        if not active_agents:
            logging.warning(f"No active agents for job_scope '{job_scope}' in MobileDevelopmentCrew. Crew will have no agents.")
        if not filtered_tasks:
            logging.warning(f"No tasks were matched for the active agents with job_scope '{job_scope}' in MobileDevelopmentCrew. Crew will have no tasks.")

        created_crew = ValidatedCrew(
            agents=active_agents,
            tasks=filtered_tasks,
            process=Process.sequential,
            verbose=True, # Keep True for now
            llm=default_llm
        )
        created_crew.configure_quality_gate(
            keyword_check=True,
            custom_validators=[example_summary_validator]
        )
        return created_crew

# Example usage (conceptual)
# if __name__ == '__main__':
#     mobile_crew = MobileDevelopmentCrew()
#     android_inputs = {
#         'screen_name': 'LoginScreen',
#         'platform': 'Android',
#         'design_specifications': 'android_login_design.fig',
#         'api_endpoint': '/auth/login',
#         'feature_name': 'User Login',
#         'api_documentation': 'auth_api.md',
#         'data_entity': 'UserProfile',
#         'storage_solution': 'Room',
#         'schema_details': 'user_profile_schema.json'
#     }
#     # ios_inputs = { ... }
#     result = mobile_crew.crew().kickoff(inputs=android_inputs) # or ios_inputs
#     print(result)
