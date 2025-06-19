from mycrews.qrew.tools.inbuilt_tools import (
    code_interpreter_tool,
    file_read_tool,
    file_write_tool,
    directory_read_tool,
    directory_search_tool,
    code_docs_search_tool,
    github_search_tool,
    txt_search_tool,
    pdf_search_tool,
    mdx_search_tool,
    exa_search_tool,
    serper_dev_tool,
    website_search_tool,
    ui_converter,
    schema_generator,
    security_scanner,
    ai_code_generator,
    python_docs_tool,
    get_rag_tool # To fetch RAG tools
)

TOOL_REGISTRY = {}

# Add standard tools
standard_tools = [
    code_interpreter_tool,
    file_read_tool,
    file_write_tool,
    directory_read_tool,
    directory_search_tool,
    code_docs_search_tool,
    github_search_tool,
    txt_search_tool,
    pdf_search_tool,
    mdx_search_tool,
    exa_search_tool,
    serper_dev_tool,
    website_search_tool,
    ui_converter,
    schema_generator,
    security_scanner,
    ai_code_generator,
    python_docs_tool
]

for tool in standard_tools:
    if tool and hasattr(tool, 'name') and tool.name:
        TOOL_REGISTRY[tool.name] = tool
    elif tool:
        print(f"Warning: Tool {tool} does not have a name or is None, skipping registration.")

# Add RAG tools
try:
    from mycrews.qrew.tools.inbuilt_tools import _configured_rag_tools as actual_rag_tools_map
    if actual_rag_tools_map:
        for name, tool_instance in actual_rag_tools_map.items():
            if tool_instance and hasattr(tool_instance, 'name') and tool_instance.name:
                TOOL_REGISTRY[tool_instance.name] = tool_instance
            elif tool_instance:
                print(f"Warning: RAG Tool for '{name}' from _configured_rag_tools map exists but has no name or is None, skipping registration.")
    else: # If empty, try to call configure_rag_tools with an empty dict to initialize it, then try again.
        from mycrews.qrew.tools.inbuilt_tools import configure_rag_tools
        configure_rag_tools({}) # Initialize with no specific KBs, just to get structure if any default exists
        from mycrews.qrew.tools.inbuilt_tools import _configured_rag_tools as updated_rag_tools_map
        if updated_rag_tools_map:
            for name, tool_instance in updated_rag_tools_map.items():
                 if tool_instance and hasattr(tool_instance, 'name') and tool_instance.name:
                    TOOL_REGISTRY[tool_instance.name] = tool_instance
        elif not updated_rag_tools_map:
             # If still no RAG tools after attempted configuration, it's fine, just means none are set up.
             print("No RAG tools found or configured after attempting initialization.")


except ImportError:
    print("Warning: Could not import _configured_rag_tools from inbuilt_tools to populate RAG tools.")
except Exception as e:
    print(f"Error when trying to populate RAG tools from _configured_rag_tools: {e}")


print(f"TOOL_REGISTRY populated with {len(TOOL_REGISTRY)} tools.")
# print("Registered tools:", list(TOOL_REGISTRY.keys()))
