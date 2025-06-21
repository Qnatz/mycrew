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
        print(f"DEBUG_ONNXEMBEDDER: embed_documents called with {len(texts)} documents.")
        if not ONNXEmbedder.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY or self.actual_onnx_embed_function is None:
            print("DEBUG_ONNXEMBEDDER: Underlying embedding system not ready. Returning empty embeddings for documents.")
            return [[] for _ in texts]

        embeddings = []
        for i, text_item in enumerate(texts):
            print(f"DEBUG_ONNXEMBEDDER: Processing document {i+1}/{len(texts)}, snippet: '{text_item[:100]}...'")
            try:
                np_embedding = self.actual_onnx_embed_function(text_item)
                if isinstance(np_embedding, np.ndarray) and np_embedding.size > 0 and np.any(np_embedding):
                    print(f"DEBUG_ONNXEMBEDDER: Doc {i+1} - Embedding successful, shape: {np_embedding.shape}")
                    embeddings.append(np_embedding.tolist())
                else:
                    print(f"DEBUG_ONNXEMBEDDER: Doc {i+1} - Warning - received zero, empty, or invalid embedding. np_embedding type: {type(np_embedding)}, content: {str(np_embedding)[:100]}")
                    embeddings.append([])
            except Exception as e:
                print(f"DEBUG_ONNXEMBEDDER: Doc {i+1} - Error in embed_documents: {e}")
                import traceback
                traceback.print_exc()
                embeddings.append([])
        print(f"DEBUG_ONNXEMBEDDER: embed_documents finished. Returning {len(embeddings)} embeddings.")
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        print(f"DEBUG_ONNXEMBEDDER: embed_query called with text snippet: '{text[:100]}...'")
        if not ONNXEmbedder.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY or self.actual_onnx_embed_function is None:
            print("DEBUG_ONNXEMBEDDER: Underlying embedding system not ready. Returning empty embedding for query.")
            return []

        try:
            np_embedding = self.actual_onnx_embed_function(text)
            if isinstance(np_embedding, np.ndarray) and np_embedding.size > 0 and np.any(np_embedding): # Check size and if not all zeros
                print(f"DEBUG_ONNXEMBEDDER: Query embedding successful, shape: {np_embedding.shape}")
                return np_embedding.tolist()
            else:
                print(f"DEBUG_ONNXEMBEDDER: Warning - received zero, empty, or invalid embedding for query. np_embedding type: {type(np_embedding)}, content: {str(np_embedding)[:100]}")
                return []
        except Exception as e:
            print(f"DEBUG_ONNXEMBEDDER: Error in embed_query: {e}")
            import traceback
            traceback.print_exc()
            return []

    def __call__(self, texts: Documents) -> Embeddings:
        # texts is List[str] (aliased as Documents by ChromaDB)
        # Embeddings is List[List[float]]
        return self.embed_documents(texts)
