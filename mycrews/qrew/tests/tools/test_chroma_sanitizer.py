# mycrews/qrew/tests/tools/test_chroma_sanitizer.py
import pytest # Assuming pytest is the test runner
from mycrews.qrew.tools.chroma_sanitizer import sanitize_metadata

# Dummy class for testing stringification of other objects
class SomeCustomObj:
    def __init__(self, name="test_object"):
        self.name = name

    def __str__(self):
        return f"<CustomObject: {self.name}>"

def test_sanitize_metadata_basic_types():
    """Test that basic supported types (str, int, float, bool) are unchanged."""
    raw = {
        "string_val": "hello",
        "int_val": 123,
        "float_val": 45.67,
        "bool_true": True,
        "bool_false": False,
    }
    clean = sanitize_metadata(raw.copy()) # Use .copy() to avoid modifying original raw
    assert clean["string_val"] == "hello"
    assert clean["int_val"] == 123
    assert clean["float_val"] == 45.67
    assert clean["bool_true"] is True
    assert clean["bool_false"] is False
    assert len(clean) == 5

def test_sanitize_metadata_none_values():
    """Test that None values are dropped from the metadata."""
    raw = {
        "present_key": "value",
        "none_key": None,
        "another_key": 123
    }
    clean = sanitize_metadata(raw.copy())
    assert "present_key" in clean
    assert "none_key" not in clean
    assert "another_key" in clean
    assert len(clean) == 2

def test_sanitize_metadata_list_conversion():
    """Test list conversions: empty, single item, multiple items."""
    raw = {
        "empty_list": [],
        "single_item_list": ["taskmaster"],
        "multi_item_list": ["alpha", "beta", 123, True],
        "list_with_none": ["item1", None, "item3"] # Note: None within list becomes "None" string
    }
    clean = sanitize_metadata(raw.copy())
    assert clean["empty_list"] == "none"
    assert clean["single_item_list"] == "taskmaster"
    assert clean["multi_item_list"] == "alpha, beta, 123, True"
    assert clean["list_with_none"] == "item1, None, item3" # `map(str, ...)` converts None to "None"
    assert len(clean) == 4

def test_sanitize_metadata_other_object_types():
    """Test that other object types are stringified."""
    custom_obj_instance = SomeCustomObj(name="example")
    raw = {
        "custom_object": custom_obj_instance,
        "another_type": {"nested_dict": "should_be_string"}, # A dict itself is not a base type
        "set_type": {1, 2, 3} # A set is also not a base type
    }
    clean = sanitize_metadata(raw.copy())

    assert "custom_object" in clean
    assert isinstance(clean["custom_object"], str)
    assert clean["custom_object"] == str(custom_obj_instance) # Explicitly "<CustomObject: example>"

    assert "another_type" in clean
    assert isinstance(clean["another_type"], str)
    assert clean["another_type"] == str({"nested_dict": "should_be_string"})

    assert "set_type" in clean
    assert isinstance(clean["set_type"], str)
    assert clean["set_type"] == str({1, 2, 3}) # Order might vary for sets, but it will be stringified

    assert len(clean) == 3

def test_sanitize_metadata_from_issue():
    """Test case directly from the issue description to ensure compliance."""
    raw_from_issue = {
        "empty_list": [],
        "multi": ["taskmaster"], # Issue showed "taskmaster" but lists are comma separated
                                 # so if it's a list of one, it becomes just the string of that one item.
        "none": None,
        "num": 123,
        "obj": SomeCustomObj(), # Assuming SomeCustomObj is defined as in this test file
    }
    clean = sanitize_metadata(raw_from_issue.copy())

    assert clean["empty_list"] == "none"
    # For a list with a single string item, map(str, value) yields that string,
    # and ", ".join(["taskmaster"]) is just "taskmaster". This matches the issue's expectation.
    assert clean["multi"] == "taskmaster"
    assert "none" not in clean  # Key 'none' with value None should be dropped
    assert "num" in clean and clean["num"] == 123
    assert "obj" in clean and isinstance(clean["obj"], str)
    assert clean["obj"] == str(SomeCustomObj()) # Default name is "test_object"
    assert len(clean) == 4 # empty_list, multi, num, obj

def test_sanitize_metadata_mixed_values():
    """Test a mix of all conditions simultaneously."""
    raw = {
        "my_string": "text",
        "my_int": 99,
        "my_float": 3.14,
        "my_true_bool": True,
        "my_list_empty": [],
        "my_list_items": [1, "two", False, None],
        "my_none_val": None,
        "my_obj": SomeCustomObj("mixed_test"),
        "another_string": "more text"
    }
    clean = sanitize_metadata(raw.copy())

    assert clean["my_string"] == "text"
    assert clean["my_int"] == 99
    assert clean["my_float"] == 3.14
    assert clean["my_true_bool"] is True
    assert clean["my_list_empty"] == "none"
    assert clean["my_list_items"] == "1, two, False, None"
    assert "my_none_val" not in clean
    assert isinstance(clean["my_obj"], str)
    assert clean["my_obj"] == "<CustomObject: mixed_test>"
    assert clean["another_string"] == "more text"
    assert len(clean) == 8 # 9 original keys - 1 (my_none_val)
