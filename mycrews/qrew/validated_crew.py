from typing import Optional, Any, List
import logging

from crewai import Crew, Agent, Task, Process # Added Process
# from crewai.enums import TaskProcess # Removed
# from crewai.shared import SharedContext # Removed
# from crewai.utilities.task_output_adapter import TaskOutputAdapter # Removed

# from crewai.utilities.logger import logger as crewai_logger # Using standard logging for this example

# Configure a logger for this module
log = logging.getLogger(__name__)
# Example: If you want to see these logs, configure basicConfig once in your main entry point
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')


class QualityGateFailedError(Exception):
    """Custom exception for when a task fails the quality gate after all retries."""
    def __init__(self, task_description: str, messages: List[str]):
        self.task_description = task_description
        self.messages = messages
        super().__init__(f"Task '{task_description}' failed quality gate after all retries. Issues: {'; '.join(messages)}")


class ValidatedCrew(Crew):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._keyword_check_enabled: bool = True
        self._custom_validators: List[callable] = []
        # Removed warning checks for Task.DEFAULT_SCHEMA["input"]


    def configure_quality_gate(
        self,
        keyword_check: bool = True,
        custom_validators: Optional[List[callable]] = None
    ):
        """Configures the quality gate settings for this crew."""
        self._keyword_check_enabled = keyword_check
        self._custom_validators = custom_validators if custom_validators is not None else []
        log.info(
            f"ValidatedCrew quality gate configured for crew (verbose={self.verbose}): " # Accessing self.verbose
            f"Keyword Check={'Enabled' if self._keyword_check_enabled else 'Disabled'}, "
            f"Custom Validators={[v.__name__ for v in self._custom_validators] if self._custom_validators else 'None'}"
        )

    def delegate_task(self, task: Task, agent: Optional[Agent] = None, context: Optional[str] = None) -> Any:
        """
        Delegates a task to an agent, applying quality gate checks and retries.
        """
        if not isinstance(task, Task):
            # Using type(task).__name__ for more informative error
            raise ValueError(f"ValidatedCrew.delegate_task expects a Task object, got {type(task).__name__}.")

        target_agent = agent if agent else task.agent
        if not target_agent:
            raise ValueError(f"No agent specified for task: {task.description}. "
                             "Either pass an agent parameter or ensure task.agent is set.")
        if not isinstance(target_agent, Agent):
            raise ValueError(f"Invalid agent provided for task '{task.description}'. Expected Agent instance, got {type(target_agent).__name__}.")

        # Get maxRetries from task or Task.DEFAULT_SCHEMA, ensuring it's an int >= 0
        max_retries_from_task = getattr(task, 'maxRetries', None)
        if isinstance(max_retries_from_task, int) and max_retries_from_task >= 0:
            max_retries = max_retries_from_task
        else:
            schema_max_retries = Task.DEFAULT_SCHEMA.get('maxRetries', {}).get('default', 1) # type: ignore
            if isinstance(schema_max_retries, int) and schema_max_retries >= 0:
                max_retries = schema_max_retries
            else:
                log.warning(f"Invalid maxRetries value in Task.DEFAULT_SCHEMA: {schema_max_retries}. Defaulting to 1.")
                max_retries = 1

        if max_retries_from_task is not None and max_retries_from_task != max_retries:
            log.info(f"Task '{task.description}' maxRetries ({max_retries_from_task}) is overridden by schema default or invalid. Using: {max_retries}.")


        feedback_messages_for_retry: List[str] = [] # Stores feedback from the most recent failed attempt

        for attempt in range(max_retries + 1):
            log.info(f"Executing task '{task.description}' with agent '{target_agent.role}'. Attempt {attempt + 1}/{max_retries + 1}.")

            current_execution_context = context # Original context for the first attempt

            if attempt > 0: # This is a retry
                feedback_string = ". ".join(feedback_messages_for_retry)
                if context: # If there was an original context
                    current_execution_context = f"{context}\n\nPREVIOUS ATTEMPT FEEDBACK:\n{feedback_string}"
                else:
                    current_execution_context = f"PREVIOUS ATTEMPT FEEDBACK:\n{feedback_string}"
                log.info(f"Retrying task '{task.description}' with feedback in context: {feedback_string}")

            try:
                # Pass current_execution_context to the agent
                result = target_agent.execute_task(task=task, context=current_execution_context)
            except Exception as e:
                log.error(f"Exception during task execution by '{target_agent.role}' for task '{task.description}' on attempt {attempt + 1}: {e}", exc_info=True)
                feedback_messages_for_retry = [f"Execution error on attempt {attempt + 1}: {str(e)}"]
                if attempt < max_retries:
                    log.info(f"Retrying task '{task.description}' due to execution error.")
                    continue
                else:
                    raise QualityGateFailedError(task.description, feedback_messages_for_retry) from e

            passed_quality_gate = True
            current_attempt_feedback_messages: List[str] = [] # Feedback for *this* attempt's QG failures

            # --- Start of added debug logging ---
            log.debug(f"QG PRE-CHECK FOR TASK: '{task.description[:100]}...'")
            log.debug(f"Task object type: {type(task)}")
            try:
                task_vars = [attr for attr in dir(task) if not attr.startswith('_')]
                log.debug(f"Task attributes: {task_vars}")
            except Exception as e:
                log.debug(f"Could not get dir(task): {e}")

            has_sc_attr = hasattr(task, 'successCriteria')
            log.debug(f"Task has 'successCriteria' attribute: {has_sc_attr}")

            if has_sc_attr:
                try:
                    sc_value = task.successCriteria
                    log.debug(f"Value of task.successCriteria: {sc_value}")
                    log.debug(f"Type of task.successCriteria: {type(sc_value)}")
                except Exception as e:
                    log.debug(f"Error accessing task.successCriteria directly: {e}")
            # --- End of added debug logging ---

            # 1. Keyword Check
            criteria_to_check = getattr(task, 'successCriteria', []) # Use getattr with default empty list

            if self._keyword_check_enabled and criteria_to_check: # Now checks criteria_to_check
                result_str_for_keyword_check = str(result.get("output", result) if isinstance(result, dict) else result)

                # Handle empty output vs empty criteria explicitly first
                if not result_str_for_keyword_check and not criteria_to_check:
                    # This case means: output is empty, and no criteria were set. This is a PASS for keyword check.
                    pass
                elif not result_str_for_keyword_check and criteria_to_check:
                     # Output is empty, but criteria were expected. This is a FAIL.
                     passed_quality_gate = False
                     current_attempt_feedback_messages.append("Output was empty, but successCriteria were expected.")
                     log.info(f"Task '{task.description}' failed keyword check: Output empty, criteria present.")
                else: # Output is not empty, and criteria might be present
                    for criterion in criteria_to_check: # Iterate using criteria_to_check
                        if criterion.lower() not in result_str_for_keyword_check.lower():
                            passed_quality_gate = False
                            current_attempt_feedback_messages.append(f"Keyword criterion not met: '{criterion}'")
                            log.info(f"Task '{task.description}' failed keyword check: '{criterion}' not in output.")

            if self._custom_validators:
                for validator in self._custom_validators:
                    try:
                        if not validator(task, result):
                            passed_quality_gate = False
                            # Assuming validator logs its own failure reason if it wants to be specific
                            current_attempt_feedback_messages.append(f"Custom validator '{validator.__name__}' failed.")
                            log.info(f"Task '{task.description}' failed custom validator '{validator.__name__}'.")
                    except Exception as e:
                        passed_quality_gate = False
                        current_attempt_feedback_messages.append(f"Error in custom validator '{validator.__name__}': {str(e)}")
                        log.error(f"Task '{task.description}': Error executing custom validator '{validator.__name__}': {e}", exc_info=True)

            if passed_quality_gate:
                log.info(f"Task '{task.description}' passed quality gate on attempt {attempt + 1}.")
                return result # Successfully executed and passed QG

            # If not passed, prepare feedback for next attempt or final failure
            feedback_messages_for_retry = current_attempt_feedback_messages
            if attempt < max_retries:
                log.info(f"Task '{task.description}' failed quality gate. Feedback: '{'. '.join(feedback_messages_for_retry)}'. Retrying ({attempt + 1}/{max_retries} retries used)...")
            else: # All retries used up
                log.error(f"Task '{task.description}' failed quality gate after {max_retries + 1} attempts. Final issues: {'; '.join(feedback_messages_for_retry)}")
                raise QualityGateFailedError(task.description, feedback_messages_for_retry)

        # Fallback, should ideally not be reached if max_retries >= 0, as loop runs max_retries + 1 times
        # This implies an issue if reached, or if max_retries was < 0 initially (though that's guarded).
        final_error_messages = feedback_messages_for_retry if feedback_messages_for_retry else ["Unknown state after all retry attempts."]
        raise QualityGateFailedError(task.description, final_error_messages)

    def kickoff(self, inputs: Optional[dict] = None) -> Any:
        """
        Kicks off the crew's tasks, ensuring each task goes through the
        quality gate defined in `delegate_task`.
        This override is for sequential processing.
        """
        log.info(f"ValidatedCrew kickoff initiated. Inputs: {inputs if inputs else 'None'}")

        if self.process == Process.sequential: # Changed condition
            if not self.tasks:
                log.warning("ValidatedCrew kickoff: No tasks to execute.")
                return "No tasks to execute."

            task_outputs = [] # Store all task outputs

            for task in self.tasks:
                if not task.agent:
                    # Try to assign a default agent from the crew if available and task has no agent
                    if len(self.agents) == 1: # Or some other logic to pick a default
                        task.agent = self.agents[0]
                        log.info(f"Task '{task.description}' has no agent. Assigned default agent '{task.agent.role}'.")
                    else:
                        raise ValueError(
                            f"Task '{task.description}' has no agent assigned and no single default agent could be determined for the crew."
                        )

                original_description = task.description # Store before potential interpolation
                if inputs:
                    try:
                        # Ensure description is a string before calling format
                        if isinstance(task.description, str):
                            task.description = task.description.format(**inputs)
                            log.info(f"Interpolated task '{original_description}' to '{task.description}' using kickoff inputs.")
                        else:
                            log.warning(f"Task '{original_description}' description is not a string. Skipping input interpolation.")
                    except KeyError as e:
                        log.warning(f"KeyError during input interpolation for task '{original_description}': {e}. Using original description.")
                        task.description = original_description # Revert if interpolation fails

                log.info(f"Executing task via delegate_task (from kickoff): {task.description}")
                # Use task.agent as it's now guaranteed to be set or error was raised
                task_result = self.delegate_task(task=task, agent=task.agent)

                log.info(f"Task '{task.description}' completed via kickoff. Result: {str(task_result)[:200]}...")
                task_outputs.append(task_result)

                # Restore original task description
                task.description = original_description


            # Return the output of the last task, similar to standard sequential kickoff
            return task_outputs[-1] if task_outputs else "No task outputs from kickoff."

        elif self.process == Process.hierarchical: # Changed condition
            if not self.manager_agent:
                raise ValueError("Manager agent not set for hierarchical process.")
            log.info(f"ValidatedCrew kickoff: Hierarchical process with manager agent '{self.manager_agent.role}'.")

            manager_task_description = "Coordinate and manage the defined tasks to achieve the crew's overall goal."
            if inputs: # Try to interpolate inputs into manager task description if they seem relevant
                try:
                    # A generic way to make inputs available, manager agent needs to know how to use them
                    manager_task_description = f"{manager_task_description} Initial inputs for the overall goal: {inputs}"
                except Exception: # Broad catch if inputs are not string-formattable easily
                    pass


            manager_task = Task(
                description=manager_task_description,
                agent=self.manager_agent,
                expected_output="The final result from the coordinated execution of all tasks."
            )
            # If the manager agent needs to know about the sub-tasks, they should be passed in the payload
            # or the manager agent's logic should be aware of `self.tasks` from the crew.
            # For now, we keep it simple; manager is expected to have its logic for task discovery or gets them via tools.
            return self.delegate_task(task=manager_task, agent=self.manager_agent)
        else:
            raise NotImplementedError(
                f"Process '{self.process}' not implemented in ValidatedCrew.kickoff."
            )
