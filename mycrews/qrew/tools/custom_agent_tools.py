import logging
from typing import Optional, Dict, Any, List, Type
from pydantic import BaseModel, Field # Use Pydantic V2

# CrewAI specific imports - adjust paths if these are not standard crewai locations
# For this subtask, we'll assume these are the correct import paths.
# If these cause issues later, they might need to be from `crewai.agent`, `crewai.task`, etc.
from crewai.agent import Agent
from crewai.task import Task
from crewai.tools.base_tool import BaseTool
from crewai.utilities.constants import NOT_SPECIFIED
from crewai.utilities.string_utils import interpolate_only
# from crewai.i18n import I18N # I18N might be needed for Task creation if agent doesn't have it

logger = logging.getLogger(__name__)

# Schemas
class CustomDelegateWorkToolSchema(BaseModel):
    """Input for CustomDelegateWorkTool."""
    task: str = Field(..., description="The task to delegate. Can contain placeholders if 'inputs' are provided.")
    coworker: str = Field(..., description="The specific agent role to delegate the work to.")
    context_str: Optional[str] = Field(default=None, description="Optional additional context or information to provide to the agent for the task.")
    inputs: Optional[Dict[str, Any]] = Field(default=None, description="Optional dictionary of inputs to interpolate into the task description.")
    prerequisite_task_ids: Optional[List[str]] = Field(default=None, description="Optional list of task IDs from previously executed tasks. Their outputs will be used as context.")

class CustomAskQuestionToolSchema(BaseModel):
    """Input for CustomAskQuestionTool."""
    question: str = Field(..., description="The question to ask. Can contain placeholders if 'inputs' are provided.")
    coworker: str = Field(..., description="The specific agent role to ask the question to.")
    context_str: Optional[str] = Field(default=None, description="Optional additional context or information to provide to the agent for the question.")
    inputs: Optional[Dict[str, Any]] = Field(default=None, description="Optional dictionary of inputs to interpolate into the question string.")
    prerequisite_task_ids: Optional[List[str]] = Field(default=None, description="Optional list of task IDs from previously executed tasks. Their outputs will be used as context.")

# Tools
class CustomDelegateWorkTool(BaseTool):
    context: Any = Field(default=None, exclude=True, description="Context injected by the agent execution environment.")
    name: str = "Delegate Work to Coworker (Custom)"
    description: str = "A custom tool to delegate a specific task to a designated coworker agent, allowing for input interpolation and prerequisite task context."
    args_schema: Type[BaseModel] = CustomDelegateWorkToolSchema
    # context will be injected by the agent using the tool if properly set up
    # agents: List[Agent] = Field(default_factory=list, description="List of agents in the crew available for delegation.")
    # crew_tasks: List[Task] = Field(default_factory=list, description="List of all tasks executed so far in the crew.")

    def _sanitize_agent_name(self, name: str) -> str:
        if not name:
            return ""
        # Normalize all whitespace (including newlines) to single spaces
        normalized = " ".join(name.split())
        # Remove quotes and convert to lowercase
        return normalized.replace('"', "").casefold()

    def _run(
        self,
        task: str, # This is the task description for the delegatee
        coworker: str,
        context_str: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        prerequisite_task_ids: Optional[List[str]] = None
    ) -> str:
        if not self.context or not hasattr(self.context, 'crew') or not self.context.crew:
            logger.error("Tool is not properly initialized with crew context. Cannot access agents or task history.")
            return "Error: Tool is not properly initialized with crew context. Cannot access agents or task history."

        # Ensure crew_agents and crew_tasks_history are available
        crew_agents = getattr(self.context.crew, 'agents', [])
        crew_tasks_history = getattr(self.context.crew, 'tasks', [])

        # 1. Agent Selection
        sanitized_coworker_name = self._sanitize_agent_name(coworker)
        delegatee_agent: Optional[Agent] = None
        for agent_in_crew in crew_agents:
            if self._sanitize_agent_name(agent_in_crew.role) == sanitized_coworker_name:
                delegatee_agent = agent_in_crew
                break

        if not delegatee_agent:
            available_roles = ", ".join([ag.role for ag in crew_agents])
            logger.warning(f"Coworker agent '{coworker}' (sanitized: '{sanitized_coworker_name}') not found. Available: {available_roles}")
            return f"Error: Coworker agent '{coworker}' not found. Available agents: {available_roles}"

        # 2. Input Interpolation
        final_task_description = task
        if inputs:
            try:
                final_task_description = interpolate_only(task, inputs)
            except Exception as e:
                logger.error(f"Error interpolating inputs into task description: {e}")
                return f"Error during input interpolation: {e}"

        # 3. Context Building from Prerequisites
        delegated_task_context_objects: List[Task] = []
        if prerequisite_task_ids and crew_tasks_history:
            task_id_map = {str(t.id): t for t in crew_tasks_history if hasattr(t, 'id')}
            for task_id in prerequisite_task_ids:
                if task_id in task_id_map:
                    delegated_task_context_objects.append(task_id_map[task_id])
                else:
                    logger.warning(f"Prerequisite task ID '{task_id}' not found in crew's task history. Skipping.")

        final_task_context = None
        if delegated_task_context_objects: # If it's a non-empty list
            final_task_context = delegated_task_context_objects
        elif prerequisite_task_ids is not None: # If keys were provided but none were found (empty list)
            final_task_context = []
        # Else (prerequisite_task_ids was None), final_task_context remains None (which is default for Task.context)

        # 4. Task Creation
        try:
            # Ensure delegatee_agent has i18n initialized, if not, provide a default from the tool's own context if available
            # For simplicity, we assume the agent has i18n. A more robust solution might involve passing i18n explicitly or having a default.
            # agent_i18n = getattr(delegatee_agent, 'i18n', self.context.i18n if self.context and hasattr(self.context, 'i18n') else I18N())
            # For now, let's assume Task will handle i18n if agent has it or defaults.

            new_task_for_delegatee = Task(
                description=final_task_description,
                agent=delegatee_agent,
                expected_output="Actionable results based on the delegated task description and provided context.", # Generic, can be improved
                context=final_task_context,
                i18n=delegatee_agent.i18n # Explicitly pass agent's i18n
            )
        except Exception as e:
            logger.error(f"Error creating new task for delegatee: {e}")
            return f"Error creating task for delegation: {e}"

        # 5. Execution
        logger.info(f"Delegating task '{new_task_for_delegatee.description}' to agent '{delegatee_agent.role}'. Context string: '{context_str}'. Prerequisite tasks used for context: {[str(t.id) for t in delegated_task_context_objects if hasattr(t, 'id')]}.")
        try:
            result = delegatee_agent.execute_task(
                task=new_task_for_delegatee,
                context=context_str
            )
            return result
        except Exception as e:
            logger.error(f"Error during delegated task execution by '{delegatee_agent.role}': {e}")
            return f"Error during execution by '{delegatee_agent.role}': {e}"

class CustomAskQuestionTool(BaseTool):
    context: Any = Field(default=None, exclude=True, description="Context injected by the agent execution environment.")
    name: str = "Ask Question to Coworker (Custom)"
    description: str = "A custom tool to ask a specific question to a designated coworker agent, allowing for input interpolation and prerequisite task context."
    args_schema: Type[BaseModel] = CustomAskQuestionToolSchema
    # context will be injected by the agent using the tool
    # agents: List[Agent] = Field(default_factory=list, description="List of agents in the crew available for questioning.")
    # crew_tasks: List[Task] = Field(default_factory=list, description="List of all tasks executed so far in the crew.")

    def _sanitize_agent_name(self, name: str) -> str: # Added sanitize method
        if not name:
            return ""
        normalized = " ".join(name.split())
        return normalized.replace('"', "").casefold()

    def _run(
        self,
        question: str, # Renamed from task for clarity
        coworker: str,
        context_str: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        prerequisite_task_ids: Optional[List[str]] = None
    ) -> str:
        if not self.context or not hasattr(self.context, 'crew') or not self.context.crew:
            logger.error("Tool is not properly initialized with crew context. Cannot access agents or task history.")
            return "Error: Tool is not properly initialized with crew context. Cannot access agents or task history."

        crew_agents = getattr(self.context.crew, 'agents', [])
        crew_tasks_history = getattr(self.context.crew, 'tasks', [])

        # 1. Agent Selection
        sanitized_coworker_name = self._sanitize_agent_name(coworker)
        delegatee_agent: Optional[Agent] = None
        for agent_in_crew in crew_agents:
            if self._sanitize_agent_name(agent_in_crew.role) == sanitized_coworker_name:
                delegatee_agent = agent_in_crew
                break

        if not delegatee_agent:
            available_roles = ", ".join([ag.role for ag in crew_agents])
            logger.warning(f"Coworker agent '{coworker}' (sanitized: '{sanitized_coworker_name}') not found for question. Available: {available_roles}")
            return f"Error: Coworker agent '{coworker}' not found for question. Available agents: {available_roles}"

        # 2. Input Interpolation
        final_question_description = question # Renamed variable
        if inputs:
            try:
                final_question_description = interpolate_only(question, inputs)
            except Exception as e:
                logger.error(f"Error interpolating inputs into question: {e}")
                return f"Error during input interpolation for question: {e}"

        # 3. Context Building from Prerequisites
        delegated_task_context_objects: List[Task] = []
        if prerequisite_task_ids and crew_tasks_history:
            task_id_map = {str(t.id): t for t in crew_tasks_history if hasattr(t, 'id')}
            for task_id in prerequisite_task_ids:
                if task_id in task_id_map:
                    delegated_task_context_objects.append(task_id_map[task_id])
                else:
                    logger.warning(f"Prerequisite task ID '{task_id}' not found in crew's task history for question. Skipping.")

        final_task_context_for_asker = None # Default to None
        if delegated_task_context_objects: # If it's a non-empty list
            final_task_context_for_asker = delegated_task_context_objects
        elif prerequisite_task_ids is not None: # If keys were provided but none were found (empty list)
            final_task_context_for_asker = []
        # Else (prerequisite_task_ids was None), final_task_context_for_asker remains None

        # 4. Task Creation (representing the question)
        try:
            # agent_i18n = getattr(delegatee_agent, 'i18n', self.context.i18n if self.context and hasattr(self.context, 'i18n') else I18N())
            new_task_for_asker = Task( # Renamed variable
                description=final_question_description, # Use interpolated question
                agent=delegatee_agent,
                expected_output="Clear and concise answer to the question, based on provided context.", # Modified expected output
                context=final_task_context_for_asker,
                i18n=delegatee_agent.i18n # Explicitly pass agent's i18n
            )
        except Exception as e:
            logger.error(f"Error creating new task (for question) for delegatee: {e}")
            return f"Error creating task (for question) for delegation: {e}"

        # 5. Execution (asking the question)
        logger.info(f"Asking question '{new_task_for_asker.description}' to agent '{delegatee_agent.role}'. Context string: '{context_str}'. Prerequisite tasks used for context: {[str(t.id) for t in delegated_task_context_objects if hasattr(t, 'id')]}.")
        try:
            result = delegatee_agent.execute_task(
                task=new_task_for_asker, # Pass the new "question" task
                context=context_str
            )
            return result
        except Exception as e:
            logger.error(f"Error during question execution by '{delegatee_agent.role}': {e}")
            return f"Error during execution by '{delegatee_agent.role}': {e}"
