# mycrews/qrew/utils/llm_factory.py

def get_llm_for_agent(agent_type: str):
    if agent_type == "default":
        return "local-onnx"  # Or whatever logic you're using
    raise ValueError(f"No LLM defined for agent type: {agent_type}")
