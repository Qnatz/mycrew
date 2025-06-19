from pydantic import BaseModel, Field
from typing import Dict, Any, List

class ToolAction(BaseModel):
    name: str = Field(..., description="Must match a key in TOOL_REGISTRY")
    args: Dict[str, Any] = Field(default_factory=dict, description="Flat JSON object, primitives or lists of primitives only")
