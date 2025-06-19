import os
import traceback
import sys
from typing import Optional, Dict, Any
import numpy as np
from .tools.knowledge_base_tool import KnowledgeBaseTool # Changed import
from .tools.chroma_logger import ChromaLogger # Added import
import json
import hashlib
from pathlib import Path
from datetime import datetime
from .utils import ErrorSummary

PROJECTS_INDEX = Path(__file__).parent / "projects_index.json"
PROJECTS_ROOT = Path(__file__).parent / "projects/"

class ProjectStateManager:
    def __init__(self, project_name, config: Optional[Dict[str, bool]] = None):
        PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
        self.project_info = self._get_or_create_project(project_name)

        default_config = {
            "enable_kb_logging": os.getenv("ENABLE_KB_LOGGING", "true").lower() == "true",
            "enable_db_logging": os.getenv("ENABLE_DB_LOGGING", "true").lower() == "true",
            "enable_auto_resume": os.getenv("ENABLE_AUTO_RESUME", "true").lower() == "true"
        }
        self.config = default_config
        if config: # Apply user-provided config over defaults and env vars
            self.config.update(config)

        self.kb_tool = KnowledgeBaseTool() if self.config.get("enable_kb_logging") else None # Changed instantiation
        self.chroma_logger = ChromaLogger() if self.config.get("enable_db_logging") else None # Changed to ChromaLogger
        self.resume_attempts = {}

        self.state_file = Path(self.project_info['path']) / "state.json"
        self.error_summary = ErrorSummary()
        self.load_state()

    def update_config(self, new_config: Dict[str, bool]):
        """Updates the project's configuration and re-initializes related components."""
        self.config.update(new_config)

        # Re-initialize components based on the new config
        if "enable_kb_logging" in new_config:
            self.kb_tool = KnowledgeBaseTool() if self.config.get("enable_kb_logging") else None # Changed instantiation
        if "enable_db_logging" in new_config:
            self.chroma_logger = ChromaLogger() if self.config.get("enable_db_logging") else None # Changed to ChromaLogger

        # Note: enable_auto_resume is used directly, so no specific re-initialization needed here
        # for self.resume_attempts, it's managed per stage.
        print(f"Project config updated: {self.config}")

    def _log_to_knowledge_base(self, error_details: Dict[str, Any]):
        """Logs error details to the knowledge base if enabled."""
        # if self.kb_tool and hasattr(self.kb_tool, 'memory_instance') and hasattr(self.kb_tool, '_embed_text'):
        #     try:
        #         # Construct a meaningful single text entry for the KB
        #         full_entry_text = f"Project: {error_details.get('project', 'N/A')}, Stage: {error_details.get('stage', 'Unknown')}, Error: {error_details.get('error_message', 'N/A')}. Details: {json.dumps(error_details)}"

        #         # Generate embedding using the kb_tool's own embedder
        #         embedding_vector = self.kb_tool._embed_text(full_entry_text) # This should return np.ndarray

        #         if embedding_vector is not None and embedding_vector.size > 0 : # Check if embedding is valid
        #             # Add to knowledge base via its memory_instance
        #             # ONNXObjectBoxMemory.add_knowledge expects text and vector.
        #             # The full_entry_text already contains the JSON dump of error_details.
        #             self.kb_tool.memory_instance.add_knowledge(text=full_entry_text, vector=embedding_vector)
        #             print(f"Logged error to knowledge base via memory_instance. Project: {error_details.get('project', 'N/A')}, Stage: {error_details.get('stage', 'Unknown')}")
        #         else:
        #             print(f"Warning: Failed to generate embedding for KB logging. Error for project {error_details.get('project', 'N/A')}, Stage: {error_details.get('stage', 'Unknown')} not logged to KB.")

        #     except Exception as e:
        #         print(f"Failed to log error to knowledge base: {e}")
        #         self.error_summary.add("knowledge_base_logging", False, f"KB Logging Failed: {e}")
        # elif self.kb_tool:
        #     # This condition means kb_tool exists but doesn't have the expected structure.
        #     print(f"Warning: kb_tool (type: {type(self.kb_tool)}) is missing 'memory_instance' or '_embed_text' method. Cannot log to KB for project {error_details.get('project', 'N/A')}.")
        print(f"Warning: _log_to_knowledge_base is currently disabled pending review. Project: {error_details.get('project', 'N/A')}, Stage: {error_details.get('stage', 'Unknown')}")
        pass # Signifies that this functionality is intentionally bypassed for now


    def _log_to_chroma(self, error_details: Dict[str, Any]): # Renamed method
        """Logs error details to ChromaDB if enabled."""
        if self.chroma_logger:
            try:
                log_content = f"Error in stage {error_details.get('stage', 'Unknown')}: {error_details.get('error', 'No error message')}"
                # Metadata is the error_details dictionary itself
                # log_type is "error"
                self.chroma_logger.log(
                    content=log_content,
                    stage=error_details.get('stage', 'Unknown'), # Pass stage separately
                    log_type="error",
                    metadata=error_details
                )
                print(f"Logged error to ChromaDB for project {self.project_info.get('name')}, stage {error_details.get('stage', 'Unknown')}")
            except Exception as e:
                print(f"Failed to log error to ChromaDB: {e}")
                # Optionally, add to error_summary or handle as per project's error handling strategy
                self.error_summary.add("chroma_logging", False, f"ChromaDB Logging Failed: {e}")

    def _prepare_auto_resume(self, stage_name: str, error_details: Dict[str, Any]):
        """Prepares context for auto-resume if enabled."""
        if self.config.get("enable_auto_resume"):
            timestamp = datetime.utcnow().isoformat()
            self.resume_attempts.setdefault(stage_name, []).append({
                "timestamp": timestamp,
                "error": str(error_details.get("error", "Unknown error")),
                "traceback": error_details.get("traceback", "No traceback"),
                "attempt_count": len(self.resume_attempts[stage_name]) + 1
            })
            # Persist resume_attempts to state for durability across sessions
            self.state["resume_attempts"] = self.resume_attempts
            self.save_state() # Ensure state is saved with resume attempts
            print(f"Prepared auto-resume context for stage {stage_name} (Attempt {len(self.resume_attempts[stage_name])})")

    def get_resume_context(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves the latest resume context for a given stage."""
        if self.config.get("enable_auto_resume"):
            # Ensure resume_attempts is loaded from state if not already in memory
            if not self.resume_attempts and "resume_attempts" in self.state:
                self.resume_attempts = self.state["resume_attempts"]

            stage_attempts = self.resume_attempts.get(stage_name, [])
            if stage_attempts:
                return stage_attempts[-1] # Return the latest attempt's context
        return None

    def clear_resume_context(self, stage_name: str):
        """Clears resume context for a stage, typically after successful completion."""
        if stage_name in self.resume_attempts:
            del self.resume_attempts[stage_name]
            # Update state
            self.state["resume_attempts"] = self.resume_attempts
            self.save_state()
            print(f"Cleared auto-resume context for stage {stage_name}")

    def auto_resume_stage(self, stage_name: str, executor: callable):
        """
        Attempts to automatically resume a failed stage using the provided executor.
        The executor function is expected to take `resume_context` as a keyword argument.
        """
        if not self.config.get("enable_auto_resume"):
            print(f"Auto-resume disabled. Skipping resume attempt for stage {stage_name}.")
            return False # Auto-resume not enabled

        resume_context = self.get_resume_context(stage_name)
        if not resume_context:
            print(f"No resume context found for stage {stage_name}. Cannot auto-resume.")
            return False # No context to resume from

        # Limit resume attempts (e.g., max 3 attempts)
        MAX_RESUME_ATTEMPTS = self.config.get("max_resume_attempts", 3) # Default to 3 if not in config
        if resume_context.get("attempt_count", 0) >= MAX_RESUME_ATTEMPTS:
            print(f"Max resume attempts reached for stage {stage_name}. Manual intervention required.")
            self.fail_stage(stage_name, f"Auto-resume failed after {MAX_RESUME_ATTEMPTS} attempts. Last error: {resume_context.get('error')}")
            return False

        print(f"Attempting auto-resume for stage {stage_name} (Attempt {resume_context.get('attempt_count', 0) + 1})")

        try:
            # The executor is called with the resume_context.
            # It's the executor's responsibility to use this context to modify its behavior.
            # For example, retrying with different parameters, or skipping certain initial steps.
            # If the executor is a method of a class, it might need to be bound or passed with `self`.
            # This example assumes executor is a standalone function or a bound method.
            executor(resume_context=resume_context) # Pass resume_context to the executor

            print(f"Stage {stage_name} resumed successfully.")
            self.clear_resume_context(stage_name) # Clear context on success
            # Assuming the executor calls complete_stage internally or it should be called here
            return True
        except Exception as e:
            print(f"❌ Auto-resume failed: {str(e)}")
            # Will be caught by fail_stage again
            raise

    def _get_current_traceback(self):
        """Helper to get the current traceback as a string."""
        return "".join(traceback.format_stack())

    def _slugify(self, name: str) -> str:
        safe = "".join(c if c.isalnum() else "_" for c in name).lower()
        return safe[:50]

    def _load_index(self):
        if PROJECTS_INDEX.exists():
            try:
                return json.loads(PROJECTS_INDEX.read_text())
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_index(self, index):
        PROJECTS_INDEX.write_text(json.dumps(index, indent=2))

    def _get_or_create_project(self, name: str) -> dict:
        index = self._load_index()
        name_hash = hashlib.sha1(name.encode()).hexdigest()[:8]
        key = f"{self._slugify(name)}_{name_hash}"

        if key in index:
            proj_details = index[key]
            # Assumes path stored is absolute or correctly resolvable
            proj_path = Path(proj_details["path"])
            status = "continuing"
        else:
            proj_path = PROJECTS_ROOT / key
            proj_path.mkdir(parents=True, exist_ok=True)
            proj_details = {"name": name, "id": key, "path": str(proj_path.resolve())}
            index[key] = proj_details
            self._save_index(index)
            status = "new"
        return {"status": status, **proj_details}

    def load_state(self):
        state_loaded_from_json = False
        if self.state_file.exists():
            try:
                loaded_state = json.loads(self.state_file.read_text())
                self.state = loaded_state
                # When loading state, rehydrate ErrorSummary from the loaded records
                self.error_summary.records = [] # Clear existing records before loading
                for record in self.state.get("error_summary", []):
                    # Ensure all components of the record are passed to add
                    self.error_summary.add(record["stage"], record["success"], record["message"])
                state_loaded_from_json = True
            except json.JSONDecodeError:
                print(f"Warning: state.json for project {self.project_info['name']} is corrupted.")
                self.state = None # Mark state as None to trigger Chroma load or initial state
        else:
            self.state = None # Mark state as None to trigger Chroma load or initial state

        # If state couldn't be loaded from JSON (file not found or corrupted)
        if not state_loaded_from_json:
            if self.chroma_logger and self.config.get("enable_db_logging"):
                print(f"Attempting to load state from ChromaDB for project {self.project_info['name']}...")
                try:
                    chroma_state = self.chroma_logger.get_project_state(self.project_info["name"])
                    if chroma_state:
                        self.state = chroma_state
                        # Rehydrate ErrorSummary from the loaded state from Chroma
                        self.error_summary.records = [] # Clear existing records
                        for record in self.state.get("error_summary", []):
                             self.error_summary.add(record["stage"], record["success"], record["message"])
                        print(f"Successfully loaded state from ChromaDB for project {self.project_info['name']}.")
                    else:
                        print(f"No state found in ChromaDB for project {self.project_info['name']}. Initializing new state.")
                        self.state = self._initial_state() # This will also re-init error_summary
                except Exception as e:
                    print(f"Error loading state from ChromaDB: {e}. Initializing new state.")
                    self.state = self._initial_state() # This will also re-init error_summary
            else:
                # If JSON load failed and Chroma is not available/enabled, then initialize.
                print(f"ChromaDB logging disabled or logger not available. Initializing new state for project {self.project_info['name']}.")
                self.state = self._initial_state() # This will also re-init error_summary

        # Final check to ensure error_summary is an ErrorSummary instance, especially if _initial_state wasn't called.
        # This path is less likely now with _initial_state() re-initializing error_summary.
        if not isinstance(self.error_summary, ErrorSummary):
            self.error_summary = ErrorSummary()
            if self.state and "error_summary" in self.state: # If state exists and has summary
                 for record in self.state.get("error_summary", []):
                    self.error_summary.add(record["stage"], record["success"], record["message"])


    def _initial_state(self):
        self.error_summary = ErrorSummary() # Ensure a fresh ErrorSummary instance
        return {
            "project_name": self.project_info["name"],
            "created_at": datetime.utcnow().isoformat(),
            "current_stage": "initialized",
            "completed_stages": [],
            "artifacts": {},
            "error_summary": [], # Initial error summary is empty
            "status": "in_progress"
        }

    def save_state(self):
        """Save current state to file"""
        self.state["error_summary"] = self.error_summary.to_dict()
        self.state["updated_at"] = datetime.utcnow().isoformat()

        # Ensure the directory for the state file exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.state_file.write_text(json.dumps(self.state, indent=2))
        except Exception as e:
            print(f"Error saving state to state.json: {e}")
            # Optionally, log this error to error_summary or handle as critical

        # Save state to ChromaDB if enabled
        if self.chroma_logger and self.config.get("enable_db_logging"):
            try:
                print(f"Saving project state to ChromaDB for project {self.project_info['name']}...")
                self.chroma_logger.save_project_state(self.project_info["name"], self.state)
                print(f"Successfully saved project state to ChromaDB for project {self.project_info['name']}.")
            except Exception as e:
                print(f"Error saving project state to ChromaDB: {e}")
                # Optionally, log this error to error_summary or a fallback mechanism
                self.error_summary.add("chroma_state_save", False, f"ChromaDB State Save Failed: {e}")


    def start_stage(self, stage_name):
        self.state["current_stage"] = stage_name
        # No direct error_summary.add here; stage start is not an event for summary
        self.save_state()

    def complete_stage(self, stage_name, artifacts=None):
        if stage_name not in self.state["completed_stages"]:
            self.state["completed_stages"].append(stage_name)

        if artifacts:
            try:
                # Attempt to serialize to ensure artifacts are storable
                json.dumps(artifacts)
                self.state["artifacts"][stage_name] = artifacts
            except TypeError as e:
                # Log non-serializable artifacts issue
                error_msg = f"Artifacts for stage {stage_name} are not JSON serializable: {e}"
                print(f"Warning: {error_msg}")
                self.state["artifacts"][stage_name] = {"error": "not_serializable", "details": str(artifacts)}
                # Optionally, log this as a non-critical error/warning in summary
                # self.error_summary.add(stage_name, True, f"Completed with non-serializable artifacts: {error_msg}")

        self.error_summary.add(stage_name, True, "Completed successfully")
        self.save_state()

    def fail_stage(self, stage_name, error_message, exception_obj=None, input_context=None):
        """Enhanced failure logging with configurable diagnostics"""
        self.state["status"] = "failed"

        # Capture detailed error info
        error_details = {
            "error_message": error_message,
            "exception_type": str(type(exception_obj).__name__) if exception_obj else "N/A",
            "stack_trace": traceback.format_exc() if exception_obj else self._get_current_traceback(),
            "input_context": input_context,
            "stage": stage_name,
            "project": self.project_info["name"],
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add to error summary
        # Ensure ErrorSummary can handle a JSON string or a more structured message.
        # The original code had self.error_summary.add(stage_name, False, error_message)
        # The new code from issue has: self.error_summary.add(stage_name, False, json.dumps(error_details, indent=2))
        # Let's use the new version.
        self.error_summary.add(stage_name, False, json.dumps(error_details, indent=2))

        # Conditional logging
        if self.config.get("enable_kb_logging"): # Use .get for safety, though defaults should exist
            self._log_to_knowledge_base(error_details)

        if self.config.get("enable_db_logging"): # Use .get for safety
            self._log_to_chroma(error_details) # Changed to _log_to_chroma

        # Auto-resume logic
        if self.config.get("enable_auto_resume"): # Use .get for safety
            self._prepare_auto_resume(stage_name, error_details)

        self.save_state()

    def get_artifacts(self, stage_name=None):
        if stage_name:
            return self.state["artifacts"].get(stage_name, {})
        return self.state["artifacts"]

    def is_completed(self, stage_name):
        return stage_name in self.state["completed_stages"]

    def resume_point(self):
        # If project is marked completed, no resume point.
        if self.state.get("status") == "completed":
            return None

        workflow_stages = [
            "taskmaster",
            "architecture",
            "crew_assignment",
            "subagent_execution",
            "final_assembly"
        ]

        for stage in workflow_stages:
            if not self.is_completed(stage):
                return stage # Return the first incomplete stage

        # If all defined workflow stages are complete, but project not finalized.
        # This could mean it's ready for finalization or an edge case.
        # For now, if all stages are done, we can consider it None (no next stage).
        # Or, it might imply a final "project_finalization" stage if it's part of the workflow.
        if all(self.is_completed(s) for s in workflow_stages):
            # If project isn't 'completed' but all stages are, it implies it's ready for finalization
            # or has finished the defined flow. Returning None is consistent.
            return None

        # Default to the first stage if no state indicates otherwise (should be handled by _initial_state)
        return workflow_stages[0]

    def finalize_project(self):
        # Mark the "project_finalization" stage as completed first
        # This ensures that is_completed("project_finalization") will be true
        # when the orchestrator checks all stages from its canonical list.
        self.complete_stage("project_finalization", artifacts={"summary": "Project finalized successfully by ProjectStateManager."})
        # Note: complete_stage already calls self.save_state() and adds to error_summary.
        # So, the explicit error_summary.add below might be redundant if complete_stage's message is sufficient.
        # However, keeping it for clarity or if a more specific message is desired from finalize_project itself.

        self.state["status"] = "completed" # Set overall project status
        self.state["completed_at"] = datetime.utcnow().isoformat()

        # This will add another entry to error_summary for "project_finalization" or update if stage already added.
        # ErrorSummary logic might need to handle duplicate stage entries if that's an issue,
        # or ensure complete_stage's message is what we want.
        # For now, let's assume ErrorSummary can handle it or it's a minor duplication.
        # To avoid exact duplicate message, let's make this one slightly different.
        self.error_summary.add("project_finalization", True, "Overall project status marked as COMPLETED.")

        self.save_state() # Ensure final status and timestamp are saved.

    def get_summary(self):
        return self.error_summary

    @staticmethod
    def list_projects():
        projects_list = []
        if not PROJECTS_ROOT.exists() or not PROJECTS_ROOT.is_dir():
            return []

        for item in PROJECTS_ROOT.iterdir():
            if item.is_dir():
                project_key = item.name # directory name is the key
                project_path = item
                state_file_path = project_path / "state.json"

                # Default values
                status = "Error - State file missing"
                # Default project name from key, can be overridden by state.json
                project_name_from_state = project_key.replace('_', ' ').title()
                last_updated = "N/A"
                error_message_str = None
                rich_name_prefix = "" # Default to no prefix

                if state_file_path.exists() and state_file_path.is_file():
                    try:
                        state_json = json.loads(state_file_path.read_text())
                        status = state_json.get("status", "Unknown")
                        project_name_from_state = state_json.get("project_name", project_name_from_state)

                        # Get last updated time, fallback to created_at
                        raw_last_updated = state_json.get("updated_at", state_json.get("created_at", "N/A"))
                        if isinstance(raw_last_updated, str) and raw_last_updated != "N/A":
                            try:
                                dt_obj = datetime.fromisoformat(raw_last_updated.replace("Z", "+00:00"))
                                last_updated = dt_obj.strftime("%Y-%m-%d %H:%M:%S %Z").strip()
                            except ValueError:
                                last_updated = raw_last_updated # Keep as is if parsing fails
                        else:
                            last_updated = "N/A"

                        if status == "failed":
                            error_summary_list = state_json.get("error_summary", [])
                            if isinstance(error_summary_list, list) and error_summary_list:
                                for record in reversed(error_summary_list): # Get the latest error
                                    if isinstance(record, dict) and not record.get("success", True):
                                        error_message_str = record.get("message", "No specific error message found.")
                                        break
                                if error_message_str is None:
                                     error_message_str = "Failed, but no specific error message recorded in summary."
                            else:
                                error_message_str = "Failed, error summary not available or empty."

                    except json.JSONDecodeError:
                        status = "Error - State file corrupted"
                        error_message_str = "State.json is corrupted."
                        last_updated = "N/A" # Reset as state is corrupt
                else: # State file does not exist
                    error_message_str = "State.json is missing for this project."


                # Set rich_name_prefix based on status
                if status == "completed":
                    rich_name_prefix = "✅ "
                elif status == "failed":
                    rich_name_prefix = "❌ "
                elif status.startswith("Error -") or status == "Unknown":
                    rich_name_prefix = "⚠️ "
                # else: in_progress or other statuses might not need a prefix or could have a different one

                projects_list.append({
                    "key": project_key,
                    "name": project_name_from_state,
                    "status": status,
                    "rich_name": f"{rich_name_prefix}{project_name_from_state}",
                    "last_updated": last_updated,
                    "path": str(project_path.resolve()),
                    "error_message": error_message_str
                })

        # Sort projects: failed first, then error statuses, then completed, then others, then by name
        def sort_key_func(p):
            status_lower = p['status'].lower()
            if 'failed' in status_lower: # Catches "failed"
                return 0
            elif status_lower.startswith('error -'): # Catches "Error - State file missing/corrupted"
                return 1
            elif 'completed' in status_lower: # Catches "completed"
                return 2
            elif 'unknown' in status_lower : # Catches "Unknown"
                return 3
            else: # For "in_progress", etc.
                return 4

        projects_list.sort(key=lambda p: (sort_key_func(p), p['name']))
        return projects_list
