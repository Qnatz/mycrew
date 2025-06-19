# mycrews/qrew/workflows/sharding_demo_workflow.py
from crewai import Crew # Process import removed as it's not used in final example
from ..agents.demo_agents.content_analyzer_agent import content_analyzer_agent
from ..utils.task_utils import shard_and_enqueue_tasks
from ..utils.llm_factory import get_llm # For the crew's LLM if needed

def run_sharding_demo_workflow():
    print("## Running Sharding Demo Workflow ##")

    # 1. Define the list of items to process
    text_snippets = [
        "The quick brown fox jumps over the lazy dog.",
        "CrewAI is a framework for orchestrating role-playing autonomous AI agents.",
        "Large language models can perform a variety of text generation tasks.",
        "Sharding tasks can help manage context windows and distribute work.",
        "Pydantic models are useful for data validation and settings management.",
        "Asynchronous programming can improve application responsiveness.",
        "Unit testing is crucial for maintaining code quality.",
        "A well-defined architecture is key to scalable software.",
        "The TaskMaster agent delegates work to specialized agents.",
        "Sanitizing inputs and outputs enhances system robustness.",
        "API keys should be managed securely using environment variables.",
        "Continuous integration helps automate testing and deployment.",
        "Code documentation should be clear and up-to-date.",
        "Error handling is important for creating resilient applications.",
        "Memory management in agents can involve summarization and vector stores.",
        "The IdeaInterpreter agent translates concepts into technical requirements.",
        "Rate limiting protects APIs from abuse and overload.",
        "Context length errors occur when input exceeds the model's limit.",
        "Structured outputs make LLM responses more reliable.",
        "A modular design promotes maintainability and reusability."
    ] # 20 snippets

    # 2. Define the crew (can be simple for this demo)
    crew_llm = get_llm("default_crew_llm") # Get a default LLM for the crew manager

    demo_crew = Crew(
        agents=[content_analyzer_agent],
        tasks=[], # Tasks will be added via sharding utility
        verbose=2,
        manager_llm=crew_llm
        # process=Process.sequential # Not using Process here
    )

    # 3. Use shard_and_enqueue_tasks to create tasks
    sharded_summary_tasks = shard_and_enqueue_tasks(
        crew=demo_crew,
        target_agent=content_analyzer_agent,
        items_to_process=text_snippets,
        base_task_description="Summarize the key point of the following text snippet: {item}",
        expected_output_description="A concise one-sentence summary of the provided text snippet.",
        chunk_size=1
    )

    # 4. Add the created tasks to the crew
    if sharded_summary_tasks:
        demo_crew.tasks.extend(sharded_summary_tasks)
    else:
        print("No tasks were created by sharding utility.")
        return {"error": "No tasks created for the demo."}

    # 5. Kick off the crew
    print(f"Kicking off sharding demo crew with {len(demo_crew.tasks)} tasks...")
    results = demo_crew.kickoff()

    print("\n## Sharding Demo Workflow Completed ##")
    print("Results:")
    if isinstance(results, list):
        for idx, task_output in enumerate(results):
            print(f"  Output for Task {idx + 1}: {task_output}")
    else:
        print(f"  Combined Output: {results}")

    return results

if __name__ == "__main__":
    output = run_sharding_demo_workflow()
    # print("\nFinal aggregated output from main:", output)
