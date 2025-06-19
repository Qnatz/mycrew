import os
import sys
# Ensure 'mycrews' is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from mycrews.qrew.tools import knowledge_base_tool_instance
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_tool_instance_directly():
    print("--- Starting Taskmaster's KnowledgeBaseTool Instance Test ---")

    # This was done in a previous step.

    # 1. Verify the type and configuration of the memory_instance
    print(f"KB Tool Memory Instance Type: {type(knowledge_base_tool_instance.memory_instance)}")
    assert isinstance(knowledge_base_tool_instance.memory_instance, ONNXObjectBoxMemory), \
        f"Expected ONNXObjectBoxMemory, got {type(knowledge_base_tool_instance.memory_instance)}"

    actual_db_path = knowledge_base_tool_instance.memory_instance.store_path
    print(f"KB Tool Memory Instance DB Path: {actual_db_path}")
    assert actual_db_path == expected_db_path, \
        f"Expected DB path {expected_db_path}, got {actual_db_path}"
    print("KnowledgeBaseTool instance is configured with the correct ONNXObjectBoxMemory and path.")

    # 2. Perform a direct query using the tool instance
    query1 = "What is Python?"
    print(f"\nDirectly querying tool instance with: '{query1}'")
    result1 = knowledge_base_tool_instance._run(query1)
    print("Result 1:")
    print(result1)
    assert "Python is a programming language" in result1, "Test 1 Failed: Python info not found."
    print("Test 1 Passed.")

    query2 = "Tell me about ObjectBox." # This was also in the sample data
    print(f"\nDirectly querying tool instance with: '{query2}'")
    result2 = knowledge_base_tool_instance._run(query2)
    print("Result 2:")
    print(result2)
    assert "ObjectBox is a NoSQL database for mobile apps" in result2, "Test 2 Failed: ObjectBox info not found."
    print("Test 2 Passed.")

    # 3. Test with dictionary input (without LLM)
    query3_dict = {"question": "Describe CrewAI concepts"} # CrewAI is not in default data, should be no result
    # The sample data for embed_and_store.py was:
    # "Python is a programming language."
    # "Kotlin is used for Android development."
    # "ObjectBox is a NoSQL database for mobile apps."
    # So, CrewAI is not there.
    print(f"\nDirectly querying tool instance with dict: {query3_dict}")
    result3 = knowledge_base_tool_instance._run(query3_dict)
    print("Result 3:")
    print(result3)
    assert "No relevant information found" in result3, "Test 3 Failed: Should not find CrewAI."
    print("Test 3 Passed.")

    print("\n--- End of Taskmaster's KnowledgeBaseTool Instance Test ---")

if __name__ == "__main__":
    test_tool_instance_directly()
