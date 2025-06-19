# mycrews/qrew/llm_config.py
import os
from crewai import LLM
from typing import Optional # For type hinting LLM | None

# List to store initialization statuses
llm_initialization_statuses = []

# Comment out all previous Gemini model constant definitions
# Define New User-Provided Gemini Model Constants
# GEMINI_1_5_PRO = "gemini/gemini-1.5-pro"
# GEMINI_1_5_FLASH = "gemini/gemini-1.5-flash"
# GEMINI_2_0_FLASH = "gemini/gemini-2.0-flash"
# GEMINI_2_0_FLASH_LITE_001 = "gemini/gemini-2.0-flash-lite-001"
# GEMINI_2_5_FLASH_PREVIEW_04_17 = "gemini/gemini-2.5-flash-preview-04-17"
# GEMINI_2_5_PRO_EXP_03_25 = "gemini/gemini-2.5-pro-exp-03-25"

# Comment out or remove old Gemini constants
# NEW_PRO_MODEL = "gemini/gemini-2.5-pro-preview-06-05"
# NEW_FLASH_MODEL = "gemini/gemini-2.5-flash-preview-05-20"
# PRO_MODEL_PRIMARY = "gemini/gemini-1.5-pro-002"
# FLASH_STABLE_ALIAS = "gemini/gemini-1.5-flash"
# FLASH_OLDER_STABLE = "gemini/gemini-2.0-flash"

# Old constants M1, M2, M3 are removed as their roles are superseded by the new constants and logic.

# Verified working models based on user testing
VERIFIED_GEMINI_1_5_FLASH = "gemini/gemini-1.5-flash"
VERIFIED_GEMINI_1_5_FLASH_8B = "gemini/gemini-1.5-flash-8b"
VERIFIED_GEMINI_2_0_FLASH = "gemini/gemini-2.0-flash"
VERIFIED_GEMINI_2_0_FLASH_LITE = "gemini/gemini-2.0-flash-lite-001"
VERIFIED_GEMINI_2_5_FLASH_PREVIEW = "gemini/gemini-2.5-flash-preview-04-17"
# VERIFIED_GEMINI_2_0_FLASH_THINKING_EXP = "gemini/gemini-2.0-flash-thinking-exp-01-21" # Keep available if needed
# VERIFIED_GEMINI_2_0_FLASH_001 = "gemini/gemini-2.0-flash-001" # Likely same as VERIFIED_GEMINI_2_0_FLASH


# Create a Comprehensive List of New Gemini Models
# USER_SPECIFIED_GEMINI_MODELS = [
#     {"model": GEMINI_1_5_PRO, "max_tokens": 3000, "temperature": 0.7},
#     {"model": GEMINI_1_5_FLASH, "max_tokens": 2500, "temperature": 0.7},
#     {"model": GEMINI_2_0_FLASH, "max_tokens": 2500, "temperature": 0.7},
#     {"model": GEMINI_2_0_FLASH_LITE_001, "max_tokens": 2000, "temperature": 0.7},
#     {"model": GEMINI_2_5_FLASH_PREVIEW_04_17, "max_tokens": 2500, "temperature": 0.7},
#     {"model": GEMINI_2_5_PRO_EXP_03_25, "max_tokens": 3000, "temperature": 0.7},
# ]

# Create a Comprehensive List of Verified Working Gemini Models
# VERIFIED_GEMINI_MODELS_CONFIG = [
#     {"model": VERIFIED_GEMINI_2_5_FLASH_PREVIEW, "max_tokens": 3000, "temperature": 0.7}, # Good for higher capability tasks
#     {"model": VERIFIED_GEMINI_1_5_FLASH, "max_tokens": 2800, "temperature": 0.7},       # Solid general purpose
#     {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "max_tokens": 2800, "temperature": 0.7},    # 8B variant of 1.5 flash
#     {"model": VERIFIED_GEMINI_2_0_FLASH, "max_tokens": 2500, "temperature": 0.7},       # Another general purpose option
#     {"model": VERIFIED_GEMINI_2_0_FLASH_LITE, "max_tokens": 2000, "temperature": 0.7}  # For lighter tasks
# ]

# Comment out old CFG objects and template lists
# CFG_2_5_FLASH_PREVIEW = {"model": VERIFIED_GEMINI_2_5_FLASH_PREVIEW, "max_tokens": 3000, "temperature": 0.7}
# CFG_1_5_FLASH = {"model": VERIFIED_GEMINI_1_5_FLASH, "max_tokens": 2800, "temperature": 0.7}
# CFG_1_5_FLASH_8B = {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "max_tokens": 2800, "temperature": 0.7}
# CFG_2_0_FLASH = {"model": VERIFIED_GEMINI_2_0_FLASH, "max_tokens": 2500, "temperature": 0.7}
# CFG_2_0_FLASH_LITE = {"model": VERIFIED_GEMINI_2_0_FLASH_LITE, "max_tokens": 2000, "temperature": 0.7}

# HIGH_CAPABILITY_MODELS_A = [CFG_2_5_FLASH_PREVIEW, CFG_1_5_FLASH, CFG_1_5_FLASH_8B]
# HIGH_CAPABILITY_MODELS_B = [CFG_1_5_FLASH, CFG_2_5_FLASH_PREVIEW, CFG_2_0_FLASH]
# STANDARD_CAPABILITY_MODELS_A = [CFG_1_5_FLASH, CFG_2_0_FLASH, CFG_2_5_FLASH_PREVIEW]
# STANDARD_CAPABILITY_MODELS_B = [CFG_2_0_FLASH, CFG_1_5_FLASH_8B, CFG_2_5_FLASH_PREVIEW]
# UTILITY_CAPABILITY_MODELS_A = [CFG_2_0_FLASH_LITE, CFG_2_0_FLASH, CFG_1_5_FLASH]
# UTILITY_CAPABILITY_MODELS_B = [CFG_2_0_FLASH, CFG_2_0_FLASH_LITE, CFG_1_5_FLASH_8B]

# Configuration objects based on user's matrix for verified Flash models
CFG_1_5_FLASH_DETERMINISTIC = {"model": VERIFIED_GEMINI_1_5_FLASH, "temperature": 0.1, "max_tokens": 1500}
CFG_1_5_FLASH_8B_BASIC = {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "temperature": 0.2, "max_tokens": 1000}
CFG_2_0_FLASH_SCAFFOLD = {"model": VERIFIED_GEMINI_2_0_FLASH, "temperature": 0.4, "max_tokens": 2000}
CFG_2_0_FLASH_LITE_UTILITY = {"model": VERIFIED_GEMINI_2_0_FLASH_LITE, "temperature": 0.3, "max_tokens": 768}
CFG_2_5_FLASH_PREVIEW_E2E = {"model": VERIFIED_GEMINI_2_5_FLASH_PREVIEW, "temperature": 0.3, "max_tokens": 3000}

# New config for code_writer_agent
CFG_2_0_FLASH_CODE_WRITER = {"model": VERIFIED_GEMINI_2_0_FLASH, "temperature": 0.1, "max_tokens": 2000}

# New CFG objects for code generation with larger context
CFG_1_5_FLASH_8B_CODE_WRITER_LARGE = {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "temperature": 0.2, "max_tokens": 8192}
CFG_1_5_FLASH_8B_MODULE = {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "temperature": 0.2, "max_tokens": 4096}
CFG_2_0_FLASH_MODULE_DETERMINISTIC = {"model": VERIFIED_GEMINI_2_0_FLASH, "temperature": 0.2, "max_tokens": 4096}

# New config for coordinators
CFG_1_5_FLASH_COORD = {"model": VERIFIED_GEMINI_1_5_FLASH, "temperature": 0.3, "max_tokens": 1500}

# Template model lists by capability using new CFG objects
PLANNING_DESIGN_MODELS = [CFG_2_5_FLASH_PREVIEW_E2E, CFG_2_0_FLASH_SCAFFOLD, CFG_1_5_FLASH_DETERMINISTIC]
SCAFFOLDING_API_MODELS = [CFG_2_0_FLASH_SCAFFOLD, CFG_2_5_FLASH_PREVIEW_E2E, CFG_1_5_FLASH_DETERMINISTIC]
DETERMINISTIC_CODE_MODELS = [CFG_1_5_FLASH_DETERMINISTIC, CFG_2_0_FLASH_SCAFFOLD, CFG_1_5_FLASH_8B_BASIC]
DOCS_UTILITY_MODELS_A = [CFG_2_0_FLASH_LITE_UTILITY, CFG_1_5_FLASH_8B_BASIC, CFG_1_5_FLASH_DETERMINISTIC]
DOCS_UTILITY_MODELS_B = [CFG_1_5_FLASH_8B_BASIC, CFG_2_0_FLASH_LITE_UTILITY, CFG_1_5_FLASH_DETERMINISTIC]
UI_GEN_MODELS = [CFG_2_0_FLASH_SCAFFOLD, CFG_2_5_FLASH_PREVIEW_E2E, CFG_1_5_FLASH_DETERMINISTIC]
COORDINATOR_MODELS_A = [CFG_1_5_FLASH_COORD, CFG_2_0_FLASH_SCAFFOLD, CFG_2_5_FLASH_PREVIEW_E2E] # Updated primary model
COORDINATOR_MODELS_B = [CFG_1_5_FLASH_8B_BASIC, CFG_2_0_FLASH_SCAFFOLD, CFG_2_5_FLASH_PREVIEW_E2E]

# Specific model list for Taskmaster Agent with adjusted temperature (remains from previous step, uses VERIFIED constants)
TASKMASTER_AGENT_MODELS = [
    {"model": VERIFIED_GEMINI_1_5_FLASH, "max_tokens": 2800, "temperature": 0.3},
    {"model": VERIFIED_GEMINI_2_5_FLASH_PREVIEW, "max_tokens": 3000, "temperature": 0.1},
    {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "max_tokens": 2800, "temperature": 0.3}
]

# Specific model list for Final Assembler Agent with stricter temperature
FINAL_ASSEMBLER_AGENT_MODELS = [
    {"model": VERIFIED_GEMINI_2_0_FLASH, "temperature": 0.0, "max_tokens": 4096},
    {"model": VERIFIED_GEMINI_2_5_FLASH_PREVIEW, "temperature": 0.1, "max_tokens": 4096},
    {"model": VERIFIED_GEMINI_1_5_FLASH, "temperature": 0.1, "max_tokens": 4096}
]

# Specific model list for Code Writer Agent to mitigate rate limiting
CODE_WRITER_AGENT_MODELS_ALT = [
    CFG_2_0_FLASH_CODE_WRITER,    # Primary: gemini/gemini-2.0-flash, temp 0.1
    CFG_1_5_FLASH_8B_BASIC        # Fallback 1: gemini/gemini-1.5-flash-8b, temp 0.2
]

# New Model Lists for updated code generation strategy
GENERIC_CODE_WRITER_MODELS = [CFG_1_5_FLASH_8B_CODE_WRITER_LARGE, CFG_2_0_FLASH_CODE_WRITER]
BACKEND_MODULE_MODELS = [CFG_1_5_FLASH_8B_MODULE, CFG_2_0_FLASH_MODULE_DETERMINISTIC]
WEB_PAGE_MODELS = BACKEND_MODULE_MODELS # Reusing BACKEND_MODULE_MODELS
MOBILE_COMPONENT_MODELS = BACKEND_MODULE_MODELS # Reusing BACKEND_MODULE_MODELS

# Define the mapping of agent identifiers to a list of model configurations (for fallback)
MODEL_BY_AGENT = {
    # --- High-capability/Orchestration/Planning Agents ---
    "idea_interpreter_agent": PLANNING_DESIGN_MODELS,
    "project_architect_agent": PLANNING_DESIGN_MODELS,
    "taskmaster_agent": TASKMASTER_AGENT_MODELS, # Special case with lower temp
    "final_assembler_agent": FINAL_ASSEMBLER_AGENT_MODELS, # Updated for stricter temperature
    "execution_manager_agent": PLANNING_DESIGN_MODELS,
    "tech_vetting_council_agent": PLANNING_DESIGN_MODELS,
    "stack_advisor_agent_tech_committee": PLANNING_DESIGN_MODELS,

    # Lead Agents (Coordinators)
    "backend_project_coordinator_agent": COORDINATOR_MODELS_A,
    "devops_and_integration_coordinator_agent": COORDINATOR_MODELS_B,
    "mobile_project_coordinator_agent": COORDINATOR_MODELS_A,
    "offline_support_coordinator_agent": DOCS_UTILITY_MODELS_A, # Simpler coordination
    "web_project_coordinator_agent": COORDINATOR_MODELS_B,
    "auth_coordinator_agent": COORDINATOR_MODELS_A,

    # --- Specialized Implementation/Utility Agents ---
    "software_engineer_agent": GENERIC_CODE_WRITER_MODELS, # If it's used for large coding tasks

    "otp_verifier_agent": DOCS_UTILITY_MODELS_A,
    "api_creator_agent": BACKEND_MODULE_MODELS,
    "auth_agent_backend": BACKEND_MODULE_MODELS, # Security-sensitive code
    "config_agent_backend": DOCS_UTILITY_MODELS_B, # Often simpler, structured files
    "data_model_agent_backend": BACKEND_MODULE_MODELS, # Needs precision
    "queue_agent_backend": DOCS_UTILITY_MODELS_A,
    "storage_agent_backend": BACKEND_MODULE_MODELS, # Logic for DB interaction
    "sync_agent_backend": DOCS_UTILITY_MODELS_B,
    "code_writer_agent": GENERIC_CODE_WRITER_MODELS, # Dev utilities generic code writer
    "debugger_agent": DETERMINISTIC_CODE_MODELS, # Needs to understand code precisely
    "logger_agent_devutils": DOCS_UTILITY_MODELS_A,
    "tester_agent_devutils": DOCS_UTILITY_MODELS_B, # Test generation can be creative but also structured
    "devops_agent": SCAFFOLDING_API_MODELS, # Scripts, configs

    "android_api_client_agent": MOBILE_COMPONENT_MODELS,
    "android_ui_agent": MOBILE_COMPONENT_MODELS,
    "ios_api_client_agent": MOBILE_COMPONENT_MODELS,
    "ios_ui_agent": MOBILE_COMPONENT_MODELS,
    "android_storage_agent": DOCS_UTILITY_MODELS_B, # Simpler file/DB interactions
    "ios_storage_agent": DOCS_UTILITY_MODELS_A,

    "local_storage_agent_offline": DOCS_UTILITY_MODELS_B,
    "sync_agent_offline": DOCS_UTILITY_MODELS_A,

    "asset_manager_agent_web": DOCS_UTILITY_MODELS_B,
    "dynamic_page_builder_agent_web": WEB_PAGE_MODELS,
    "static_page_builder_agent_web": WEB_PAGE_MODELS, # Template-heavy

    "constraint_checker_agent_tech_committee": DOCS_UTILITY_MODELS_A, # Analysis, not generation
    "documentation_writer_agent_tech_committee": DOCS_UTILITY_MODELS_B, # Text generation focus
    "knowledge_base_tool_summarizer": DOCS_UTILITY_MODELS_A,

    # --- Crew-level LLMs ---
    "final_assembly_crew": PLANNING_DESIGN_MODELS,
    "backend_development_crew": SCAFFOLDING_API_MODELS,
    "devops_crew": SCAFFOLDING_API_MODELS,
    "full_stack_crew": PLANNING_DESIGN_MODELS, # Needs broader understanding
    "mobile_development_crew": UI_GEN_MODELS,
    "offline_support_crew": DOCS_UTILITY_MODELS_A,
    "code_writing_crew": DETERMINISTIC_CODE_MODELS,
    "web_development_crew": UI_GEN_MODELS,

    # --- Default LLMs ---
    "default_crew_llm": [CFG_1_5_FLASH_DETERMINISTIC, CFG_2_0_FLASH_SCAFFOLD, CFG_1_5_FLASH_8B_BASIC],
    "default_agent_llm": [CFG_1_5_FLASH_8B_BASIC, CFG_2_0_FLASH_LITE_UTILITY, CFG_1_5_FLASH_DETERMINISTIC]
}

def get_llm_for_agent(agent_identifier: str, default_model_key: str = "default_agent_llm") -> Optional[LLM]:
    """
    Retrieves a configured LLM instance for a specific agent.

    Args:
        agent_identifier: A unique string identifying the agent (e.g., its role or variable name).
        default_model_key: The key in MODEL_BY_AGENT to use if agent_identifier is not found.
                           Defaults to "default_agent_llm".

    Returns:
        An LLM instance or None if configuration fails or API key is missing.
    """
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        llm_initialization_statuses.append((f"API_KEY_MISSING_FOR_{agent_identifier}", False))
        return None

    model_configs_list = MODEL_BY_AGENT.get(agent_identifier)
    if not model_configs_list:
        # print(f"No specific config list for agent '{agent_identifier}'. Using default config key: '{default_model_key}'.") # Suppressed
        model_configs_list = MODEL_BY_AGENT.get(default_model_key)
        if not model_configs_list:
            # print(f"Error: Default config key '{default_model_key}' not found. Cannot configure LLM for '{agent_identifier}'.") # Suppressed
            llm_initialization_statuses.append((f"CONFIG_LIST_ERROR_FOR_{agent_identifier}", False))
            return None

    if not isinstance(model_configs_list, list):
        # print(f"Error: Agent configuration for '{agent_identifier}' is not a list. Found: {type(model_configs_list)}") # Suppressed
        llm_initialization_statuses.append((f"CONFIG_NOT_LIST_FOR_{agent_identifier}", False))
        return None

    for i, agent_config in enumerate(model_configs_list):
        model_str = agent_config.get("model")
        max_tokens_val = agent_config.get("max_tokens")
        temp_val = agent_config.get("temperature")

        if not model_str:
            # print(f"Error: 'model' not specified in config entry {i} for '{agent_identifier}'. Config: {agent_config}") # Suppressed
            # Log this attempt as a failure for this specific model string if available, else generic
            llm_initialization_statuses.append((f"MODEL_UNDEFINED_IN_LIST_FOR_{agent_identifier}_{i}", False))
            continue # Try next model in the list

        llm_params = {"model": model_str, "num_retries": 3} # num_retries can also be configurable
        if max_tokens_val is not None:
            llm_params["max_tokens"] = max_tokens_val
        if temp_val is not None:
            llm_params["temperature"] = temp_val

        # print(f"Attempting to initialize LLM for agent '{agent_identifier}' with model config {i+1}/{len(model_configs_list)}: {llm_params}") # Suppressed
        try:
            llm = LLM(**llm_params)
            # If LLM instantiation is successful, consider it primarily successful for this configuration.
            # print(f"Successfully initialized LLM for agent '{agent_identifier}' with model '{model_str}'.") # Suppressed
            llm_initialization_statuses.append((f"{model_str} (initialized)", True))
            return llm # Return the successfully initialized LLM
        except Exception as e_init:
            # print(f"Failed to initialize LLM for agent '{agent_identifier}' with model '{model_str}' (Attempt {i+1}/{len(model_configs_list)}): {e_init}") # Suppressed
            llm_initialization_statuses.append((f"{model_str} (init_exception: {str(e_init)[:50]})", False))
            # Continue to the next model in the list if initialization fails

    # print(f"All model configurations failed for agent '{agent_identifier}'.") # Suppressed
    return None # Return None if all models in the list fail

# Global default LLM for general use by Crews or as a fallback if an agent-specific one isn't assigned directly.
default_crew_llm = get_llm_for_agent("default_crew_llm") # default_model_key will be "default_agent_llm" if "default_crew_llm" not found

# The initialization of default_crew_llm itself will append to llm_initialization_statuses via get_llm_for_agent.
# So, no separate print or status update is needed here for default_crew_llm's own initialization.
# We can add a general print statement that confirms its status based on the list, if desired, for clarity.

if not default_crew_llm:
    # This specific print is useful because it indicates a critical failure for the default LLM.
    # The status list will reflect this, but an explicit message here is fine.
    # print("llm_config.py: `default_crew_llm` (and thus `default_llm`) could not be initialized. This is critical.") # Suppressed
    # Ensure its status is logged if get_llm_for_agent failed before appending (e.g. API key missing early)
    # However, get_llm_for_agent should handle appending its own failure.
    pass # The failure is recorded in llm_initialization_statuses
else:
    # This print is mostly for confirmation during script load. The status list is the source of truth for display.
    # print(f"llm_config.py: `default_crew_llm` (and `default_llm`) initialization attempt completed. Check status list for details.") # Suppressed
    pass

# Note: The old `default_llm` variable is no longer the primary way to get LLMs.
# Agents/Crews should ideally call `get_llm_for_agent(their_identifier)` or be passed an LLM.
# `default_crew_llm` is provided as a general fallback, particularly for Crew instances.
# For clarity in main.py, it might import and use `default_crew_llm` for the crew.
# Or, main.py could choose a specific agent's LLM for the crew if that's more appropriate.
# This file no longer defines a single `default_llm` for all purposes.
# However, to maintain compatibility with how `main.py` currently imports `default_llm`,
# we can alias `default_crew_llm` to `default_llm` for now.
default_llm = default_crew_llm
# The status of default_llm is already captured by the call to get_llm_for_agent for 'default_crew_llm'.
# No need for further status updates or prints here regarding default_llm specifically,
# as they would be redundant with the get_llm_for_agent logging and status list.

# Final check for clarity in logs (optional)
# found_default_status = False
# for name, status in llm_initialization_statuses:
#     if name == "default_crew_llm" or name.startswith("default_crew_llm "): # Handles the modified name if default was used
#         found_default_status = True
#         print(f"llm_config.py: `default_llm` (alias for `default_crew_llm`) status in list: {'Ready' if status else 'Failed'}.")
#         break
# if not found_default_status:
#     print("llm_config.py: Status for `default_crew_llm` not found in list, this might indicate an issue before status recording.")

# The print statements within get_llm_for_agent and the one for default_crew_llm initialization failure
# are sufficient for console feedback during module load. The UI display will use llm_initialization_statuses.
