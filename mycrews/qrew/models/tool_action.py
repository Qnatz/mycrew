from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class ToolName(str, Enum):
    READ_FILE = "ReadFile"
    SEARCH_DIRECTORY = "SearchDirectory"
    RUN_COMMAND = "RunCommand"
    # Add other tool names as needed


class ToolAction(BaseModel):
    name: ToolName = Field(..., description="Name of the tool to invoke")
    arguments: Dict[str, Any] = Field(..., description="Arguments required by the tool")
    description: Optional[str] = Field(None, description="Optional human-readable description of the tool action")

    def __str__(self):
        return f"ToolAction(name={self.name}, arguments={self.arguments})"
