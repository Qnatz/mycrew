# mycrews/qrew/workflows/tech_vetting_flow.py
import json
from crewai import Crew, Task
from ..orchestrators.tech_stack_committee.crews.tech_vetting_council_crew import TechVettingCouncilCrew
# Import agents if they need to be instantiated here or passed to the crew directly.
# For now, assuming TechVettingCouncilCrew handles its agent composition.
# from ..orchestrators.tech_stack_committee.agents.stack_advisor_agent import stack_advisor_agent
# from ..orchestrators.tech_stack_committee.agents.constraint_checker_agent import constraint_checker_agent
# from ..orchestrators.tech_stack_committee.agents.documentation_writer_agent_tech_committee import documentation_writer_agent_tech_committee
# from ..orchestrators.tech_stack_committee.agents.tech_vetting_council_agent import tech_vetting_council_agent


def run_tech_vetting_workflow(inputs: dict) -> dict:
    print(f"DEBUG: Entering run_tech_vetting_workflow with inputs: {inputs.get('project_name', 'N/A')} scope: {inputs.get('taskmaster', {}).get('project_scope', 'N/A')}")
    """
    Orchestrates the tech vetting process using the TechVettingCouncilCrew.
    """
    print("--- Executing Tech Vetting Workflow ---")

    refined_brief = inputs.get("refined_brief", "")
    project_name = inputs.get("project_name", "UnnamedProject")
    # Potentially, other inputs like 'requirements_document_markdown' could be passed if available.
    # initial_requirements = inputs.get("requirements_document_markdown", "")

    if not refined_brief:
        print("Error: Refined brief not provided to Tech Vetting workflow.")
        return {
            "status": "error",
            "message": "Refined brief is required for tech vetting.",
            "vetting_report_markdown": "# Tech Vetting Failed\n\nReason: Refined brief not provided.",
            "recommended_tech_stack": {},
            "architectural_guidelines_markdown": ""
        }

    # Instantiate the Tech Vetting Crew
    # The TechVettingCouncilCrew class has properties for its agents.
    council_crew_instance_provider = TechVettingCouncilCrew() # Instance of the CrewBase class

    # Define Tasks for the Tech Vetting Crew
    # Task 1: Analyze Project Requirements & Identify Key Tech Decisions
    analysis_task = Task(
        description=f"Analyze the refined project brief for '{project_name}':\n'''{refined_brief}'''\n"
                    f"Identify key technological decision points, areas of uncertainty, and specific technical requirements. "
                    f"Consider scalability, maintainability, security, and integration needs. "
                    f"Output a summary of these key decision points and areas requiring tech stack choices.",
        agent=council_crew_instance_provider.stack_advisor, # Assign to Stack Advisor
        expected_output="A document summarizing key technical decision points, areas of uncertainty, and explicit technical requirements derived from the brief."
    )

    # Task 2: Research and Propose Technology Options
    research_task = Task(
        description=f"Based on the analysis of key technical decision points (output of previous task), "
                    f"research and propose suitable technology options for each point. "
                    f"For each option, briefly outline its pros and cons in the context of the project '{project_name}'. "
                    f"Consider the refined_brief and any known constraints.",
        agent=council_crew_instance_provider.stack_advisor, # Assign to Stack Advisor
        context=[analysis_task],
        expected_output="A document outlining proposed technology options for each identified decision point, with pros and cons for each."
    )

    # Task 3: Evaluate Proposed Technologies Against Constraints & Refined Brief
    evaluation_task = Task(
        description=f"Evaluate the proposed technology options (from research task) against the project's refined brief for '{project_name}', "
                    f"and any specified constraints (e.g., budget, team skills, existing infrastructure if known). "
                    f"The stack_advisor_agent has provided options; your primary role as constraint_checker_agent is to validate these. "
                    f"Prioritize options that best fit the project goals and constraints.",
        agent=council_crew_instance_provider.constraint_checker, # Assign to Constraint Checker
        context=[research_task, analysis_task], # analysis_task for original requirements, research_task for options
        expected_output="An evaluation report detailing how each technology option aligns with project goals and constraints. Clearly state if any options violate constraints."
    )

    # Task 4: Formulate Tech Stack Recommendation and Overall Vetting Report (by Doc Writer, using inputs from others)
    # This task is more about consolidation and documentation.
    # The actual recommendation might be synthesized by Stack Advisor or a lead, then documented.
    # For simplicity, let's assume Doc Writer synthesizes based on prior outputs.
    recommendation_task = Task(
        description=f"Consolidate the findings for project '{project_name}'. Based on the initial analysis (analysis_task), "
                    f"technology research (research_task), and constraint evaluation (evaluation_task), "
                    f"compile a final tech vetting report. This report should include: "
                    f"1. A summary of the vetting process. "
                    f"2. The recommended technology stack (e.g., {{'frontend': 'React', 'backend': 'Node.js'}}). "
                    f"3. High-level architectural guidelines and best practices based on the chosen stack. "
                    f"4. Rationale for choices, alternatives considered, and any identified risks or open questions. "
                    f"Present the overall report in markdown, and extract the recommended_tech_stack as a clean JSON-compatible dictionary within the final JSON output.",
        agent=council_crew_instance_provider.doc_writer, # Assign to Documentation Writer
        context=[evaluation_task, research_task, analysis_task], # All previous tasks provide context
        expected_output="A JSON object containing: "
                        "'recommended_tech_stack': (dict, e.g., {{'frontend': 'React', 'backend': 'Node.js', 'database': 'PostgreSQL'}}), "
                        "'architectural_guidelines_markdown': (string, markdown format, outlining high-level guidelines and best practices), "
                        "and 'vetting_report_markdown': (string, markdown format, summarizing the entire vetting process, options considered, rationale for choices, and any identified risks or open questions)."
    )

    # Create the crew object, passing the agents and the defined tasks
    # The TechVettingCouncilCrew().crew() method uses its own @task decorated methods,
    # which we are overriding here by passing a specific list of tasks.
    final_crew = Crew(
        agents=[
            council_crew_instance_provider.stack_advisor,
            council_crew_instance_provider.constraint_checker,
            council_crew_instance_provider.doc_writer
        ],
        tasks=[analysis_task, research_task, evaluation_task, recommendation_task],
        process="sequential", # Ensure tasks run in order
        verbose=True
    )

    # Kick off the crew's process
    print(f"Kicking off Tech Vetting Crew for project: {project_name}...")
    vetting_results = final_crew.kickoff()

    if not vetting_results:
        print("Error: Tech Vetting Crew execution failed or produced no output.")
        return {
            "status": "error",
            "message": "Tech Vetting Crew execution failed.",
            "vetting_report_markdown": "# Tech Vetting Failed\n\nReason: Crew execution error or no output.",
            "recommended_tech_stack": {},
            "architectural_guidelines_markdown": ""
        }

    # Assuming the final task (recommendation_task) produces the structured JSON output
    # The actual output might be in vetting_results.raw or a specific task's output
    # For now, let's assume it's directly in vetting_results if it's the last task's output and correctly formatted.
    # This might need adjustment based on how Crew.kickoff() returns combined results or last task output.

    # Try to parse the raw output of the last task if it's a string
    final_output_data = {}
    if isinstance(vetting_results, str):
        try:
            final_output_data = json.loads(vetting_results)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse Tech Vetting Crew's final output as JSON. Raw: {vetting_results[:200]}...")
            # Attempt to extract from task outputs if possible (more complex)
            # For now, return raw as part of the report.
            return {
                "status": "partial_success",
                "message": "Tech Vetting Crew finished, but final output parsing failed.",
                "vetting_report_markdown": f"# Tech Vetting Report (Partial)\n\nFinal output was not valid JSON.\nRaw output:\n```\n{vetting_results}\n```",
                "recommended_tech_stack": {},
                "raw_output": vetting_results
            }
    elif isinstance(vetting_results, dict): # If kickoff already returns a dict (e.g. from a tool call of the last agent)
        final_output_data = vetting_results
    else: # If it's some other type, like TaskOutput object
         # Look for raw output in the last task, assuming tasks are executed sequentially and results are stored
        last_task = tech_vetting_crew.tasks[-1]
        if hasattr(last_task, 'output') and hasattr(last_task.output, 'raw') and isinstance(last_task.output.raw, str):
            try:
                final_output_data = json.loads(last_task.output.raw)
            except json.JSONDecodeError:
                 print(f"Warning: Could not parse raw output of last task. Raw: {last_task.output.raw[:200]}...")
                 return {
                    "status": "partial_success",
                    "message": "Tech Vetting Crew finished, but last task output parsing failed.",
                    "vetting_report_markdown": f"# Tech Vetting Report (Partial)\n\nRaw output of last task:\n```\n{last_task.output.raw}\n```",
                    "recommended_tech_stack": {},
                    "raw_output": last_task.output.raw
                }
        else:
            print(f"Warning: Tech Vetting Crew output is not in expected string or dict format. Type: {type(vetting_results)}")
            return {
                "status": "error",
                "message": f"Tech Vetting Crew output in unexpected format: {type(vetting_results)}",
                "vetting_report_markdown": f"# Tech Vetting Failed\n\nReason: Output in unexpected format.",
                "recommended_tech_stack": {}
            }


    print("Tech Vetting Workflow completed.")
    print(f"DEBUG: Exiting run_tech_vetting_workflow")
    return {
        "status": "success",
        "message": "Tech vetting completed successfully.",
        "vetting_report_markdown": final_output_data.get("vetting_report_markdown", "# Report Missing\n\nNo vetting report content found in output."),
        "recommended_tech_stack": final_output_data.get("recommended_tech_stack", {}),
        "architectural_guidelines_markdown": final_output_data.get("architectural_guidelines_markdown", "# Guidelines Missing\n\nNo architectural guidelines found.")
    }
