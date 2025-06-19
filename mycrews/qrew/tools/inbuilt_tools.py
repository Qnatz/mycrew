# mycrews/qrew/tools/inbuilt_tools.py
# Description: Defines and groups a suite of tools for use by CrewAI agents.
# Notes:
# - Ensure API keys (SERPER_API_KEY, EXA_API_KEY, GITHUB_TOKEN) are set as environment variables.
# - Placeholder tools (UIConverter, SchemaGenerator, SecurityScanner) need real implementations.
# - RAG tool configuration is a placeholder and depends on the specific RagTool API.

import os
from typing import Optional, List, Dict, Any # Added typing imports
from crewai_tools import (
    CodeInterpreterTool,
    FileReadTool,
    FileWriterTool,
    CodeDocsSearchTool,
    # GithubSearchTool, # Commented out or removed if only using the wrapper directly
    DirectoryReadTool,
    DirectorySearchTool,
    TXTSearchTool,
    PDFSearchTool,
    MDXSearchTool,
    EXASearchTool,
    WebsiteSearchTool,
    SerperDevTool,
    RagTool,
)
from crewai_tools import GithubSearchTool as OriginalCrewAIGithubSearchTool # Import the original
from .github_tool_wrapper import GithubSearchWrapperTool # Import our new wrapper tool class
import os # Ensure os is imported
import chromadb # Added chromadb import
# from chromadb.utils.embedding_functions import OnnxEmbeddingFunction # Removed
from ..tools.onnx_embedder import ONNXEmbedder # Ensure this is present
from crewai.tools.base_tool import BaseTool  # Updated import path
from pydantic import BaseModel, Field  # Updated to use standard Pydantic v2 imports

# API Key Placeholders (using os.getenv)
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# Add other API key retrievals as necessary based on tool requirements

# Basic Tool Instantiations
code_interpreter_tool = CodeInterpreterTool()
file_read_tool = FileReadTool()
file_write_tool = FileWriterTool()
directory_read_tool = DirectoryReadTool()
directory_search_tool = DirectorySearchTool()
code_docs_search_tool = CodeDocsSearchTool()

# 1. Initialize the *original* GithubSearchTool from crewai_tools
raw_github_search_tool: Optional[OriginalCrewAIGithubSearchTool] = None # Type hint for clarity
if GITHUB_TOKEN:
    try:
        raw_github_search_tool = OriginalCrewAIGithubSearchTool(
            gh_token=GITHUB_TOKEN,
            content_types=['code', 'repo', 'issue'] # Default content types
        )
        print("Original CrewAI GithubSearchTool initialized successfully (for use by wrapper).")
    except Exception as e:
        print(f"Warning: Failed to initialize original CrewAI GithubSearchTool: {e}. It will be None.")
        raw_github_search_tool = None
else:
    print("Warning: GITHUB_TOKEN not found. Original CrewAI GithubSearchTool will be None.")
    raw_github_search_tool = None

# 2. Now, create an instance of our wrapper tool.
#    This GithubSearchWrapperTool will internally call run_github_search,
#    which will need access to the raw_github_search_tool defined above.
#    This requires github_tool_wrapper.py to import raw_github_search_tool.

github_search_tool = GithubSearchWrapperTool() # This is the tool exposed to agents
print("GithubSearchWrapperTool instance created to be used by agents.")
if raw_github_search_tool is None:
    print("Note: The underlying original GitHub search functionality for the wrapper is NOT available.")

txt_search_tool = TXTSearchTool()
pdf_search_tool = PDFSearchTool()
mdx_search_tool = MDXSearchTool()

# Robust initialization for EXASearchTool
if EXA_API_KEY:
    try:
        exa_search_tool = EXASearchTool(api_key=EXA_API_KEY)
        print("EXASearchTool initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize EXASearchTool (API key was present but init failed): {e}. Tool will be disabled.")
        exa_search_tool = None
else:
    print("Warning: EXA_API_KEY not found in environment. EXASearchTool will be disabled.")
    exa_search_tool = None

# Robust initialization for SerperDevTool
if SERPER_API_KEY:
    try:
        serper_dev_tool = SerperDevTool(api_key=SERPER_API_KEY)
        print("SerperDevTool initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize SerperDevTool (API key was present but init failed): {e}. Tool will be disabled.")
        serper_dev_tool = None
else:
    print("Warning: SERPER_API_KEY not found in environment. SerperDevTool will be disabled.")
    serper_dev_tool = None

website_search_tool = WebsiteSearchTool()

# Path to the ONNX model directory from inbuilt_tools.py
# inbuilt_tools.py -> tools -> qrew -> mycrews -> (root) -> models/onnx
# So, from tools directory: ../../../models/onnx
# this_file_dir = os.path.dirname(os.path.abspath(__file__)) # No longer needed for direct model loading here
# onnx_model_directory = os.path.join(this_file_dir, "..", "..", "..", "models", "onnx") # No longer needed

try:
    # ONNXEmbedder wrapper no longer takes model_dir directly.
    # It relies on embed_and_store.py for model loading.
    onnx_embedder_instance = ONNXEmbedder()
    print("ONNXEmbedder instance (wrapper) created successfully.")
# FileNotFoundError is less likely here unless embed_and_store.py itself is missing,
# but ImportError for embed_and_store or its dependencies is the main concern.
except ImportError as ie_e:
    onnx_embedder_instance = None
    print(f"Warning: Failed to import dependencies or embed_and_store for ONNXEmbedder (wrapper): {ie_e}. RagTool will use default embedding.")
except Exception as e:
    onnx_embedder_instance = None
    # onnx_embedder_instance = None # Removed custom wrapper instance
    # print(f"Warning: Failed to initialize ONNXEmbedder (wrapper): {e}. RagTool will use default embedding.")
    pass # Keep the block structure if other except clauses were there for other things

CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "db", "chroma_db")
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
print(f"ChromaDB persistence path set to: {CHROMA_DB_PATH}")

try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    print("ChromaDB PersistentClient initialized successfully.")
except Exception as e:
    chroma_client = None
    print(f"Warning: Failed to initialize ChromaDB PersistentClient: {e}. RagTool setup will likely fail or use defaults.")

# Instantiate our ONNXEmbedder for RAG tools
onnx_embedder_for_rag: Optional[ONNXEmbedder] = None # Added type hint for clarity
try:
    onnx_embedder_for_rag = ONNXEmbedder() # Instance for RAG tools
    if not onnx_embedder_for_rag.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY: # type: ignore
        print(f"inbuilt_tools.py: Warning - ONNXEmbedder for RAG's underlying system in .embed_and_store is not ready. RAG tool embeddings may not work.")
    print(f"inbuilt_tools.py: ONNXEmbedder for RAG tools created.")
except ImportError as ie:
    print(f"inbuilt_tools.py: CRITICAL - Failed to import or initialize ONNXEmbedder for RAG: {ie}. RAG tools will likely use default/no embeddings.")
    onnx_embedder_for_rag = None
except Exception as e:
    print(f"inbuilt_tools.py: Warning - Failed to initialize ONNXEmbedder for RAG: {e}. RAG tools will likely use default/no embeddings.")
    onnx_embedder_for_rag = None

# Custom/Placeholder Tool Definitions
class UIConverterToolPlaceholder(BaseTool):
    name: str = "UI Converter Placeholder"
    description: str = "Converts UI descriptions or designs to code. Needs real implementation."
    config: dict = {}

    def _run(self, task_details: str) -> str:
        effective_kwargs = self.config
        print(f"Placeholder: UIConverterTool running for: {task_details}, with stored config {effective_kwargs}")
        return f"Placeholder: Converted UI for task: {task_details}"

    def with_config(self, **kwargs):
        self.config = kwargs
        print(f"Placeholder: UIConverterTool instance configured with {kwargs}. Call run() on this instance.")
        return self

ui_converter = UIConverterToolPlaceholder()

class SchemaGeneratorToolPlaceholder(BaseTool):
    name: str = "Schema Generator Placeholder"
    description: str = "Generates database or API schemas from descriptions. Needs real implementation."

    def _run(self, description_and_type: str) -> str:
        print(f"Placeholder: SchemaGeneratorTool generating schema for: {description_and_type}")
        return f"Placeholder: Generated schema for {description_and_type}"

schema_generator = SchemaGeneratorToolPlaceholder()

class SecurityScannerToolPlaceholder(BaseTool):
    name: str = "Security Scanner Placeholder"
    description: str = "Scans code or configurations for vulnerabilities. Needs real implementation."

    def _run(self, path_to_scan: str) -> str:
        print(f"Placeholder: SecurityScannerTool scanning: {path_to_scan}")
        return f"Placeholder: No vulnerabilities found in {path_to_scan} (placeholder)"

security_scanner = SecurityScannerToolPlaceholder()

def ai_code_generator_func(task_description: str, framework: str):
    print(f"Placeholder: AI Code Generation for task: {task_description}, framework: {framework}")
    return f"# Placeholder code for {task_description} in {framework}\npass"

class AICodeGeneratorArgs(BaseModel):
    task_description: str = Field(..., description="Description of the coding task.")
    framework: str = Field(..., description="The framework to generate code for.")

class AICodeGeneratorToolWrapper(BaseTool):
    name: str = "AI Code Generator"
    description: str = "Generates code snippets based on task description and framework using an AI model."
    args_schema: type[BaseModel] = AICodeGeneratorArgs

    def _run(self, task_description: str, framework: str) -> str:
        return ai_code_generator_func(task_description, framework)

ai_code_generator = AICodeGeneratorToolWrapper()

# RAG Tool Configuration Function
_configured_rag_tools = {}

def configure_rag_tools(knowledge_bases: dict):
    global _configured_rag_tools, chroma_client, onnx_embedder_for_rag # Updated global
    _configured_rag_tools.clear()

    for name, path_or_config in knowledge_bases.items():
        try:
            tool_name = f"{name.replace('_', ' ').title()} RAG Search"
            tool_description = f"Performs RAG search over the {name.replace('_', ' ')} knowledge base. Config: '{path_or_config}'."

            current_tool_instance = None
            if chroma_client and onnx_embedder_for_rag and onnx_embedder_for_rag.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY: # type: ignore
                try:
                    collection_name = f"qrew_kb_{name.replace('_', '-')}"
                    # Get or create the collection with our ONNXEmbedder instance
                    chroma_collection = chroma_client.get_or_create_collection(
                        name=collection_name,
                        embedding_function=onnx_embedder_for_rag # Pass our ONNXEmbedder instance
                    )

                    current_tool_instance = RagTool(
                        source=path_or_config,
                        name=tool_name,
                        description=tool_description,
                        vector_store=chroma_collection # Pass the pre-configured collection
                        # No 'embedder', 'db_path', or 'collection_name' params for RagTool directly
                    )
                    print(f"Initialized RAG tool for '{name}' using source '{path_or_config}' and ChromaDB collection '{collection_name}' with project's ONNXEmbedder.")
                except Exception as e_rag_chroma:
                    print(f"Warning: Failed to initialize RagTool for '{name}' with ChromaDB collection and ONNXEmbedder: {e_rag_chroma}.")
                    # Fallback if specific setup fails
                    current_tool_instance = RagTool(source=path_or_config, name=tool_name, description=tool_description)
                    print(f"Initialized RAG tool for '{name}' with source '{path_or_config}' (ChromaDB/ONNXEmbedder setup failed, using RagTool default behavior).")
            else:
                # Fallback if chroma_client or onnx_embedder_for_rag is not available/ready
                current_tool_instance = RagTool(source=path_or_config, name=tool_name, description=tool_description)
                if not chroma_client:
                    print(f"Initialized RAG tool for '{name}' (Chroma client not available).")
                if not (onnx_embedder_for_rag and onnx_embedder_for_rag.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY): # type: ignore
                    print(f"Initialized RAG tool for '{name}' (Project's ONNXEmbedder not available/ready).")

            if current_tool_instance:
                _configured_rag_tools[name] = current_tool_instance
        except Exception as e:
            print(f"Failed to initialize RAG tool for '{name}' with '{path_or_config}': {e}")
            # _configured_rag_tools[name] will not be set for this tool
    return _configured_rag_tools

def get_rag_tool(name: str):
    return _configured_rag_tools.get(name)

# Preconfigured Tool Groups
file_system_tools = [file_read_tool, file_write_tool, directory_read_tool, directory_search_tool]
search_tools_general = [serper_dev_tool, exa_search_tool, website_search_tool]
code_search_tools = [code_docs_search_tool, github_search_tool]

api_dev_tools = [website_search_tool, code_docs_search_tool, exa_search_tool, github_search_tool, schema_generator]
cloud_dev_tools = [website_search_tool, code_docs_search_tool, github_search_tool]
mobile_dev_tools = [website_search_tool, github_search_tool, code_docs_search_tool, ui_converter]
web_dev_tools = file_system_tools + search_tools_general + code_search_tools + [ui_converter, serper_dev_tool]

security_tools = [security_scanner]
schema_tools = [schema_generator, code_docs_search_tool]
dev_utility_tools = [
    ai_code_generator,
    code_docs_search_tool,
    github_search_tool,
    code_interpreter_tool,
    file_read_tool,
    file_write_tool
]

coordinator_tools = [file_read_tool, directory_search_tool, github_search_tool, website_search_tool]
base_developer_tools = file_system_tools + [code_interpreter_tool, github_search_tool, code_docs_search_tool, ai_code_generator]

python_docs_tool = CodeDocsSearchTool(name="Python Documentation Search", description="Searches official Python documentation.")

print("QREW In-built tools module loaded.")
if SERPER_API_KEY:
    print("Serper API Key: Loaded")
else:
    print("Warning: Serper API Key (SERPER_API_KEY) not found in environment.")

if EXA_API_KEY:
    print("Exa API Key: Loaded")
else:
    print("Warning: Exa API Key (EXA_API_KEY) not found in environment.")

if GITHUB_TOKEN:
    print("GitHub Token: Loaded")
else:
    print("Warning: GitHub Token (GITHUB_TOKEN) for GithubSearchTool not found in environment. Some functionalities might be limited or fail.")
