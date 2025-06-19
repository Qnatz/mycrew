# mycrews/qrew/utils/sanitizers.py
from typing import Dict, Any, List # Add List for type hint

def sanitize_metadata(meta: dict) -> dict:
    """
    Ensure all metadata values are of type str, int, float, or bool for ChromaDB.
    - Lists become comma-separated strings (empty lists become "none").
    - None values are dropped.
    - Other types are stringified.
    """
    clean = {}
    for k, v in meta.items(): # Changed key, value to k, v to match provided snippet
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif isinstance(v, list):
            clean[k] = ", ".join(map(str, v)) if v else "none"
        elif v is None:
            continue
        else:
            clean[k] = str(v)
    return clean

# Appending the new sanitize_tool_args function
def sanitize_tool_args(args: Dict[str, Any], schema: Dict[str, type]) -> Dict[str, Any]:
    """
    Ensure args match a basic schema dict: e.g., {"param_name": str, "count": int}.
    Raises TypeError on type mismatch or if a required key from schema is missing.
    Only validates types specified in the schema; extra args are passed through.
    """
    clean_args = args.copy()

    for key, expected_type in schema.items():
        if key in args:
            val = args[key]
            if not isinstance(val, expected_type):
                raise TypeError(
                    f"Argument '{key}' expected type {expected_type.__name__}, "
                    f"but got type {type(val).__name__} with value '{val}'."
                )
        else:
            raise TypeError(f"Required argument '{key}' of type {expected_type.__name__} is missing.")

    return clean_args
