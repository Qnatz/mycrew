import pytest
from pydantic import ValidationError
from mycrews.qrew.models import ToolAction # Assuming models.py is in mycrews.qrew.models

def test_tool_action_valid():
    data = {"name": "TestTool", "args": {"param1": "value1", "param2": 123}}
    action = ToolAction.parse_obj(data)
    assert action.name == "TestTool"
    assert action.args == {"param1": "value1", "param2": 123}

def test_tool_action_empty_args():
    data = {"name": "TestTool"}
    action = ToolAction.parse_obj(data) # args should default to {}
    assert action.name == "TestTool"
    assert action.args == {}

def test_tool_action_args_explicitly_empty_dict():
    data = {"name": "TestTool", "args": {}}
    action = ToolAction.parse_obj(data)
    assert action.name == "TestTool"
    assert action.args == {}

def test_tool_action_args_none(): # Pydantic v2: None is not allowed if default_factory is set unless Optional
    # With `args: Dict[str, Any] = Field(default_factory=dict)`, None is not directly assignable.
    # If args is missing, default_factory is used. If args is present and None, it depends on Optional.
    # Current ToolAction: args: Dict[str, Any] = Field(default_factory=dict, ...)
    # This means 'args' key can be missing (then defaults to {}), or it can be a dict.
    # If it's explicitly set to None in the input data, Pydantic might raise error if not Dict | None
    data = {"name": "TestTool", "args": None}
    with pytest.raises(ValidationError):
         ToolAction.parse_obj(data)

def test_tool_action_missing_name():
    data = {"args": {"param1": "value1"}}
    with pytest.raises(ValidationError):
        ToolAction.parse_obj(data)

def test_tool_action_name_not_string():
    data = {"name": 123, "args": {}}
    with pytest.raises(ValidationError):
        ToolAction.parse_obj(data)

def test_tool_action_args_not_dict():
    data = {"name": "TestTool", "args": "not_a_dict"}
    with pytest.raises(ValidationError):
        ToolAction.parse_obj(data)

def test_tool_action_list_in_args():
    data = {"name": "ListTool", "args": {"items": [1, "two", 3.0, True]}}
    action = ToolAction.parse_obj(data)
    assert action.name == "ListTool"
    assert action.args == {"items": [1, "two", 3.0, True]}
