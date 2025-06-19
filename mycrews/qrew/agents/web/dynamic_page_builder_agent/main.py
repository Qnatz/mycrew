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

from .agent import dynamic_page_builder_agent # Import the specific agent instance

# Enable LiteLLM debugging if needed
# os.environ["LITELLM_DEBUG"] = "1"

from crewai import Task, Crew # type: ignore

def run_dynamic_page_builder_agent_task(task_description: str):
    """
    Runs a task using the dynamic_page_builder_agent (web) with retry logic.
    """
    print(f"Initializing task for Web Dynamic Page Builder Agent with description: '{task_description}'")

    # Define the task for the DynamicPageBuilderAgent
    agent_task = Task(
        description=task_description,
        expected_output="Task output, typically HTML/JS/CSS code for dynamic web pages, component implementations, or status messages.",
        agent=dynamic_page_builder_agent # Use the imported dynamic_page_builder_agent
    )

    # Create a crew for the DynamicPageBuilderAgent
    agent_crew = Crew(
        agents=[dynamic_page_builder_agent], # Use the imported dynamic_page_builder_agent
        tasks=[agent_task],
        llm=default_llm,
        verbose=True
    )

    print("\nKicking off Web Dynamic Page Builder Agent task...")
    max_retries = 3
    attempts = 0
    last_exception = None

    while attempts < max_retries:
        try:
            result = agent_crew.kickoff()
            print("\nWeb Dynamic Page Builder Agent Task Complete.")
            print("--------------------------------------")
            print("Result from Web Dynamic Page Builder Agent:")
            if result:
                print(result.raw if hasattr(result, 'raw') else str(result))
            else:
                print("Web Dynamic Page Builder Agent produced no output.")
            print("--------------------------------------")
            return result
        except Exception as e:
            attempts += 1
            last_exception = e
            print(f"\nAn error occurred during Web Dynamic Page Builder Agent task execution (Attempt {attempts}/{max_retries}): {e}")
            if attempts < max_retries:
                print("Retrying...")
            else:
                print("All retries failed.")
                break

    error_message = f"Web Dynamic Page Builder Agent task failed after {max_retries} attempts."
    if last_exception:
        error_message += f" Last exception: {str(last_exception)}"

    print(error_message)
    return error_message


if __name__ == "__main__":
    # Example usage:
    sample_task = "Create a React component for a dynamic product listing page. The component should fetch product data from an API and display it in a grid format with filtering options."
    print(f"Running Web Dynamic Page Builder Agent with sample task: '{sample_task}'")

    result = run_dynamic_page_builder_agent_task(sample_task)

    print("\n\n####################################################")
    print("## Web Dynamic Page Builder Agent Main Execution Result:")
    print("####################################################\n")
    if result and not isinstance(result, str):
        print("Final output from the Web Dynamic Page Builder Agent task:")
        print(result.raw if hasattr(result, 'raw') else str(result))
    elif isinstance(result, str):
        print(f"Task execution failed or produced a message: {result}")
    else:
        print("Web Dynamic Page Builder Agent task produced no definitive output or an error occurred.")

    if isinstance(result, str) and ("api_key" in result.lower() or "authentication" in result.lower()):
        print("\nTroubleshooting Tip: The error message suggests an API key or authentication issue.")
        print("Please ensure your LLM provider (e.g., OpenAI, Gemini, Anthropic) API key is correctly set in your environment variables.")
        print("Refer to `mycrews/qrew/llm_config.py` for details on LLM configuration.")

    print("\n--- End of example execution ---")
