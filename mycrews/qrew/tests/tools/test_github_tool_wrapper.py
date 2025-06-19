# mycrews/qrew/tests/tools/test_github_tool_wrapper.py
import pytest
from unittest.mock import patch, MagicMock

# Import the functions and classes to be tested
from mycrews.qrew.tools.github_tool_wrapper import (
    run_github_search,
    GithubSearchWrapperTool,
    GithubToolNotInitializedError,
    DEFAULT_CONTENT_TYPES
)

# This is the path to the 'raw_github_search_tool' instance within the inbuilt_tools module,
# which run_github_search will try to import and use.
# Corrected path: it's looked up in inbuilt_tools by the run_github_search function.
MOCK_RAW_TOOL_PATH = "mycrews.qrew.tools.inbuilt_tools.raw_github_search_tool"

# --- Tests for run_github_search function ---

def test_run_github_search_invalid_types_raise():
    """Test that run_github_search raises TypeError for invalid input types."""
    with pytest.raises(TypeError, match="search_query must be a string"):
        run_github_search(123) # type: ignore

    with pytest.raises(TypeError, match="github_repo must be a string or None"):
        run_github_search("query", github_repo=123) # type: ignore

    with pytest.raises(TypeError, match="content_types must be a list of strings or None"):
        run_github_search("query", content_types="not-a-list") # type: ignore

    with pytest.raises(TypeError, match="content_types must be a list of strings or None"):
        run_github_search("query", content_types=[123]) # type: ignore

@patch(MOCK_RAW_TOOL_PATH)
def test_run_github_search_valid_call_all_args(mock_raw_tool_run_instance):
    """Test run_github_search with all valid arguments."""
    # Configure the mock for the raw tool instance itself
    mock_raw_tool_run_instance.run = MagicMock(return_value={"success": True})

    result = run_github_search(
        search_query="test query",
        github_repo="owner/repo",
        content_types=["code", "issue"]
    )
    assert result == {"success": True}
    expected_tool_input = {
        "search_query": "test query",
        "github_repo": "owner/repo",
        "content_types": ["code", "issue"]
    }
    mock_raw_tool_run_instance.run.assert_called_once_with(expected_tool_input)

@patch(MOCK_RAW_TOOL_PATH)
def test_run_github_search_valid_call_optional_missing(mock_raw_tool_run_instance):
    """Test run_github_search with optional arguments missing (should use defaults)."""
    mock_raw_tool_run_instance.run = MagicMock(return_value={"default_success": True})

    result = run_github_search(search_query="another query")
    assert result == {"default_success": True}
    expected_tool_input = {
        "search_query": "another query",
        "content_types": DEFAULT_CONTENT_TYPES # github_repo is omitted, content_types defaults
    }
    mock_raw_tool_run_instance.run.assert_called_once_with(expected_tool_input)

@patch(MOCK_RAW_TOOL_PATH, None) # Patch raw_github_search_tool to be None
def test_run_github_search_tool_not_initialized():
    """Test run_github_search when raw_github_search_tool is None."""
    with pytest.raises(GithubToolNotInitializedError, match="Original GithubSearchTool .* is not available"):
        run_github_search("query")

@patch(MOCK_RAW_TOOL_PATH)
def test_run_github_search_raw_tool_raises_exception(mock_raw_tool_run_instance):
    """Test run_github_search when the raw tool's run method raises an exception."""
    mock_raw_tool_run_instance.run = MagicMock(side_effect=ValueError("Raw tool error"))

    with pytest.raises(ValueError, match="Raw tool error"):
        run_github_search("query")

# --- Tests for GithubSearchWrapperTool class ---

def test_github_search_wrapper_tool_schema_and_description():
    """Test basic properties of GithubSearchWrapperTool."""
    tool = GithubSearchWrapperTool()
    assert tool.name == "GitHub Search"
    assert "Searches GitHub for repositories, code, issues" in tool.description
    assert tool.args_schema is not None
    # Check a few fields in the schema
    schema_props = tool.args_schema.model_json_schema()["properties"]
    assert "search_query" in schema_props
    assert schema_props["search_query"]["type"] == "string"

    assert "github_repo" in schema_props
    github_repo_schema = schema_props["github_repo"]
    assert github_repo_schema.get("default") is None # Indicates optionality
    assert any(item.get("type") == "string" for item in github_repo_schema.get("anyOf", []))
    assert any(item.get("type") == "null" for item in github_repo_schema.get("anyOf", []))

    assert "content_types" in schema_props
    content_types_schema = schema_props["content_types"]
    assert content_types_schema.get("default") is None # Indicates optionality
    assert any(item.get("type") == "array" and item.get("items", {}).get("type") == "string" for item in content_types_schema.get("anyOf", []))
    assert any(item.get("type") == "null" for item in content_types_schema.get("anyOf", []))


# We need to patch 'run_github_search' as it's called by the tool's _run method
@patch("mycrews.qrew.tools.github_tool_wrapper.run_github_search")
def test_github_search_wrapper_tool_run_method_success(mock_run_wrapper_func):
    """Test GithubSearchWrapperTool._run method calls run_github_search correctly."""
    mock_run_wrapper_func.return_value = {"search_results": "some data"}

    tool = GithubSearchWrapperTool()
    # Arguments for the tool's _run method, matching its args_schema
    result = tool._run(
        search_query="test query",
        github_repo="owner/repo",
        content_types=["code"]
    )

    assert result == {"search_results": "some data"}
    mock_run_wrapper_func.assert_called_once_with(
        search_query="test query",
        github_repo="owner/repo",
        content_types=["code"]
    )

@patch("mycrews.qrew.tools.github_tool_wrapper.run_github_search")
def test_github_search_wrapper_tool_run_method_handles_tool_not_init_error(mock_run_wrapper_func):
    """Test _run returns error message when run_github_search raises GithubToolNotInitializedError."""
    error_message = "GithubTool is not available due to config issues."
    mock_run_wrapper_func.side_effect = GithubToolNotInitializedError(error_message)

    tool = GithubSearchWrapperTool()
    result = tool._run(search_query="query")

    assert result == f"Error: {error_message}"
    mock_run_wrapper_func.assert_called_once_with(
        search_query="query",
        github_repo=None,
        content_types=None # run_github_search handles defaulting this
    )

@patch("mycrews.qrew.tools.github_tool_wrapper.run_github_search")
def test_github_search_wrapper_tool_run_method_handles_type_error(mock_run_wrapper_func):
    """Test _run returns error message when run_github_search raises TypeError."""
    # This scenario is less likely if Pydantic validation in BaseTool works,
    # but tests the error handling in GithubSearchWrapperTool._run.
    error_message = "Invalid type for argument."
    mock_run_wrapper_func.side_effect = TypeError(error_message)

    tool = GithubSearchWrapperTool()
    result = tool._run(search_query="query") # Args are valid for _run itself

    assert result == f"TypeError in tool execution: {error_message}"

@patch("mycrews.qrew.tools.github_tool_wrapper.run_github_search")
def test_github_search_wrapper_tool_run_method_handles_general_exception(mock_run_wrapper_func):
    """Test _run returns error message for other exceptions from run_github_search."""
    error_message = "Some unexpected tool failure."
    mock_run_wrapper_func.side_effect = Exception(error_message)

    tool = GithubSearchWrapperTool()
    result = tool._run(search_query="query")

    assert result == f"An unexpected error occurred: {error_message}"
