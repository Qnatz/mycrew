import json
import logging
from typing import Any, Dict

# Setup basic logging for the example
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Assuming models.py and tool_dispatcher.py are accessible via the Python path
# For this example, we'll assume they are in mycrews.qrew.models and mycrews.qrew.utils
try:
    from mycrews.qrew.models import ToolAction
    from mycrews.qrew.utils.tool_dispatcher import dispatch_tool
    # We also need TOOL_REGISTRY to be populated for dispatch_tool to work
    # For this example, we assume tool_registry.py has run and populated it.
    # To ensure tools are available for the example, we can try to import and print the registry.
    from mycrews.qrew.tool_registry import TOOL_REGISTRY
    if not TOOL_REGISTRY:
        logger.warning("TOOL_REGISTRY is empty. Tool dispatch will fail. Ensure inbuilt_tools.py configures tools and tool_registry.py populates them.")
    else:
        logger.info(f"TOOL_REGISTRY loaded with tools: {list(TOOL_REGISTRY.keys())}")

except ImportError as e:
    logger.error(f"Failed to import necessary modules: {e}. This example may not run correctly.")
    # Define dummy versions for the script to run without breaking if imports fail
    class ToolAction:
        def __init__(self, name, args): self.name = name; self.args = args
        @staticmethod
        def parse_obj(obj): return ToolAction(obj.get("name"), obj.get("args", {}))

    def dispatch_tool(action):
        return {"error": "Dispatch tool not available due to import error."}
    TOOL_REGISTRY = {}


# --- Agent Prompt Guidance ---
# This text should be part of the agent's system prompt or task instructions.
# It instructs the LLM on how to format its output when it needs to use a tool.
# (This is conceptual for this subtask as we are not modifying the agent's actual prompt mechanism)

agent_prompt_guidance = '''
When you need to use a tool, your response MUST be a VALID JSON object that strictly adheres to the following ToolAction schema:
{
    "name": "tool_name_from_registry",  // String, exact name of the tool from the allowed list.
    "args": {                           // Object, arguments for the tool.
        "arg_name1": "value1",          // Arguments must be primitives (string, number, boolean)
        "arg_name2": ["item1", "item2"] // or lists of primitives.
    }
}
Available tools for you:
- "File Writer Tool": Writes content to a file. Args: {"file_path": "path/to/file.txt", "text": "content to write"}
- "Directory Search Tool": Searches for files or directories. Args: {"search_query": "query"}
- "Text File Search Tool": Searches text within files. Args: {"search_query": "text to search"}
If you do not need to use a tool, provide your response as plain text.
If you intend to call a tool but the action name is unclear or you are unsure, use "None" for the "name" field
and provide a clarifying question in the "args" like {"clarification_needed": "your question here"}.
'''

logger.info("Agent Prompt Guidance (Conceptual):")
logger.info(agent_prompt_guidance)
logger.info("-" * 30)


# --- Example LLM Outputs (simulated) ---
# These would be the raw string output from the LLM
llm_output_valid_tool_call = '''
{
    "name": "File Writer Tool",
    "args": {
        "file_path": "example_log.txt",
        "text": "This is a test log message from the Logger Agent."
    }
}
'''

llm_output_none_tool_call = '''
{
    "name": "None",
    "args": {
        "clarification_needed": "I need to write a log, but which file path should I use for critical errors vs. regular info?"
    }
}
'''

llm_output_malformed_json = '''
{
    "name": "File Writer Tool"
    "args": {
        "file_path": "another_log.txt",
        "text": "This JSON is malformed."
}
''' # Missing comma

llm_output_invalid_action_schema = '''
{
    "tool_name": "File Writer Tool",
    "parameters": {
        "file_path": "schema_error.txt",
        "text": "This doesn't match ToolAction."
    }
}
'''

# --- Agent's Tool Processing Logic (New) ---
# This function simulates how an agent would process an LLM's output.
def process_llm_tool_response(llm_response_str: str) -> Any:
    logger.info(f"Processing LLM Response: {llm_response_str.strip()}")
    parsed_action = None
    try:
        # Attempt to parse the LLM output as JSON
        llm_output_json = json.loads(llm_response_str)

        # Attempt to parse the JSON into a ToolAction object
        # Pydantic's parse_obj will raise a ValidationError if the structure is wrong
        parsed_action = ToolAction.parse_obj(llm_output_json)

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to decode LLM output as JSON: {e}. LLM Output: {llm_response_str}")
        # Agent should handle this, perhaps by asking LLM to reformat or by returning an error.
        return {"error": f"LLM output was not valid JSON: {e}"}

    except Exception as e: # Catches Pydantic's ValidationError and other unexpected errors
        logger.warning(f"Failed to parse LLM output into ToolAction: {e}. LLM Output: {llm_output_json}")
        # Agent should handle this.
        return {"error": f"LLM output did not match ToolAction schema: {e}"}

    # Check if action name is "None" (as per issue spec for fallback/logging)
    if parsed_action.name == "None":
        logger.warning(f"LLM requested clarification or indicated no specific tool: {parsed_action.args}")
        # Agent could then ask the LLM to clarify, as suggested in the issue.
        # For this example, we just return the args which might contain the clarification.
        return {"clarification_request": parsed_action.args}

    if not parsed_action.name: # Handles cases where name might be empty string after parsing
        logger.warning(f"LLM output parsed, but tool name is missing or empty. Action: {parsed_action}")
        return {"error": "Tool name missing in parsed action."}

    # If parsing is successful and tool name is not "None", dispatch the tool
    logger.info(f"Successfully parsed ToolAction: Name='{parsed_action.name}', Args='{parsed_action.args}'")
    return dispatch_tool(parsed_action)

# --- Run Examples ---
logger.info("\n" + "="*10 + " Example 1: Valid Tool Call " + "="*10)
result1 = process_llm_tool_response(llm_output_valid_tool_call)
logger.info(f"Result 1: {result1}\n")

logger.info("="*10 + " Example 2: 'None' Tool Call (Clarification) " + "="*10)
result2 = process_llm_tool_response(llm_output_none_tool_call)
logger.info(f"Result 2: {result2}\n")

logger.info("="*10 + " Example 3: Malformed JSON " + "="*10)
result3 = process_llm_tool_response(llm_output_malformed_json)
logger.info(f"Result 3: {result3}\n")

logger.info("="*10 + " Example 4: Invalid Action Schema " + "="*10)
result4 = process_llm_tool_response(llm_output_invalid_action_schema)
logger.info(f"Result 4: {result4}\n")

# Example of a tool not in registry (if dispatch_tool is working)
llm_output_unknown_tool = '''
{
    "name": "NonExistentTool",
    "args": {}
}
'''
logger.info("="*10 + " Example 5: Unknown Tool " + "="*10)
result5 = process_llm_tool_response(llm_output_unknown_tool)
logger.info(f"Result 5: {result5}\n")
