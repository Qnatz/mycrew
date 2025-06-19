from crewai import Task # For type hint, should already be there
from typing import Any  # For type hint for 'result'
import logging
from uuid import uuid4

log = logging.getLogger(__name__)
# If you need to see these logs immediately during testing without other logging setup:
# logging.basicConfig(level=logging.INFO)

Task.DEFAULT_SCHEMA = {
    "id": {"type": "uuid", "default_factory": uuid4},
    "description": {"type": "string"},
    "expected_output": {"type": "string", "default": ""},
    "successCriteria": {"type": "list[string]", "default": []},
    "maxRetries": {"type": "integer", "default": 2},
    "metadata": {"type": "object", "default": {}},
}
print("CrewAI Task.DEFAULT_SCHEMA configured in config.py")

def example_summary_validator(task: Task, result: Any) -> bool:
    description_lower = task.description.lower()

    # Check if task description implies a summary is a key part of the output
    if "summary" in description_lower or "summarize" in description_lower:
        result_str = str(result) # Convert agent's output to string for checking

        # Define keywords that indicate a summary is present
        summary_keywords = ["summary", "overview", "abstract", "brief", "recap"] # Added "recap"

        found_summary_keyword = False
        for keyword in summary_keywords:
            if keyword in result_str.lower():
                found_summary_keyword = True
                break

        if not found_summary_keyword:
            # Log the failure detail before returning False
            # Using a slice for potentially long descriptions in logs
            log.info(f"QualityGate Fail (Custom Validator): Task '{task.description[:150]}...' expected a summary, "
                     f"but keywords like {summary_keywords} were missing in the string result.")
            # Optional: Keep a print for immediate visibility during runs if logs are not actively monitored
            # print(f"QualityGate Fail (Custom Validator): Task '{task.description[:150]}...' expected a summary, "
            #       f"but keywords like {summary_keywords} were missing in the string result.")
            return False
    return True
