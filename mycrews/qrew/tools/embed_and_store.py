# tools/embed_and_store.py
import os
import numpy as np

# Conditionally import onnxruntime
try:
    import onnxruntime as ort
except ImportError:
    print("Warning: onnxruntime package not found. ONNX embedding will be disabled.")
    ort = None

# Conditionally import tokenizers.Tokenizer
try:
    from tokenizers import Tokenizer
except ImportError:
    print("Warning: tokenizers package not found. ONNX embedding will be disabled.")
    Tokenizer = None # Make Tokenizer None if import fails

# Define embedding dimension for all-MiniLM-L6-v2
EMBEDDING_DIMENSION = 384

# Keep local Entity and build_model if other local funcs depend on them,
# otherwise, they are managed by ONNXObjectBoxMemory.
# For this refactor, we'll assume they are no longer needed for the main script logic.

# Local KnowledgeEntry and build_model are no longer needed as ONNXObjectBoxMemory handles its own.
# Removing them makes the script cleaner.

# ----------------------------
# ONNX & Tokenizer Setup
# ----------------------------

tokenizer = None # Initialize tokenizer to None
TOKENIZER_PATH = "models/onnx/tokenizer.json"
if Tokenizer is not None: # Check if Tokenizer class was imported
    try:
        if os.path.exists(TOKENIZER_PATH):
            tokenizer = Tokenizer.from_file(TOKENIZER_PATH)
            print(f"Tokenizer loaded successfully from {TOKENIZER_PATH}")
        else:
            print(f"Warning: Tokenizer file not found at {TOKENIZER_PATH}. Tokenizer will be disabled.")
            # tokenizer remains None
    except Exception as e:
        print(f"Warning: Failed to load tokenizer from {TOKENIZER_PATH}: {e}. Tokenizer will be disabled.")
        tokenizer = None
else:
    # Tokenizer class itself is None because import failed
    pass # tokenizer is already None

# Configure ONNX session
session = None # Initialize session to None
MODEL_PATH = "models/onnx/model.onnx"
if ort is not None: # Check if onnxruntime was imported
    try:
        if os.path.exists(MODEL_PATH):
            options = ort.SessionOptions()
            options.intra_op_num_threads = os.cpu_count() if os.cpu_count() is not None else 1
            session = ort.InferenceSession(MODEL_PATH, options)
            print(f"ONNX session initialized successfully with model: {MODEL_PATH}")
        else:
            print(f"Warning: ONNX model file not found at {MODEL_PATH}. ONNX session will be disabled.")
            # session remains None
    except Exception as e:
        print(f"Warning: Failed to initialize ONNX session with model {MODEL_PATH}: {e}. ONNX session will be disabled.")
        session = None
else:
    # ort is None because import failed
    pass # session is already None


def embed_text(text: str) -> np.ndarray:
    if session is None or tokenizer is None or Tokenizer is None or ort is None:
        print(f"Warning: Embedding disabled for text '{text[:30]}...' due to missing ONNX session, tokenizer, or core libraries.")
        return np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)

    encoded = tokenizer.encode(text) # type: ignore # tokenizer might be None, but check above handles it
    ids = np.array([encoded.ids], dtype=np.int64)
    mask = np.array([encoded.attention_mask], dtype=np.int64)
    types = np.array([encoded.type_ids], dtype=np.int64)
    
    inputs = {
        "input_ids": ids,
        "attention_mask": mask,
        "token_type_ids": types
    }
    
    # Get token embeddings from model
    token_embeddings = session.run(None, inputs)[0][0]  # Shape: (seq_len, hidden_size)
    
    # Convert to sentence embedding using mean pooling
    return np.mean(token_embeddings, axis=0)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# ----------------------------
# Main Logic
# ----------------------------

# The __main__ block has been removed as it was related to ONNXObjectBoxMemory usage.
