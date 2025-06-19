import sys
import os

# Add the project root (/app) to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../..')) # Adjusted path for deeper nesting
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add the project's src directory to sys.path to allow 'from crewai import ...'
project_src_path = os.path.join(project_root, "src")
if project_src_path not in sys.path:
    sys.path.insert(1, project_src_path)

# Ensure the llm_config is loaded first to set up the default LLM
# Adjusted path to llm_config.py, assuming it's in the 'qrew' directory
from mycrews.qrew.llm_config import default_llm

from .agent import offline_sync_agent # Import the specific agent instance

# Enable LiteLLM debugging if needed
# os.environ["LITELLM_DEBUG"] = "1"

from crewai import Task, Crew # type: ignore

def run_offline_sync_agent_task(task_description: str):
    """
    Runs a task using the offline_sync_agent with retry logic.
    """
    print(f"Initializing task for Offline Sync Agent with description: '{task_description}'")

    # Define the task for the OfflineSyncAgent
    agent_task = Task(
        description=task_description,
        expected_output="Task output, typically strategies for data synchronization, conflict resolution for offline scenarios, or status messages.",
        agent=offline_sync_agent # Use the imported offline_sync_agent
    )

    # Create a crew for the OfflineSyncAgent
    agent_crew = Crew(
        agents=[offline_sync_agent], # Use the imported offline_sync_agent
        tasks=[agent_task],
        llm=default_llm,
        verbose=True
    )

    print("\nKicking off Offline Sync Agent task...")
    max_retries = 3
    attempts = 0
    last_exception = None

    while attempts < max_retries:
        try:
            result = agent_crew.kickoff()
            print("\nOffline Sync Agent Task Complete.")
            print("--------------------------------------")
            print("Result from Offline Sync Agent:")
            if result:
                print(result.raw if hasattr(result, 'raw') else str(result))
            else:
                print("Offline Sync Agent produced no output.")
            print("--------------------------------------")
            return result
        except Exception as e:
            attempts += 1
            last_exception = e
            print(f"\nAn error occurred during Offline Sync Agent task execution (Attempt {attempts}/{max_retries}): {e}")
            if attempts < max_retries:
                print("Retrying...")
            else:
                print("All retries failed.")
                break

    error_message = f"Offline Sync Agent task failed after {max_retries} attempts."
    if last_exception:
        error_message += f" Last exception: {str(last_exception)}"

    print(error_message)
    return error_message


if __name__ == "__main__":
    # Example usage:
    sample_task = "Design a robust strategy for handling data synchronization and conflict resolution when the application transitions from offline to online mode. Consider potential data conflicts and how to merge them."
    print(f"Running Offline Sync Agent with sample task: '{sample_task}'")

    result = run_offline_sync_agent_task(sample_task)

    print("\n\n####################################################")
    print("## Offline Sync Agent Main Execution Result:")
    print("####################################################\n")
    if result and not isinstance(result, str):
        print("Final output from the Offline Sync Agent task:")
        print(result.raw if hasattr(result, 'raw') else str(result))
    elif isinstance(result, str):
        print(f"Task execution failed or produced a message: {result}")
    else:
        print("Offline Sync Agent task produced no definitive output or an error occurred.")

    if isinstance(result, str) and ("api_key" in result.lower() or "authentication" in result.lower()):
        print("\nTroubleshooting Tip: The error message suggests an API key or authentication issue.")
        print("Please ensure your LLM provider (e.g., OpenAI, Gemini, Anthropic) API key is correctly set in your environment variables.")
        print("Refer to `mycrews/qrew/llm_config.py` for details on LLM configuration.")

    print("\n--- End of example execution ---")
