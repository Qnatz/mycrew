import logging
from typing import Type, Optional, Any # Added Any and Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from chromadb import PersistentClient
from .onnx_embedder import ONNXEmbedder # Assumes onnx_embedder.py is in the same 'tools' directory
from crewai import LLM as CrewAILLMBase # Corrected import for type hinting the LLM

logger = logging.getLogger(__name__)

class CustomWebComponentsRagToolSchema(BaseModel):
    query: str = Field(..., description="The search query to find relevant web components or project context.")

class CustomWebComponentsRagTool(BaseTool):
    name: str = "Web Components RAG Search"
    description: str = (
        "Essential for project analysis. Searches for existing projects, web components, "
        "and contextual information to understand and define new web-related project scopes. "
        "Use this for requests about websites or web applications."
    )
    args_schema: Type[BaseModel] = CustomWebComponentsRagToolSchema
    chroma_client: Optional[PersistentClient] = None
    embedding_function: Optional[ONNXEmbedder] = None
    llm: Optional[CrewAILLMBase] = None
    collection_name: str = "qrew_kb_web-components"

    def __init__(self,
                 chroma_client: PersistentClient,
                 embedding_function: ONNXEmbedder,
                 llm: Optional[CrewAILLMBase],
                 collection_name: str = "qrew_kb_web-components",
                 **kwargs: Any):
        super().__init__(**kwargs)
        self.chroma_client = chroma_client
        self.embedding_function = embedding_function # Stored, but Chroma client usually uses collection's EF for query
        self.llm = llm
        self.collection_name = collection_name

        if not self.chroma_client:
            logger.error(f"{self.name}: ChromaDB client not provided during initialization. Tool will not function.")
        if not self.embedding_function: # Though Chroma collection might have its own
            logger.warning(f"{self.name}: Embedding function not explicitly provided. Chroma will use collection's default.")
        if not self.llm:
            logger.warning(f"{self.name}: LLM not provided. Synthesis step will be skipped; returning raw documents.")

    def _run(self, query: str) -> str:
        if not self.chroma_client:
            return "Error: ChromaDB client not initialized for RAG tool."
        if not query or not query.strip():
            return "Error: Search query cannot be empty."

        logger.info(f"{self.name}: Received query: {query}")
        try:
            # Ensure the collection exists. get_collection will use the EF defined at collection creation.
            # The embedding_function stored in self might be for query-time embedding if the client needs it explicitly,
            # but typically client.query embeds using its own or collection's EF.
            collection = self.chroma_client.get_collection(name=self.collection_name)
            logger.info(f"{self.name}: Successfully retrieved collection '{self.collection_name}'.")
        except Exception as e:
            logger.error(f"{self.name}: Error getting ChromaDB collection '{self.collection_name}': {e}", exc_info=True)
            return f"Error: Could not access knowledge base collection '{self.collection_name}'."

        try:
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            logger.info(f"{self.name}: ChromaDB query executed. Found {len(results.get('documents', [[]])[0]) if results.get('documents') and results.get('documents',[[]]) else 0} results.")

            context_docs = results.get('documents', [[]])[0]

            if not context_docs:
                return "No relevant information found in web components knowledge base for your query."

            context_string = "\n\n---\n\n".join(context_docs)

            if not self.llm:
                logger.info(f"{self.name}: No LLM provided, returning raw retrieved context.")
                return f"Retrieved context:\n{context_string}"

            prompt = f"""Based on the following context from the 'web components' knowledge base, please answer the user's query.
If the context does not provide a direct answer, state that the information is not found in the provided context.

Context:
{context_string}

User's Query:
{query}

Answer:"""

            logger.info(f"{self.name}: Sending prompt to LLM for synthesis.")
            try:
                answer = self.llm.invoke(prompt) # Assumes CrewAI LLM wrapper's invoke returns string
                logger.info(f"{self.name}: LLM synthesis successful.")
                return str(answer) # Ensure it's a string
            except Exception as e_llm:
                logger.error(f"{self.name}: Error during LLM synthesis: {e_llm}", exc_info=True)
                return f"Error: Failed to synthesize answer using LLM. Details: {e_llm}"

        except Exception as e_query:
            logger.error(f"{self.name}: Error querying ChromaDB collection '{self.collection_name}': {e_query}", exc_info=True)
            return f"Error: Could not query knowledge base. Details: {e_query}"

# Example instantiation (for reference, actual instantiation is in inbuilt_tools.py)
# from ..llm_config import default_llm
# from .onnx_embedder import ONNXEmbedder
# if __name__ == '__main__':
#     # This is placeholder setup for testing the tool structure locally if needed
#     # It requires actual instances of chroma_client, onnx_embedder, and llm.
#     class MockLLM:
#         def invoke(self, prompt): return f"LLM processed: {prompt[:50]}..."
#
#     mock_chroma_client = None # Replace with actual client for local test
#     mock_embedder = None    # Replace with actual embedder for local test
#
#     if mock_chroma_client and mock_embedder:
#         tool = CustomWebComponentsRagTool(
#             chroma_client=mock_chroma_client,
#             embedding_function=mock_embedder,
#             llm=MockLLM()
#         )
#         # result = tool._run(query="What are common login components?")
#         # print(result)
#     else:
#         print("Mock Chroma client or embedder not available for local tool test.")
