# mycrews/qrew/models/common_outputs.py
from pydantic import BaseModel, Field
from typing import List, Optional # Using List from typing for specificity

class TaskOutput(BaseModel):
    """
    A standard structure for representing the output of many agent tasks.
    """
    summary: str = Field(..., description="A concise summary of the task's findings or results.")
    action_items: Optional[List[str]] = Field(default=None, description="A list of actionable items derived from the task, if any.")
    confidence: Optional[float] = Field(default=None, description="A score indicating the agent's confidence in its output, typically between 0.0 and 1.0.")
    raw_output: Optional[str] = Field(default=None, description="The raw text output from the LLM, for debugging or if parsing fails.")
    error_message: Optional[str] = Field(default=None, description="Any error message encountered during task execution or output parsing.")

    # You could add a model validator or root validator here if needed, e.g.,
    # to ensure confidence is within a certain range, or that either summary or error_message is present.
    # from pydantic import root_validator
    # @root_validator
    # def check_confidence_range(cls, values):
    #     confidence = values.get('confidence')
    #     if confidence is not None and not (0.0 <= confidence <= 1.0):
    #         raise ValueError('Confidence score must be between 0.0 and 1.0')
    #     return values

class StructuredCodeOutput(BaseModel): # Corrected class name casing
    """
    Represents a task output that primarily consists of a code block and explanation.
    """
    code_block: str = Field(..., description="The generated or analyzed block of code.")
    language: Optional[str] = Field(default=None, description="The programming language of the code block (e.g., 'python', 'javascript').")
    explanation: str = Field(..., description="An explanation of the code block, its purpose, or analysis findings.")
    dependencies: Optional[List[str]] = Field(default_factory=list, description="A list of dependencies or libraries required/identified in the code.")
    raw_output: Optional[str] = Field(default=None, description="The raw text output from the LLM.")
    error_message: Optional[str] = Field(default=None, description="Any error message encountered.")

# Add other common output models here as they are identified.
# For example, an output model for API definitions, file lists, etc.
