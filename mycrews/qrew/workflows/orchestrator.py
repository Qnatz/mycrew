import json
import logging # Added logging
import os # Added for os.path.join, os.makedirs, etc.
import re # Added import
from typing import Any, Optional
from crewai import Crew, Task
from crewai.tasks.task_output import TaskOutput
# from ..orchestrators.idea_interpreter_agent.agent import idea_interpreter_agent # Removed
# from .idea_to_architecture_flow import run_idea_to_architecture_flow # Moved to __init__
from .crew_lead_workflow import run_crew_lead_workflow
from .subagent_execution_workflow import run_subagent_execution_workflow
from .final_assembly_workflow import run_final_assembly_workflow
from .tech_vetting_flow import run_tech_vetting_workflow # Added import
from ..project_manager import ProjectStateManager
from ..utils import RichProjectReporter # Added import

import yaml # Added for loading tasks from YAML

# Guardrail function for Taskmaster output (original, for old hardcoded task)
def validate_taskmaster_hardcoded_output(task_output: TaskOutput) -> tuple[bool, Any]:
    if not hasattr(task_output, 'raw') or not isinstance(task_output.raw, str):
        return False, "Guardrail input (task_output.raw) must be a string and present."
    output_str = task_output.raw.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", output_str, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(1)
    else:
        first_brace = output_str.find('{')
        last_brace = output_str.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = output_str[first_brace:last_brace+1]
        else:
            json_str = output_str
    try:
        logging.info(f"Guardrail (hardcoded): Attempting to parse as JSON: '{json_str}'")
        data = json.loads(json_str)
        if not isinstance(data, dict):
            logging.warning(f"Parsed data is not a dictionary. Raw (cleaned) string was: {json_str}")
            return False, "Output must be a JSON dictionary."
        required_keys = ["project_name", "refined_brief", "is_new_project", "recommended_next_stage", "project_scope"]
        for key in required_keys:
            if key not in data:
                logging.warning(f"Missing key '{key}' in parsed JSON. Raw (cleaned) string was: {json_str}")
                return False, f"Missing key in output: {key}"
        if not isinstance(data["project_name"], str) or not data["project_name"].strip(): return False, "project_name must be a non-empty string."
        if not isinstance(data["refined_brief"], str) or not data["refined_brief"].strip(): return False, "refined_brief must be a non-empty string."
        if not isinstance(data["is_new_project"], bool): return False, "is_new_project must be a boolean."
        if not isinstance(data["recommended_next_stage"], str) or not data["recommended_next_stage"].strip(): return False, "recommended_next_stage must be a non-empty string."
        if not isinstance(data["project_scope"], str) or not data["project_scope"].strip(): return False, "project_scope must be a non-empty string."
        known_scopes = ["web-only", "mobile-only", "backend-only", "full-stack", "documentation-only", "unknown"]
        if data["project_scope"] not in known_scopes:
            print(f"Warning: Taskmaster output 'project_scope' ('{data['project_scope']}') is not in known scopes: {known_scopes}. Proceeding.")
        return True, data
    except json.JSONDecodeError as e:
        logging.error(f"Guardrail (hardcoded): Failed to decode JSON. Error: {e}. Raw string was: '{json_str}'. Original: '{output_str}'")
        return False, "Output must be valid JSON."
    except Exception as e:
        logging.error(f"Validation error (hardcoded): {str(e)}. Raw string was: '{json_str}'. Original: '{output_str}'", exc_info=True)
        return False, f"Validation error: {str(e)}"

# New guardrail function for Taskmaster output from tasks.yaml
def validate_taskmaster_yaml_output(task_output: TaskOutput) -> tuple[bool, Any]:
    if not hasattr(task_output, 'raw') or not isinstance(task_output.raw, str):
        return False, "Guardrail input (task_output.raw) must be a string and present."
    output_str = task_output.raw.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", output_str, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(1)
    else:
        first_brace = output_str.find('{')
        last_brace = output_str.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = output_str[first_brace:last_brace+1]
        else:
            json_str = output_str # Attempt to parse the whole string if no clear JSON found
    try:
        logging.info(f"Guardrail (YAML): Attempting to parse as JSON: '{json_str}'")
        data = json.loads(json_str)
        if not isinstance(data, dict):
            logging.warning(f"Parsed data is not a dictionary. Raw (cleaned) string was: {json_str}")
            return False, "Output must be a JSON dictionary."

        required_keys = ["project_name", "refined_brief"] # Keys from tasks.yaml's first task
        for key in required_keys:
            if key not in data:
                logging.warning(f"Missing key '{key}' in parsed JSON from YAML task. Raw (cleaned) string was: {json_str}")
                return False, f"Missing key in output: {key}"
        if not isinstance(data["project_name"], str) or not data["project_name"].strip():
            logging.warning(f"Validation failed for 'project_name' (YAML task). Raw (cleaned) string was: {json_str}")
            return False, "project_name must be a non-empty string."
        if not isinstance(data["refined_brief"], str) or not data["refined_brief"].strip():
            logging.warning(f"Validation failed for 'refined_brief' (YAML task). Raw (cleaned) string was: {json_str}")
            return False, "refined_brief must be a non-empty string."

        # DO NOT ADD DEFAULT VALUES FOR is_new_project, recommended_next_stage, project_scope HERE.
        # The orchestrator will handle determining these.
        return True, data
    except json.JSONDecodeError as e:
        logging.error(f"Guardrail (YAML): Failed to decode JSON. Error: {e}. Raw string was: '{json_str}'. Original: '{output_str}'")
        return False, "Output must be valid JSON."
    except Exception as e:
        logging.error(f"Validation error (YAML): {str(e)}. Raw string was: '{json_str}'. Original: '{output_str}'", exc_info=True)
        return False, f"Validation error: {str(e)}"

class WorkflowOrchestrator:
    ALL_PIPELINE_STAGES = [
        "taskmaster",
        "tech_vetting",
        "architecture",
        "crew_assignment",
        "subagent_execution",
        "final_assembly",
        "persist_generated_code", # New stage
        "project_finalization" # Ensure this is marked by ProjectStateManager
    ]

    def __init__(self, project_name: str = None):
        self.initial_project_name_hint = project_name
        if project_name:
            self.state = ProjectStateManager(project_name)
        else:
            self.state = None # Will be initialized after taskmaster runs

        # Import moved here to attempt to resolve circular dependency
        from .idea_to_architecture_flow import run_idea_to_architecture_flow

        # The workflow functions themselves are expected to handle their inputs
        # and interact with ProjectStateManager if they need to load/save intermediate artifacts
        # specific to their internal steps, or check if they can be skipped.
        self.workflows = {
            "taskmaster": self.run_taskmaster_workflow,
            "tech_vetting": run_tech_vetting_workflow, # Added tech_vetting
            "architecture": run_idea_to_architecture_flow,
            "crew_assignment": run_crew_lead_workflow,
            "subagent_execution": run_subagent_execution_workflow,
            "final_assembly": run_final_assembly_workflow,
            "persist_generated_code": self.run_persist_code_files_workflow # Added new workflow
        }

    def run_persist_code_files_workflow(self, inputs: dict):
        print(f"DEBUG: Entering run_persist_code_files_workflow for project '{self.state.project_info.get('name', 'N/A')}'")
        if not self.state or not self.state.project_info:
            error_msg = "Error: Project state or project_info not initialized in persist_code_files_workflow."
            print(error_msg)
            return {"status": "error", "message": error_msg, "files_written": []}

        project_path = self.state.project_info.get('path')
        if not project_path:
            error_msg = "Error: Project path not found in project_info."
            print(error_msg)
            return {"status": "error", "message": error_msg, "files_written": []}

        final_assembly_artifacts = inputs.get("final_assembly", {})
        if not isinstance(final_assembly_artifacts, dict): # Check if it's a dict
            error_msg = f"Error: final_assembly artifacts are not in the expected dictionary format. Found: {type(final_assembly_artifacts)}"
            print(error_msg)
            # Try to access .raw if it's a TaskOutput object, as a common case
            if hasattr(final_assembly_artifacts, 'raw') and isinstance(final_assembly_artifacts.raw, dict):
                print("DEBUG: Attempting to use .raw attribute from final_assembly_artifacts.")
                final_assembly_artifacts = final_assembly_artifacts.raw
            else:
                return {"status": "error", "message": error_msg, "files_written": []}


        generated_files_dict = final_assembly_artifacts.get("generated_files", {})
        if not generated_files_dict:
            print("Info: No 'generated_files' found in final_assembly_artifacts or it's empty. No files to persist.")
            return {"status": "success", "message": "No files to persist.", "files_written": [], "output_path": project_path}

        if not isinstance(generated_files_dict, dict):
            error_msg = f"Error: 'generated_files' is not a dictionary. Found: {type(generated_files_dict)}"
            print(error_msg)
            return {"status": "error", "message": error_msg, "files_written": []}

        files_written_paths = []
        errors_encountered = []

        print(f"Persisting {len(generated_files_dict)} generated file(s) to path: {project_path}")
        for file_path_in_manifest, code_content in generated_files_dict.items():
            if not isinstance(file_path_in_manifest, str) or not file_path_in_manifest.strip():
                print(f"Warning: Invalid file_path_in_manifest (empty or not a string): '{file_path_in_manifest}'. Skipping.")
                errors_encountered.append(f"Invalid file path: {file_path_in_manifest}")
                continue

            if not isinstance(code_content, str):
                if code_content is not None:
                    print(f"Warning: Code content for '{file_path_in_manifest}' is not a string (type: {type(code_content)}). Will attempt to write as str().")
                code_content = str(code_content) if code_content is not None else ""


            try:
                sanitized_relative_path = os.path.normpath(file_path_in_manifest.lstrip('/\\'))
                if ".." in sanitized_relative_path.split(os.path.sep):
                    print(f"Error: Invalid file path '{file_path_in_manifest}' contains '..'. Skipping for security.")
                    errors_encountered.append(f"Path traversal attempt: {file_path_in_manifest}")
                    continue

                target_file_path = os.path.join(project_path, sanitized_relative_path)

                os.makedirs(os.path.dirname(target_file_path), exist_ok=True)

                with open(target_file_path, "w", encoding="utf-8") as f:
                    f.write(code_content)
                files_written_paths.append(sanitized_relative_path)
                print(f"Successfully wrote: {target_file_path}")
            except Exception as e:
                error_msg = f"Error writing file '{file_path_in_manifest}' to '{target_file_path}': {e}"
                print(error_msg)
                errors_encountered.append(error_msg)

        if errors_encountered:
            return {
                "status": "partial_success",
                "message": "Completed persisting files, but some errors were encountered.",
                "files_written": files_written_paths,
                "errors": errors_encountered,
                "output_path": project_path
            }

        return {
            "status": "success",
            "message": "All generated files persisted successfully.",
            "files_written": files_written_paths,
            "output_path": project_path
        }

    # run_idea_interpretation_workflow method will be deleted by removing all its lines.
    # The diff will show this as a deletion of the block.

    def run_taskmaster_workflow(self, inputs: dict):
        logging.info("Executing Taskmaster workflow...")
        from ..taskmaster.taskmaster_agent import taskmaster_agent
        user_request = inputs.get("user_request", "")
        if not user_request:
            logging.error("No user_request provided to Taskmaster workflow.")
            return {
                "project_name": "error_no_user_request",
                "refined_brief": "Taskmaster failed: No user request was provided.",
                # Default values for fields previously expected from hardcoded task
                "is_new_project": True,
                "recommended_next_stage": "architecture",
                "project_scope": "unknown",
                "taskmaster_error": "No user_request provided"
            }

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            tasks_file_path = os.path.join(current_dir, "..", "taskmaster", "tasks.yaml")
            with open(tasks_file_path, 'r') as f:
                all_taskmaster_tasks_data = yaml.safe_load(f)

            if not all_taskmaster_tasks_data or 'tasks' not in all_taskmaster_tasks_data or not all_taskmaster_tasks_data['tasks']:
                logging.error("Failed to load tasks from taskmaster/tasks.yaml or no tasks found.")
                return {
                    "project_name": "error_task_def_load_failed",
                    "refined_brief": "Taskmaster failed: Could not load task definitions.",
                    "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                    "taskmaster_error": "Failed to load task definitions from YAML."
                }

            task_data = all_taskmaster_tasks_data['tasks'][0] # Use the first task

            # Prepare context for formatting, ensuring all potential keys are present
            formatting_context = {
                "user_request": user_request,
                "project_goal_statement": inputs.get("project_goal_statement", ""), # Default if not provided
                "priority_level": inputs.get("priority_level", "Normal") # Default if not provided
                # Add other placeholders from the YAML task description here if any
            }
            try:
                task_description = task_data['description'].format(**formatting_context)
            except KeyError as ke:
                logging.error(f"Missing key '{ke}' in formatting_context for Taskmaster task description. Provided: {formatting_context.keys()}")
                return {
                    "project_name": "error_task_desc_format_failed",
                    "refined_brief": f"Taskmaster failed: Missing data for task description placeholder '{ke}'.",
                    "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                    "taskmaster_error": f"Task description formatting error: missing '{ke}'."
                }

            task_expected_output = task_data['expected_output']

        except FileNotFoundError:
            logging.error(f"Taskmaster tasks.yaml not found at expected path: {tasks_file_path}")
            return {
                "project_name": "error_task_def_not_found",
                "refined_brief": "Taskmaster failed: Task definition file not found.",
                "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                "taskmaster_error": "Task definition file (tasks.yaml) not found."
            }
        except Exception as e:
            logging.error(f"Error loading or processing Taskmaster tasks.yaml: {e}", exc_info=True)
            return {
                "project_name": "error_task_def_processing_failed",
                "refined_brief": f"Taskmaster failed: Error processing task definitions - {e}.",
                "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                "taskmaster_error": f"Error loading or processing tasks.yaml: {e}"
            }

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            tasks_file_path = os.path.join(current_dir, "..", "taskmaster", "tasks.yaml")
            with open(tasks_file_path, 'r') as f:
                all_taskmaster_tasks_data = yaml.safe_load(f)

            if not all_taskmaster_tasks_data or 'tasks' not in all_taskmaster_tasks_data or not all_taskmaster_tasks_data['tasks']:
                logging.error("Failed to load tasks from taskmaster/tasks.yaml or no tasks found.")
                return {
                    "project_name": "error_task_def_load_failed",
                    "refined_brief": "Taskmaster failed: Could not load task definitions.",
                    "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                    "taskmaster_error": "Failed to load task definitions from YAML."
                }

            task_data = all_taskmaster_tasks_data['tasks'][0] # Use the first task

            # Prepare context for formatting, ensuring all potential keys are present
            formatting_context = {
                "user_request": user_request,
                "project_goal_statement": inputs.get("project_goal_statement", ""), # Default if not provided
                "priority_level": inputs.get("priority_level", "Normal") # Default if not provided
                # Add other placeholders from the YAML task description here if any
            }
            try:
                task_description = task_data['description'].format(**formatting_context)
            except KeyError as ke:
                logging.error(f"Missing key '{ke}' in formatting_context for Taskmaster task description. Provided: {formatting_context.keys()}")
                return {
                    "project_name": "error_task_desc_format_failed",
                    "refined_brief": f"Taskmaster failed: Missing data for task description placeholder '{ke}'.",
                    "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                    "taskmaster_error": f"Task description formatting error: missing '{ke}'."
                }

            task_expected_output = task_data['expected_output']

        except FileNotFoundError:
            logging.error(f"Taskmaster tasks.yaml not found at expected path: {tasks_file_path}")
            return {
                "project_name": "error_task_def_not_found",
                "refined_brief": "Taskmaster failed: Task definition file not found.",
                "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                "taskmaster_error": "Task definition file (tasks.yaml) not found."
            }
        except Exception as e:
            logging.error(f"Error loading or processing Taskmaster tasks.yaml: {e}", exc_info=True)
            return {
                "project_name": "error_task_def_processing_failed",
                "refined_brief": f"Taskmaster failed: Error processing task definitions - {e}.",
                "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                "taskmaster_error": f"Error loading or processing tasks.yaml: {e}"
            }

        taskmaster_task = Task(
            description=task_description,
            agent=taskmaster_agent,
            expected_output=task_expected_output, # Expected output from YAML
            guardrail=validate_taskmaster_yaml_output, # Use the new guardrail
            max_retries=1
        )

        task_crew = Crew(
            agents=[taskmaster_agent],
            tasks=[taskmaster_task],
            verbose=True
        )
        logging.info(f"Kicking off Taskmaster crew with YAML-defined task for request: '{user_request[:100]}...'")
        try:
            crew_kickoff_result = task_crew.kickoff()
        except Exception as e:
            logging.error(f"Taskmaster crew kickoff failed: {e}", exc_info=True)
            return {
                "project_name": "error_taskmaster_kickoff_exception",
                "refined_brief": f"Taskmaster crew kickoff failed with exception: {e}",
                "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                "taskmaster_error": f"Kickoff exception: {e}"
            }

        if not (hasattr(taskmaster_task, 'output') and taskmaster_task.output is not None):
            logging.error("Taskmaster task completed kickoff but task.output is missing or None.")
            return {
                "project_name": "error_task_no_output_attr",
                "refined_brief": "Taskmaster task completed kickoff but its .output attribute was not set.",
                "is_new_project": True, "recommended_next_stage": "architecture", "project_scope": "unknown",
                "taskmaster_error": "Task .output attribute missing after kickoff"
            }

        # After crew.kickoff(), taskmaster_task.output is a TaskOutput object.
        # The guardrail (validate_taskmaster_yaml_output) was called by CrewAI during execution.
        # If the guardrail did not raise an exception or cause CrewAI to halt (e.g. by returning False),
        # we assume the content in taskmaster_task.output.raw is what the guardrail validated.
        # We then re-apply the JSON extraction from the raw output.
        if taskmaster_task.output and hasattr(taskmaster_task.output, 'raw') and isinstance(taskmaster_task.output.raw, str):
            output_str = taskmaster_task.output.raw.strip()
            # Apply the same JSON extraction logic used inside the guardrail
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", output_str, re.DOTALL | re.IGNORECASE)
            json_str_to_parse = ""
            if match:
                json_str_to_parse = match.group(1)
            else:
                first_brace = output_str.find('{')
                last_brace = output_str.rfind('}')
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    json_str_to_parse = output_str[first_brace:last_brace+1]
                else:
                    json_str_to_parse = output_str # Fallback, try to parse the whole raw string

            try:
                data = json.loads(json_str_to_parse)
                # We still need to validate the structure here, as the guardrail's return
                # of (True, data) doesn't automatically make 'data' the task.output.
                # The guardrail primarily acts as a validation step that CrewAI uses.
                if isinstance(data, dict) and \
                   "project_name" in data and isinstance(data["project_name"], str) and data["project_name"].strip() and \
                   "refined_brief" in data and isinstance(data["refined_brief"], str) and data["refined_brief"].strip():
                    logging.info(f"Taskmaster workflow successful. Parsed from raw output after guardrail validation: {data}")
                    return data # This dict only has project_name and refined_brief
                else:
                    logging.error(f"Taskmaster output parsed from raw, but not a valid dict or missing/invalid keys. Data: {data}. Original raw: '{taskmaster_task.output.raw}'")
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON from task.output.raw: '{json_str_to_parse}'. Error: {e}. Original raw: '{taskmaster_task.output.raw}'")

        # If we reach here, something went wrong with output processing or the output object itself
        error_message = "Taskmaster: Failed to obtain and parse valid dictionary output from raw response after guardrail."
        raw_output_detail = taskmaster_task.output.raw if (taskmaster_task.output and hasattr(taskmaster_task.output, 'raw')) else "No raw output"
        logging.error(f"{error_message} Raw output: '{raw_output_detail}'")
        return {
            "project_name": "error_taskmaster_raw_parse_failed", # More specific error key
            "refined_brief": error_message,
            "taskmaster_error": error_message
        }

    def execute_pipeline(self, initial_inputs: dict, mock_taskmaster_output: Optional[dict] = None):
        current_artifacts = {}
        # Ensure logging is configured
        # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


        defined_pipeline_stages = [
            "taskmaster",
            "tech_vetting",
            "architecture",
            "crew_assignment",
            "subagent_execution",
            "final_assembly",
            "persist_generated_code"
        ]

        stages_to_run = []
        next_stage_index = 0

        if mock_taskmaster_output and self.state is None:
            logging.debug("Using MOCKED Taskmaster output.")
            taskmaster_output_from_mock = mock_taskmaster_output

            actual_project_name = taskmaster_output_from_mock.get("project_name")
            if not actual_project_name:
                logging.error("Mocked Taskmaster output missing 'project_name'. Cannot proceed.")
                return {"error": "Mocked Taskmaster output missing project_name"}

            is_truly_new_project_mock = taskmaster_output_from_mock.get("is_new_project", True)
            recommended_next_stage_mock = taskmaster_output_from_mock.get("recommended_next_stage", "architecture")
            project_scope_mock = taskmaster_output_from_mock.get("project_scope", "unknown")

            self.state = ProjectStateManager(actual_project_name)
            self.state.set_project_info("refined_brief", taskmaster_output_from_mock.get("refined_brief"))
            self.state.set_project_info("is_new_project", is_truly_new_project_mock)
            self.state.set_project_info("recommended_next_stage", recommended_next_stage_mock)
            self.state.set_project_info("project_scope", project_scope_mock)

            current_artifacts["taskmaster"] = {
                "project_name": actual_project_name,
                "refined_brief": taskmaster_output_from_mock.get("refined_brief"),
                "is_new_project": is_truly_new_project_mock,
                "recommended_next_stage": recommended_next_stage_mock,
                "project_scope": project_scope_mock
            }
            self.state.start_stage("taskmaster")
            self.state.complete_stage("taskmaster", artifacts=current_artifacts["taskmaster"])
            initial_inputs["project_name"] = actual_project_name

            stages_to_run.append("taskmaster")
            if recommended_next_stage_mock == "tech_vetting":
              stages_to_run.extend(["tech_vetting", "architecture", "crew_assignment", "subagent_execution", "final_assembly", "persist_generated_code"])
            elif recommended_next_stage_mock == "architecture":
              stages_to_run.extend(["architecture", "crew_assignment", "subagent_execution", "final_assembly", "persist_generated_code"])
            else:
              logging.warning(f"Unknown recommended_next_stage '{recommended_next_stage_mock}' in mock. Defaulting to architecture flow.")
              stages_to_run.extend(["architecture", "crew_assignment", "subagent_execution", "final_assembly", "persist_generated_code"])
            next_stage_index = 0

        elif self.state is None: # New project flow
            logging.info("Orchestrator: New project flow. Running Taskmaster workflow...")
            taskmaster_output_raw = self.run_taskmaster_workflow(initial_inputs) # This now returns dict with project_name, refined_brief

            if "taskmaster_error" in taskmaster_output_raw or not taskmaster_output_raw.get("project_name"):
                logging.error(f"Taskmaster failed. Output: {taskmaster_output_raw}")
                error_project_name = taskmaster_output_raw.get("project_name", "taskmaster_failed_project")
                if "error_" in error_project_name or not error_project_name.replace("_", "").isalnum():
                     error_project_name = "taskmaster_failed_unnamed"

                self.state = ProjectStateManager(error_project_name)
                self.state.fail_stage("taskmaster", taskmaster_output_raw.get("refined_brief", "Taskmaster critical failure"))
                stages_to_run = [] # Stop pipeline
            else:
                actual_project_name = taskmaster_output_raw.get("project_name")
                logging.info(f"Taskmaster returned project name: {actual_project_name}")

                temp_checker_psm = ProjectStateManager(project_name=actual_project_name, load_existing=True)
                is_truly_new_project = not temp_checker_psm.project_exists()
                del temp_checker_psm

                self.state = ProjectStateManager(actual_project_name)

                self.state.set_project_info("refined_brief", taskmaster_output_raw.get("refined_brief"))
                self.state.set_project_info("is_new_project", is_truly_new_project)

                recommended_next_stage = "architecture"
                project_scope = "unknown"

                self.state.set_project_info("recommended_next_stage", recommended_next_stage)
                self.state.set_project_info("project_scope", project_scope)

                logging.info(f"Project '{actual_project_name}' is_new_project: {is_truly_new_project}. Defaulted next_stage: '{recommended_next_stage}', scope: '{project_scope}'.")

                current_artifacts["taskmaster"] = {
                    "project_name": actual_project_name,
                    "refined_brief": taskmaster_output_raw.get("refined_brief"),
                    "is_new_project": is_truly_new_project,
                    "recommended_next_stage": recommended_next_stage,
                    "project_scope": project_scope
                }
                self.state.start_stage("taskmaster")
                self.state.complete_stage("taskmaster", artifacts=current_artifacts["taskmaster"])
                initial_inputs["project_name"] = actual_project_name

                stages_to_run.append("taskmaster")
                if recommended_next_stage == "tech_vetting":
                    stages_to_run.extend(["tech_vetting", "architecture", "crew_assignment", "subagent_execution", "final_assembly", "persist_generated_code"])
                elif recommended_next_stage == "architecture":
                    stages_to_run.extend(["architecture", "crew_assignment", "subagent_execution", "final_assembly", "persist_generated_code"])
                else:
                    logging.warning(f"Unknown recommended_next_stage '{recommended_next_stage}'. Defaulting to architecture flow.")
                    stages_to_run.extend(["architecture", "crew_assignment", "subagent_execution", "final_assembly", "persist_generated_code"])
                next_stage_index = 0

        else: # Resuming an existing project
            if "project_name" not in initial_inputs and hasattr(self.state, 'project_info'):
                 initial_inputs["project_name"] = self.state.project_info.get("name", self.initial_project_name_hint)
            print(f"Resuming existing project: {initial_inputs.get('project_name', 'Unknown')}")
            current_artifacts = self.state.get_artifacts() # Load all existing artifacts

            resume_point = self.state.resume_point()
            if resume_point is None and self.state.state.get("status") == "completed":
                print("Project already completed.")
                # Report will be generated at the end.
                stages_to_run = [] # Skip loop
            elif resume_point is None and self.state.state.get("status") != "failed":
                 if self.state.state.get("status") != "completed": # Should have been caught by finalize_project
                    print("All stages completed. Finalizing project...")
                    self.state.finalize_project()
                 stages_to_run = [] # Skip loop
            elif resume_point:
                print(f"Resuming at stage: {resume_point}")
                # Determine the sequence of stages from the resume point.
                # This needs to consider the original recommended path if stored, or assume full path.
                # For simplicity now, assume the defined_pipeline_stages is the path.
                try:
                    resume_idx = defined_pipeline_stages.index(resume_point)
                    stages_to_run = defined_pipeline_stages # Run all stages from the full list
                    next_stage_index = resume_idx # Start loop from this index
                except ValueError:
                    print(f"Error: Resume point '{resume_point}' not found in defined stages. Cannot resume.")
                    self.state.fail_stage("orchestrator_resume", f"Invalid resume point: {resume_point}")
                    stages_to_run = [] # Skip loop
            else: # No resume point, project not completed or failed (e.g. just initialized but no stages run)
                # This case might indicate needing to run taskmaster again or re-evaluate.
                # For now, assume it means start from the beginning of a standard flow.
                # This path needs careful consideration if Taskmaster's recommendation isn't persisted.
                # Let's assume if we are here, it's like a new project that somehow has state.
                # Fallback: attempt to run a default sequence.
                # However, if taskmaster output is in artifacts, we can use its recommendation.
                taskmaster_output = current_artifacts.get("taskmaster", {})
                recommended_next = taskmaster_output.get("recommended_next_stage", "architecture")
                print(f"No clear resume point, using Taskmaster recommendation ('{recommended_next}') or default flow.")
                if recommended_next == "tech_vetting" and not self.state.is_completed("tech_vetting"):
                    stages_to_run = defined_pipeline_stages
                elif recommended_next == "architecture" and not self.state.is_completed("architecture"):
                     stages_to_run = [s for s in defined_pipeline_stages if s != "tech_vetting"]
                else: # Default or if recommended stage is already done, try full sequence
                    stages_to_run = defined_pipeline_stages
                next_stage_index = 0


        # Main execution loop
        for i in range(next_stage_index, len(stages_to_run)):
            stage = stages_to_run[i]

            if self.state.is_completed(stage):
                print(f"Stage '{stage}' already completed. Skipping.")
                if stage not in current_artifacts and self.state.get_artifacts(stage): # Ensure artifacts are loaded
                    current_artifacts[stage] = self.state.get_artifacts(stage)
                continue

            if stage not in self.workflows:
                print(f"Warning: Stage '{stage}' is defined in the run sequence but no corresponding workflow method exists. Skipping.")
                self.state.fail_stage(stage, f"Workflow for stage '{stage}' not found.") # Log as failure for this stage
                break # Stop pipeline execution if a stage is missing its method

            self.state.start_stage(stage)

            try:
                inputs_for_stage = {**initial_inputs, **current_artifacts}

                # Ensure project_name is in inputs_for_stage from self.state if available
                if "project_name" not in inputs_for_stage and self.state.project_info:
                    inputs_for_stage["project_name"] = self.state.project_info.get("name")


                print(f"\nStarting {stage} stage for project '{inputs_for_stage.get('project_name', 'N/A')}'...")
                result = self.workflows[stage](inputs_for_stage)

                self.state.complete_stage(stage, artifacts=result)
                if result:
                    current_artifacts[stage] = result
                print(f"Completed {stage} stage successfully.")

            except Exception as e:
                error_msg = f"Stage {stage} failed: {str(e)}"
                self.state.fail_stage(stage, error_msg)
                print(error_msg)
                import traceback
                traceback.print_exc()
                break

        # Finalize project if all prerequisite stages completed successfully
        if self.state.state["status"] != "failed":
            # Define prerequisite stages as all stages in ALL_PIPELINE_STAGES except "project_finalization"
            prerequisite_stages_for_finalization = [s for s in self.ALL_PIPELINE_STAGES if s != "project_finalization"]

            all_prerequisites_done = all(self.state.is_completed(s) for s in prerequisite_stages_for_finalization)

            if all_prerequisites_done:
                # If project status is already 'completed', it implies finalize_project was likely called before
                # (e.g. in a resumed run that found all prerequisites done).
                if self.state.state.get("status") != "completed":
                    print("All prerequisite stages are complete. Finalizing project...")
                    self.state.finalize_project() # This will internally mark 'project_finalization' as complete
                else:
                    # This case implies all prerequisites are done AND project status is 'completed'.
                    # This means 'project_finalization' stage should also be complete.
                    if not self.state.is_completed("project_finalization"):
                        # This would be an inconsistent state: project is "completed" but "project_finalization" stage isn't.
                        # Call finalize_project() again to ensure the stage is marked.
                        print("Project status is 'completed' but 'project_finalization' stage was not marked. Re-finalizing...")
                        self.state.finalize_project()
                    else:
                        print("Project already marked as completed and all prerequisite stages (including finalization) are done.")
            else:
                print("Workflow execution finished, but not all prerequisite stages were completed. Project not finalized by orchestrator.")

        if self.state: # Ensure state is initialized before printing summary
            # self.state.get_summary().print() # Replaced by RichProjectReporter
            reporter = RichProjectReporter(self.state.state) # Pass the state dictionary
            reporter.print_report()
            return self.state.get_artifacts() # Still return artifacts
        else: # Should not happen if taskmaster ran correctly
            print("Error: Orchestrator state was not initialized.")
            return {"error": "Orchestrator state not initialized."}
