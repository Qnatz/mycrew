# REMAINING IMPORTS IF ANY (e.g. for other global crews or tools not moved)
# For this refactoring, most direct operational imports are moved.
# We might still need json for the __main__ block's print output, so let's keep it.
import json

# New import for the refactored workflow
from .workflows.idea_to_architecture_flow import run_idea_to_architecture_workflow

# Custom tools - If these were truly global and used by other parts of main_workflow.py
# (not just the moved function), their instantiation would remain here.
# For now, they were moved as they seemed coupled with the agents in the moved flow.
# from .tools.custom_agent_tools import CustomDelegateWorkTool, CustomAskQuestionTool
# custom_delegate_tool = CustomDelegateWorkTool()
# custom_ask_tool = CustomAskQuestionTool()


# The `qrew_main_crew` and `all_qrew_agents` have been moved to the new workflow file
# as they are primarily used by/for that specific workflow's delegation tasks.
# If there were other crews or a truly global `qrew_main_crew` for multiple distinct workflows,
# its definition might remain here.

if __name__ == "__main__":
    print("## Starting QREW Main Entry Point (which will call Idea to Architecture Workflow)")

    initial_user_idea_for_taskmaster = "Develop a market-leading application for interactive pet training that is fun and engaging. It should include video streaming, progress tracking, and social sharing features. We want it to be scalable and secure."
    simulated_taskmaster_output_as_user_idea = f"Project Brief from TaskMaster: The user wants an interactive pet training app. Key features: video, progress tracking, social sharing. Goal: fun, engaging, scalable, secure. Details: {initial_user_idea_for_taskmaster}"

    stakeholder_feedback_notes = "User retention is key. Gamification might be important. Mobile-first approach preferred."
    market_research_summary = "Competitors X and Y lack real-time interaction. Users want personalized training plans."
    project_constraints_for_workflow = "Team has strong Python and React skills. Initial deployment on AWS. Budget for external services is moderate."
    project_technical_vision_for_workflow = "A modular microservices architecture is preferred for scalability. Prioritize user data privacy."

    inputs_for_workflow = {
        "user_idea": simulated_taskmaster_output_as_user_idea,
        "stakeholder_feedback": stakeholder_feedback_notes,
        "market_research_data": market_research_summary,
        "constraints": project_constraints_for_workflow,
        "technical_vision": project_technical_vision_for_workflow
    }

    final_result = run_idea_to_architecture_workflow(inputs_for_workflow)

    print("\n\n########################")
    print("## Workflow Execution Result (from main_workflow.py direct run):")
    print("########################\n")
    if final_result and isinstance(final_result, dict):
        print("Final output from the Idea-to-Architecture crew (dictionary):")
        try:
            print(json.dumps(final_result, indent=2))
        except Exception as e:
            print(f"Could not JSON dump final_result (dict), printing as is: {final_result}")
    elif final_result: # It's not None and not a dict
        print("Final output from the Idea-to-Architecture crew (unexpected type):")
        print(str(final_result))
    else:
        print("Idea-to-Architecture Crew produced no output or an error occurred.")
