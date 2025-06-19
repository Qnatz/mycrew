from crewai import Crew, Process, Agent, Task
from crewai.project import CrewBase, agent, crew, task

# Import the ExecutionManagerAgent
from mycrews.qrew.orchestrators.execution_manager_agent.agent import execution_manager_agent

@CrewBase
class ExecutionManagerCrew:
    """ExecutionManagerCrew is responsible for the high-level orchestration of project execution."""

    # Expose the imported agent as a property
    @property
    def manager(self) -> Agent:
        return execution_manager_agent

    # The tasks for this crew are those defined for the ExecutionManagerAgent.
    # We'll define placeholder tasks here that mirror those from execution_manager_agent/tasks.yaml
    # In a more dynamic setup, these tasks could be loaded from that YAML.

    @task
    def project_decomposition_task(self) -> Task:
        return Task(
            description="Decompose the {project_plan_url} into major phases and assign them to appropriate "
                        "Lead Agents or specialized crews. Define objectives, deliverables, and timelines for each phase. "
                        "Input: {project_plan_url}, {available_lead_agents_and_crews_map}.",
            expected_output="A phased execution plan with assigned responsibilities and timelines.",
            agent=self.manager # type: ignore[attr-defined]
        )

    @task
    def progress_monitoring_task(self) -> Task:
        return Task(
            description="Monitor overall execution progress of {project_name} against {key_milestones}. "
                        "Identify risks and bottlenecks, and facilitate inter-crew communication. "
                        "Input: {project_name}, {key_milestones}, {execution_timeline}.",
            expected_output="Comprehensive project status reports and risk assessments.",
            agent=self.manager # type: ignore[attr-defined]
        )

    @task
    def change_management_task(self) -> Task:
        return Task(
            description="Manage changes to the project scope or timeline for {project_name}. "
                        "Assess impact and coordinate adjustments with Lead Agents. "
                        "Input: {project_name}, {change_request_details}, {impact_assessment_template}.",
            expected_output="Updated project execution plan and communication of changes.",
            agent=self.manager # type: ignore[attr-defined]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Execution Manager crew"""
        return Crew(
            agents=[self.manager], # The ExecutionManagerAgent itself
            tasks=self.tasks,    # Tasks defined above
            process=Process.sequential, # Tasks for the manager are likely sequential
            verbose=True
        )
