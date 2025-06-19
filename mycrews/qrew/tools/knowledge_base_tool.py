from crewai.tools import BaseTool
from typing import Union, Any, Optional
import chromadb # Added import
from chromadb.config import Settings # Added import
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store ONNX embedding model initialization status
ONNX_EMBEDDING_INITIALIZATION_STATUS = [("ONNX Embedding Model", False)]

class KnowledgeBaseTool(BaseTool): # Renamed from EnhancedKnowledgeBaseTool
    name: str = "Enhanced Knowledge Base Tool" # Name from the new tool
    description: str = (
        "A comprehensive knowledge base system that combines semantic search with LLM reasoning. "
        "First retrieves relevant context using embeddings, then generates answers using an LLM. "
        "Input can be a simple string question or a dictionary with: "
        "{'question': 'your question', 'llm': llm_instance, 'max_context': 5}"
    )
    embedding_session: Optional[ort.InferenceSession] = None
    tokenizer: Optional[Tokenizer] = None
    kb_client: Optional[chromadb.ClientAPI] = None # Changed API to ClientAPI
    kb_collection: Optional[chromadb.Collection] = None # Added kb_collection

    def __init__(
        self,
        # memory_instance is removed
        onnx_model_path: str = "models/onnx/model.onnx", # Default path from new tool
        tokenizer_path: str = "models/onnx/tokenizer.json", # Default path from new tool
        kb_persist_path: str = "kb_chroma_storage", # Added kb_persist_path
        **kwargs
    ):
        super().__init__(**kwargs)
        # self.memory_instance removed

        # Initialize ChromaDB for Knowledge Base
        try:
            os.makedirs(kb_persist_path, exist_ok=True)
            self.kb_client = chromadb.PersistentClient(path=kb_persist_path, settings=Settings(allow_reset=False))
            # The embedding_function is set to self, so this class needs a __call__ method.
            self.kb_collection = self.kb_client.get_or_create_collection(name="knowledge_base", embedding_function=self)
            logger.info(f"ChromaDB client initialized for knowledge base at {kb_persist_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB for knowledge base: {str(e)}")
            self.kb_client = None
            self.kb_collection = None

        # Initialize embedding model
        try:
            options = ort.SessionOptions()
            options.intra_op_num_threads = os.cpu_count() or 1
            self.embedding_session = ort.InferenceSession(onnx_model_path, options)
            self.tokenizer = Tokenizer.from_file(tokenizer_path)
            logger.info("Embedding model loaded successfully")
            ONNX_EMBEDDING_INITIALIZATION_STATUS[0] = ("ONNX Embedding Model", True)
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            self.embedding_session = None
            self.tokenizer = None

    def __call__(self, input: list[str]) -> list[list[float]]: # Changed 'texts' to 'input'
        """Embedding function interface for ChromaDB."""
        embeddings = []
        # Determine embedding dimension dynamically if possible, or use a fixed known one.
        # For this example, assuming 768 based on common models. This should be verified.
        # embedding_dim = self.embedding_session.get_outputs()[0].shape[-1] if self.embedding_session else 768
        # The above line is an example, actual way to get dim might vary or be fixed.
        # Let's assume _embed_text returns an ndarray of shape (dim,)
        # For now, using a placeholder dimension. This needs to be accurate.
        # A more robust way is to inspect the model's output shape during initialization.
        # However, self.embedding_session.run output shape is (1, sequence_length, dim)
        # and _embed_text averages it to (dim,). So, we need that dim.
        # If _embed_text fails, it returns None. We need to handle this.
        # Let's assume the dimension is 768 as a fallback.
        # A better approach would be to get this from the model metadata if possible,
        # or by running a dummy embedding once.
        # If self._embed_text("test") returns an array of shape (D,), then D is the dimension.
        # For now, we'll use 768 as per instructions.
        embedding_dim = 768 # Placeholder, verify this.

        # Try to get embedding dimension from a dummy run if not already known
        if self.embedding_session and self.tokenizer:
            try:
                dummy_emb = self._embed_text("test")
                if dummy_emb is not None:
                    embedding_dim = dummy_emb.shape[0]
                else: # if dummy_emb is None, _embed_text failed.
                    logger.warning(f"Dummy embedding failed, defaulting to dimension {embedding_dim}")
            except Exception as e:
                logger.warning(f"Could not determine embedding dimension dynamically: {e}, defaulting to {embedding_dim}")


        for text in input: # Changed 'texts' to 'input'
            embedding = self._embed_text(text)
            if embedding is not None:
                embeddings.append(embedding.tolist())
            else:
                # Handle cases where embedding fails, e.g., add a zero vector
                logger.warning(f"Embedding failed for text: '{text[:50]}...'. Using zero vector.")
                embeddings.append([0.0] * embedding_dim)
        return embeddings

    def _embed_text(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text using ONNX model. Returns np.ndarray."""
        if not self.tokenizer or not self.embedding_session:
            logger.warning("Tokenizer or embedding session not available for embedding text.")
            return None

        try:
            encoded = self.tokenizer.encode(text)
            inputs = {
                "input_ids": np.array([encoded.ids], dtype=np.int64),
                "attention_mask": np.array([encoded.attention_mask], dtype=np.int64),
                "token_type_ids": np.array([encoded.type_ids], dtype=np.int64)
            }
            token_embeddings = self.embedding_session.run(None, inputs)[0][0]
            return np.mean(token_embeddings, axis=0).astype(np.float32)
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            return None

    def _run(self, input_data: Union[str, dict, Any]) -> str:
        # Parse input
        question = ""
        llm = None
        max_context = 3

        if isinstance(input_data, str):
            question = input_data
        elif isinstance(input_data, dict):
            question = input_data.get("question", input_data.get("description", ""))
            llm = input_data.get("llm")
            max_context = input_data.get("max_context", 3)
        else:
            return "Error: Invalid input format. Please provide a string or dictionary with 'question' key"

        if not question:
            return "Error: No question provided"

        logger.info(f"Knowledge query: {question}")

        # Retrieve context using embeddings
        try:
            if self.embedding_session and self.tokenizer and self.kb_collection:
                query_embedding_array = self._embed_text(question)
                if query_embedding_array is not None:
                    logger.info("Successfully generated query embedding.")
                    # ChromaDB expects a list of lists for query_embeddings
                    query_embedding_list = [query_embedding_array.tolist()]

                    chroma_results = self.kb_collection.query(
                        query_embeddings=query_embedding_list,
                        n_results=max_context,
                        # include=["documents", "metadatas", "distances"] # Optional: specify what to include
                    )

                    # Process ChromaDB results
                    # chroma_results is a dict with keys like 'ids', 'documents', 'metadatas', 'distances'
                    # Each key maps to a list of lists (one inner list per query embedding)
                    if not chroma_results or not chroma_results.get("documents") or not chroma_results["documents"][0]:
                        return "No relevant information found in the knowledge base."

                    # Assuming we are interested in the documents from the first query result
                    # context_documents = [doc for doc in chroma_results["documents"][0] if doc is not None]
                    # If you store full content in metadata, you might use that instead or combine.
                    # For example, if metadata contains the original text or more structured info.
                    # Let's assume the 'documents' field contains the text we need.

                    # Check if metadatas are available and useful
                    context_items = []
                    if chroma_results.get("documents") and chroma_results["documents"][0]:
                        docs = chroma_results["documents"][0]
                        metas = chroma_results.get("metadatas", [[]])[0] if chroma_results.get("metadatas") else [None] * len(docs)
                        dists = chroma_results.get("distances", [[]])[0] if chroma_results.get("distances") else [None] * len(docs)

                        for i, doc_content in enumerate(docs):
                            meta_info = metas[i] if i < len(metas) and metas[i] else {}
                            dist_info = dists[i] if i < len(dists) and dists[i] is not None else "N/A"
                            # Example: Constructing context string, adjust as needed
                            # If 'doc_content' is what you need, use it. If metadata has the primary text, use that.
                            # This example assumes 'doc_content' (from Chroma's 'documents') is the main text.
                            context_items.append(f"Content: {doc_content} (Source: {meta_info.get('source', 'Unknown')}, Distance: {dist_info:.4f})")

                    if not context_items:
                         return "No relevant information found in the knowledge base (after processing results)."

                    context_str = "\n\n".join([f"• {item}" for item in context_items])
                    logger.info(f"Retrieved {len(context_items)} context items from ChromaDB.")

                else:
                    logger.warning("Embedding generation failed. Cannot perform vector search without query embedding.")
                    return "Embedding generation failed, cannot perform search."
            else:
                missing_components = []
                if not self.embedding_session: missing_components.append("Embedding session")
                if not self.tokenizer: missing_components.append("Tokenizer")
                if not self.kb_collection: missing_components.append("KB collection")
                logger.warning(f"{', '.join(missing_components)} not available. Cannot perform vector search.")
                return f"{', '.join(missing_components)} not available, cannot perform search."
        except Exception as e:
            logger.error(f"Knowledge retrieval error from ChromaDB: {str(e)}")
            traceback.print_exc() # Print traceback for debugging
            return f"Knowledge retrieval error: {str(e)}"

        # Generate answer with LLM if available
        if llm:
            try:
                prompt = f"""
                You are an expert knowledge assistant. Use the provided context to answer the user's question.
                If the context doesn't contain the answer, say you don't know. Don't generate false information.

                Context:
                {context_str}

                Question: {question}

                Answer:
                """
                # Assuming llm object has a 'generate' or similar method
                # This part might need adjustment based on the actual LLM interface in crewAI
                if hasattr(llm, 'generate'):
                    return llm.generate(prompt)
                elif hasattr(llm, 'invoke'): # Common in Langchain
                    return llm.invoke(prompt)
                elif hasattr(llm, 'chat'): # Another common interface
                    return llm.chat(prompt)
                else:
                    logger.error("LLM object does not have a recognized generation method (e.g., generate, invoke, chat).")
                    return f"LLM interface error. Relevant context:\n\n{context_str}"

            except Exception as e:
                logger.error(f"LLM generation error: {str(e)}")
                return f"LLM generation error: {str(e)}\n\nRelevant context:\n{context_str}"

        # Fallback to returning context if no LLM provided
        return f"Relevant knowledge context:\n\n{context_str}"

    async def _arun(self, input_data: Union[str, dict, Any]) -> str:
        # Basic async wrapper, consider true async implementation if I/O bound
        logger.info("Async _arun called, currently wraps sync _run. For true async, implement I/O calls with await.")
        return self._run(input_data) # Consider using asyncio.to_thread for CPU bound sync code in async

# Removed instantiation of knowledge_base_tool_instance
# The tool should be instantiated by the agent/system that uses it.
