from crewai import Crew, Process, Agent, Task
from crewai.project import CrewBase, agent, crew, task

# Import the actual tech stack committee agents
from mycrews.qrew.orchestrators.tech_stack_committee.stack_advisor_agent import stack_advisor_agent
from mycrews.qrew.orchestrators.tech_stack_committee.constraint_checker_agent import constraint_checker_agent
from mycrews.qrew.orchestrators.tech_stack_committee.documentation_writer_agent import documentation_writer_agent

@CrewBase
class TechVettingCouncilCrew:
    """TechVettingCouncilCrew is responsible for detailed analysis and documentation of tech choices."""

    @property
    def stack_advisor(self) -> Agent:
        return stack_advisor_agent

    @property
    def constraint_checker(self) -> Agent:
        return constraint_checker_agent

    @property
    def doc_writer(self) -> Agent:
        return documentation_writer_agent

    # Tasks for this crew will be assigned by the TechVettingCouncilAgent (the orchestrator).
    # The tasks defined here are examples of what this crew *can* do,
    # and would typically be loaded and configured based on the specific vetting request.
    # For this structure, we'll assume tasks are defined in the TechVettingCouncilAgent's YAML
    # and passed to this crew, or this crew's tasks are dynamically created.
    # However, to follow the @task pattern for CrewBase, we can define some generic tasks
    # that showcase the agents' roles within this crew.

    @task
    def technology_evaluation_task(self) -> Task:
        return Task(
            description="Evaluate the proposed {technology_or_architecture} based on {evaluation_criteria}. "
                        "Consider its pros, cons, alignment with {project_goals}, and potential risks. "
                        "Input: {technology_or_architecture}, {evaluation_criteria}, {project_goals}, {current_tech_stack}.",
            expected_output="A detailed evaluation report for {technology_or_architecture}, "
                            "including a recommendation and justifications.",
            agent=self.stack_advisor # type: ignore[attr-defined]
        )

    @task
    def constraint_compliance_check_task(self) -> Task:
        return Task(
            description="Verify that the {proposed_item} (e.g., technology, library, vendor) "
                                "complies with all specified {constraints_list} (e.g., budget, security, licensing). "
                                "Input: {proposed_item}, {constraints_list}.",
            expected_output="A compliance report for {proposed_item}, detailing adherence to each constraint "
                                    "and highlighting any violations or concerns.",
            agent=self.constraint_checker # type: ignore[attr-defined]
        )

    @task
    def decision_documentation_task(self) -> Task:
        return Task(
            description="Document the final decision and rationale for {vetted_item_name}. "
                                "Include details of the evaluation, alternatives considered, and any conditions for approval. "
                                "Input: {vetted_item_name}, {council_decision_summary}, {supporting_documents_links}, {documentation_template}.",
            expected_output="A comprehensive document recording the vetting decision for {vetted_item_name}, "
                                    "suitable for archival and stakeholder communication.",
            agent=self.doc_writer # type: ignore[attr-defined]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Tech Vetting Council analysis crew"""
        return Crew(
            agents=[self.stack_advisor, self.constraint_checker, self.doc_writer],
            tasks=self.tasks, # Tasks decorated with @task
            process=Process.sequential, # Or could be parallel if tasks are independent for a given proposal
            verbose=True
        )
