import json
from ..agents.dev_utilities.code_writer_agent.agent import code_writer_agent
from ..agents.dev_utilities.tester_agent.agent import tester_agent
from ..crews.backend_development_crew import BackendDevelopmentCrew
from ..crews.mobile_development_crew import MobileDevelopmentCrew
from ..crews.web_development_crew import WebDevelopmentCrew
from crewai import Task # Assuming crewai is installed in the environment and accessible

def run_code_implementation_workflow(architecture_design):
    print("\n📦 Starting Code Implementation Workflow...")

    # 🔹 Breakdown architecture into module specs
    backend_spec = None
    mobile_spec = None
    web_spec = None

    # Attempt to extract specs from various possible structures of architecture_design
    actual_design_dict = None
    if isinstance(architecture_design, dict):
        actual_design_dict = architecture_design
    elif hasattr(architecture_design, 'raw_output') and architecture_design.raw_output:
        if isinstance(architecture_design.raw_output, dict):
            actual_design_dict = architecture_design.raw_output
        elif isinstance(architecture_design.raw_output, str):
            try:
                parsed_output = json.loads(architecture_design.raw_output)
                if isinstance(parsed_output, dict):
                    actual_design_dict = parsed_output
                else:
                    print(f"Warning: Parsed architecture_design.raw_output (from string) is not a dictionary. Type: {type(parsed_output)}. Specs will be None.")
            except json.JSONDecodeError:
                print(f"Warning: architecture_design.raw_output is a string but not valid JSON. Content: {architecture_design.raw_output[:200]}. Specs will be None.")
            except Exception as e:
                print(f"Error processing string architecture_design.raw_output: {e}. Specs will be None.")
        else:
            print(f"Warning: architecture_design.raw_output is of unhandled type: {type(architecture_design.raw_output)}. Specs will be None.")
    elif hasattr(architecture_design, 'raw') and isinstance(architecture_design.raw, dict):
        actual_design_dict = architecture_design.raw
    elif hasattr(architecture_design, 'pydantic_output') and isinstance(architecture_design.pydantic_output, dict):
        actual_design_dict = architecture_design.pydantic_output
    # Note: The generic 'get' attribute case is removed as it's too broad if 'architecture_design' is not a dict itself.
    # If it has a 'get' method, it should ideally be caught by 'isinstance(architecture_design, dict)'.

    if actual_design_dict:
        backend_spec = actual_design_dict.get("backend_spec_content") or actual_design_dict.get("backend_spec")
        mobile_spec = actual_design_dict.get("mobile_spec_content") or actual_design_dict.get("mobile_spec")
        web_spec = actual_design_dict.get("web_spec_content") or actual_design_dict.get("web_spec")

        # One more check: if the spec itself is a dictionary with a "content" key
        if isinstance(backend_spec, dict) and "content" in backend_spec:
            backend_spec = backend_spec.get("content")
        if isinstance(mobile_spec, dict) and "content" in mobile_spec:
            mobile_spec = mobile_spec.get("content")
        if isinstance(web_spec, dict) and "content" in web_spec:
            web_spec = web_spec.get("content")

    else:
        print(f"Warning: Could not resolve architecture_design (type: {type(architecture_design)}) to a dictionary. Specs will likely be None.")

    results = []

    if backend_spec:
        print(f"Backend spec found. Preparing task for backend_development_crew. Spec: {str(backend_spec)[:100]}...")
        backend_crew_instance = BackendDevelopmentCrew()
        task_backend = Task(
            description="Implement backend APIs from architecture.",
            agent=code_writer_agent,
            expected_output="Python/FastAPI or NodeJS code implementing endpoints",
            context={ "spec": backend_spec },
            successCriteria=["compilable", "auth logic implemented", "modular code"]
        )
        if backend_crew_instance:
            # The @task decorator in CrewBase adds tasks to an instance's list.
            # We might need to pass the task to the kickoff method if tasks are not pre-registered on instantiation.
            # For now, assuming tasks are handled by the .crew() method's setup.
            # Let's assign the task to the list of tasks for the specific crew instance to be created.
            # The @crew method in the CrewBase class should use self.tasks.
            # So, we set the tasks on the instance of BackendDevelopmentCrew first.
            backend_crew_instance.tasks = [task_backend] # Set the task for the crew instance
            runnable_crew = backend_crew_instance.crew() # Get the actual ValidatedCrew object
            backend_result_item = runnable_crew.kickoff()
            if backend_result_item is not None:
                 results.append(backend_result_item)
            else:
                print("Warning: backend_development_crew.kickoff() returned None.")
        else:
            print("Warning: backend_development_crew not available or not imported correctly.")
    else:
        print("Backend spec not found or is empty. Skipping backend development.")

    if mobile_spec:
        print(f"Mobile spec found. Preparing task for mobile_development_crew. Spec: {str(mobile_spec)[:100]}...")
        mobile_crew_instance = MobileDevelopmentCrew()
        task_mobile = Task(
            description="Implement Android mobile UI from design spec.",
            agent=code_writer_agent,
            expected_output="Kotlin/Jetpack Compose code for mobile app UI",
            context={ "spec": mobile_spec },
            successCriteria=["UI matches design", "navigable", "reactive layout"]
        )
        if mobile_crew_instance:
            mobile_crew_instance.tasks = [task_mobile] # Set the task
            runnable_crew = mobile_crew_instance.crew() # Get the actual ValidatedCrew object
            mobile_result_item = runnable_crew.kickoff()
            if mobile_result_item is not None:
                results.append(mobile_result_item)
            else:
                print("Warning: mobile_development_crew.kickoff() returned None.")
        else:
            print("Warning: mobile_development_crew not available or not imported correctly.")
    else:
        print("Mobile spec not found or is empty. Skipping mobile development.")

    if web_spec:
        print(f"Web spec found. Preparing task for web_development_crew. Spec: {str(web_spec)[:100]}...")
        web_crew_instance = WebDevelopmentCrew()
        task_web = Task(
            description="Implement responsive web UI from design spec.",
            agent=code_writer_agent,
            expected_output="HTML/CSS/JS code for responsive site",
            context={ "spec": web_spec },
            successCriteria=["responsive layout", "semantic HTML"]
        )
        if web_crew_instance:
            web_crew_instance.tasks = [task_web] # Set the task
            runnable_crew = web_crew_instance.crew() # Get the actual ValidatedCrew object
            web_result_item = runnable_crew.kickoff()
            if web_result_item is not None:
                results.append(web_result_item)
            else:
                print("Warning: web_development_crew.kickoff() returned None.")
        else:
            print("Warning: web_development_crew not available or not imported correctly.")
    else:
        print("Web spec not found or is empty. Skipping web development.")

    if not results:
        print("No specs were processed, or all kickoff calls returned None/empty. Results list is empty.")
    else:
        print(f"Collected {len(results)} result(s) from dispatched crews.")

    print("✅ Code generation workflow finished.")
    return results
