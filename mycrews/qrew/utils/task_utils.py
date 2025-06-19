# mycrews/qrew/utils/task_utils.py
from typing import List, Any, TypeVar
from crewai import Task, Agent, Crew # Make sure Crew is imported if tasks are added to a crew instance

# Define a generic type for items in the list to be sharded
T = TypeVar('T')

def shard_and_enqueue_tasks(
    crew: Crew,
    target_agent: Agent,
    items_to_process: List[T],
    base_task_description: str, # e.g., "Process the following log entry: {item}"
                                # or "Analyze this code file: {item_path}"
    expected_output_description: str, # Generic expected output for each sharded task
    chunk_size: int = 5,
    item_placeholder: str = "{item}" # Placeholder in description for the item
) -> List[Task]:
    """
    Shards a list of items into smaller chunks and creates a task for each chunk.
    The created tasks are returned and can be added to a crew by the caller.

    Args:
        crew: The Crew instance (used here for context, but tasks are returned, not directly added).
        target_agent: The Agent assigned to process each chunk.
        items_to_process: The list of items to be sharded and processed.
        base_task_description: A template string for the task description.
                               It should include a placeholder (default: {item})
                               that will be replaced by the item or chunk.
                               If chunk_size > 1, placeholder will be the list of items in chunk.
        expected_output_description: A string describing the expected output for each sharded task.
        chunk_size: The number of items to include in each task chunk.
                    If chunk_size is 1, each item gets its own task.
                    If chunk_size > 1, each task gets a list of items.
        item_placeholder: The placeholder string in base_task_description to replace.

    Returns:
        A list of the Task objects created.
    """
    created_tasks: List[Task] = []

    if not items_to_process:
        print("[TaskUtils] No items provided to shard_and_enqueue_tasks. No tasks created.")
        return created_tasks

    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")

    for i in range(0, len(items_to_process), chunk_size):
        chunk = items_to_process[i:i + chunk_size]

        # Prepare the description for this specific task/chunk
        if chunk_size == 1:
            # If chunk_size is 1, the item itself is the focus
            current_item_representation = str(chunk[0]) # Ensure it's a string for interpolation
            task_description = base_task_description.replace(item_placeholder, current_item_representation)
        else:
            # If chunk_size > 1, the placeholder refers to the list of items in the chunk
            chunk_representation = ", ".join(map(str, chunk))
            task_description = base_task_description.replace(item_placeholder, f"the following items: [{chunk_representation}]")

        new_task = Task(
            description=task_description,
            agent=target_agent,
            expected_output=expected_output_description
        )

        created_tasks.append(new_task)

        print(f"[TaskUtils] Created task for agent '{target_agent.role}' with description: '{task_description[:100]}...'")

    return created_tasks

# Example Usage (conceptual, would be in agent or workflow logic):
#
# from crewai import Crew, Agent
# from mycrews.qrew.utils.task_utils import shard_and_enqueue_tasks
#
# # Assume 'my_crew' is an initialized Crew object
# # Assume 'log_processing_agent' is an initialized Agent object
#
# my_crew = Crew(agents=[], tasks=[], verbose=True) # Simplified
# log_processing_agent = Agent(role="Log Processor", goal="Process logs", backstory="...", tools=[], llm=None) # Simplified
#
# log_file_paths = ["path/to/log1.txt", "path/to/log2.txt", "path/to/log3.txt", ..., "path/to/log100.txt"]
#
# if log_file_paths:
#   sharded_log_tasks = shard_and_enqueue_tasks(
#       crew=my_crew, # Pass the crew instance
#       target_agent=log_processing_agent,
#       items_to_process=log_file_paths,
#       base_task_description="Analyze the log file at path: {item}. Identify critical errors and summarize findings.",
#       expected_output_description="A JSON object with 'summary', 'critical_errors' (list), and 'confidence'.",
#       chunk_size=1 # Process one log file per task
#   )
#   my_crew.tasks.extend(sharded_log_tasks) # Add the created tasks to the crew
#
# # Later... my_crew.kickoff()
