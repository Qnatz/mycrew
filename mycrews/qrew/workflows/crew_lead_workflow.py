import json
from typing import Any # Added Any
from crewai import Crew, Process, Task
from crewai.tasks.task_output import TaskOutput # Added
from ..lead_agents.backend_project_coordinator_agent.agent import backend_project_coordinator_agent
from ..lead_agents.web_project_coordinator_agent.agent import web_project_coordinator_agent
from ..lead_agents.mobile_project_coordinator_agent.agent import mobile_project_coordinator_agent
from ..lead_agents.devops_and_integration_coordinator_agent.agent import devops_and_integration_coordinator_agent

def validate_json_plan_output(task_output: TaskOutput) -> tuple[bool, Any]:
    """
    Validates if the LLM output (from task_output.raw) is a JSON object
    with a 'tasks' key containing a list.
    """
    if not hasattr(task_output, 'raw') or not isinstance(task_output.raw, str):
        return False, "Guardrail input (task_output.raw) must be a string and present."
    output_str = task_output.raw

    # Strip markdown fences if present
    if output_str.startswith("```json"):
        output_str = output_str[len("```json"):].strip()
        if output_str.endswith("```"):
            output_str = output_str[:-len("```")].strip()
    elif output_str.startswith("```"):
        output_str = output_str[len("```"):].strip()
        if output_str.endswith("```"):
            output_str = output_str[:-len("```")].strip()

    # Ensure the string starts with { and ends with } after stripping, if it's not empty
    # This is a gentle correction, as json.loads() will fail anyway if it's not a valid object/array start/end.
    # However, LLMs sometimes forget the final brace after stripping.
    # This specific check might be too aggressive or not needed if json.loads() is the ultimate validator.
    # For now, let's rely on the stripping and then the json.loads() to do its job.
    # An empty string after stripping should also fail json.loads() correctly.

    # Attempt to extract JSON object/array if it's embedded and not found by simple stripping
    # Ensure output_str is not empty before checking strip().startswith()
    if output_str and output_str.strip() and not output_str.strip().startswith('{') and not output_str.strip().startswith('['):
        print(f"GUARDRAIL_DEBUG: Output does not start with JSON object/array after initial stripping. Attempting to find embedded JSON. Original (first 200 chars): '{output_str[:200]}'")
        # Try to find the first '{' and last '}' for an object
        first_brace = output_str.find('{')
        last_brace = output_str.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            potential_json = output_str[first_brace:last_brace+1].strip()
            # Basic check to see if this substring could be JSON
            # Avoids replacing a valid non-JSON string with just its first/last braces if they are incidental
            # This heuristic might need refinement.
            # For now, if it looks like a plausible JSON object, try it.
            # A simple check: does it start with { and end with } and contain a colon (common in JSON objects)?
            if potential_json.startswith('{') and potential_json.endswith('}') and ':' in potential_json:
                print(f"GUARDRAIL_DEBUG: Extracted potential JSON object: '{potential_json[:200]}'")
                output_str = potential_json
            else:
                print(f"GUARDRAIL_DEBUG: Found braces, but extracted substring '{potential_json[:200]}' doesn't look like a simple JSON object. Trying array next.")
                # Try to find first '[' and last ']' for an array
                first_bracket = output_str.find('[')
                last_bracket = output_str.rfind(']')
                if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
                    potential_json_array = output_str[first_bracket:last_bracket+1].strip()
                    if potential_json_array.startswith('[') and potential_json_array.endswith(']'): # Basic check for array
                        print(f"GUARDRAIL_DEBUG: Extracted potential JSON array: '{potential_json_array[:200]}'")
                        output_str = potential_json_array
                    else:
                        print(f"GUARDRAIL_DEBUG: Found brackets, but extracted substring '{potential_json_array[:200]}' doesn't look like a simple JSON array. Proceeding with original output_str for parsing attempt.")
                else:
                    print(f"GUARDRAIL_DEBUG: No clear JSON object or array structure found by brace/bracket hunting. Proceeding with original output_str for parsing attempt.")
        else: # No matching braces, try brackets for array
            first_bracket = output_str.find('[')
            last_bracket = output_str.rfind(']')
            if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
                potential_json_array = output_str[first_bracket:last_bracket+1].strip()
                if potential_json_array.startswith('[') and potential_json_array.endswith(']'): # Basic check for array
                    print(f"GUARDRAIL_DEBUG: Extracted potential JSON array (no prior object found): '{potential_json_array[:200]}'")
                    output_str = potential_json_array
                else:
                    print(f"GUARDRAIL_DEBUG: Found brackets, but extracted substring '{potential_json_array[:200]}' doesn't look like a simple JSON array. Proceeding with original output_str for parsing attempt.")
            else:
                 print(f"GUARDRAIL_DEBUG: No JSON object/array found by simple brace/bracket hunting. Proceeding with original output_str for parsing attempt.")

    try:
        data = json.loads(output_str)
        if isinstance(data, dict) and "tasks" in data and isinstance(data["tasks"], list):
            # Further check if all tasks in the list are strings, as per original intent
            if all(isinstance(task_item, str) for task_item in data["tasks"]):
                return True, data
            else:
                return False, "All items in the 'tasks' list must be strings."
        else:
            return False, "Output must be a valid JSON object with a 'tasks' key containing a list of strings."
    except json.JSONDecodeError:
        print(f"GUARDRAIL_JSON_DECODE_ERROR: Failed to parse JSON. Content that failed (first 500 chars): '{output_str[:500]}'")
        return False, "Output must be valid JSON." # output_str implied
    except Exception as e: # Catch any other unexpected errors during validation
        return False, f"Validation error: {str(e)}"


def run_crew_lead_workflow(inputs: dict):
    print(f"DEBUG: Entering run_crew_lead_workflow with inputs: {inputs.get('project_name', 'N/A')} scope: {inputs.get('taskmaster', {}).get('project_scope', 'N/A')}")
    project_name = inputs.get("project_name", "UnnamedProject")
    project_scope = inputs.get("taskmaster", {}).get("project_scope", "unknown")
    architecture_summary_str = json.dumps(inputs.get("architecture", {}), indent=2)

    print(f"Crew Lead Workflow: Project '{project_name}', Scope '{project_scope}'")

    active_tasks = []
    active_agents = []

    # Define task details (can be further templatized)
    task_expected_output_template = (
        "Output a JSON object with a single key 'tasks'. The value of 'tasks' must be a list of strings. "
        "Each string should be a detailed task description for {domain} implementation. "
        "Example: {{'tasks': ['Design the user login API endpoint.', 'Implement the user database schema.']}}"
    )

    backend_task_details = {
        "description": f"Plan backend implementation for {project_name} based on Architecture: {architecture_summary_str}. "
                       f"Your primary goal is to decompose the backend requirements into a comprehensive list of specific, actionable tasks, "
                       f"each tailored for a distinct backend specialization. For each task, clearly indicate the type of work "
                       f"(e.g., 'data model design for X module', 'API endpoint creation for Y feature', 'authentication logic for Z service', "
                       f"'setup message queue for A', 'configure B service', 'implement data storage for C', 'develop data synchronization for D'). "
                       f"Ensure tasks are granular enough to be handled by specialized agents like DataModelAgent, ApiCreatorAgent, AuthAgent, "
                       f"ConfigAgent, QueueAgent, StorageAgent, SyncAgent, etc. The output must be a list of these detailed task strings.",
        "agent": backend_project_coordinator_agent,
        "expected_output": task_expected_output_template.format(domain="backend")
    }
    web_task_details = {
        "description": f"Plan frontend (web) implementation for {project_name} based on Architecture: {architecture_summary_str}. "
                       f"Decompose web requirements into specific, actionable tasks, each tailored for a distinct frontend specialization. "
                       f"Indicate task types like 'static page creation for X', 'dynamic UI component development for Y feature using Z framework', "
                       f"'asset management and optimization for A section', 'API integration for B feature'. "
                       f"Ensure tasks are granular for agents like StaticPageBuilderAgent, DynamicPageBuilderAgent, AssetManagerAgent. "
                       f"Output a list of these detailed task strings.",
        "agent": web_project_coordinator_agent,
        "expected_output": task_expected_output_template.format(domain="frontend")
    }
    mobile_task_details = {
        "description": f"Plan mobile implementation for {project_name} (for relevant platforms like Android/iOS) based on Architecture: {architecture_summary_str}. "
                       f"Decompose mobile requirements into specific, actionable tasks for distinct mobile specializations. "
                       f"Indicate task types like 'Android UI for X screen', 'iOS UI for Y screen', 'Android API client for Z service', "
                       f"'iOS data storage for A feature'. Ensure tasks are granular for agents like AndroidUIAgent, IOSUIAgent, "
                       f"AndroidAPIClientAgent, IOSAPIClientAgent, AndroidStorageAgent, IOSStorageAgent. "
                       f"Output a list of these detailed task strings.",
        "agent": mobile_project_coordinator_agent,
        "expected_output": task_expected_output_template.format(domain="mobile")
    }
    devops_task_details = {
        "description": f"Plan deployment, CI/CD pipeline, and infrastructure setup for {project_name} based on Architecture: {architecture_summary_str}. "
                       f"Decompose DevOps requirements into specific, actionable tasks. Indicate task types like 'setup Kubernetes deployment for X service', "
                       f"'configure CI/CD pipeline for Y repository', 'database setup and migration script for Z', 'implement monitoring for A'. "
                       f"Ensure tasks are granular for a DevOps specialist. Output a list of these detailed task strings.",
        "agent": devops_and_integration_coordinator_agent,
        "expected_output": task_expected_output_template.format(domain="deployment")
    }

    agent_to_plan_key_map = {
        backend_project_coordinator_agent.role: "backend_plan", # Assuming agent has a unique role attribute
        web_project_coordinator_agent.role: "frontend_plan",
        mobile_project_coordinator_agent.role: "mobile_plan",
        devops_and_integration_coordinator_agent.role: "deployment_plan",
    }
    # Fallback if agent.role is not available or not unique: use agent name or a custom mapping
    if not hasattr(backend_project_coordinator_agent, 'role'): # Simple check, can be more robust
        agent_to_plan_key_map = {
            "Backend Project Coordinator": "backend_plan", # Replace with actual agent names if role isn't there
            "Web Project Coordinator": "frontend_plan",
            "Mobile Project Coordinator": "mobile_plan",
            "DevOps and Integration Coordinator": "deployment_plan"
        }


    if project_scope == "full-stack":
        active_agents.extend([backend_project_coordinator_agent, web_project_coordinator_agent, mobile_project_coordinator_agent])
        active_tasks.extend([Task(**backend_task_details), Task(**web_task_details), Task(**mobile_task_details)])
    elif project_scope == "web-only":
        active_agents.extend([backend_project_coordinator_agent, web_project_coordinator_agent])
        active_tasks.extend([Task(**backend_task_details), Task(**web_task_details)])
    elif project_scope == "mobile-only":
        active_agents.extend([backend_project_coordinator_agent, mobile_project_coordinator_agent]) # Assuming mobile often needs a backend
        active_tasks.extend([Task(**backend_task_details), Task(**mobile_task_details)])
    elif project_scope == "backend-only":
        active_agents.append(backend_project_coordinator_agent)
        active_tasks.append(Task(**backend_task_details))
    elif project_scope == "documentation-only":
        pass # No planning tasks for these leads
    else: # "unknown" or any other scope
        print(f"Warning: Project scope '{project_scope}' is 'unknown' or not specifically handled. Defaulting to web and backend planning only.")
        active_agents.extend([backend_project_coordinator_agent, web_project_coordinator_agent])
        active_tasks.extend([Task(**backend_task_details), Task(**web_task_details)])

    # DevOps is typically always needed if any other development is happening
    if active_tasks:
        active_agents.append(devops_and_integration_coordinator_agent)
        active_tasks.append(Task(**devops_task_details))

    if not active_tasks:
        print(f"Warning: No active tasks generated by CrewLeadWorkflow for project '{project_name}' with scope '{project_scope}'.")
        return {
            "backend_plan": {"tasks": []}, "frontend_plan": {"tasks": []},
            "mobile_plan": {"tasks": []}, "deployment_plan": {"tasks": []},
            "notes": f"No planning tasks generated due to project scope '{project_scope}'."
        }

    crew = Crew(
        agents=list(set(active_agents)), # Ensure unique agents if one agent could be added twice by logic
        tasks=active_tasks,
        process=Process.sequential, # Or parallel if tasks are independent. Sequential is safer for outputs.
        verbose=True
    )
    result = crew.kickoff()

    # Initialize output structure with default empty plans
    output_plans = {
        "backend_plan": {"tasks": []},
        "frontend_plan": {"tasks": []},
        "mobile_plan": {"tasks": []},
        "deployment_plan": {"tasks": []},
        "notes": ""
    }
    default_error_plan_text = "Error: Failed to generate a valid plan or task was not run."

    if result and result.tasks_output:
        for i, task_output_obj in enumerate(result.tasks_output):
            # Determine which plan this output belongs to by checking the agent of the original task
            # This assumes active_tasks order is preserved in tasks_output
            if i < len(active_tasks):
                task_agent = active_tasks[i].agent
                plan_key = None
                # Try to map agent to plan_key using role, then by direct object comparison or name
                if hasattr(task_agent, 'role') and task_agent.role in agent_to_plan_key_map:
                    plan_key = agent_to_plan_key_map[task_agent.role]
                elif task_agent.name in agent_to_plan_key_map: # Fallback to agent name if role is not good
                     plan_key = agent_to_plan_key_map[task_agent.name]
                else: # Last resort, try direct agent object comparison (less reliable across sessions if agents are re-instantiated)
                    for ag, pk in agent_to_plan_key_map.items(): # This map needs to be {agent_obj: plan_key} for this to work
                        if task_agent == ag: # This comparison might fail if agents are not the exact same objects
                            plan_key = pk
                            break

                if not plan_key:
                    print(f"Warning: Could not map agent {task_agent.name if hasattr(task_agent, 'name') else 'UnknownAgent'} to a plan key. Skipping its output.")
                    continue

                current_plan_name_for_error = plan_key.replace("_plan", "").capitalize()

                if task_output_obj and hasattr(task_output_obj, 'raw') and task_output_obj.raw:
                    try:
                        # Guardrail should have ensured this is valid JSON if task was successful
                        parsed_plan = json.loads(task_output_obj.raw)
                        if isinstance(parsed_plan, dict) and "tasks" in parsed_plan and isinstance(parsed_plan["tasks"], list):
                            output_plans[plan_key] = parsed_plan
                        else:
                            print(f"Warning: Output for {current_plan_name_for_error} plan was not in the expected format. Raw: {task_output_obj.raw}")
                            output_plans[plan_key] = {"tasks": [default_error_plan_text + f" (Bad format for {current_plan_name_for_error})"]}
                    except json.JSONDecodeError:
                        print(f"Error: Failed to parse JSON for {current_plan_name_for_error} plan. Raw: {task_output_obj.raw}")
                        output_plans[plan_key] = {"tasks": [default_error_plan_text + f" (JSON parse error for {current_plan_name_for_error})"]}
                else:
                    print(f"Error: No valid output found for {current_plan_name_for_error} plan.")
                    output_plans[plan_key] = {"tasks": [default_error_plan_text + f" (No output for {current_plan_name_for_error})"]}
            else:
                print(f"Warning: More task outputs than active tasks defined. Index {i}. Discarding extra output.")
    else:
        output_plans["notes"] = "Crew execution did not produce any task outputs."
        # All plans remain as default empty / error indication
        for key in output_plans:
            if key != "notes" and not output_plans[key]["tasks"]:
                 output_plans[key] = {"tasks": [default_error_plan_text + f" (No crew output for {key.replace('_plan','').capitalize()})"]}

    print(f"DEBUG: Exiting run_crew_lead_workflow")
    return output_plans
