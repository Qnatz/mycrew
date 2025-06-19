import logging
from typing import Dict, Any, List, Union # Added Union
from mycrews.qrew.models import ToolAction
from mycrews.qrew.tool_registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)

def sanitize_args(args: Dict[str, Any]) -> Dict[str, Any]:
    clean = {}
    if not isinstance(args, dict):
        logger.warning(f"sanitize_args received non-dict input: {type(args)}. Returning empty dict.")
        return clean

    for k, v in args.items():
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif isinstance(v, list):
            clean[k] = [item for item in v if isinstance(item, (str, int, float, bool))]
        else:
            logger.debug(f"Argument '{k}' with value '{v}' of type {type(v)} is being converted to string.")
            clean[k] = str(v)
    return clean

def dispatch_tool(action: ToolAction) -> Union[Any, Dict[str, str]]: # Return type updated
    # 1) Validate tool exists
    if not isinstance(action, ToolAction):
        error_msg = "Invalid action object provided to dispatch_tool."
        logger.error(error_msg)
        return {"error": error_msg}

    if action.name not in TOOL_REGISTRY:
        error_msg = f"Tool '{action.name}' not registered."
        logger.error(error_msg)
        return {"error": error_msg}

    tool = TOOL_REGISTRY[action.name]

    # 2) Sanitize args
    safe_args = sanitize_args(action.args)

    # 3) Execute tool
    logger.info(f"Dispatching tool '{action.name}' with sanitized args: {safe_args}")
    try:
        result = tool.run(**safe_args)
        return result
    except Exception as e:
        error_msg = f"Tool dispatch failed for {action.name} with args {safe_args}: {e}"
        logger.error(error_msg, exc_info=True) # exc_info=True will log the traceback
        return {"error": str(e)} # Return structured error as per issue
