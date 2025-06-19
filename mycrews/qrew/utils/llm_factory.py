# mycrews/qrew/utils/llm_factory.py

def get_llm(agent_type: str): # Renamed function
    if agent_type == "default":
        return "local-onnx"  # Or whatever logic you're using
    raise ValueError(f"No LLM defined for agent type: {agent_type}")
