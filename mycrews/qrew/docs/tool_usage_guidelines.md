# Tool Usage Guidelines for QREW Agents

This document outlines the standardized a_pproach for defining, registering, and invoking tools within the QREW framework. Adhering to these guidelines ensures robust and error-free tool interactions by agents.

## Core Components

1.  **`ToolAction` Pydantic Model (`mycrews.qrew.models.ToolAction`)**:
    All tool invocations requested by an LLM must conform to this Pydantic model.

    ```python
    from pydantic import BaseModel, Field
    from typing import Dict, Any, List

    class ToolAction(BaseModel):
        name: str = Field(..., description="Must match a key in TOOL_REGISTRY")
        args: Dict[str, Any] = Field(default_factory=dict, description="Flat JSON object, primitives or lists of primitives only")
    ```

    *   `name`: The exact string name of the tool as registered in the `TOOL_REGISTRY`.
    *   `args`: A dictionary where keys are argument names and values are primitives (string, integer, float, boolean) or lists of such primitives.

2.  **`TOOL_REGISTRY` (`mycrews.qrew.tool_registry.TOOL_REGISTRY`)**:
    A centralized dictionary where all available tool instances are registered.
    *   **Key**: The unique string name of the tool (e.g., `"File Writer Tool"`).
    *   **Value**: The actual tool instance.
    Tools are primarily defined and instantiated in `mycrews.qrew.tools.inbuilt_tools.py` and then collected into the `TOOL_REGISTRY` in `mycrews.qrew.tool_registry.py`.

3.  **`sanitize_args` function (`mycrews.qrew.utils.tool_dispatcher.sanitize_args`)**:
    This utility function processes the `args` dictionary from a `ToolAction`.
    *   It ensures that all argument values are primitives or lists of primitives.
    *   If an argument value is not one of these types (e.g., a complex object or a nested dictionary), it will be converted to its string representation (`str(value)`). This is to prevent type errors when passing arguments to tools that might not expect complex objects directly via the generalized dispatch mechanism.
    *   Agents should strive to provide already-sanitized arguments, but this function acts as a safeguard.

4.  **`dispatch_tool` function (`mycrews.qrew.utils.tool_dispatcher.dispatch_tool`)**:
    This is the **only** function that should be used to execute a tool based on an agent's request.
    *   It takes a `ToolAction` object as input.
    *   It validates that the tool name exists in `TOOL_REGISTRY`.
    *   It calls `sanitize_args` on the `action.args`.
    *   It executes the tool's `.run(**safe_args)` method.
    *   It handles errors gracefully, logging them and returning a structured error dictionary: `{"error": "description of error"}`.

## Agent Development Guidelines

### 1. LLM Output for Tool Calls

When an agent's LLM decides to use a tool, its raw output **must** be a JSON string that can be parsed into the `ToolAction` model.

**Example LLM JSON Output:**

```json
{
    "name": "File Writer Tool",
    "args": {
        "file_path": "logs/qrew_agent_log.txt",
        "text": "Agent successfully completed its task."
    }
}
```

Or, for a tool with no arguments:

```json
{
    "name": "Environment Check Tool",
    "args": {}
}
```

### 2. Prompting the LLM

The agent's system prompt or task-specific instructions must clearly guide the LLM to:
*   List the available tools by their registered names (from `TOOL_REGISTRY`).
*   Specify the expected `ToolAction` JSON schema.
*   Provide the argument structure for each available tool.
*   Instruct the LLM to use `"None"` as the `name` if it needs to ask for clarification instead of calling a specific tool (e.g., `{"name": "None", "args": {"clarification_needed": "Which file should I write to?"}}`).

(Refer to `mycrews/qrew/examples/agent_tool_processing_example.py` for an example of such prompt guidance).

### 3. Processing LLM Output in Agent Logic

The agent's code that handles the LLM's response must:
1.  Attempt to parse the LLM's string output into a `ToolAction` object (e.g., using `ToolAction.parse_obj(json.loads(llm_output_str))`).
2.  Handle potential `json.JSONDecodeError` (if the output isn't valid JSON) and `pydantic.ValidationError` (if the JSON doesn't match the `ToolAction` schema). Log these errors or ask the LLM to retry/reformat.
3.  If parsing is successful:
    *   Check if `action.name` is `"None"`. If so, log a warning and handle the clarification request (e.g., by asking the user or another LLM).
    *   If `action.name` is a valid tool, call `dispatch_tool(action)`.
    *   Handle the result from `dispatch_tool`, which will either be the tool's execution result or an error dictionary.

(Refer to `mycrews/qrew/examples/agent_tool_processing_example.py` for an example of this processing logic).

## CI Checks (Conceptual)

To enforce these guidelines and maintain system integrity, the following CI checks should be implemented:

1.  **Static Analysis / Linter Rule**:
    *   **Purpose**: To detect and flag direct tool invocations that bypass the `dispatch_tool` mechanism and improper tool instantiations.
    *   **Checks**:
        *   Flag any calls to `some_tool_instance.run(...)` or `some_tool_instance._run(...)` that originate from agent logic files (outside of `dispatch_tool` itself or test mocks). Abstract Syntax Tree (AST) parsing can identify such call patterns.
        *   Flag direct instantiation of tool classes (e.g., `MyToolClass()`) outside of `mycrews/qrew/tools/inbuilt_tools.py`. This encourages centralization of tool definitions.
    *   **Tools**: Custom Flake8 plugin, Pylint custom checker, or a dedicated script using `ast` module.

2.  **Pre-commit Hook**:
    *   **Purpose**: To run the static analysis checks automatically before code is committed.
    *   **Implementation**: Use the `pre-commit` framework and configure it to run the custom linter/static analysis script.

3.  **Unit Test Coverage**:
    *   **Purpose**: Ensure that the core tool dispatch logic (`tool_dispatcher.py`, `models.py`) and any agent-side parsing logic are thoroughly tested.
    *   **Requirement**: Maintain high unit test coverage (e.g., >90%) for these critical components. CI should fail if coverage drops below the threshold.

By implementing these components and adhering to the guidelines, the QREW framework will achieve more reliable and standardized tool usage across all agents.
