import sys
import os
import json
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, InvalidResponse # Added InvalidResponse
from collections import OrderedDict # To maintain order for display after processing
# Add the project root (/app) to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')) # Corrected path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Add the project's src directory to sys.path to allow 'from crewai import ...'
project_src_path = os.path.join(project_root, "src")
if project_src_path not in sys.path:
    sys.path.insert(1, project_src_path)

# Ensure the llm_config is loaded first
# We'll import llm_initialization_statuses after modifying llm_config.py
from .llm_config import default_llm, llm_initialization_statuses # Adjusted import
from . import config as crew_config
from .tools.knowledge_base_tool import ONNX_EMBEDDING_INITIALIZATION_STATUS as onnx_embedding_status
from .tools.inbuilt_tools import configure_rag_tools # Added RAG config import
from .tools.chroma_logger import ChromaLogger
from .tools.fallback_logger import fallback_log
# os is already imported at the top of the file, so no need to add it here again.

# Initialize Rich Console
console = Console()

# TaskMasterAgent import is removed as it's handled by the orchestrator's "taskmaster" stage
# from .taskmaster import taskmaster_agent

os.environ["LITELLM_DEBUG"] = "0" # Disabled debug for cleaner output, can be "1"

from .project_manager import ProjectStateManager # Added import

def display_model_initialization_status(title: str, statuses: list[tuple[str, bool]]):
    """Displays the initialization status of unique models in a Rich Panel."""
    if not statuses:
        content = Text("No models to display status for in this category.", style="italic yellow")
    else:
        # Aggregate statuses: if a model key has at least one True, it's True.
        # Using OrderedDict to preserve the order of first appearance, then sorting for final display.
        processed_statuses = OrderedDict()
        for model_key, success_bool in statuses:
            if model_key not in processed_statuses:
                processed_statuses[model_key] = False # Default to False
            if success_bool: # If any attempt is true, mark it as true for that model key
                processed_statuses[model_key] = True

        if not processed_statuses:
             content = Text("No valid model statuses to display after processing.", style="italic yellow")
        else:
            status_texts = []
            # Sort items by model_key for consistent display order
            sorted_model_statuses = sorted(processed_statuses.items())

            for model_key, aggregated_success_bool in sorted_model_statuses:
                # Ensure model_key is a string for Text()
                model_key_str = str(model_key) if model_key is not None else "N/A"
                model_text = Text(f"{model_key_str}: ", style="default")
                if aggregated_success_bool:
                    model_text.append("✅", style="bright_green") # Changed to ✅
                else:
                    model_text.append("❌", style="bright_red")   # Use bright_red
                status_texts.append(model_text)
            content = Text("\n").join(status_texts)

    # Ensure title is Text if it's a string with markup, or already Text
    panel_title = title if isinstance(title, Text) else Text.from_markup(title)
    panel = Panel(content, title=panel_title, border_style="blue", expand=False, padding=(1, 2))
    console.print(panel)

def run_qrew():
    # --- Logger Instantiation Test ---
    print("\n--- Testing Logger Initialization ---")

    # Define test paths relative to main.py's location (mycrews/qrew/main.py)
    # main.py -> qrew -> db -> ...
    main_script_dir = os.path.dirname(os.path.abspath(__file__))
    chroma_test_db_path = os.path.join(main_script_dir, "..", "db", "chroma_logger_initial_test")
    fallback_test_log_dir_name = "fallback_logger_initial_test" # This will be created inside <project_root>/db/

    try:
        print(f"Attempting to initialize ChromaLogger at: {chroma_test_db_path}")
        chroma_logger_instance = ChromaLogger(persist_directory=chroma_test_db_path, collection_name="initial_test_logs")
        if chroma_logger_instance and chroma_logger_instance.collection:
            print("ChromaLogger initialized successfully for initial test.")
            chroma_logger_instance.log(content="ChromaLogger initial test log.", stage="main_test", log_type="debug")
            print("Test log sent to ChromaLogger.")

            # Test project state functions (optional, but good for early check)
            test_project_name = "logger_init_test_project"
            initial_state_save = chroma_logger_instance.save_project_state(test_project_name, {"status": "testing_init", "value": 123})
            if initial_state_save:
                print(f"ChromaLogger.save_project_state test successful for {test_project_name}.")
                retrieved_state = chroma_logger_instance.get_project_state(test_project_name)
                if retrieved_state and retrieved_state.get("value") == 123:
                    print(f"ChromaLogger.get_project_state test successful: {retrieved_state}")
                else:
                    print(f"ChromaLogger.get_project_state test failed or state mismatch. Retrieved: {retrieved_state}")
            else:
                print(f"ChromaLogger.save_project_state test failed for {test_project_name}.")

        else:
            print("ChromaLogger initialization failed for initial test.")
    except Exception as e_chroma_test:
        print(f"Error during ChromaLogger initial test: {e_chroma_test}")

    try:
        # Fallback logger's path is relative to where Python is run from.
        # For consistency, let's make it relative to project root/db like Chroma.
        # Project root from main.py (mycrews/qrew/main.py) is two levels up.
        project_root_dir = os.path.join(main_script_dir, "..", "..")
        fallback_base_dir = os.path.join(project_root_dir, "db") # Base for fallback logs
        actual_fallback_log_path = os.path.join(fallback_base_dir, fallback_test_log_dir_name)
        print(f"Attempting to use fallback_log. Logs will be in: {actual_fallback_log_path}")

        fallback_log(content="Fallback logger initial test log.", metadata={"stage": "main_test", "type": "debug"}, log_dir=actual_fallback_log_path)
        print("Test log sent to fallback_logger.")
    except Exception as e_fallback_test:
        print(f"Error during fallback_logger initial test: {e_fallback_test}")

    print("--- End of Logger Initialization Test ---\n")
    # --- The rest of the run_qrew() function continues below ---
    # Display LLM initialization status first using Rich
    display_model_initialization_status("[bold cyan]--- LLM Initialization ---[/bold cyan]", llm_initialization_statuses)

    # Placeholder for TFLite and other models as per requirements, also using Rich
    display_model_initialization_status("[bold cyan]--- ONNX Model Initialization ---[/bold cyan]", onnx_embedding_status)
    # Example with placeholder models:
    # display_model_initialization_status("[bold cyan]--- Other Model Initialization ---[/bold cyan]", [("Embedding Model", True), ("Another Model", False)])

    # --- Configure RAG Tools ---
    # Define knowledge base configurations
    # Paths are relative and will be resolved based on the execution context.
    knowledge_base_configs = {
        'web_components': './knowledge/web_components',
        'mobile_patterns': './knowledge/mobile_patterns',
        'api_specs': './knowledge/api_specs',
        'cloud_templates': './knowledge/cloud_templates'
    }
    try:
        print("\nConfiguring RAG tools...")
        configure_rag_tools(knowledge_base_configs)
        print("RAG tools configuration process initiated.")
    except Exception as e:
        print(f"Error during RAG tool configuration: {e}")
        # Decide if this should be a critical error or just a warning

    # Configure basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Attempt to silence LiteLLM enterprise warnings
    try:
        logging.getLogger('litellm_enterprise').setLevel(logging.WARNING)
        logging.getLogger('litellm.licensing').setLevel(logging.WARNING) # Add this for broader coverage
    except Exception as e:
        # Log this attempt, but don't let it crash the app
        logging.warning(f"Attempt to set LiteLLM log levels failed: {e}")

    # The old "Initializing Qrew System..." print might be redundant or can be styled too.
    # For now, let's keep it or use console.print for consistency if desired.
    # console.print("\n[bold]Initializing Qrew System...[/bold]")
    # Keeping the original print for now, as the focus is on the status boxes.
    print("\nInitializing Qrew System...")

    project_name_for_orchestrator = None
    pipeline_inputs = {}

    listed_projects = ProjectStateManager.list_projects()

    if listed_projects:
        project_display_lines = []
        intro_text = Text("Select a project to resume or start a new one:\n", style="bold green")
        # project_display_lines.append(intro_text) # Will be assembled later

        for i, proj in enumerate(listed_projects):
            display_text = Text(f"{i+1}. ")

            raw_rich_name = proj.get('rich_name', '') # Use .get for safety
            if not isinstance(raw_rich_name, str): # Ensure it's a string
                raw_rich_name = str(raw_rich_name)

            prefix = ""
            name_part = raw_rich_name
            known_prefixes = ["✅ ", "❌ ", "⚠️ "] # Prefixes include a space

            for p_prefix in known_prefixes: # Renamed p to p_prefix to avoid conflict with Panel
                if raw_rich_name.startswith(p_prefix):
                    prefix = p_prefix
                    name_part = raw_rich_name[len(p_prefix):]
                    break

            if prefix:
                # Append prefix (which is safe for Text.from_markup as it's just an emoji and space)
                display_text.append(Text.from_markup(prefix))
                # Append the rest of the name as plain text to avoid markup issues
                display_text.append(Text(name_part))
            else:
                # If no known prefix, treat the whole rich_name as plain text
                display_text.append(Text(name_part))

            display_text.append(Text(f" - Last updated: {proj['last_updated']}", style="dim"))

            if proj['status'] == 'failed' and proj.get('error_message'):
                error_text = Text(f"   Error: {proj['error_message']}", style="italic red")
                display_text.append("\n") # Add a newline before the error
                display_text.append(error_text)
            project_display_lines.append(display_text)

        new_project_option_num = len(listed_projects) + 1
        new_project_text = Text(f"{new_project_option_num}. Start New Project", style="bold yellow")
        project_display_lines.append(new_project_text)

        project_list_text = Text("\n").join(project_display_lines)
        panel_content = Text.assemble(intro_text, project_list_text)
        panel_title = "[bold cyan]Project Options[/bold cyan]"
        console.print(Panel(panel_content, title=panel_title, border_style="green", expand=False, padding=(1,2)))

        choice_prompt = f"Enter project number (1-{len(listed_projects)}) to resume, or '{new_project_option_num}' (or 'n') for a new project"

        while True:
            try:
                raw_choice = Prompt.ask(choice_prompt).strip().lower()
                if raw_choice == 'n' or raw_choice == str(new_project_option_num):
                    user_idea = Prompt.ask("[bold yellow]Please enter your new project idea or request[/bold yellow]")
                    pipeline_inputs = {"user_request": user_idea}
                    project_name_for_orchestrator = None # Taskmaster will handle naming for new projects
                    logging.info("Starting a new project.")
                    break

                chosen_idx = int(raw_choice) - 1
                if 0 <= chosen_idx < len(listed_projects):
                    chosen_project = listed_projects[chosen_idx]
                    project_name_for_orchestrator = chosen_project['name'] # Use name to load project state
                    # For resuming, pipeline_inputs might not need 'user_request' initially if orchestrator handles resume logic
                    # pipeline_inputs = {"project_name": project_name_for_orchestrator}
                    # The orchestrator's __init__ takes project_name, so this is enough.
                    # execute_pipeline might need specific inputs if resuming a particular stage,
                    # but for now, just loading the project is the primary goal.
                    # If Taskmaster is the first stage for resume, it might need a way to know it's a resume.
                    # For now, let's assume the orchestrator handles this via project_name.
                    # The 'pipeline_inputs' for a resumed project might be different or even empty if the orchestrator
                    # just picks up from the saved state.
                    # For now, let's set it to indicate a resume if needed by later stages.
                    pipeline_inputs = {"project_name": project_name_for_orchestrator, "action": "resume"}
                    logging.info(f"Resuming project: {project_name_for_orchestrator}")
                    break
                else:
                    console.print(f"[bold red]Invalid selection. Please choose a number between 1 and {new_project_option_num} or 'n'.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number or 'n'.[/bold red]")
            except InvalidResponse: # Should not happen with basic Prompt.ask, but good practice
                console.print("[bold red]Invalid response received from prompt.[/bold red]")
    else:
        console.print(Panel(Text("No existing projects found.", style="italic"), title="[bold cyan]Project Status[/bold cyan]", border_style="yellow"))
        user_idea = Prompt.ask("[bold yellow]Please enter your new project idea or request[/bold yellow]")
        pipeline_inputs = {"user_request": user_idea}
        project_name_for_orchestrator = None

    # --- Execute Pipeline ---
    # Pass project_name_for_orchestrator to WorkflowOrchestrator constructor
    # This allows it to load the project state if a project name is provided.
    # For mocked run, project_name_for_orchestrator is None, so orchestrator.state will be None initially.
    from .workflows.orchestrator import WorkflowOrchestrator
    orchestrator = WorkflowOrchestrator(project_name=project_name_for_orchestrator)
    try:
        # pipeline_inputs now contains the user's request.
        # The mock_taskmaster_output is removed as Taskmaster will run live.
        results = orchestrator.execute_pipeline(pipeline_inputs)

        # The orchestrator's ProjectStateManager instance holds the final state
        final_state_manager = orchestrator.state

        if not final_state_manager:
            logging.error("Critical Error: Orchestrator state not initialized after pipeline execution.")
            logging.error(f"Pipeline Results (if any): {json.dumps(results, indent=2)}")
            # Early exit if state manager is None, means Taskmaster likely failed critically.
            # The orchestrator.execute_pipeline should return error details in 'results' in this case.
            if results and "error" in results:
                 logging.error(f"Taskmaster error details: {results.get('details')}")
            return # Stop further processing

        actual_project_name = final_state_manager.project_info.get("name", "UnknownProject")
        project_path = final_state_manager.project_info.get("path", ".") # Default to current dir if path missing

        logging.info(f"Project '{actual_project_name}' Execution Summary:")
        logging.info("===================================================")

        if final_state_manager.state.get("status") == "completed":
            logging.info(f"Project '{actual_project_name}' successfully completed and finalized.")
            final_output_artifact = results.get("final_assembly", {})
            if not final_output_artifact and results:
                final_output_artifact = results

            logging.info(f"Final Output Artifacts: {json.dumps(final_output_artifact, indent=2)}")

            output_file_path = os.path.join(project_path, "final_pipeline_output.json")
            try:
                os.makedirs(project_path, exist_ok=True) # Ensure directory exists
                with open(output_file_path, "w") as f:
                    json.dump(results, f, indent=2)
                logging.info(f"All pipeline artifacts saved to: {output_file_path}")
            except OSError as e:
                logging.error(f"Error saving final output file: {e}. Path: {output_file_path}")


        elif final_state_manager.state.get("status") == "failed":
            logging.warning(f"Project '{actual_project_name}' execution failed at stage: {final_state_manager.state.get('current_stage')}")
            logging.warning("Review the Workflow Summary printed by the orchestrator for error details.")
        else:
            logging.info(f"Project '{actual_project_name}' execution finished with status: {final_state_manager.state.get('status')}. Not all stages may have completed.")

    except Exception as e:
        logging.error(f"An unexpected error occurred during Qrew pipeline execution: {e}", exc_info=True)
        # Print error summary from orchestrator if available
        if 'orchestrator' in locals() and hasattr(orchestrator, 'state') and orchestrator.state is not None:
            # This part uses Rich console, so it's not converted to logging
            console.print("\n[bold red]Partial Workflow Summary (on error):[/bold red]")
            orchestrator.state.get_summary().print()

        # These are user-facing troubleshooting tips, keep as print or convert to console.print
        print("\nTroubleshooting Tips from main.py:")
        print("------------------------------------")
        error_str = str(e).lower()
        litellm_model_env = os.environ.get("LITELLM_MODEL", "").lower()
        if "api_key" in error_str or "authentication" in error_str or "permission" in error_str:
            print("- The error suggests an API key issue or authentication failure.")
        elif "model_not_found" in error_str:
            print(f"- Model '{litellm_model_env}' not found.")
        else:
            print("- Ensure LLM configuration is correct.")

if __name__ == "__main__":
    run_qrew()
