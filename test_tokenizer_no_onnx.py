import numpy as np # Explicitly import numpy for the script's own usage if needed, though tokenizer might not directly expose it in tokens if return_tensors="np" handles it internally.

print("Attempting to import AutoTokenizer...")
try:
    from transformers import AutoTokenizer
    print("AutoTokenizer imported successfully.")
except Exception as e:
    print(f"Failed to import AutoTokenizer: {e}")
    exit(1)

tokenizer_name = "sentence-transformers/all-MiniLM-L6-v2"
print(f"Attempting to load tokenizer: {tokenizer_name}...")
try:
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    print("Tokenizer loaded successfully.")
except Exception as e:
    print(f"Failed to load tokenizer: {e}")
    exit(1)

test_text = "This is a test sentence."
print(f"Attempting to tokenize text: '{test_text}'...")
try:
    tokens = tokenizer(test_text, padding="max_length", truncation=True, max_length=128, return_tensors="np")
    print(f"Tokenization successful. Input IDs: {tokens['input_ids']}")
    # Further check if 'input_ids' is what we expect, e.g., a numpy array.
    if not hasattr(tokens, 'input_ids') or not hasattr(tokens['input_ids'], 'shape'):
         print(f"Tokenization output is not as expected: {tokens}")
         exit(1)
    # Check if the output is a numpy array, as per return_tensors="np"
    if not isinstance(tokens['input_ids'], np.ndarray):
        print(f"Tokenization output 'input_ids' is not a numpy array as expected: {type(tokens['input_ids'])}")
        exit(1)
    print("Tokenizer test passed successfully.")
except Exception as e:
    print(f"Failed to tokenize text: {e}")
    exit(1)
