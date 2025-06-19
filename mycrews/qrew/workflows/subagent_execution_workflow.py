from crewai import Crew, Process, Task
from ..crews.backend_development_crew import BackendDevelopmentCrew
from ..crews.web_development_crew import WebDevelopmentCrew
from ..crews.mobile_development_crew import MobileDevelopmentCrew
from ..crews.devops_crew import DevOpsCrew
from crewai.tasks.task_output import TaskOutput # Ensure TaskOutput is imported
from typing import Any # Ensure Any is imported
import re # Added import re
# Direct imports for specialized backend agents
from ..agents.backend.api_creator_agent.agent import api_creator_agent
from ..agents.backend.data_model_agent.agent import data_model_agent
from ..agents.backend.auth_agent.agent import auth_agent as backend_auth_agent
from ..agents.backend.config_agent.agent import config_agent
from ..agents.backend.queue_agent.agent import queue_agent
from ..agents.backend.storage_agent.agent import storage_agent as backend_storage_agent
from ..agents.backend.sync_agent.agent import sync_agent as backend_sync_agent

# Direct imports for specialized web agents
from ..agents.web.dynamic_page_builder_agent.agent import dynamic_page_builder_agent
from ..agents.web.static_page_builder_agent.agent import static_page_builder_agent
from ..agents.web.asset_manager_agent.agent import asset_manager_agent

# Direct imports for specialized mobile agents from platform-specific subdirectories
from ..agents.mobile.android.android_api_client_agent.agent import android_api_client_agent
from ..agents.mobile.android.android_storage_agent.agent import android_storage_agent
from ..agents.mobile.android.android_ui_agent.agent import android_ui_agent
from ..agents.mobile.ios.ios_api_client_agent.agent import ios_api_client_agent
from ..agents.mobile.ios.ios_storage_agent.agent import ios_storage_agent
from ..agents.mobile.ios.ios_ui_agent.agent import ios_ui_agent

from ..agents.devops import devops_agent

def validate_and_extract_code_output(task_output: TaskOutput) -> tuple[bool, Any]:
    try:
        if not hasattr(task_output, 'raw') or not isinstance(task_output.raw, str):
            print("GUARDRAIL_CODE_EXTRACT: Input task_output.raw is not a string or not present.")
            return False, "Guardrail input (task_output.raw) must be a string and present."

        output_str = task_output.raw.strip()
        print(f"GUARDRAIL_CODE_EXTRACT: Original output (first 300 chars): '{output_str[:300]}'")

        extracted_code_blocks = []

        # Regex to find common fenced code blocks (non-greedy)
        # Matches ```optional_lang
    #...code...
    #``` or ```...code...```
        fence_patterns = [
            re.compile(r"```(?:[a-zA-Z0-9_]+)?\s*\n(.*?)\n```", re.DOTALL), # For multi-line blocks with language
            re.compile(r"```(.*?)```", re.DOTALL) # For single or multi-line blocks without explicit language
        ]

        temp_output_str = output_str
        for pattern in fence_patterns:
            matches = pattern.findall(temp_output_str)
            if matches:
                for match in matches:
                    extracted_code_blocks.append(match.strip())
                # Remove found blocks to avoid re-matching if there are multiple types of fences
                temp_output_str = pattern.sub("", temp_output_str).strip()

        final_extracted_code = ""
        if extracted_code_blocks:
            final_extracted_code = "\n\n".join(extracted_code_blocks).strip()
            print(f"GUARDRAIL_CODE_EXTRACT: Extracted code using fences (first 300 chars): '{final_extracted_code[:300]}'")
        else:
            # Fallback: If no fences, assume the whole (or significant part of) string might be code if it's not conversational.
            # This is a basic heuristic: if it's short and mostly plain language, it's probably not just code.
            # A more sophisticated check might involve token counting, keyword density, etc.
            # For now, if it didn't have fences, we'll take it as is but check if it's empty.
            # The hyper-focused prompts are meant to minimize conversational text.
            if len(output_str.split()) > 50 and len(re.findall(r'[;,=\{\}\[\]\(\)<>]', output_str)) < 5: # Heuristic: many words, few code symbols
                 print(f"GUARDRAIL_CODE_EXTRACT: No fences found, and output looks more like text than code. Length: {len(output_str.split())} words.")
                 # Previously, the error was "The task result does not solely provide code/configuration examples... It includes significant explanatory text"
                 # This guardrail should now return the extracted code. If nothing is extracted and the original output is verbose, it should fail.
                 return False, "Output appears to be mainly explanatory text without clear code blocks, or code is not properly fenced."
            final_extracted_code = output_str # Take the whole string if no fences and it's not clearly verbose text
            print(f"GUARDRAIL_CODE_EXTRACT: No fences found. Assuming entire content might be code/config (first 300 chars): '{final_extracted_code[:300]}'")


        if not final_extracted_code:
            print("GUARDRAIL_CODE_EXTRACT: No code content could be extracted.")
            return False, "No code/configuration content could be extracted from the output."

        # At this point, final_extracted_code contains the best effort extraction.
        # The previous error message was: "The task result does not solely provide code/configuration examples... It includes significant explanatory text..."
        # This guardrail's purpose is to *extract* the code. If successful, it returns (True, extracted_code).
        # The external guardrail (if CrewAI applies another one based on the string) would then judge this *extracted_code*.
        # For a functional guardrail, we decide here.
        # Let's refine the condition for success: extracted code should be substantial.
        if len(final_extracted_code) < 10 and not ("def" in final_extracted_code or "class" in final_extracted_code or "{" in final_extracted_code or "<" in final_extracted_code): # very short, not looking like code
             print(f"GUARDRAIL_CODE_EXTRACT: Extracted content is very short and doesn't resemble typical code structures: '{final_extracted_code}'")
             return False, f"Extracted content is too short or doesn't resemble code: '{final_extracted_code}'"

        print(f"GUARDRAIL_CODE_EXTRACT: Successfully extracted code/configuration. Length: {len(final_extracted_code)}")
        return True, final_extracted_code # Return the extracted code
    except Exception as e:
        print(f"GUARDRAIL_CODE_EXTRACT: Error during code extraction: {str(e)}")
        return False, f"Error during guardrail code extraction: {str(e)}"

def run_subagent_execution_workflow(inputs: dict):
    project_scope = inputs.get("taskmaster", {}).get("project_scope", "unknown")
    print(f"DEBUG: Entering run_subagent_execution_workflow for project_name: {inputs.get('project_name', 'N/A')}, project_scope: {project_scope}")

    # Backend implementation
    backend_result = None
    if project_scope in ["backend-only", "full-stack", "web-only"]: # web-only often implies backend for APIs
        print(f"INFO: Initializing BackendDevelopmentCrew for project_scope: {project_scope}")
        backend_crew_instance = BackendDevelopmentCrew()

        # Pass all high-level inputs from the workflow.
        # BackendDevelopmentCrew's tasks are expected to use these inputs via placeholders.
        # For example, if a task in BackendDevelopmentCrew needs '{feature_description}',
        # it should be present in the main 'inputs' dictionary passed to this workflow.
        final_kickoff_inputs = {**inputs}
        # Add any specific transformations or keys if needed, e.g.:
        # final_kickoff_inputs["planned_backend_task_descriptions"] = inputs.get("crew_assignment", {}).get("backend_plan", {}).get("tasks", [])

        print(f"DEBUG: Kicking off BackendDevelopmentCrew with job_scope='{project_scope}' and input keys: {list(final_kickoff_inputs.keys())}")

        backend_result = backend_crew_instance.crew(job_scope=project_scope).kickoff(inputs=final_kickoff_inputs)
        print("INFO: BackendDevelopmentCrew execution completed.")
    else:
        print(f"INFO: Skipping BackendDevelopmentCrew for project_scope: {project_scope}")
        # Ensure backend_result has a structure that extract_outputs can handle
        backend_result = {"message": f"Skipped backend development due to project_scope: {project_scope}", "tasks_output": []}


    # Web implementation
    web_result = None
    if project_scope in ["web-only", "full-stack"]:
        print(f"INFO: Initializing WebDevelopmentCrew for project_scope: {project_scope}")
        web_crew_instance = WebDevelopmentCrew()
        final_kickoff_inputs = {**inputs}
        print(f"DEBUG: Kicking off WebDevelopmentCrew with job_scope='{project_scope}' and input keys: {list(final_kickoff_inputs.keys())}")
        web_result = web_crew_instance.crew(job_scope=project_scope).kickoff(inputs=final_kickoff_inputs)
        print("INFO: WebDevelopmentCrew execution completed.")
    else:
        print(f"INFO: Skipping WebDevelopmentCrew for project_scope: {project_scope}")
        web_result = {"message": f"Skipped web development due to project_scope: {project_scope}", "tasks_output": []}

    # Mobile implementation
    mobile_result = None
    if project_scope in ["mobile-only", "full-stack"]:
        print(f"INFO: Initializing MobileDevelopmentCrew for project_scope: {project_scope}")
        mobile_crew_instance = MobileDevelopmentCrew()
        final_kickoff_inputs = {**inputs}
        print(f"DEBUG: Kicking off MobileDevelopmentCrew with job_scope='{project_scope}' and input keys: {list(final_kickoff_inputs.keys())}")
        mobile_result = mobile_crew_instance.crew(job_scope=project_scope).kickoff(inputs=final_kickoff_inputs)
        print("INFO: MobileDevelopmentCrew execution completed.")
    else:
        print(f"INFO: Skipping MobileDevelopmentCrew for project_scope: {project_scope}")
        mobile_result = {"message": f"Skipped mobile development due to project_scope: {project_scope}", "tasks_output": []}

    # DevOps implementation
    devops_result = None
    is_dev_scope_active = any(s in project_scope for s in ["backend", "web", "mobile", "full-stack"]) or \
                           project_scope in ["backend-only", "web-only", "mobile-only", "full-stack"]

    if is_dev_scope_active:
        print(f"INFO: Initializing DevOpsCrew for project_scope: {project_scope} (Dev scope active)")
        devops_crew_instance = DevOpsCrew()
        final_kickoff_inputs = {**inputs}
        # Optionally add previous results if needed by DevOps tasks, e.g.:
        # final_kickoff_inputs['backend_artifacts_summary'] = backend_result.summary if backend_result else None
        # final_kickoff_inputs['web_artifacts_summary'] = web_result.summary if web_result else None
        # final_kickoff_inputs['mobile_artifacts_summary'] = mobile_result.summary if mobile_result else None
        print(f"DEBUG: Kicking off DevOpsCrew with job_scope='devops' and input keys: {list(final_kickoff_inputs.keys())}")
        devops_result = devops_crew_instance.crew(job_scope="devops").kickoff(inputs=final_kickoff_inputs)
        print("INFO: DevOpsCrew execution completed.")
    else:
        print(f"INFO: Skipping DevOpsCrew as no primary development scope was active for project_scope: {project_scope}")
        devops_result = {"message": f"Skipped devops due to project_scope: {project_scope}", "tasks_output": []}

    def extract_outputs(crew_output):
        if crew_output and hasattr(crew_output, 'tasks_output') and crew_output.tasks_output:
            # Filter out None task_out objects more carefully
            raw_outputs = []
            for task_out in crew_output.tasks_output:
                if task_out is not None and hasattr(task_out, 'raw') and task_out.raw is not None: # Check .raw is not None
                    raw_outputs.append(task_out.raw)
                elif task_out is not None and (not hasattr(task_out, 'raw') or task_out.raw is None): # .raw missing or None
                    # If task_out exists but .raw is missing/None, it might be an error or different structure
                    raw_outputs.append(f"Warning: Task output found but '.raw' attribute missing or None. Task description: '{getattr(task_out, 'description', 'N/A')}'")

            if not raw_outputs and crew_output.tasks_output: # tasks_output was not empty, but all .raw were None/missing or empty strings if .strip() was used
                 return ["Warning: Tasks were present but yielded no processable raw output or failed internally."]
            # If raw_outputs is empty after processing, it means no valid .raw content was found.
            return raw_outputs if raw_outputs else ["Info: No raw output content found in completed tasks for this segment."]

        elif crew_output is None:
            return ["Info: No tasks were executed for this segment as the plan was empty."]

        # This case handles if crew_output is not None, but doesn't have tasks_output or it's empty.
        return ["Info: No tasks were run or no valid crew output for this segment."]

    return {
        "backend": extract_outputs(backend_result),
        "web": extract_outputs(web_result),
        "mobile": extract_outputs(mobile_result),
        "devops": extract_outputs(devops_result)
    }
    print(f"DEBUG: Exiting run_subagent_execution_workflow") # Added exit print before the final return
