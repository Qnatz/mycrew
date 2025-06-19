import sys
import os

# Add the project root (/app) to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')) # Adjusted path for deeper nesting
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add the project's src directory to sys.path to allow 'from crewai import ...'
project_src_path = os.path.join(project_root, "src")
if project_src_path not in sys.path:
    sys.path.insert(1, project_src_path)

# Ensure the llm_config is loaded first to set up the default LLM
# Adjusted path to llm_config.py, assuming it's in the 'qrew' directory
from mycrews.qrew.llm_config import default_llm

from .agent import offline_support_coordinator_agent # Import the specific agent instance

# Enable LiteLLM debugging if needed
# os.environ["LITELLM_DEBUG"] = "1"

from crewai import Task, Crew # type: ignore

def run_offline_support_coordinator_agent_task(task_description: str):
    """
    Runs a task using the offline_support_coordinator_agent with retry logic.
    """
    print(f"Initializing task for Offline Support Coordinator Agent with description: '{task_description}'")

    # Define the task for the OfflineSupportCoordinatorAgent
    agent_task = Task(
        description=task_description,
        expected_output="Task output, typically strategies for offline data storage, synchronization plans, or status messages.",
        agent=offline_support_coordinator_agent # Use the imported offline_support_coordinator_agent
    )

    # Create a crew for the OfflineSupportCoordinatorAgent
    agent_crew = Crew(
        agents=[offline_support_coordinator_agent], # Use the imported offline_support_coordinator_agent
        tasks=[agent_task],
        llm=default_llm,
        verbose=True
    )

    print("\nKicking off Offline Support Coordinator Agent task...")
    max_retries = 3
    attempts = 0
    last_exception = None

    while attempts < max_retries:
        try:
            result = agent_crew.kickoff()
            print("\nOffline Support Coordinator Agent Task Complete.")
            print("--------------------------------------")
            print("Result from Offline Support Coordinator Agent:")
            if result:
                print(result.raw if hasattr(result, 'raw') else str(result))
            else:
                print("Offline Support Coordinator Agent produced no output.")
            print("--------------------------------------")
            return result
        except Exception as e:
            attempts += 1
            last_exception = e
            print(f"\nAn error occurred during Offline Support Coordinator Agent task execution (Attempt {attempts}/{max_retries}): {e}")
            if attempts < max_retries:
                print("Retrying...")
            else:
                print("All retries failed.")
                break

    error_message = f"Offline Support Coordinator Agent task failed after {max_retries} attempts."
    if last_exception:
        error_message += f" Last exception: {str(last_exception)}"

    print(error_message)
    return error_message


if __name__ == "__main__":
    # Example usage:
    sample_task = "Coordinate the implementation of offline capabilities for the application. This includes defining local storage strategies and data synchronization mechanisms for when the app regains connectivity."
    print(f"Running Offline Support Coordinator Agent with sample task: '{sample_task}'")

    result = run_offline_support_coordinator_agent_task(sample_task)

    print("\n\n####################################################")
    print("## Offline Support Coordinator Agent Main Execution Result:")
    print("####################################################\n")
    if result and not isinstance(result, str):
        print("Final output from the Offline Support Coordinator Agent task:")
        print(result.raw if hasattr(result, 'raw') else str(result))
    elif isinstance(result, str):
        print(f"Task execution failed or produced a message: {result}")
    else:
        print("Offline Support Coordinator Agent task produced no definitive output or an error occurred.")

    if isinstance(result, str) and ("api_key" in result.lower() or "authentication" in result.lower()):
        print("\nTroubleshooting Tip: The error message suggests an API key or authentication issue.")
        print("Please ensure your LLM provider (e.g., OpenAI, Gemini, Anthropic) API key is correctly set in your environment variables.")
        print("Refer to `mycrews/qrew/llm_config.py` for details on LLM configuration.")

    print("\n--- End of example execution ---")
