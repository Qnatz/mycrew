import os
import numpy as np

try:
    import onnxruntime as ort
    print("Successfully imported onnxruntime.")
except ImportError:
    print("ERROR: onnxruntime package not found.")
    ort = None
    exit()

try:
    from tokenizers import Tokenizer
    print("Successfully imported tokenizers.")
except ImportError:
    print("ERROR: tokenizers package not found.")
    Tokenizer = None
    exit()

# Define embedding dimension for all-MiniLM-L6-v2 (example)
EMBEDDING_DIMENSION = 384 # This should match your model

tokenizer = None
TOKENIZER_PATH = "models/onnx/tokenizer.json"
if Tokenizer is not None:
    try:
        if os.path.exists(TOKENIZER_PATH):
            tokenizer = Tokenizer.from_file(TOKENIZER_PATH)
            print(f"Tokenizer loaded successfully from {TOKENIZER_PATH}")
        else:
            print(f"ERROR: Tokenizer file not found at {TOKENIZER_PATH}")
            tokenizer = None
    except Exception as e:
        print(f"ERROR: Failed to load tokenizer from {TOKENIZER_PATH}: {e}")
        tokenizer = None
else:
    print("ERROR: Tokenizer class not available due to import failure.")


session = None
MODEL_PATH = "models/onnx/model.onnx"
if ort is not None:
    try:
        if os.path.exists(MODEL_PATH):
            options = ort.SessionOptions()
            # Set a reasonable number of threads for intra_op_num_threads
            cpu_count = os.cpu_count()
            options.intra_op_num_threads = cpu_count if cpu_count is not None else 1

            session = ort.InferenceSession(MODEL_PATH, options)
            print(f"ONNX session initialized successfully with model: {MODEL_PATH}")
            print(f"Using {options.intra_op_num_threads} intra_op_num_threads.")

            # Print model input and output details
            print("\nModel Inputs:")
            for i, model_input in enumerate(session.get_inputs()):
                print(f"  Input {i}: Name='{model_input.name}', Shape={model_input.shape}, Type={model_input.type}")

            print("\nModel Outputs:")
            for i, model_output in enumerate(session.get_outputs()):
                print(f"  Output {i}: Name='{model_output.name}', Shape={model_output.shape}, Type={model_output.type}")

        else:
            print(f"ERROR: ONNX model file not found at {MODEL_PATH}")
            session = None
    except Exception as e:
        print(f"ERROR: Failed to initialize ONNX session with model {MODEL_PATH}: {e}")
        session = None
else:
    print("ERROR: onnxruntime not available due to import failure.")


def embed_text_minimal(text: str) -> np.ndarray:
    if session is None or tokenizer is None:
        print(f"ERROR: Embedding disabled for text '{text[:30]}...' due to missing ONNX session or tokenizer.")
        # Return a zero array of the expected dimension if known, otherwise an empty array or raise error
        return np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)

    try:
        encoded = tokenizer.encode(text)
        ids = np.array([encoded.ids], dtype=np.int64)
        mask = np.array([encoded.attention_mask], dtype=np.int64)
        types = np.array([encoded.type_ids], dtype=np.int64)

        inputs = {
            "input_ids": ids,
            "attention_mask": mask,
            "token_type_ids": types
        }

        # Verify that these input names match session.get_inputs()
        model_input_names = [inp.name for inp in session.get_inputs()]
        for key in inputs.keys():
            if key not in model_input_names:
                print(f"WARNING: Input key '{key}' not found in model's expected inputs: {model_input_names}")

        token_embeddings_output = session.run(None, inputs)

        # The output structure can vary. For sentence-transformers/all-MiniLM-L6-v2 ONNX,
        # it's often a list where the first element is the tensor of last_hidden_state.
        # And then you might need to select the [CLS] token or mean pool.
        # Assuming the structure [batch_size, sequence_length, hidden_size] for token_embeddings
        # Example: token_embeddings = token_embeddings_output[0][0] for first sentence in batch

        # Based on embed_and_store.py: session.run(None, inputs)[0][0]
        # This implies the output is a list, take first element (output tensor, e.g. "last_hidden_state")
        # then take first element of that (for batch size 1).
        if not token_embeddings_output or not isinstance(token_embeddings_output, list) or len(token_embeddings_output[0]) == 0:
            print(f"ERROR: Unexpected output structure from ONNX session.run: {token_embeddings_output}")
            return np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)

        token_embeddings = token_embeddings_output[0][0]  # Shape: (seq_len, hidden_size)

        # Mean pooling
        sentence_embedding = np.mean(token_embeddings, axis=0)
        return sentence_embedding

    except Exception as e:
        print(f"ERROR during embedding for text '{text[:30]}...': {e}")
        import traceback
        traceback.print_exc()
        return np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)


if __name__ == "__main__":
    print("\n--- Running Minimal ONNX Embedding Test ---")
    if session and tokenizer:
        test_sentence = "This is a test sentence for ONNX embedding."
        print(f"\nEmbedding test sentence: '{test_sentence}'")
        embedding = embed_text_minimal(test_sentence)

        if embedding.any(): # Check if not all zeros
            print(f"Successfully generated embedding of shape: {embedding.shape}")
            print(f"Embedding dtype: {embedding.dtype}")
            print(f"First 5 elements of embedding: {embedding[:5]}")
        else:
            print("Embedding resulted in all zeros or failed.")

        another_sentence = "Another example for testing."
        print(f"\nEmbedding another sentence: '{another_sentence}'")
        embedding2 = embed_text_minimal(another_sentence)
        if embedding2.any():
            print(f"Successfully generated embedding of shape: {embedding2.shape}")
        else:
            print("Embedding resulted in all zeros or failed for the second sentence.")
    else:
        print("\nSkipping embedding test because ONNX session or tokenizer failed to load.")

    print("\n--- Minimal ONNX Test Complete ---")
