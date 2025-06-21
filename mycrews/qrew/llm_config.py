# mycrews/qrew/llm_config.py
import os
import logging
from crewai import LLM
from typing import Optional # For type hinting LLM | None

logger = logging.getLogger(__name__)

# List to store initialization statuses
llm_initialization_statuses = []

# --- Environment Variable Based Model Names ---
# User can override these via environment variables if needed
_gemini_model_env_var = os.getenv("GEMINI_MODEL_NAME")
if _gemini_model_env_var and "gemini" in _gemini_model_env_var.lower() and not _gemini_model_env_var.startswith("google_ai_studio/"):
    USER_SPECIFIED_GEMINI_MODEL = "google_ai_studio/" + _gemini_model_env_var
elif _gemini_model_env_var: # If set, but not gemini, or already correctly prefixed
    USER_SPECIFIED_GEMINI_MODEL = _gemini_model_env_var
else: # Default if env var is not set
    USER_SPECIFIED_GEMINI_MODEL = "google_ai_studio/gemini-1.5-flash"

USER_SPECIFIED_OPENAI_MODEL = os.getenv("OPENAI_MODEL_NAME", "gpt-4o") # Default from user prompt

# --- Gemini Model Constants (using USER_SPECIFIED_GEMINI_MODEL as the base for variations) ---
# These allow easy reference if specific Gemini models are hardcoded for certain roles,
# but primary model selection should be flexible.
VERIFIED_GEMINI_1_5_FLASH = USER_SPECIFIED_GEMINI_MODEL # Main user-specified Gemini
# Fallback/alternative Gemini models (can be adjusted or expanded)
VERIFIED_GEMINI_1_5_FLASH_8B = "google_ai_studio/gemini-1.5-flash-8b" # Added prefix
VERIFIED_GEMINI_2_0_FLASH = "google_ai_studio/gemini-2.0-flash" # Added prefix
VERIFIED_GEMINI_2_0_FLASH_LITE = "google_ai_studio/gemini-2.0-flash-lite-001" # Added prefix
VERIFIED_GEMINI_2_5_FLASH_PREVIEW = "google_ai_studio/gemini-2.5-flash-preview-04-17" # Added prefix


# --- OpenAI Model Constants ---
VERIFIED_OPENAI_GPT4O = USER_SPECIFIED_OPENAI_MODEL # Main user-specified OpenAI

# --- Configuration Objects (CFG) ---
# These define specific parameter sets for models.

# Gemini Configurations
CFG_GEMINI_1_5_FLASH_DEFAULT = {"model": VERIFIED_GEMINI_1_5_FLASH, "temperature": 0.7, "max_tokens": 2800}
CFG_GEMINI_1_5_FLASH_DETERMINISTIC = {"model": VERIFIED_GEMINI_1_5_FLASH, "temperature": 0.1, "max_tokens": 1500}
CFG_GEMINI_1_5_FLASH_8B_BASIC = {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "temperature": 0.2, "max_tokens": 1000}
CFG_GEMINI_2_0_FLASH_SCAFFOLD = {"model": VERIFIED_GEMINI_2_0_FLASH, "temperature": 0.4, "max_tokens": 2000}
CFG_GEMINI_2_0_FLASH_LITE_UTILITY = {"model": VERIFIED_GEMINI_2_0_FLASH_LITE, "temperature": 0.3, "max_tokens": 768}
CFG_GEMINI_2_5_FLASH_PREVIEW_E2E = {"model": VERIFIED_GEMINI_2_5_FLASH_PREVIEW, "temperature": 0.3, "max_tokens": 3000}
CFG_GEMINI_2_0_FLASH_CODE_WRITER = {"model": VERIFIED_GEMINI_2_0_FLASH, "temperature": 0.1, "max_tokens": 2000}
CFG_GEMINI_1_5_FLASH_8B_CODE_WRITER_LARGE = {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "temperature": 0.2, "max_tokens": 8192}
CFG_GEMINI_1_5_FLASH_8B_MODULE = {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "temperature": 0.2, "max_tokens": 4096}
CFG_GEMINI_2_0_FLASH_MODULE_DETERMINISTIC = {"model": VERIFIED_GEMINI_2_0_FLASH, "temperature": 0.2, "max_tokens": 4096}
CFG_GEMINI_1_5_FLASH_COORD = {"model": VERIFIED_GEMINI_1_5_FLASH, "temperature": 0.3, "max_tokens": 1500}

# OpenAI Configurations
CFG_OPENAI_GPT4O_DEFAULT = {"model": VERIFIED_OPENAI_GPT4O, "temperature": 0.7, "max_tokens": 3000}
CFG_OPENAI_GPT4O_DETERMINISTIC = {"model": VERIFIED_OPENAI_GPT4O, "temperature": 0.1, "max_tokens": 4000}

# --- Template Model Lists by Capability ---
# These lists define fallback chains of model configurations for different types of tasks.
# They primarily use Gemini models but can be mixed with OpenAI or other providers.

PLANNING_DESIGN_MODELS = [CFG_GEMINI_2_5_FLASH_PREVIEW_E2E, CFG_GEMINI_2_0_FLASH_SCAFFOLD, CFG_GEMINI_1_5_FLASH_DETERMINISTIC, CFG_OPENAI_GPT4O_DEFAULT]
SCAFFOLDING_API_MODELS = [CFG_GEMINI_2_0_FLASH_SCAFFOLD, CFG_GEMINI_2_5_FLASH_PREVIEW_E2E, CFG_GEMINI_1_5_FLASH_DETERMINISTIC]
DETERMINISTIC_CODE_MODELS = [CFG_GEMINI_1_5_FLASH_DETERMINISTIC, CFG_GEMINI_2_0_FLASH_SCAFFOLD, CFG_GEMINI_1_5_FLASH_8B_BASIC]
DOCS_UTILITY_MODELS_A = [CFG_GEMINI_2_0_FLASH_LITE_UTILITY, CFG_GEMINI_1_5_FLASH_8B_BASIC, CFG_GEMINI_1_5_FLASH_DETERMINISTIC]
DOCS_UTILITY_MODELS_B = [CFG_GEMINI_1_5_FLASH_8B_BASIC, CFG_GEMINI_2_0_FLASH_LITE_UTILITY, CFG_GEMINI_1_5_FLASH_DETERMINISTIC]
UI_GEN_MODELS = [CFG_GEMINI_2_0_FLASH_SCAFFOLD, CFG_GEMINI_2_5_FLASH_PREVIEW_E2E, CFG_GEMINI_1_5_FLASH_DETERMINISTIC]
COORDINATOR_MODELS_A = [CFG_GEMINI_1_5_FLASH_COORD, CFG_GEMINI_2_0_FLASH_SCAFFOLD, CFG_GEMINI_2_5_FLASH_PREVIEW_E2E]
COORDINATOR_MODELS_B = [CFG_GEMINI_1_5_FLASH_8B_BASIC, CFG_GEMINI_2_0_FLASH_SCAFFOLD, CFG_GEMINI_2_5_FLASH_PREVIEW_E2E]

TASKMASTER_AGENT_MODELS = [
    {"model": VERIFIED_GEMINI_1_5_FLASH, "max_tokens": 2800, "temperature": 0.3},
    {"model": VERIFIED_GEMINI_2_5_FLASH_PREVIEW, "max_tokens": 3000, "temperature": 0.1},
    {"model": VERIFIED_GEMINI_1_5_FLASH_8B, "max_tokens": 2800, "temperature": 0.3},
    CFG_OPENAI_GPT4O_DETERMINISTIC # Adding OpenAI as a fallback for taskmaster
]
FINAL_ASSEMBLER_AGENT_MODELS = [
    {"model": VERIFIED_GEMINI_2_0_FLASH, "temperature": 0.0, "max_tokens": 4096},
    {"model": VERIFIED_GEMINI_2_5_FLASH_PREVIEW, "temperature": 0.1, "max_tokens": 4096},
    {"model": VERIFIED_GEMINI_1_5_FLASH, "temperature": 0.1, "max_tokens": 4096},
    CFG_OPENAI_GPT4O_DETERMINISTIC # Adding OpenAI as a fallback
]
CODE_WRITER_AGENT_MODELS_ALT = [
    CFG_GEMINI_2_0_FLASH_CODE_WRITER,
    CFG_GEMINI_1_5_FLASH_8B_BASIC
]
GENERIC_CODE_WRITER_MODELS = [CFG_GEMINI_1_5_FLASH_8B_CODE_WRITER_LARGE, CFG_GEMINI_2_0_FLASH_CODE_WRITER, CFG_OPENAI_GPT4O_DEFAULT]
BACKEND_MODULE_MODELS = [CFG_GEMINI_1_5_FLASH_8B_MODULE, CFG_GEMINI_2_0_FLASH_MODULE_DETERMINISTIC, CFG_OPENAI_GPT4O_DEFAULT]
WEB_PAGE_MODELS = BACKEND_MODULE_MODELS
MOBILE_COMPONENT_MODELS = BACKEND_MODULE_MODELS

# --- Agent to Model Mapping ---
MODEL_BY_AGENT = {
    # High-capability/Orchestration/Planning Agents
    "idea_interpreter_agent": PLANNING_DESIGN_MODELS,
    "project_architect_agent": PLANNING_DESIGN_MODELS,
    "taskmaster_agent": TASKMASTER_AGENT_MODELS,
    "final_assembler_agent": FINAL_ASSEMBLER_AGENT_MODELS,
    "execution_manager_agent": PLANNING_DESIGN_MODELS,
    "tech_vetting_council_agent": PLANNING_DESIGN_MODELS,
    "stack_advisor_agent_tech_committee": PLANNING_DESIGN_MODELS,

    # Lead Agents (Coordinators)
    "backend_project_coordinator_agent": COORDINATOR_MODELS_A,
    "devops_and_integration_coordinator_agent": COORDINATOR_MODELS_B,
    "mobile_project_coordinator_agent": COORDINATOR_MODELS_A,
    "offline_support_coordinator_agent": DOCS_UTILITY_MODELS_A,
    "web_project_coordinator_agent": COORDINATOR_MODELS_B,
    "auth_coordinator_agent": COORDINATOR_MODELS_A,

    # Specialized Implementation/Utility Agents
    "software_engineer_agent": GENERIC_CODE_WRITER_MODELS,
    "otp_verifier_agent": DOCS_UTILITY_MODELS_A,
    "api_creator_agent": BACKEND_MODULE_MODELS,
    "auth_agent_backend": BACKEND_MODULE_MODELS,
    "config_agent_backend": DOCS_UTILITY_MODELS_B,
    "data_model_agent_backend": BACKEND_MODULE_MODELS,
    "queue_agent_backend": DOCS_UTILITY_MODELS_A,
    "storage_agent_backend": BACKEND_MODULE_MODELS,
    "sync_agent_backend": DOCS_UTILITY_MODELS_B,
    "code_writer_agent": GENERIC_CODE_WRITER_MODELS, # Dev utilities generic code writer
    "debugger_agent": DETERMINISTIC_CODE_MODELS,
    "logger_agent_devutils": DOCS_UTILITY_MODELS_A,
    "tester_agent_devutils": DOCS_UTILITY_MODELS_B,
    "devops_agent": SCAFFOLDING_API_MODELS,

    "android_api_client_agent": MOBILE_COMPONENT_MODELS,
    "android_ui_agent": MOBILE_COMPONENT_MODELS,
    "ios_api_client_agent": MOBILE_COMPONENT_MODELS,
    "ios_ui_agent": MOBILE_COMPONENT_MODELS,
    "android_storage_agent": DOCS_UTILITY_MODELS_B,
    "ios_storage_agent": DOCS_UTILITY_MODELS_A,

    "local_storage_agent_offline": DOCS_UTILITY_MODELS_B,
    "sync_agent_offline": DOCS_UTILITY_MODELS_A,

    "asset_manager_agent_web": DOCS_UTILITY_MODELS_B,
    "dynamic_page_builder_agent_web": WEB_PAGE_MODELS,
    "static_page_builder_agent_web": WEB_PAGE_MODELS,

    "constraint_checker_agent_tech_committee": DOCS_UTILITY_MODELS_A,
    "documentation_writer_agent_tech_committee": DOCS_UTILITY_MODELS_B,
    "knowledge_base_tool_summarizer": DOCS_UTILITY_MODELS_A,

    # Example of an agent primarily using OpenAI
    "openai_powered_summarizer": [CFG_OPENAI_GPT4O_DETERMINISTIC, CFG_GEMINI_1_5_FLASH_DETERMINISTIC],


    # Crew-level LLMs
    "final_assembly_crew": PLANNING_DESIGN_MODELS,
    "backend_development_crew": SCAFFOLDING_API_MODELS,
    "devops_crew": SCAFFOLDING_API_MODELS,
    "full_stack_crew": PLANNING_DESIGN_MODELS,
    "mobile_development_crew": UI_GEN_MODELS,
    "offline_support_crew": DOCS_UTILITY_MODELS_A,
    "code_writing_crew": DETERMINISTIC_CODE_MODELS,
    "web_development_crew": UI_GEN_MODELS,

    # Default LLMs
    "default_crew_llm": [CFG_GEMINI_1_5_FLASH_DETERMINISTIC, CFG_GEMINI_2_0_FLASH_SCAFFOLD, CFG_GEMINI_1_5_FLASH_8B_BASIC, CFG_OPENAI_GPT4O_DEFAULT],
    "default_agent_llm": [CFG_GEMINI_1_5_FLASH_8B_BASIC, CFG_GEMINI_2_0_FLASH_LITE_UTILITY, CFG_GEMINI_1_5_FLASH_DETERMINISTIC, CFG_OPENAI_GPT4O_DETERMINISTIC]
}

def get_api_key_for_model(model_name: str) -> Optional[str]:
    """Determines the appropriate API key environment variable name based on the model provider."""
    model_lower = model_name.lower()
    # Check for Google AI Studio Gemini models first
    if model_lower.startswith("google_ai_studio/gemini"):
        return os.getenv("GEMINI_API_KEY")
    # Fallback for direct gemini/ prefix if it's ever used without google_ai_studio and means something else
    elif model_lower.startswith("gemini/"): # Could be Vertex if not google_ai_studio
        # This path might still lead to DefaultCredentialsError if ADC not set for Vertex
        # but we prioritize explicit google_ai_studio calls with GEMINI_API_KEY
        logger.warning(f"Model '{model_name}' starts with 'gemini/' but not 'google_ai_studio/'. Attempting GEMINI_API_KEY but Vertex AI might be assumed by LiteLLM without ADC.")
        return os.getenv("GEMINI_API_KEY") # Or potentially a different key if Vertex had its own
    elif model_lower.startswith("gpt-") or model_lower.startswith("openai/"): # Common OpenAI prefixes
        return os.getenv("OPENAI_API_KEY")
    # Add other providers as needed:
    # elif model_lower.startswith("anthropic"):
    #     return os.getenv("ANTHROPIC_API_KEY")
    logger.warning(f"Could not determine API key for model: {model_name}. No specific provider matched for API key lookup.")
    return None # Default to None if no specific provider match

def get_llm_for_agent(agent_identifier: str, default_model_key: str = "default_agent_llm") -> Optional[LLM]:
    model_configs_list = MODEL_BY_AGENT.get(agent_identifier)
    if not model_configs_list:
        logger.info(f"No specific config list for agent '{agent_identifier}'. Using default config key: '{default_model_key}'.")
        model_configs_list = MODEL_BY_AGENT.get(default_model_key)
        if not model_configs_list:
            logger.error(f"Default config key '{default_model_key}' not found. Cannot configure LLM for '{agent_identifier}'.")
            llm_initialization_statuses.append((f"CONFIG_LIST_ERROR_FOR_{agent_identifier}", False))
            return None

    if not isinstance(model_configs_list, list):
        logger.error(f"Agent configuration for '{agent_identifier}' is not a list. Found: {type(model_configs_list)}")
        llm_initialization_statuses.append((f"CONFIG_NOT_LIST_FOR_{agent_identifier}", False))
        return None

    for i, agent_config in enumerate(model_configs_list):
        model_str = agent_config.get("model")
        max_tokens_val = agent_config.get("max_tokens")
        temp_val = agent_config.get("temperature")

        if not model_str:
            logger.error(f"'model' not specified in config entry {i} for '{agent_identifier}'. Config: {agent_config}")
            llm_initialization_statuses.append((f"MODEL_UNDEFINED_IN_LIST_FOR_{agent_identifier}_{i}", False))
            continue

        api_key_to_use = get_api_key_for_model(model_str)

        if not api_key_to_use:
            # Mask part of the model string if it's too long for the status
            model_display_name = model_str if len(model_str) < 30 else model_str[:27] + "..."
            error_msg = f"API_KEY_MISSING_FOR_MODEL_{model_display_name}_AGENT_{agent_identifier}"
            logger.error(f"No API key found for model '{model_str}' needed by agent '{agent_identifier}'.")
            llm_initialization_statuses.append((error_msg, False))
            continue # Try next model in the list if API key is missing for current one

        # Mask API key for logging
        masked_api_key = f"{api_key_to_use[:4]}...{api_key_to_use[-4:]}" if api_key_to_use and len(api_key_to_use) > 8 else "API_KEY_PRESENT"

        llm_params = {
            "model": model_str,
            "api_key": api_key_to_use, # Pass the specific API key
            "num_retries": 3
        }
        if max_tokens_val is not None:
            llm_params["max_tokens"] = max_tokens_val
        if temp_val is not None:
            llm_params["temperature"] = temp_val

        # LiteLLM specific params (if any, like api_base for custom OpenAI endpoints)
        # could be added to agent_config and then to llm_params here.
        # For example: if "api_base" in agent_config: llm_params["api_base"] = agent_config["api_base"]

        logger.info(
            f"Attempting to initialize LLM for agent '{agent_identifier}' "
            f"with model config {i+1}/{len(model_configs_list)}: "
            f"Model='{model_str}', Temp='{temp_val}', MaxTokens='{max_tokens_val}', API_Key_Source='{masked_api_key}'"
        )
        try:
            llm = LLM(**llm_params)
            logger.info(f"Successfully initialized LLM for agent '{agent_identifier}' with model '{model_str}'.")
            llm_initialization_statuses.append((f"{model_str} (Agent: {agent_identifier})", True))
            return llm
        except Exception as e_init:
            logger.error(
                f"Failed to initialize LLM for agent '{agent_identifier}' with model '{model_str}' "
                f"(Attempt {i+1}/{len(model_configs_list)}): {e_init}", exc_info=True
            )
            llm_initialization_statuses.append((f"{model_str} (init_exception: {str(e_init)[:50]})", False))

    logger.warning(f"All model configurations failed for agent '{agent_identifier}'.")
    return None

# Global default LLM
default_crew_llm = get_llm_for_agent("default_crew_llm")

if not default_crew_llm:
    logger.critical("`default_crew_llm` (and thus `default_llm`) could not be initialized. This is critical.")
else:
    logger.info(f"`default_crew_llm` (and `default_llm`) initialization attempt completed. Status in list.")

default_llm = default_crew_llm
