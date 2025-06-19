import logging
from crewai import Process, Agent, Task # Crew removed
from crewai.project import CrewBase, agent, crew, task

from ..llm_config import default_llm
from ..config import example_summary_validator
from ..validated_crew import ValidatedCrew # Added ValidatedCrew

# Import actual agents that could form a full-stack team
from mycrews.qrew.agents.backend import api_creator_agent, data_model_agent
from mycrews.qrew.agents.web import dynamic_page_builder_agent # Assuming frontend might be web for this crew
from mycrews.qrew.agents.dev_utilities import tester_agent, code_writer_agent # For general coding and testing

# Potentially also:
# from mycrews.qrew.agents.auth import auth_coordinator_agent # If handling auth directly
# from mycrews.qrew.agents.devops import devops_agent # If this crew also handles its deployment

@CrewBase
class FullStackCrew:
    """
    FullStackCrew handles end-to-end development tasks for a specific feature,
    coordinating backend, frontend (web), and testing aspects.
    """
    # agents_config = 'config/agents.yaml' # This would load configurations for these specific agents if needed
    # tasks_config = 'config/full_stack_crew_tasks.yaml' # This crew would have its own task definitions

    @property
    def backend_api_dev(self) -> Agent:
        return api_creator_agent

    @property
    def backend_data_modeler(self) -> Agent:
        return data_model_agent

    @property
    def frontend_web_dev(self) -> Agent: # More specific name
        return dynamic_page_builder_agent

    @property
    def general_code_writer(self) -> Agent: # For tasks not covered by specialized builders
        return code_writer_agent

    @property
    def quality_assurer(self) -> Agent: # More specific name
        return tester_agent

    # Tasks defined by this crew
    @task
    def design_and_develop_api_task(self) -> Task:
        return Task(
            description="Design and develop the backend API endpoints required for the '{feature_name}' feature. "
                        "This includes defining data models, creating API logic, and ensuring proper request/response handling. "
                        "Collaborate with the data modeler for database schema aspects. "
                        "Input: {feature_name}, {feature_requirements}, {api_design_guidelines}.",
            expected_output="Fully functional and documented API endpoints for '{feature_name}'. "
                            "Swagger/OpenAPI documentation generated. Unit tests passed for API logic.",
            agent=self.backend_api_dev, # type: ignore[attr-defined]
            successCriteria=["API endpoints functional", "Documentation generated", "Unit tests passed"],
            # No specific context, this is often a starting point.
        )

    @task
    def develop_database_schema_task(self) -> Task:
        return Task(
            description="Develop the necessary database schema changes (tables, columns, relationships) "
                        "to support the '{feature_name}' feature, based on {data_requirements}. "
                        "Generate migration scripts if applicable. "
                        "Input: {feature_name}, {data_requirements}, {current_database_schema_info}.",
            expected_output="Database schema updated or created for '{feature_name}'. "
                            "Migration scripts generated and tested. Schema documentation updated.",
            agent=self.backend_data_modeler, # type: ignore[attr-defined]
            context=[self.design_and_develop_api_task], # Schema might be influenced by API needs or vice-versa
            successCriteria=["Schema updated/created", "Migration scripts functional", "Schema documented"]
        )

    @task
    def develop_frontend_web_task(self) -> Task:
        return Task(
            description="Develop the frontend web interface for the '{feature_name}' feature. "
                        "Implement UI components, user interactions, and integrate with the backend API endpoints. "
                        "Input: {feature_name}, {ui_ux_specifications}, {api_endpoint_details_for_feature}.",
            expected_output="A responsive and interactive web interface for '{feature_name}', "
                            "meeting all UI/UX specifications and successfully integrated with the backend.",
            agent=self.frontend_web_dev, # type: ignore[attr-defined]
            context=[self.design_and_develop_api_task], # Depends on API being ready
            successCriteria=["Web interface implemented", "UI/UX specifications met", "Backend integrated"]
        )

    @task
    def general_coding_support_task(self) -> Task:
        return Task(
            description="Provide general coding support for the '{feature_name}' feature. This may include writing utility functions, "
                        "helper scripts, or addressing specific coding challenges identified by other agents. "
                        "Input: {feature_name}, {coding_task_description}, {relevant_code_files}.",
            expected_output="Completed coding task as per {coding_task_description}. Code should be well-documented and tested.",
            agent=self.general_code_writer, # type: ignore[attr-defined]
            successCriteria=["Coding task completed", "Code documented", "Code tested"],
            # This task might be triggered ad-hoc or be a dependency for others.
        )

    @task
    def end_to_end_testing_task(self) -> Task:
        return Task(
            description="Conduct comprehensive end-to-end testing for the '{feature_name}' feature. "
                        "This includes testing API integrations, frontend UI functionality, and overall user workflows. "
                        "Input: {feature_name}, {test_plan_document_url}, {user_stories_for_feature}.",
            expected_output="A detailed test report for '{feature_name}', including: "
                            "- Summary of test execution (passed/failed). "
                            "- List of identified bugs with steps to reproduce. "
                            "- Confirmation of requirements coverage.",
            agent=self.quality_assurer, # type: ignore[attr-defined]
            context=[self.develop_frontend_web_task, self.develop_database_schema_task], # Depends on frontend and backend parts being somewhat ready
            successCriteria=["Test report generated", "Bugs listed", "Requirements coverage confirmed"]
        )

    @crew
    def crew(self, job_scope: str | list[str]) -> ValidatedCrew: # Return type changed
        """Creates the Full Stack Development crew"""
        if isinstance(job_scope, str):
            job_scope = [job_scope]

        all_agents = [
            self.backend_api_dev,
            self.backend_data_modeler,
            self.frontend_web_dev,
            self.general_code_writer,
            self.quality_assurer
        ]
        active_agents = [
            agt for agt in all_agents if hasattr(agt, 'type') and (agt.type == "common" or agt.type in job_scope)
        ]

        # Log active agents (optional, for debugging)
        # logging.info(f"Active agents for job_scope '{job_scope}': {[a.role for a in active_agents]}")


        all_tasks = self.tasks # self.tasks is already populated by the @task decorator
        filtered_tasks = [
            tsk for tsk in all_tasks if tsk.agent in active_agents
        ]

        # Log filtered tasks (optional, for debugging)
        # logging.info(f"Filtered tasks for job_scope '{job_scope}': {[t.description for t in filtered_tasks]}")

        pruned_tasks = [task for task in all_tasks if task not in filtered_tasks]
        if pruned_tasks:
            pruned_task_descriptions = [task.description for task in pruned_tasks]
            logging.info(f"Pruned tasks for job_scope '{job_scope}' in FullStackCrew: {pruned_task_descriptions}")

        if not active_agents:
            logging.warning(f"No active agents found for job_scope: {job_scope}. Crew will have no agents.")
        if not filtered_tasks:
            logging.warning(f"No tasks were matched for the active agents with job_scope: {job_scope}. Crew will have no tasks.")


        created_crew = ValidatedCrew( # Changed to ValidatedCrew
            agents=active_agents,
            tasks=filtered_tasks,    # Use filtered tasks
            process=Process.sequential, # Default, can be hierarchical if manager agent is added
            verbose=True,
            llm=default_llm
        )
        # The configure_quality_gate call is already correctly placed from previous step
        created_crew.configure_quality_gate(
            keyword_check=True,
            custom_validators=[example_summary_validator]
        )
        return created_crew

# Example of how this crew might be run (conceptual)
# if __name__ == "__main__":
#     inputs = {
#         'feature_name': 'User Profile Page V2',
#         'feature_requirements': 'Display user details, activity feed, and allow editing profile information.',
#         'api_design_guidelines': 'RESTful, use OpenAPI spec v3.',
#         'data_requirements': 'User table needs new fields: bio (TEXT), profile_picture_url (VARCHAR). Activity table for feed.',
#         'current_database_schema_info': 'Link to current schema dump or ERD.',
#         'ui_ux_specifications': 'Link to Figma designs for Profile Page V2.',
#         'api_endpoint_details_for_feature': 'Endpoints: GET /users/{id}, PUT /users/{id}, GET /users/{id}/activity',
#         'coding_task_description': 'Create a Python script to seed sample user activity data.',
#         'relevant_code_files': 'user_model.py, activity_model.py',
#         'test_plan_document_url': 'Link to E2E test plan for Profile Page V2.',
#         'user_stories_for_feature': 'As a user, I can view my profile. As a user, I can edit my bio.'
#     }
#     full_stack_crew = FullStackCrew()
#     result = full_stack_crew.crew().kickoff(inputs=inputs)
#     print("\n\nFull Stack Crew execution finished.")
#     print("Result:")
#     print(result)
