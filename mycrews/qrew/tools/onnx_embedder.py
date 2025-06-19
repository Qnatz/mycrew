# mycrews/qrew/tools/onnx_embedder.py
import numpy as np
from typing import List, Optional # Ensure List and Optional are imported
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

# actual_onnx_embed_function will be imported dynamically in __init__
# from .embed_and_store import embed_text as actual_onnx_embed_function

class ONNXEmbedder(EmbeddingFunction): # Inherits from EmbeddingFunction
    EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY = False # Class-level attribute

    def __init__(self):
        """
        Wrapper for the ONNX embedding logic in embed_and_store.py,
        now compatible with ChromaDB's EmbeddingFunction interface.
        Initialization of the actual ONNX model and tokenizer happens
        within embed_and_store.py's global scope when it's first imported.
        """
        self.actual_onnx_embed_function: Optional[callable] = None
        try:
            from .embed_and_store import embed_text
            if callable(embed_text):
                self.actual_onnx_embed_function = embed_text
                ONNXEmbedder.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY = True
                print("[ONNXEmbedder] Successfully imported and configured 'embed_text' from .embed_and_store.")
            else:
                print("[ONNXEmbedder] Warning: 'embed_text' from .embed_and_store is not callable. Semantic capabilities may be unavailable.")
                # Flag remains False
        except ImportError as e:
            print(f"[ONNXEmbedder] Warning: Failed to import embedding system from .embed_and_store: {e}. Semantic capabilities may be unavailable.")
            # Flag remains False
        except Exception as e_init: # Catch any other potential errors during setup
            print(f"[ONNXEmbedder] Warning: An unexpected error occurred during ONNXEmbedder initialization: {e_init}. Semantic capabilities may be unavailable.")
            # Flag remains False

        if ONNXEmbedder.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY:
            print("[ONNXEmbedder] ChromaDB compatible wrapper initialized successfully.")
        else:
            print("[ONNXEmbedder] Warning: ChromaDB compatible wrapper initialized, but underlying embedding system is NOT ready.")


    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not ONNXEmbedder.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY or self.actual_onnx_embed_function is None:
            # Log this situation or return a specific value indicating failure
            print("[ONNXEmbedder] Underlying embedding system not ready. Returning empty embeddings for documents.")
            return [[] for _ in texts] # Return empty list of lists for each text

        embeddings = []
        for text_item in texts:
            try:
                np_embedding = self.actual_onnx_embed_function(text_item)
                if isinstance(np_embedding, np.ndarray) and np_embedding.size > 0 and np.any(np_embedding): # Check size and if not all zeros
                    embeddings.append(np_embedding.tolist())
                else:
                    print(f"[ONNXEmbedder] Warning - received zero, empty, or invalid embedding for document item: '{text_item[:50]}...'")
                    embeddings.append([]) # Append empty list for this item
            except Exception as e:
                print(f"[ONNXEmbedder] Error in embed_documents for item '{text_item[:50]}...': {e}")
                embeddings.append([]) # Append empty list for this item
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        if not ONNXEmbedder.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY or self.actual_onnx_embed_function is None:
            print("[ONNXEmbedder] Underlying embedding system not ready. Returning empty embedding for query.")
            return [] # Return empty list for the query

        try:
            np_embedding = self.actual_onnx_embed_function(text)
            if isinstance(np_embedding, np.ndarray) and np_embedding.size > 0 and np.any(np_embedding): # Check size and if not all zeros
                return np_embedding.tolist()
            else:
                print(f"[ONNXEmbedder] Warning - received zero, empty, or invalid embedding for query: '{text[:50]}...'")
                return [] # Return empty list
        except Exception as e:
            print(f"[ONNXEmbedder] Error in embed_query for item '{text[:50]}...': {e}")
            return [] # Return empty list

    def __call__(self, texts: Documents) -> Embeddings:
        # texts is List[str] (aliased as Documents by ChromaDB)
        # Embeddings is List[List[float]]
        return self.embed_documents(texts)
