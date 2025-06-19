import logging
from crewai import Process, Agent, Task # Crew removed
from crewai.project import CrewBase, agent, crew, task

from ...llm_config import default_llm # Corrected path to ..
from ...config import example_summary_validator # Corrected path to ..
from ...validated_crew import ValidatedCrew # Added ValidatedCrew

# Import actual dev utility agents
from mycrews.qrew.agents.dev_utilities import (
    code_writer_agent,
    debugger_agent,
    tester_agent
)

@CrewBase
class CodeWritingCrew:
    """
    CodeWritingCrew focuses on code generation, debugging, and testing tasks,
    utilizing specialized agents from dev_utilities.
    """
    # tasks_config = 'config/code_writing_crew_tasks.yaml' # Example path

    @property
    def writer(self) -> Agent: # Renamed for brevity
        return code_writer_agent

    @property
    def debugger(self) -> Agent: # Renamed for brevity
        return debugger_agent

    @property
    def tester(self) -> Agent: # Renamed for brevity
        return tester_agent

    # Tasks defined by this crew, now assigned to actual agents
    @task
    def code_generation_task(self) -> Task:
        return Task(
            description="Generate code based on the following requirements: {code_requirements}. "
                        "Ensure the code is clean, follows coding standards, and includes necessary comments and basic error handling. "
                        "Input: {code_requirements}, {target_language_or_framework}.",
            expected_output="Well-written and functional code for {code_requirements} in {target_language_or_framework}, "
                            "including inline documentation and ready for initial review or testing.",
            agent=self.writer, # type: ignore[attr-defined]
            successCriteria=["Code generated", "Follows coding standards", "Includes comments", "Basic error handling included"]
        )

    @task
    def debugging_task(self) -> Task:
        return Task(
            description="Debug the provided {code_to_debug_snippet_or_path} to resolve the reported {issue_description}. "
                        "Identify the root cause, implement a robust fix, and explain the changes. "
                        "Input: {code_to_debug_snippet_or_path}, {issue_description}, {steps_to_reproduce_bug}.",
            expected_output="Corrected code with the identified bug fixed. "
                            "A brief report detailing the root cause, the fix applied, and verification steps.",
            agent=self.debugger, # type: ignore[attr-defined]
            context=[self.code_generation_task], # Optional context: debugging might follow initial generation
            successCriteria=["Bug fixed", "Root cause identified", "Fix explained", "Verification steps provided"]
        )

    @task
    def unit_testing_task(self) -> Task: # Made more specific to unit testing
        return Task(
            description="Write and execute unit tests for the {code_module_or_function} to ensure its correctness and reliability. "
                        "Achieve a target of {target_coverage_percentage}% code coverage if specified. "
                        "Input: {code_module_or_function_path}, {test_specifications_or_requirements}, {target_coverage_percentage}.",
            expected_output="A suite of unit tests for {code_module_or_function}. "
                            "A test execution report showing all tests passing and code coverage achieved. "
                            "Any identified bugs from testing should be reported.",
            agent=self.tester, # type: ignore[attr-defined]
            context=[self.debugging_task], # Testing usually follows debugging (or initial dev)
            successCriteria=["Unit tests written", "Tests executed successfully", "Test report generated", "Code coverage achieved"]
        )

    @crew
    def crew(self, job_scope: str | list[str]) -> ValidatedCrew: # Return type changed
        """Creates the Code Writing Utility crew"""
        if isinstance(job_scope, str):
            job_scope = [job_scope]

        all_agents = [self.writer, self.debugger, self.tester]
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
            logging.info(f"Pruned tasks for job_scope '{job_scope}' in CodeWritingCrew: {pruned_task_descriptions}")

        if not active_agents:
            logging.warning(f"No active agents for job_scope '{job_scope}' in CodeWritingCrew. Crew will have no agents.")
        if not filtered_tasks:
            logging.warning(f"No tasks were matched for the active agents with job_scope '{job_scope}' in CodeWritingCrew. Crew will have no tasks.")

        created_crew = ValidatedCrew( # Changed to ValidatedCrew
            agents=active_agents,
            tasks=filtered_tasks,
            process=Process.sequential, # These tasks often follow a sequence
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
#         'code_requirements': 'a Python class for managing a simple TO-DO list with add, remove, and view functionalities',
#         'target_language_or_framework': 'Python',
#         'code_to_debug_snippet_or_path': 'todo_list_v1.py', # Assume this file has the generated code or existing buggy code
#         'issue_description': 'Removing an item from an empty list causes a crash.',
#         'steps_to_reproduce_bug': '1. Create an empty TodoList. 2. Call remove_item("any_item").',
#         'code_module_or_function_path': 'todo_list_v2.py', # Assume this is the debugged version
#         'test_specifications_or_requirements': 'Test all public methods, including edge cases like empty list, item not found.',
#         'target_coverage_percentage': '90'
#     }
#     code_writing_crew_instance = CodeWritingCrew()
#     result = code_writing_crew_instance.crew().kickoff(inputs=inputs)
#     print("\n\nCode Writing Crew execution finished.")
#     print("Result:")
#     print(result)
