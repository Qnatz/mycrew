import json
# import logging # logging import removed as it's not used in the new version
from crewai import Crew, Task
# from ..orchestrators.idea_interpreter_agent.agent import idea_interpreter_agent # Moved into _perform_architecture_generation
# from ..orchestrators.project_architect_agent.agent import project_architect_agent # Moved into _perform_architecture_generation
from ..project_manager import ProjectStateManager


def _perform_architecture_generation(inputs: dict):
    from ..orchestrators.idea_interpreter_agent.agent import idea_interpreter_agent
    from ..orchestrators.project_architect_agent.agent import project_architect_agent
    print("Performing architecture generation using Idea Interpreter and Project Architect agents...")

    # Step A: Idea Interpretation Task
    taskmaster_artifacts = inputs.get("taskmaster", {})
    refined_brief = taskmaster_artifacts.get("refined_brief", taskmaster_artifacts.get("initial_brief", ""))
    project_name = inputs.get("project_name", taskmaster_artifacts.get("project_name", "Unknown Project"))
    project_scope = taskmaster_artifacts.get("project_scope", "unknown") # Get project_scope
    stakeholder_feedback = inputs.get("stakeholder_feedback", "")
    market_research_data = inputs.get("market_research_data", "")

    # Access Tech Vetting Artifacts
    tech_vetting_artifacts = inputs.get("tech_vetting", {})
    vetting_report = tech_vetting_artifacts.get("vetting_report_markdown")

    if not refined_brief:
        print("Error in Idea-to-Architecture: No refined_brief from Taskmaster.")
        return {"error": "Missing refined_brief from Taskmaster for idea interpretation.", "requirements_document_markdown": None, "architecture_document_markdown": None}

    idea_interpretation_task_desc = (
        f"Project Name: '{project_name}'\n"
        f"Project Scope: '{project_scope}'\n" # Add scope to context
        f"Refined Brief from Taskmaster: '{refined_brief}'\n"
        f"Stakeholder Feedback (if any): '{stakeholder_feedback}'\n"
        f"Market Research Data (if any): '{market_research_data}'\n"
    )
    if vetting_report:
        idea_interpretation_task_desc += f"\nTech Vetting Report (for context and to resolve ambiguities):\n{vetting_report}\n"

    idea_interpretation_task_desc += (
        f"\nYour primary goal is to analyze all available information and translate it into a comprehensive "
        f"technical requirements specification document. This document MUST strictly adhere to the defined 'Project Scope'. "
        f"For instance, if scope is 'web-only', user stories and functional requirements should focus solely on web interactions and necessary backend APIs, excluding mobile-specific features. "
        f"If 'documentation-only', focus on information structure, content generation needs, and target audience, not software features. "
        f"The document should include detailed user stories with acceptance criteria, clear functional requirements, "
        f"important non-functional requirements (e.g., performance, security), data requirements, a glossary if new terms are introduced, "
        f"and list any ambiguities (especially if the vetting report highlights them or helps clarify them). "
        f"Consult your knowledge base if needed for similar patterns or requirements."
    )
    idea_interpretation_expected_output = (
        "A comprehensive technical requirements specification document in Markdown format. This document should clearly outline: "
        "1. Detailed User Stories (with acceptance criteria). "
        "2. Functional Requirements. "
        "3. Non-Functional Requirements. "
        "4. Data Requirements (input/output, formats). "
        "5. Glossary of Terms (if applicable). "
        "6. Identified Ambiguities/Questions."
    )
    idea_task = Task(
        description=idea_interpretation_task_desc,
        agent=idea_interpreter_agent,
        expected_output=idea_interpretation_expected_output,
        max_retries=1
    )

    print("Running Idea Interpretation sub-task...")
    idea_crew = Crew(agents=[idea_interpreter_agent], tasks=[idea_task], verbose=False) # verbose can be True for debugging
    idea_result = idea_crew.kickoff()

    if not idea_result or not hasattr(idea_result, 'raw') or not idea_result.raw or len(idea_result.raw.strip()) == 0:
        print("Error: Idea Interpretation task failed to produce output.")
        return {"error": "Idea Interpretation failed or produced no output.", "requirements_document_markdown": None, "architecture_document_markdown": None}

    # Heuristic check for error message in output
    if "error" in idea_result.raw.lower() and len(idea_result.raw.strip()) < 200:
        print(f"Error from Idea Interpretation task: {idea_result.raw}")
        return {"error": f"Idea Interpretation agent returned an error: {idea_result.raw}", "requirements_document_markdown": None, "architecture_document_markdown": None}

    requirements_doc_markdown = idea_result.raw
    print("Idea Interpretation sub-task completed.")

    # Step B: Project Architecture Task
    constraints = inputs.get("constraints", "")
    technical_vision = inputs.get("technical_vision", "")

    # Retrieve tech vetting outputs for the architect
    recommended_tech_stack = tech_vetting_artifacts.get("recommended_tech_stack")
    architectural_guidelines = tech_vetting_artifacts.get("architectural_guidelines_markdown")

    project_architecture_task_desc = (
        f"Project Name: '{project_name}'\n"
        f"Project Scope: '{project_scope}'\n" # Add scope to context
        f"Technical Requirements Specification:\n{requirements_doc_markdown}\n\n"
        f"Project Constraints (if any): '{constraints}'\n"
        f"Technical Vision (if any): '{technical_vision}'\n\n"
    )

    if recommended_tech_stack:
        project_architecture_task_desc += (
            f"A prior Tech Vetting stage has recommended the following technology stack: {json.dumps(recommended_tech_stack)}. "
            f"You MUST base your architecture on this recommended stack. If strong reasons exist to deviate for a specific component, "
            f"you must explicitly state the deviation and provide a compelling justification, referencing the original recommendation.\n"
        )
    else:
        project_architecture_task_desc += (
            "No specific tech stack was pre-determined by a vetting stage. You will need to recommend a suitable technology stack "
            "as part of your architecture design, justifying your choices for the given project scope.\n"
        )

    if architectural_guidelines:
        project_architecture_task_desc += (
            f"Additionally, the Tech Vetting stage provided these architectural guidelines. You MUST adhere to them:\n"
            f"'''\n{architectural_guidelines}\n'''\n\n"
        )

    project_architecture_task_desc += (
        f"Your goal is to design a robust and scalable software architecture based on all the provided information. "
        f"The architectural design MUST strictly adhere to the defined 'Project Scope' ('{project_scope}'). "
        f"For instance, if scope is 'web-only', design only web components and any essential backend APIs supporting the web functionality; do not include mobile components or unrelated backend services. "
        f"If scope is 'mobile-only', focus solely on the mobile application architecture and any direct backend services it requires. "
        f"If 'documentation-only', your 'architecture' should focus on the structure of the documentation, information flow, and tools/platforms for hosting, not software components. "
        f"The architecture should align with best practices for the specified scope."
    )

    project_architecture_expected_output = (
        "A detailed software architecture document in Markdown format. This document MUST include: "
        "1. High-level system diagrams descriptions (e.g., component diagram, deployment diagram). "
        "2. Technology stack for each major component (this MUST align with pre-vetted stack if provided, or be your recommendation if not). "
        "3. Data model design overview (key entities, relationships). "
        "4. API design guidelines and key endpoint definitions (e.g., paths, methods, brief request/response structure). "
        "5. Integration points with any external services. "
        "6. Considerations for non-functional requirements (e.g., security plan, scalability strategy, performance). "
        "7. If a pre-vetted tech stack was provided, confirm its adoption or clearly justify any deviations."
    )
    architecture_task = Task(
        description=project_architecture_task_desc,
        agent=project_architect_agent,
        expected_output=project_architecture_expected_output,
        max_retries=1
    )

    print("Running Project Architecture sub-task...")
    architecture_crew = Crew(agents=[project_architect_agent], tasks=[architecture_task], verbose=False)
    architecture_result = architecture_crew.kickoff()

    if not architecture_result or not hasattr(architecture_result, 'raw') or not architecture_result.raw or len(architecture_result.raw.strip()) == 0:
        print("Error: Project Architecture task failed to produce output.")
        return {"error": "Project Architecture failed or produced no output.", "requirements_document_markdown": requirements_doc_markdown, "architecture_document_markdown": None}

    if "error" in architecture_result.raw.lower() and len(architecture_result.raw.strip()) < 200:
        print(f"Error from Project Architecture task: {architecture_result.raw}")
        return {"error": f"Project Architecture agent returned an error: {architecture_result.raw}", "requirements_document_markdown": requirements_doc_markdown, "architecture_document_markdown": None}

    architecture_document_markdown = architecture_result.raw
    print("Project Architecture sub-task completed.")

    # Step C: Return Formatted Artifacts
    # TODO: Implement parsing of architecture_document_markdown into more structured
    #       components (list/dict), database_schema (dict), technology_stack (list)
    #       as was previously simulated, to be more directly usable by downstream stages.
    return {
        "requirements_document_markdown": requirements_doc_markdown, # Adding this for completeness
        "architecture_document_markdown": architecture_document_markdown,
        "notes": "Architecture generated. Further parsing of the Markdown into structured components, DB schema, etc., is a future enhancement."
        # Keep technology_stack and system_diagrams if they are meant to be separate,
        # otherwise, they should be part of the architecture_document_markdown.
        # For now, let's assume they are part of the markdown.
        # "technology_stack": ["Placeholder: To be extracted from Markdown"],
        # "system_diagrams": {"placeholder_diagram": "To be extracted or linked from Markdown"}
    }

def run_idea_to_architecture_flow(inputs: dict):
    print(f"DEBUG: Entering run_idea_to_architecture_flow with inputs: {inputs.get('project_name', 'N/A')} scope: {inputs.get('taskmaster', {}).get('project_scope', 'N/A')}")
    project_name = inputs.get("project_name")
    if not project_name:
        # Fallback or raise error if project_name is critical and not found
        # For now, let's try to get it from a potential taskmaster artifact if this flow
        # expects to run after a taskmaster stage that might not explicitly pass project_name.
        # However, the new orchestrator should be passing project_name in initial_inputs.
        print("Warning: project_name not found directly in inputs for run_idea_to_architecture_flow.")
        # Attempt to find it in a common artifact location if this is a sub-flow context
        project_name = inputs.get("taskmaster", {}).get("project_name", "default_project_temp_name")
        if project_name == "default_project_temp_name":
             print("Critical Error: Project name could not be determined for state management in architecture flow.")
             raise ValueError("Project name is required for ProjectStateManager in run_idea_to_architecture_flow")

    state = ProjectStateManager(project_name) # Initialize with project_name

    # Check if we have existing artifacts for the "architecture" stage
    # The orchestrator already checks this, but an internal check can be a safeguard
    # or useful if this flow is ever called directly.
    # However, to align with the issue's Orchestrator which calls this for an active stage,
    # we might assume this check is optional here if orchestrator guarantees stage is active.
    # For robustness, let's keep it, especially if this flow could be resumed internally.
    # The issue example shows this check.
    if state.is_completed("architecture"):
        print(f"'{project_name}': Using cached architecture artifacts for stage 'architecture'")
        print(f"DEBUG: Exiting run_idea_to_architecture_flow")
        return state.get_artifacts("architecture")

    print(f"'{project_name}': Running main logic for 'architecture' stage.")
    try:
        # ... existing architecture workflow logic ...
        # This is now encapsulated in _perform_architecture_generation
        # The 'inputs' dictionary here is what the orchestrator provides,
        # which includes initial_inputs and all previously collected artifacts.

        # The 'user_idea' key is expected by the original task_interpret_idea.
        # If 'taskmaster' stage ran, its output might be under inputs['taskmaster']
        # Let's ensure the core logic gets what it needs.
        # For example, if taskmaster produced a brief:
        # core_logic_inputs = {**inputs, "user_idea": inputs.get("taskmaster", {}).get("initial_brief")}

        generated_artifacts = _perform_architecture_generation(inputs)

        # The 'artifacts' dictionary should match what's expected by later stages
        # or what needs to be stored for this stage.
        # The issue example returns the artifacts directly. The orchestrator handles calling complete_stage.

        print(f"'{project_name}': Architecture stage completed successfully. Returning artifacts.")
        print(f"DEBUG: Exiting run_idea_to_architecture_flow")
        return generated_artifacts # Orchestrator will call state.complete_stage with this

    except Exception as e:
        print(f"'{project_name}': Error during architecture stage: {str(e)}")
        # Log failure with the state manager. Orchestrator will also catch and log.
        state.fail_stage("architecture", f"Error in run_idea_to_architecture_flow: {str(e)}")
        print(f"DEBUG: Exiting run_idea_to_architecture_flow with error")
        raise # Re-raise for the orchestrator to handle
