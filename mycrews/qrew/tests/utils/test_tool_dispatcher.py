import pytest
import logging
from unittest.mock import MagicMock, patch

from mycrews.qrew.models import ToolAction
from mycrews.qrew.utils.tool_dispatcher import sanitize_args, dispatch_tool

# Mock Tool for testing dispatch_tool
class MockTool:
    def __init__(self, name="DefaultMockTool", description="A mock tool for testing."):
        self.name = name
        self.description = description
        self.args_schema = None # Can be set for more specific tests if needed
        self.run_method = MagicMock(return_value="MockTool executed successfully")

    def run(self, **kwargs):
        # Check if args match a predefined schema if one were set, etc.
        # For now, just call the mock method.
        return self.run_method(**kwargs)

@pytest.fixture
def mock_tool_registry(monkeypatch):
    mock_registry = {}
    # It's important that the keys in this mock registry match tool names used in tests
    # For example, if a test tries to dispatch "MyTestTool", it should be in this mock_registry.

    # Example: Add a couple of tools
    tool1 = MockTool(name="MyTestTool")
    tool2 = MockTool(name="AnotherTool")
    mock_registry["MyTestTool"] = tool1
    mock_registry["AnotherTool"] = tool2

    monkeypatch.setattr("mycrews.qrew.utils.tool_dispatcher.TOOL_REGISTRY", mock_registry)
    return mock_registry

# Tests for sanitize_args
def test_sanitize_args_primitives():
    args = {"str_val": "hello", "int_val": 10, "float_val": 3.14, "bool_val": True}
    assert sanitize_args(args) == args

def test_sanitize_args_list_of_primitives():
    args = {"list_val": ["a", 1, 2.0, False]}
    assert sanitize_args(args) == args

def test_sanitize_args_list_mixed_types():
    args = {"list_mixed": ["a", 1, {"complex": "obj"}, lambda x: x, None]}
    # According to sanitize_args logic, non-primitives in list are filtered out
    # The current implementation of sanitize_args:
    # clean[k] = [item for item in v if isinstance(item, (str, int, float, bool))]
    # So, complex objects and None in the list will be dropped.
    assert sanitize_args(args) == {"list_mixed": ["a", 1]}


def test_sanitize_args_non_primitive_values_converted_to_string():
    class CustomObj:
        def __str__(self):
            return "CustomObjectString"

    args = {"dict_val": {"a": 1}, "obj_val": CustomObj(), "none_val": None}
    # Current sanitize_args converts these to string:
    # else: clean[k] = str(v)
    sanitized = sanitize_args(args)
    assert sanitized["dict_val"] == "{'a': 1}"
    assert sanitized["obj_val"] == "CustomObjectString"
    assert sanitized["none_val"] == "None" # str(None) is 'None'

def test_sanitize_args_empty_dict():
    assert sanitize_args({}) == {}

def test_sanitize_args_non_dict_input(caplog):
    with caplog.at_level(logging.WARNING):
        assert sanitize_args("not_a_dict") == {}
    assert "sanitize_args received non-dict input" in caplog.text
    # Clear previous logs for the next assertion if caplog is not reset automatically per call
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        assert sanitize_args(None) == {} # Test with None as input
    assert "sanitize_args received non-dict input" in caplog.text


# Tests for dispatch_tool
def test_dispatch_tool_successful_call(mock_tool_registry):
    action = ToolAction.parse_obj({"name": "MyTestTool", "args": {"param": "value"}})
    mock_tool_instance = mock_tool_registry["MyTestTool"]

    result = dispatch_tool(action)

    assert result == "MockTool executed successfully"
    mock_tool_instance.run_method.assert_called_once_with(param="value")

def test_dispatch_tool_tool_not_registered(mock_tool_registry, caplog):
    action = ToolAction.parse_obj({"name": "UnknownTool", "args": {}})
    with caplog.at_level(logging.ERROR):
        result = dispatch_tool(action)
    assert result == {"error": "Tool 'UnknownTool' not registered."}
    assert "Tool 'UnknownTool' not registered." in caplog.text

def test_dispatch_tool_invalid_action_object_type(caplog):
    with caplog.at_level(logging.ERROR):
        result = dispatch_tool({"name": "MyTestTool", "args": {}}) # Not a ToolAction instance
    assert result == {"error": "Invalid action object provided to dispatch_tool."}
    assert "Invalid action object provided to dispatch_tool." in caplog.text

def test_dispatch_tool_tool_execution_raises_exception(mock_tool_registry, caplog):
    action = ToolAction.parse_obj({"name": "MyTestTool", "args": {"param": "value"}})
    mock_tool_instance = mock_tool_registry["MyTestTool"]
    expected_exception = Exception("Tool failed spectacularly!")
    mock_tool_instance.run_method.side_effect = expected_exception

    with caplog.at_level(logging.ERROR):
        result = dispatch_tool(action)

    assert result == {"error": str(expected_exception)}
    assert f"Tool dispatch failed for MyTestTool with args {{'param': 'value'}}: {expected_exception}" in caplog.text
    mock_tool_instance.run_method.assert_called_once_with(param="value")

def test_dispatch_tool_args_need_sanitization(mock_tool_registry):
    # Args that will be transformed by sanitize_args
    action = ToolAction.parse_obj({
        "name": "MyTestTool",
        "args": {"valid": "value", "complex": {"a": 1}, "num_list": [1, "two", {"b": 2}]}
    })
    mock_tool_instance = mock_tool_registry["MyTestTool"]

    result = dispatch_tool(action)

    assert result == "MockTool executed successfully"
    # Check that sanitize_args was effectively called
    # The run_method should be called with sanitized args
    expected_sanitized_args = {"valid": "value", "complex": "{'a': 1}", "num_list": [1, "two"]}
    mock_tool_instance.run_method.assert_called_once_with(**expected_sanitized_args)

def test_dispatch_tool_empty_args_provided_to_tool(mock_tool_registry):
    action = ToolAction.parse_obj({"name": "MyTestTool", "args": {}}) # Explicit empty args
    mock_tool_instance = mock_tool_registry["MyTestTool"]

    result = dispatch_tool(action)

    assert result == "MockTool executed successfully"
    mock_tool_instance.run_method.assert_called_once_with() # Called with no keyword arguments

def test_dispatch_tool_no_args_in_action_tool_called_with_no_args(mock_tool_registry):
    action = ToolAction.parse_obj({"name": "MyTestTool"}) # Args field missing, defaults to {}
    mock_tool_instance = mock_tool_registry["MyTestTool"]

    result = dispatch_tool(action)

    assert result == "MockTool executed successfully"
    mock_tool_instance.run_method.assert_called_once_with()
