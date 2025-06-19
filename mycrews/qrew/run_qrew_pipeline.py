# mycrews/qrew/run_qrew_pipeline.py
import json
import os
import time
from pathlib import Path

print(f"DEBUG: run_qrew_pipeline.py __file__: {__file__}")
# Use relative imports since utils and project_manager are in the same directory
from .utils import ErrorSummary
from .project_manager import get_or_create_project

# 1. Define Your Stages
STAGES = [
    "initial_analysis",
    "content_generation",
    "review_and_edit",
    "final_assembly"
]

# CHECKPOINT_FILE will be created in mycrews/qrew/
CHECKPOINT_FILE = Path(__file__).parent / ".qrew_checkpoint.json"
print(f"DEBUG: run_qrew_pipeline.py CHECKPOINT_FILE: {CHECKPOINT_FILE.resolve()}")

def load_progress():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE) as f:
                return json.load(f)
        except json.JSONDecodeError: # Handle empty or corrupted file
            return {"completed": {}, "results": {}}
    return {"completed": {}, "results": {}}

def save_progress(progress):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(progress, f, indent=2)

# Placeholder functions for actual stage work
def run_stage_initial_analysis(common_kwargs):
    print(f"Running initial analysis with project path: {common_kwargs.get('project_path')}")
    time.sleep(1) # Simulate work
    if common_kwargs.get("simulate_error_at_stage") == "initial_analysis":
        raise ValueError("Simulated error in initial_analysis")
    return {"analysis_summary": "Initial analysis complete.", "data_points": [1, 2, 3]}

def run_stage_content_generation(analysis_result, common_kwargs):
    print(f"Running content generation based on: {analysis_result.get('analysis_summary')}")
    print(f"Project path for content generation: {common_kwargs.get('project_path')}")
    time.sleep(1) # Simulate work
    if common_kwargs.get("simulate_error_at_stage") == "content_generation":
        raise RuntimeError("Simulated error in content_generation")
    return {"generated_content": "This is the generated content.", "version": "1.0"}

def run_stage_review_and_edit(content_result, common_kwargs):
    print(f"Running review and edit for content: {content_result.get('generated_content')}")
    print(f"Project path for review: {common_kwargs.get('project_path')}")
    time.sleep(1) # Simulate work
    if common_kwargs.get("simulate_error_at_stage") == "review_and_edit":
        raise Exception("Simulated error in review_and_edit: " + "long_message_" * 20) # Shorter long message
    return {"edited_content": "This is the reviewed and edited content.", "feedback_notes": "All good."}

def run_stage_final_assembly(edited_content_result, common_kwargs):
    print(f"Running final assembly with: {edited_content_result.get('edited_content')}")
    print(f"Project path for assembly: {common_kwargs.get('project_path')}")
    time.sleep(1) # Simulate work
    if common_kwargs.get("simulate_error_at_stage") == "final_assembly":
        raise ConnectionError("Simulated error in final_assembly")

    output_file = Path(common_kwargs["project_path"]) / "final_output.txt"
    output_file.write_text(f"Final assembled content: {edited_content_result.get('edited_content')}\nNotes: {edited_content_result.get('feedback_notes')}")
    print(f"Final output written to {output_file}")
    return {"final_product_path": str(output_file), "status": "successfully assembled"}


def run_resumable_pipeline(user_request, project_goal, priority, simulate_error_at_stage=None):
    summary = ErrorSummary()
    progress = load_progress()

    # Initialize common_kwargs early to use in print statements, then update after proj
    # This is a bit of a workaround because proj['path'] is needed for the full common_kwargs
    temp_common_kwargs_for_print = {"project_path": "projects/"} # Placeholder for initial print

    proj = get_or_create_project(project_goal) # This will use project_manager.py in the same directory
    print(f"Project '{proj['name']}' status: {proj['status']}, folder at {proj['path']}")

    common_kwargs = {
        "user_request": user_request,
        "project_id": proj["id"],
        "project_path": proj["path"], # This path is now relative to mycrews/qrew/projects/
        "project_goal": project_goal,
        "priority": priority,
        "simulate_error_at_stage": simulate_error_at_stage
    }

    # Now that common_kwargs is fully populated, we can use it for printing resolved paths
    print(f"Checkpoint file will be at: {Path(CHECKPOINT_FILE).resolve()}")
    print(f"Projects root will be at: {Path(common_kwargs['project_path']).parent.resolve()}")

    # Stage 1: Initial Analysis
    stage_name_1 = STAGES[0]
    result_stage_1 = progress["results"].get(stage_name_1) # Ensure it exists if skipped
    try:
        if not progress["completed"].get(stage_name_1):
            print(f"▶ Stage 1: {stage_name_1}")
            result_stage_1 = run_stage_initial_analysis(common_kwargs)
            progress["results"][stage_name_1] = result_stage_1
            progress["completed"][stage_name_1] = True
            save_progress(progress)
            summary.add(stage_name_1, True)
            print(f"✅ Stage 1: {stage_name_1} completed.")
        else:
            # result_stage_1 is already loaded from progress["results"]
            summary.add(stage_name_1, True, "Skipped (already done)")
            print(f"↪ Skipping Stage 1: {stage_name_1} (already done)")
    except Exception as e:
        print(f"❌ Error in Stage 1: {stage_name_1} - {e}")
        summary.add(stage_name_1, False, str(e))
        # Do not save progress here if the stage itself failed to avoid corrupting results
        # save_progress(progress)
        summary.print()
        return progress.get("results", {}) # Return current results, even if partial

    # Stage 2: Content Generation
    stage_name_2 = STAGES[1]
    result_stage_2 = progress["results"].get(stage_name_2)
    try:
        if not progress["completed"].get(stage_name_2):
            if result_stage_1 is None: # Check if previous stage output is missing
                raise Exception(f"Cannot run {stage_name_2} because output from {stage_name_1} is missing.")
            print(f"▶ Stage 2: {stage_name_2}")
            result_stage_2 = run_stage_content_generation(result_stage_1, common_kwargs)
            progress["results"][stage_name_2] = result_stage_2
            progress["completed"][stage_name_2] = True
            save_progress(progress)
            summary.add(stage_name_2, True)
            print(f"✅ Stage 2: {stage_name_2} completed.")
        else:
            summary.add(stage_name_2, True, "Skipped (already done)")
            print(f"↪ Skipping Stage 2: {stage_name_2} (already done)")
    except Exception as e:
        print(f"❌ Error in Stage 2: {stage_name_2} - {e}")
        summary.add(stage_name_2, False, str(e))
        summary.print()
        return progress.get("results", {})

    # Stage 3: Review and Edit
    stage_name_3 = STAGES[2]
    result_stage_3 = progress["results"].get(stage_name_3)
    try:
        if not progress["completed"].get(stage_name_3):
            if result_stage_2 is None:
                raise Exception(f"Cannot run {stage_name_3} because output from {stage_name_2} is missing.")
            print(f"▶ Stage 3: {stage_name_3}")
            result_stage_3 = run_stage_review_and_edit(result_stage_2, common_kwargs)
            progress["results"][stage_name_3] = result_stage_3
            progress["completed"][stage_name_3] = True
            save_progress(progress)
            summary.add(stage_name_3, True)
            print(f"✅ Stage 3: {stage_name_3} completed.")
        else:
            summary.add(stage_name_3, True, "Skipped (already done)")
            print(f"↪ Skipping Stage 3: {stage_name_3} (already done)")
    except Exception as e:
        print(f"❌ Error in Stage 3: {stage_name_3} - {e}")
        summary.add(stage_name_3, False, str(e))
        summary.print()
        return progress.get("results", {})

    # Stage 4: Final Assembly
    stage_name_4 = STAGES[3]
    # result_stage_4 = progress["results"].get(stage_name_4) # Not strictly needed if it's the last stage
    try:
        if not progress["completed"].get(stage_name_4):
            if result_stage_3 is None:
                raise Exception(f"Cannot run {stage_name_4} because output from {stage_name_3} is missing.")
            print(f"▶ Stage 4: {stage_name_4}")
            result_stage_4 = run_stage_final_assembly(result_stage_3, common_kwargs)
            progress["results"][stage_name_4] = result_stage_4
            progress["completed"][stage_name_4] = True
            save_progress(progress)
            summary.add(stage_name_4, True)
            print(f"✅ Stage 4: {stage_name_4} completed.")
        else:
            summary.add(stage_name_4, True, "Skipped (already done)")
            print(f"↪ Skipping Stage 4: {stage_name_4} (already done)")
    except Exception as e:
        print(f"❌ Error in Stage 4: {stage_name_4} - {e}")
        summary.add(stage_name_4, False, str(e))
        summary.print()
        return progress.get("results", {})

    print("\n✅ Pipeline complete.")
    summary.print()
    return progress.get("results", {})

if __name__ == "__main__":
    print("🚀 Starting qrew Resumable Pipeline Execution from 'mycrews/qrew/'...")

    # Sample inputs
    user_request_input = "Develop a new feature for the qrew project."
    project_goal_input = "Qrew Feature: Resumable Operations"
    priority_input = "High"

    # To test resumability, run from the `mycrews/qrew/` directory:
    # `python run_qrew_pipeline.py`
    #
    # Test scenarios:
    # 1. First run: All stages complete. `.qrew_checkpoint.json` and `projects/` created inside `mycrews/qrew/`.
    # 2. Second run: All stages skipped.
    # 3. Delete `.qrew_checkpoint.json`.
    # 4. Simulate error: `results = run_resumable_pipeline(..., simulate_error_at_stage="content_generation")`
    #    Pipeline stops at stage 2. Stage 1 is marked completed in checkpoint.
    # 5. Fix error simulation (set to None), rerun: Skips stage 1, resumes from stage 2.

    # Normal run:
    results = run_resumable_pipeline(user_request_input, project_goal_input, priority_input)

    # Example of simulating an error:
    # results = run_resumable_pipeline(user_request_input, project_goal_input, priority_input, simulate_error_at_stage="content_generation")

    print("\n🏁 qrew Pipeline execution finished. Final Results:")
    if results: # Check if results is not None
        print(json.dumps(results, indent=2))
    else:
        print("Pipeline did not produce final results, possibly due to an early exit on error.")

    # To clean up for a fresh run (run from mycrews/qrew/):
    # if os.path.exists(CHECKPOINT_FILE):
    #     os.remove(CHECKPOINT_FILE)
    #     print(f"\n🧹 Cleaned up {CHECKPOINT_FILE}")
    # print("Consider cleaning up the 'projects/' directory (inside mycrews/qrew/) manually if needed.")
