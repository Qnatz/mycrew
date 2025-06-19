# mycrews/qrew/tools/github_tool_wrapper.py
from typing import List, Optional, Dict, Any
# from mycrews.qrew.tools.inbuilt_tools import raw_github_search_tool # MOVED
from crewai.tools.base_tool import BaseTool
from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField


# Default content types, similar to how it's initialized in inbuilt_tools
DEFAULT_CONTENT_TYPES = ['code', 'repo', 'issue']

class GithubToolNotInitializedError(Exception):
    """Custom exception for when github_search_tool is None."""
    pass

def run_github_search(
    search_query: str,
    github_repo: Optional[str] = None,
    content_types: Optional[List[str]] = None
) -> Any:
    """
    Wrapper function to safely call the GithubSearchTool with validated primitive types.

    Args:
        search_query: The query string to search for.
        github_repo: Optional. The specific repository (e.g., "owner/repo") to search within.
                     If None, searches across all of GitHub.
        content_types: Optional. A list of content types to search (e.g., ['code', 'issue']).
                       Defaults to ['code', 'repo', 'issue'] if None.

    Returns:
        The result of the github_search_tool.run() call.

    Raises:
        TypeError: If input arguments are not of the expected primitive types.
        GithubToolNotInitializedError: If the github_search_tool itself was not initialized (is None).
    """
    if not isinstance(search_query, str):
        raise TypeError(f"search_query must be a string, got {type(search_query)}")
    if github_repo is not None and not isinstance(github_repo, str):
        raise TypeError(f"github_repo must be a string or None, got {type(github_repo)}")
    if content_types is not None and not (
        isinstance(content_types, list) and
        all(isinstance(item, str) for item in content_types)
    ):
        raise TypeError(f"content_types must be a list of strings or None, got {type(content_types)}")

    # Import raw_github_search_tool here to delay it.
    from mycrews.qrew.tools.inbuilt_tools import raw_github_search_tool

    if raw_github_search_tool is None: # Check the imported raw_github_search_tool
        # This case occurs if GITHUB_TOKEN was not found or initialization failed in inbuilt_tools.py
        raise GithubToolNotInitializedError(
            "Original GithubSearchTool (raw) is not available. " # Updated message
            "Please ensure GITHUB_TOKEN is correctly configured and the tool initialized successfully."
        )

    tool_input: Dict[str, Any] = {"search_query": search_query}

    if github_repo:
        # The key for the tool input should be "github_repo" as per user's example.
        tool_input["github_repo"] = github_repo


    # Use provided content_types or default if None
    tool_input["content_types"] = content_types if content_types is not None else DEFAULT_CONTENT_TYPES

    # The GithubSearchTool from crewai_tools expects a single dictionary argument.
    try:
        print(f"[run_github_search] Calling raw_github_search_tool with input: {tool_input}")
        result = raw_github_search_tool.run(tool_input) # Use raw_github_search_tool
        return result
    except Exception as e:
        # Catching other potential errors from the tool's execution
        print(f"[run_github_search] Error during github_search_tool.run: {e}")
        # Re-raise or return an error message, depending on desired handling
        raise # Re-raise the original exception for now

# Example of how to potentially check the args_schema if the tool is available (for dev/debug)
# if __name__ == '__main__':
#     if github_search_tool:
#         print("GithubSearchTool initialized. Args schema:")
#         try:
#             # Accessing args_schema if it's a BaseTool derivative
#             if hasattr(github_search_tool, 'args_schema') and github_search_tool.args_schema:
#                 print(github_search_tool.args_schema.model_json_schema())
#             else:
#                 print("args_schema not directly available or tool is not a BaseTool derivative with it exposed.")
#         except Exception as e:
#             print(f"Could not retrieve args_schema: {e}")
#     else:
#         print("GithubSearchTool is not initialized (None).")


# Define the Pydantic model for the arguments of the new tool
class GithubSearchWrapperToolSchema(PydanticBaseModel):
    search_query: str = PydanticField(..., description="The query string to search for on GitHub.")
    github_repo: Optional[str] = PydanticField(default=None, description="Optional. The specific repository (e.g., 'owner/repo') to search within. If None, searches across all of GitHub.")
    content_types: Optional[List[str]] = PydanticField(default=None, description="Optional. A list of content types to search (e.g., ['code', 'issue']). Defaults to ['code', 'repo', 'issue'] if None.")

class GithubSearchWrapperTool(BaseTool):
    name: str = "GitHub Search" # Keep a user-friendly name
    description: str = (
        "Searches GitHub for repositories, code, issues, etc. "
        "Input arguments should be direct values for search_query, github_repo (optional), and content_types (optional list of strings)."
    )
    args_schema: type[PydanticBaseModel] = GithubSearchWrapperToolSchema
    # github_search_tool_instance: Any = github_search_tool # Not needed if run_github_search handles it

    def _run(
        self,
        search_query: str,
        github_repo: Optional[str] = None,
        content_types: Optional[List[str]] = None,
        **kwargs # Allow for potential extra args from BaseTool.run, though we don't use them
    ) -> Any:
        """
        The actual implementation that calls the wrapper function.
        The arguments here (search_query, github_repo, content_types)
        are guaranteed by BaseTool to match the args_schema.
        """
        # The run_github_search function already handles the case where
        # the original github_search_tool from inbuilt_tools might be None.
        # It also handles default content_types if None is passed.
        try:
            return run_github_search(
                search_query=search_query,
                github_repo=github_repo,
                content_types=content_types
            )
        except GithubToolNotInitializedError as e:
            # Log or return the specific error message
            # This ensures that if the underlying tool isn't ready, this wrapped tool also signals it clearly.
            return f"Error: {str(e)}"
        except TypeError as e:
            # This should ideally not be hit if args_schema validation works, but as a safeguard for other TypeErrors.
            return f"TypeError in tool execution: {str(e)}"
        except Exception as e:
            # Catch any other unexpected errors from the run_github_search or underlying tool
            return f"An unexpected error occurred: {str(e)}"

    # If the original github_search_tool can be None, this wrapped tool should still be instantiable.
    # The _run method will then handle the None case via run_github_search.
