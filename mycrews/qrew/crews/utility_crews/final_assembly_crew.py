import logging
from crewai import Process, Agent, Task # Crew removed
from crewai.project import CrewBase, agent, crew, task

from ...llm_config import default_llm # Corrected path to ..
from ...config import example_summary_validator # Corrected path to ..
from ...validated_crew import ValidatedCrew # Added ValidatedCrew

# Import best-fit actual agents
from mycrews.qrew.orchestrators.final_assembler_agent import final_assembler_agent
# Using the tech_stack_committee's documentation writer, acknowledging it might be broader here.
from mycrews.qrew.orchestrators.tech_stack_committee.documentation_writer_agent import documentation_writer_agent as project_documentation_writer_agent
from mycrews.qrew.agents.dev_utilities import tester_agent # For final QA review

@CrewBase
class FinalAssemblyCrew:
    """
    FinalAssemblyCrew is responsible for integrating various components,
    generating final documentation, and performing a final review of the project output.
    """
    # tasks_config = 'config/final_assembly_crew_tasks.yaml' # Example

    @property
    def assembler(self) -> Agent:
        return final_assembler_agent

    @property
    def documenter(self) -> Agent:
        return project_documentation_writer_agent

    @property
    def reviewer(self) -> Agent:
        return tester_agent

    # Tasks defined by this crew
    @task
    def component_integration_and_packaging_task(self) -> Task:
        return Task(
            description="Assemble all final project components: {list_of_code_modules}, {data_artifacts}, "
                        "and {configuration_files}. Package them according to {packaging_specifications} "
                        "for final delivery or deployment. "
                        "Input: {list_of_code_modules}, {data_artifacts}, {configuration_files}, {packaging_specifications}.",
            expected_output="A complete, packaged version of the project, including all components, "
                            "ready for deployment or handover. A manifest of package contents.",
            agent=self.assembler, # type: ignore[attr-defined]
            successCriteria=["All components assembled", "Project packaged", "Manifest created"]
        )

    @task
    def final_documentation_generation_task(self) -> Task:
        return Task(
            description="Generate the final set of project documentation, including user manuals, release notes, "
                        "and system overview based on {compiled_project_information} and {documentation_requirements}. "
                        "Ensure all documentation is accurate and complete. "
                        "Input: {compiled_project_information}, {documentation_requirements}, {template_files_path}.",
            expected_output="A complete set of final project documentation, formatted and ready for distribution.",
            agent=self.documenter, # type: ignore[attr-defined]
            context=[self.component_integration_and_packaging_task], # Documentation after assembly
            successCriteria=["Final documentation generated", "User manual included", "Release notes included", "System overview accurate"]
        )

    @task
    def final_quality_assurance_review_task(self) -> Task:
        return Task(
            description="Perform a final quality assurance review of the assembled project package and its documentation. "
                        "Verify against the {final_checklist_items} and {user_acceptance_criteria}. "
                        "Report any outstanding issues. "
                        "Input: {assembled_project_package_path}, {final_documentation_path}, {final_checklist_items}, {user_acceptance_criteria}.",
            expected_output="A final QA review report, summarizing findings, "
                            "confirming adherence to checklist and acceptance criteria, or detailing any critical issues found.",
            agent=self.reviewer, # type: ignore[attr-defined]
            context=[self.final_documentation_generation_task], # Review the final package and docs
            successCriteria=["QA review report generated", "Checklist verified", "Acceptance criteria confirmed", "Issues detailed"]
        )

    @crew
    def crew(self, job_scope: str | list[str]) -> ValidatedCrew: # Return type changed
        """Creates the Final Assembly Utility crew"""
        if isinstance(job_scope, str):
            job_scope = [job_scope]

        all_agents = [self.assembler, self.documenter, self.reviewer]
        active_agents = []
        for agt in all_agents:
            # Default to 'common' if type attribute is missing, as per subtask instructions
            agt_type = getattr(agt, 'type', 'common')
            if agt_type == "common" or agt_type in job_scope:
                active_agents.append(agt)

        all_tasks = self.tasks
        filtered_tasks = [
            tsk for tsk in all_tasks if tsk.agent in active_agents
        ]

        pruned_tasks = [task for task in all_tasks if task not in filtered_tasks]
        if pruned_tasks:
            pruned_task_descriptions = [task.description for task in pruned_tasks]
            logging.info(f"Pruned tasks for job_scope '{job_scope}' in FinalAssemblyCrew: {pruned_task_descriptions}")

        if not active_agents:
            logging.warning(f"No active agents for job_scope '{job_scope}' in FinalAssemblyCrew. Crew will have no agents.")
        if not filtered_tasks:
            logging.warning(f"No tasks were matched for the active agents with job_scope '{job_scope}' in FinalAssemblyCrew. Crew will have no tasks.")

        created_crew = ValidatedCrew( # Changed to ValidatedCrew
            agents=active_agents,
            tasks=filtered_tasks,
            process=Process.sequential, # Assembly, Ddcing, then Review is a logical sequence
            verbose=True,
            llm=default_llm
        )
        created_crew.configure_quality_gate(
            keyword_check=True,
            custom_validators=[example_summary_validator]
        )
        return created_crew

# Example usage (conceptual)
# if __name__ == "__main__":
#     inputs = {
#         'list_of_code_modules': ['module_A.jar', 'module_B.whl', 'frontend_dist.zip'],
#         'data_artifacts': ['initial_db_schema.sql', 'sample_data.csv'],
#         'configuration_files': ['prod_config.json', 'service_endpoints.yaml'],
#         'packaging_specifications': 'Create a Docker image and a ZIP archive.',
#         'compiled_project_information': 'Links to all component READMEs, API docs, and architecture diagrams.',
#         'documentation_requirements': 'User manual for non-technical users, deployment guide for ops.',
#         'template_files_path': './docs/templates/',
#         'assembled_project_package_path': './dist/project_final_v1.0.zip', # or Docker image ID
#         'final_documentation_path': './dist/docs_v1.0/',
#         'final_checklist_items': 'Security scan passed, all modules versioned, license files included.',
#         'user_acceptance_criteria': 'Key user flows X, Y, Z are functional as per UAT plan.'
#     }
#     final_assembly_crew_instance = FinalAssemblyCrew()
#     result = final_assembly_crew_instance.crew().kickoff(inputs=inputs)
#     print("\n\nFinal Assembly Crew execution finished.")
#     print("Result:")
#     print(result)
