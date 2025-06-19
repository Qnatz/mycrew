import sys
import os

# Add the project root (/app) to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../..')) # Adjusted path for deeper nesting
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add the project's src directory to sys.path to allow 'from crewai import ...'
# This assumes 'src' is directly under project_root. If qrew is the new root, this might need adjustment.
project_src_path = os.path.join(project_root, "src")
if project_src_path not in sys.path:
    sys.path.insert(1, project_src_path)

# Ensure the llm_config is loaded first to set up the default LLM
# Adjusted path to llm_config.py, assuming it's in the 'qrew' directory
from mycrews.qrew.llm_config import default_llm

from .agent import auth_coordinator_agent # Import the specific agent instance

# Enable LiteLLM debugging if needed
# os.environ["LITELLM_DEBUG"] = "1"

from crewai import Task, Crew # type: ignore

def run_auth_coordinator_agent_task(task_description: str):
    """
    Runs a task using the auth_coordinator_agent with retry logic.
    """
    print(f"Initializing task for Auth Coordinator Agent with description: '{task_description}'")

    # Define the task for the AuthCoordinatorAgent
    agent_task = Task(
        description=task_description,
        expected_output="Task output, typically a status message or result from the authentication coordination.",
        agent=auth_coordinator_agent
    )

    # Create a crew for the AuthCoordinatorAgent
    agent_crew = Crew(
        agents=[auth_coordinator_agent],
        tasks=[agent_task],
        llm=default_llm,
        verbose=True
    )

    print("\nKicking off Auth Coordinator Agent task...")
    max_retries = 3
    attempts = 0
    last_exception = None

    while attempts < max_retries:
        try:
            result = agent_crew.kickoff()
            print("\nAuth Coordinator Agent Task Complete.")
            print("--------------------------------------")
            print("Result from Auth Coordinator Agent:")
            if result:
                print(result.raw if hasattr(result, 'raw') else str(result))
            else:
                print("Auth Coordinator Agent produced no output.")
            print("--------------------------------------")
            return result
        except Exception as e:
            attempts += 1
            last_exception = e
            print(f"\nAn error occurred during Auth Coordinator Agent task execution (Attempt {attempts}/{max_retries}): {e}")
            if attempts < max_retries:
                print("Retrying...")
            else:
                print("All retries failed.")
                break

    error_message = f"Auth Coordinator Agent task failed after {max_retries} attempts."
    if last_exception:
        error_message += f" Last exception: {str(last_exception)}"

    # Optionally, re-raise the last exception or return a specific error object
    # For now, just printing and returning an error message string
    print(error_message)
    # Consider raising an exception here if that's more appropriate for the calling context
    # raise last_exception if last_exception else RuntimeError(error_message)
    return error_message


if __name__ == "__main__":
    # Example usage:
    sample_task = "Coordinate the authentication process for a new user registration request. Ensure all security protocols are met."
    print(f"Running Auth Coordinator Agent with sample task: '{sample_task}'")

    result = run_auth_coordinator_agent_task(sample_task)

    print("\n\n####################################################")
    print("## Auth Coordinator Agent Main Execution Result:")
    print("####################################################\n")
    if result and not isinstance(result, str): # Check if it's a successful result object
        print("Final output from the Auth Coordinator Agent task:")
        print(result.raw if hasattr(result, 'raw') else str(result))
    elif isinstance(result, str): # It's an error message string
        print(f"Task execution failed or produced a message: {result}")
    else:
        print("Auth Coordinator Agent task produced no definitive output or an error occurred.")

    # Example of how to handle potential errors from the LLM configuration or execution
    # This is a simplified version of the error handling from the original template
    if isinstance(result, str) and ("api_key" in result.lower() or "authentication" in result.lower()):
        print("\nTroubleshooting Tip: The error message suggests an API key or authentication issue.")
        print("Please ensure your LLM provider (e.g., OpenAI, Gemini, Anthropic) API key is correctly set in your environment variables.")
        print("Refer to `mycrews/qrew/llm_config.py` for details on LLM configuration.")

    print("\n--- End of example execution ---")
