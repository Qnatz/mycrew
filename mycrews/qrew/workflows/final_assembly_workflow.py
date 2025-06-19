import json
import re # Added
from typing import Any # Added
from crewai import Crew, Process, Task
from crewai.tasks.task_output import TaskOutput # Added
from ..orchestrators.final_assembler_agent.agent import final_assembler_agent
from ..agents.dev_utilities import code_writer_agent
from ..agents.dev_utilities import debugger_agent as error_handler_agent

def validate_readiness_report(task_output: TaskOutput) -> tuple[bool, Any]:
    if not hasattr(task_output, 'raw') or not isinstance(task_output.raw, str):
        print("GUARDRAIL_READINESS_REPORT: Input task_output.raw is not a string or not present.")
        return False, "Guardrail input (task_output.raw) must be a string and present."

    output_str = task_output.raw.strip()
    print(f"GUARDRAIL_READINESS_REPORT: Validating output (first 300 chars): '{output_str[:300]}'")

    cleaned_output = output_str.lower()

    # Keywords indicating a valid assessment was made (even if it finds errors)
    assessment_keywords = [
        "readiness assessment", "error report", "integration readiness",
        "component analysis", "issues found", "vulnerabilities found",
        "components ready", "system verified", "verification complete"
    ]

    # Keywords indicating a valid report about missing data
    missing_data_keywords = [
        "cannot perform assessment", "missing component data", "input data lacking",
        "unable to assess", "components not provided", "component details from subagent execution"
        # Added the specific phrase from the new prompt
    ]

    is_valid_assessment = any(keyword in cleaned_output for keyword in assessment_keywords)
    is_valid_missing_data_report = any(keyword in cleaned_output for keyword in missing_data_keywords)

    if is_valid_assessment:
        if len(output_str) < 50: # Too short for a "comprehensive" assessment
            print("GUARDRAIL_READINESS_REPORT: Output claims assessment but is too short.")
            return False, "Assessment report is too brief to be considered comprehensive."
        print("GUARDRAIL_READINESS_REPORT: Valid assessment report detected.")
        return True, task_output.raw # Return original raw output

    if is_valid_missing_data_report:
        if len(output_str) < 30: # Too short for a clear statement about missing data
            print("GUARDRAIL_READINESS_REPORT: Output claims missing data but statement is too short.")
            return False, "Statement about missing data is too brief."
        print("GUARDRAIL_READINESS_REPORT: Valid report about missing data detected.")
        return True, task_output.raw # Return original raw output

    print("GUARDRAIL_READINESS_REPORT: Output does not seem to be a valid assessment or a clear missing data report.")
    return False, "Output is neither a readiness assessment/error report nor a clear statement about missing input components."

def validate_integration_plan_output(task_output: TaskOutput) -> tuple[bool, Any]:
    if not hasattr(task_output, 'raw') or not isinstance(task_output.raw, str):
        print("GUARDRAIL_INTEGRATION_PLAN: Input task_output.raw is not a string or not present.")
        return False, "Guardrail input (task_output.raw) must be a string and present."

    output_str = task_output.raw.strip()
    print(f"GUARDRAIL_INTEGRATION_PLAN: Validating output (first 300 chars): '{output_str[:300]}'")

    if not output_str: # Handle empty string after strip
        print("GUARDRAIL_INTEGRATION_PLAN: Output is empty.")
        return False, "Output is empty after stripping whitespace."

    cleaned_output_lower = output_str.lower()

    # Keywords indicating a planning effort
    plan_keywords = [
        "integration plan", "integration steps", "sequence of integration",
        "component interaction", "data flow", "configuration management",
        "testing strategy", "deployment considerations", "deployment sequence"
    ]

    # Keywords indicating acknowledgment of issues within a plan
    issue_keywords = [
        "blockers", "prerequisites", "missing information", "non-functional",
        "resolve them", "address these issues", "contingency"
    ]

    # Check for presence of planning content
    has_plan_content = any(keyword in cleaned_output_lower for keyword in plan_keywords)

    # Check for acknowledgment of issues (which is acceptable if a plan is also present)
    has_issue_discussion = any(keyword in cleaned_output_lower for keyword in issue_keywords)

    # Heuristic: Substantial length suggests more than just a simple refusal.
    is_substantial = len(output_str) > 150 # Arbitrary length, tune if needed

    # --- Manifest Validation ---
    manifest_heading = "File Manifest for Code Generation".lower()
    manifest_start_index = cleaned_output_lower.find(manifest_heading)

    if manifest_start_index == -1:
        print("GUARDRAIL_INTEGRATION_PLAN: 'File Manifest for Code Generation' section is missing.")
        return False, "The 'File Manifest for Code Generation' section is missing from the integration plan."

    json_block_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL | re.IGNORECASE)
    search_area_for_manifest = output_str[manifest_start_index + len(manifest_heading):]
    manifest_match = json_block_pattern.search(search_area_for_manifest)

    manifest_json_str = None
    if manifest_match:
        manifest_json_str = manifest_match.group(1).strip()
        print("GUARDRAIL_INTEGRATION_PLAN: Found fenced JSON block for File Manifest.")
    else:
        print("GUARDRAIL_INTEGRATION_PLAN: Fenced JSON block not found. Attempting lenient extraction of unfenced JSON array.")
        stripped_search_area = search_area_for_manifest.strip()
        if stripped_search_area.startswith('[') and stripped_search_area.endswith(']'):
            # Use regex to capture content within brackets, allowing for leading/trailing whitespace around the array.
            potential_json_array_match = re.match(r"\s*(\[.*?\])\s*", stripped_search_area, re.DOTALL)
            if potential_json_array_match:
                manifest_json_str = potential_json_array_match.group(1) # Get the content within brackets
                print("GUARDRAIL_INTEGRATION_PLAN: Found potential unfenced JSON array.")
            else:
                # This case might occur if stripped_search_area starts with [ and ends with ]
                # but has non-whitespace chars outside them, which re.match would fail.
                # Or if the content isn't actually a valid array structure for the regex.
                print("GUARDRAIL_INTEGRATION_PLAN: Potential unfenced JSON array started with '[' and ended with ']' but regex match failed (e.g. unexpected surrounding characters or invalid structure).")
        else:
            print("GUARDRAIL_INTEGRATION_PLAN: Lenient extraction failed: content does not start with '[' and end with ']'.")

    if manifest_json_str is None:
        print("GUARDRAIL_INTEGRATION_PLAN: Could not find a JSON code block (fenced or unfenced) for the File Manifest.")
        return False, "File Manifest section found, but it does not contain a ```json ... ``` block or a valid unfenced JSON array for the list of files."

    try:
        file_manifest = json.loads(manifest_json_str)
        if not isinstance(file_manifest, list):
            print("GUARDRAIL_INTEGRATION_PLAN: File Manifest JSON is not a list.")
            return False, "File Manifest must be a JSON list."
        if not file_manifest: # Empty list is not acceptable
            print("GUARDRAIL_INTEGRATION_PLAN: File Manifest list is empty.")
            return False, "File Manifest list cannot be empty."
        for item in file_manifest:
            if not isinstance(item, dict) or \
               not isinstance(item.get('file_path'), str) or \
               not item['file_path'].strip() or \
               not isinstance(item.get('description'), str) or \
               not item['description'].strip():
                print(f"GUARDRAIL_INTEGRATION_PLAN: Invalid item in File Manifest: {item}")
                return False, "Each item in File Manifest must be a dictionary with non-empty 'file_path' and 'description' strings."

        print("GUARDRAIL_INTEGRATION_PLAN: File Manifest appears structurally valid.")
        # If manifest validation passes, this specific check is considered OK.
        # The overall decision depends on other factors like plan content and substantiality.
    except json.JSONDecodeError:
        print(f"GUARDRAIL_INTEGRATION_PLAN: File Manifest JSON is malformed: {manifest_json_str[:100]}")
        return False, "File Manifest section contains malformed JSON."
    # --- End of Manifest Validation ---

    # Condition for passing:
    # 1. Must have planning content.
    # 2. Must be of substantial length.
    # 3. Manifest (if present and checked by reaching here) must be structurally valid.
    if has_plan_content and is_substantial: # Manifest validation passed if we reached here
        print("GUARDRAIL_INTEGRATION_PLAN: Output appears to be a substantive integration plan and manifest (if present and checked) is structurally valid.")
        return True, task_output.raw # Return original raw output

    # If it mentions issues but has no plan content or isn't substantial
    # This condition might be hit if manifest was OK but other parts failed.
    if has_issue_discussion and not has_plan_content and not is_substantial:
        print("GUARDRAIL_INTEGRATION_PLAN: Output primarily discusses issues without sufficient planning content or detail.")
        return False, "Output focuses on issues without providing a sufficient integration plan for available components or clear steps to resolve."

    # Fallback error messages if conditions not met
    if not has_plan_content:
         print("GUARDRAIL_INTEGRATION_PLAN: Output lacks clear planning content despite potentially valid manifest.")
         return False, "Output lacks clear planning content for integration."
    if not is_substantial:
        print("GUARDRAIL_INTEGRATION_PLAN: Output has planning content but is not substantial enough, despite potentially valid manifest.")
        return False, "Integration plan is too brief."

    # Default catch-all if logic is complex (should ideally be covered by above)
    print("GUARDRAIL_INTEGRATION_PLAN: Default failure - Output did not meet all criteria (plan content, substantiality, valid manifest).")
    return False, "Output does not meet all criteria for a valid integration plan including a file manifest."

# Copied from subagent_execution_workflow.py for now
def validate_and_extract_code_output(task_output: TaskOutput) -> tuple[bool, Any]:
    try:
        if not hasattr(task_output, 'raw') or not isinstance(task_output.raw, str):
            print("GUARDRAIL_CODE_EXTRACT: Input task_output.raw is not a string or not present.")
            return False, "Guardrail input (task_output.raw) must be a string and present."

        output_str = task_output.raw.strip()
        print(f"GUARDRAIL_CODE_EXTRACT: Original output (first 300 chars): '{output_str[:300]}'")

        extracted_code_blocks = []

        # Regex to find common fenced code blocks (non-greedy)
        fence_patterns = [
            re.compile(r"```(?:[a-zA-Z0-9_]+)?\s*\n(.*?)\n```", re.DOTALL),
            re.compile(r"```(.*?)```", re.DOTALL)
        ]

        temp_output_str = output_str
        for pattern in fence_patterns:
            matches = pattern.findall(temp_output_str)
            if matches:
                for match in matches:
                    extracted_code_blocks.append(match.strip())
                temp_output_str = pattern.sub("", temp_output_str).strip()

        final_extracted_code = ""
        if extracted_code_blocks:
            final_extracted_code = "\n\n".join(extracted_code_blocks).strip()
            print(f"GUARDRAIL_CODE_EXTRACT: Extracted code using fences (first 300 chars): '{final_extracted_code[:300]}'")
        else:
            if len(output_str.split()) > 50 and len(re.findall(r'[;,=\{\}\[\]\(\)<>]', output_str)) < 5:
                 print(f"GUARDRAIL_CODE_EXTRACT: No fences found, and output looks more like text than code. Length: {len(output_str.split())} words.")
                 return False, "Output appears to be mainly explanatory text without clear code blocks, or code is not properly fenced."
            final_extracted_code = output_str
            print(f"GUARDRAIL_CODE_EXTRACT: No fences found. Assuming entire content might be code/config (first 300 chars): '{final_extracted_code[:300]}'")

        if not final_extracted_code:
            print("GUARDRAIL_CODE_EXTRACT: No code content could be extracted.")
            return False, "No code/configuration content could be extracted from the output."

        if len(final_extracted_code) < 10 and not ("def" in final_extracted_code or "class" in final_extracted_code or "{" in final_extracted_code or "<" in final_extracted_code):
             print(f"GUARDRAIL_CODE_EXTRACT: Extracted content is very short and doesn't resemble typical code structures: '{final_extracted_code}'")
             return False, f"Extracted content is too short or doesn't resemble code: '{final_extracted_code}'"

        print(f"GUARDRAIL_CODE_EXTRACT: Successfully extracted code/configuration. Length: {len(final_extracted_code)}")
        return True, final_extracted_code
    except Exception as e:
        print(f"GUARDRAIL_CODE_EXTRACT: Error during code extraction: {str(e)}")
        return False, f"Error during guardrail code extraction: {str(e)}"

def run_final_assembly_workflow(inputs: dict):
    print(f"DEBUG: Entering run_final_assembly_workflow with inputs: {inputs.get('project_name', 'N/A')} scope: N/A (not directly available)")
    components_summary_str = json.dumps(inputs.get("subagent_execution", {}), indent=2) # Corrected key
    architecture_summary_str = json.dumps(inputs.get("architecture", {}), indent=2)

    # Error checking phase
    error_check_task = Task(
        description=f"Verify all components provided in the summary for integration readiness: '{components_summary_str}'. CRUCIAL: If the component summary is empty or indicates no components (e.g., '{{}}', '[]'), your output MUST clearly state that a readiness assessment cannot be performed due to missing 'component details from subagent execution' and what was expected (a summary of components). Do NOT describe hypothetical procedures you would follow if data were present. If components ARE provided (the summary is not empty), produce a detailed error report and readiness assessment for them, identifying any issues or confirming their readiness.",
        agent=error_handler_agent,
        expected_output="A comprehensive error report and readiness assessment for the provided components. OR, if component data was missing as indicated by an empty input summary (e.g., '{{}}', '[]'), the output MUST be a clear statement specifically indicating that 'Readiness assessment cannot be performed due to missing component details from subagent execution.' This statement must be direct and not include hypothetical procedures.",
        max_retries=1,
        guardrail=validate_readiness_report
    )

    # Integration planning
    integration_task = Task(
        description=f"Create a detailed integration plan based on the available components summarized as: {components_summary_str}. The overall project architecture is: {architecture_summary_str}. Your goal is to outline how these components should be combined into a functional system. IMPORTANT: If the component summary or architecture indicates some components are non-functional, incomplete, or if crucial information is missing, your integration plan MUST still be as complete as possible for the *available and functional* parts. Clearly identify any non-functional components or missing information as 'Blockers' or 'Prerequisites for Full Integration' within a dedicated section of your plan. Also, outline steps or strategies to address these blockers. Do NOT simply state you cannot create a plan. Provide a plan for what is possible now and what is needed to make the rest possible.",
        agent=final_assembler_agent,
        expected_output=(
            "YOUR RESPONSE MUST CONSIST OF TWO MAIN PARTS:\n"
            "PART 1: A DETAILED INTEGRATION PLAN (Markdown format preferred).\n"
            "PART 2: A FILE MANIFEST FOR CODE GENERATION (JSON format within a specific section).\n\n"
            "--- PART 1: DETAILED INTEGRATION PLAN ---\n"
            "The integration plan MUST include:\n"
            "1. An explicit 'Integration Sequence' for available/functional components.\n"
            "2. Details on 'Component Interactions & Data Flow'.\n"
            "3. 'Configuration Management' notes for integration.\n"
            "4. A dedicated section: 'Blockers & Prerequisites for Full Integration', listing non-functional components or missing info and proposing steps/strategies to resolve them.\n"
            "5. A 'Testing Strategy' for the integrated parts.\n"
            "6. 'Deployment Considerations' for the integrated system.\n"
            "The plan should be actionable even if some parts are blocked, by clearly separating what can be done from what needs fixing.\n\n"
            "--- PART 2: FILE MANIFEST FOR CODE GENERATION (MANDATORY REQUIREMENT) ---\n"
            "This is a CRITICAL and MANDATORY part of your output.\n"
            "You MUST include a specific section EXACTLY titled: 'File Manifest for Code Generation'.\n"
            "Under this exact heading, your output for the manifest MUST be ONLY a single markdown fenced JSON code block starting with ```json and ending with ```. Do not include any text outside of these fences for the manifest content. The JSON content itself must be a list of dictionaries.\n"
            "Each dictionary represents a file to be generated and MUST contain:\n"
            "  - 'file_path': (string) The full intended path for the file (e.g., 'src/models/user.py', 'static/css/styles.css').\n"
            "  - 'description': (string) A concise explanation of what code, class, functions, or content this file should contain, based on your integration plan and the project architecture.\n"
            "For clarity, the File Manifest section MUST look like this, including the ```json and ``` fences:\n"
            "Example of the JSON list format for the manifest:\n"
            "```json\n"
            "[\n"
            "  {\"file_path\": \"src/main.py\", \"description\": \"Main application entry point, sets up routes and initializes the Flask app.\"},\n"
            "  {\"file_path\": \"src/models/user.py\", \"description\": \"Defines the User data model including fields like id, username, email, and password hash.\"}\n"
            "]\n"
            "```\n"
            "This manifest MUST be comprehensive and include ALL files necessary to build the components and functionalities discussed in your integration plan. Task completion will be validated against the presence and correctness of this manifest."
        ),
        max_retries=1,
        guardrail=validate_integration_plan_output
    )

    # Initial crew for error checking and integration planning
    initial_crew = Crew(
        agents=[error_handler_agent, final_assembler_agent],
        tasks=[error_check_task, integration_task],
        process=Process.sequential,
        verbose=True
    )

    initial_result = initial_crew.kickoff()

    if not initial_result or not initial_result.tasks_output or len(initial_result.tasks_output) != 2:
        return "Error: Final assembly's initial phase (error check, integration plan) did not produce the expected number of task outputs."

    error_check_output_obj = initial_result.tasks_output[0]
    integration_output_obj = initial_result.tasks_output[1]

    error_check_raw = getattr(error_check_output_obj, 'raw', None)
    integration_raw = getattr(integration_output_obj, 'raw', None)

    if not error_check_raw:
        return f"Error: Error check task failed in final_assembly_workflow. No output or empty output."
    if not integration_raw: # This implies the guardrail on integration_task passed, so 'integration_raw' is the plan.
        # However, the guardrail might have returned False, and crewAI might pass along the last failing output.
        # A more robust check for task success might be needed if crewAI provides it.
        # For now, if integration_raw is empty, we assume failure.
        return f"Error: Integration task failed or produced no valid output. Error check output: {error_check_raw}"

    # Extract File Manifest from the validated integration_raw
    file_manifest = []
    try:
        temp_cleaned_lower = integration_raw.lower()
        manifest_heading = "File Manifest for Code Generation".lower()
        manifest_heading_idx = temp_cleaned_lower.find(manifest_heading)
        if manifest_heading_idx != -1:
            search_json_block_in = integration_raw[manifest_heading_idx + len(manifest_heading):]
            json_block_match = re.search(r"```json\s*\n(.*?)\n```", search_json_block_in, re.DOTALL | re.IGNORECASE)
            if json_block_match:
                manifest_json_str = json_block_match.group(1).strip()
                parsed_manifest = json.loads(manifest_json_str)
                if isinstance(parsed_manifest, list) and all(
                    isinstance(item, dict) and
                    'file_path' in item and isinstance(item['file_path'], str) and item['file_path'].strip() and
                    'description' in item and isinstance(item['description'], str) and item['description'].strip()
                    for item in parsed_manifest
                ):
                    file_manifest = parsed_manifest
                    print(f"Successfully extracted file manifest with {len(file_manifest)} items.")
                else:
                    print("Error: Extracted file manifest is not in the expected list-of-dicts format.")
            else:
                print("Error: Could not find ```json block for file manifest after heading in integration plan.")
        else:
            print("Error: 'File Manifest for Code Generation' heading not found in integration plan.")
    except Exception as e:
        print(f"Error parsing file manifest from integration plan: {e}")

    if not file_manifest:
        return f"Error: Failed to extract a valid or non-empty File Manifest from the integration plan. Integration plan (first 500 chars): {integration_raw[:500]}"

    # Iterative Code Generation Loop
    generated_code_files = {}
    print(f"\nStarting iterative code generation for {len(file_manifest)} files...")
    for i, file_spec in enumerate(file_manifest):
        file_path = file_spec.get('file_path', f'unknown_file_{i+1}.txt')
        file_description = file_spec.get('description', 'No specific description provided.')

        print(f"Generating file {i+1}/{len(file_manifest)}: {file_path} - {file_description[:100]}...")

        integration_context = integration_raw[:1500]
        architecture_context = architecture_summary_str[:1500]

        code_generation_sub_task_desc = (
            f"Generate the complete and runnable code for the specific file: '{file_path}'.\n"
            f"Purpose of this file: '{file_description}'.\n"
            f"This file is part of a larger project. Ensure it aligns with the overall project architecture and integration plan.\n"
            f"Key architectural considerations (summary): '{architecture_context}'.\n"
            f"Overall integration context (summary): '{integration_context}'.\n"
            f"Focus solely on generating the full code for '{file_path}'. All necessary imports, class/function definitions, "
            f"and logic for this single file must be included and correct."
        )
        code_generation_sub_task_expected_output = (
            f"CRITICAL: Your entire response MUST be ONLY the raw, complete code for the specified file: '{file_path}'. "
            f"NO other text, explanations, apologies, markdown code fences, or conversational filler. "
            f"ONLY the code for this single file, from the first line to the last."
        )

        individual_code_task = Task(
            description=code_generation_sub_task_desc,
            agent=code_writer_agent,
            expected_output=code_generation_sub_task_expected_output,
            guardrail=validate_and_extract_code_output,
            max_retries=1
        )

        code_writing_crew = Crew(agents=[code_writer_agent], tasks=[individual_code_task], verbose=False)
        sub_task_result = code_writing_crew.kickoff()

        if sub_task_result and hasattr(sub_task_result, 'raw') and sub_task_result.raw:
            generated_code_files[file_path] = sub_task_result.raw
            print(f"Successfully generated code for {file_path} (length: {len(sub_task_result.raw)}).")
        else:
            error_detail = getattr(sub_task_result, 'raw', "No raw output from task.") if sub_task_result else "Task execution returned None."
            print(f"Error: Failed to generate code for file: {file_path}. Details: {error_detail}")
            generated_code_files[file_path] = f"Error: Failed to generate code for this file. Details: {error_detail}"

    print("Iterative code generation completed.")

    all_successful = all(not val.startswith("Error:") for val in generated_code_files.values())
    if not all_successful:
         print("Warning: Some files failed during code generation.")
         print(f"DEBUG: Exiting run_final_assembly_workflow with partial success")
         return {"status": "partial_success_code_generation", "generated_files": generated_code_files, "message": "Some files failed generation."}

    print(f"DEBUG: Exiting run_final_assembly_workflow with success")
    return {"status": "success_code_generation", "generated_files": generated_code_files}
