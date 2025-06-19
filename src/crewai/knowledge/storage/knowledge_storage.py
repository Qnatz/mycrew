from tools.chromadb_memory import ChromaDBMemory
import contextlib
import hashlib # Keep for now, might be useful for ID generation if needed, though ObjectBox handles its own
import io
import logging
import os
import shutil
from typing import Any, Dict, List, Optional, Union


from crewai.knowledge.storage.base_knowledge_storage import BaseKnowledgeStorage
# EmbeddingConfigurator might not be needed if ChromaDBMemory handles its own embedding via tools.embedder
# from crewai.utilities import EmbeddingConfigurator
from crewai.utilities.constants import KNOWLEDGE_DIRECTORY # Might be useful for path construction
from crewai.utilities.logger import Logger
from crewai.utilities.paths import db_storage_path # For default storage path


@contextlib.contextmanager
def suppress_logging(
    level=logging.ERROR,
):
    logger = logging.getLogger(logger_name)
    original_level = logger.getEffectiveLevel()
    logger.setLevel(level)
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.suppress(UserWarning), # Keep suppressing UserWarning
    ):
        yield
    logger.setLevel(original_level)


class KnowledgeStorage(BaseKnowledgeStorage):
    """
    Uses ChromaDBMemory to store and search knowledge entries.
    """

    db_memory: ChromaDBMemory
    collection_name: str # Making collection_name non-optional, will use a default

    def __init__(
        self,
        collection_name: Optional[str] = "default_knowledge",
        # embedder parameter removed as ChromaDBMemory uses a fixed embedder
    ):
        self.collection_name = collection_name if collection_name else "default_knowledge"

        # Construct the path for ChromaDBMemory store
        specific_collection_path = os.path.join(base_storage_dir, self.collection_name)

        # Ensure the directory for this specific collection exists
        os.makedirs(specific_collection_path, exist_ok=True)

        self.db_memory = ChromaDBMemory(store_path_override=specific_collection_path)
        self.logger = Logger(self.__class__.__name__)
        self.initialize_knowledge_storage() # Call initialization logic here

    def initialize_knowledge_storage(self):
        """
        Ensures ChromaDBMemory is ready. Currently a no-op as ChromaDBMemory
        initializes its store in its own __init__.
        """
        self.logger.info(f"ObjectBoxKnowledgeStorage initialized for collection: {self.collection_name} at path: {self.db_memory._current_store_actual_path}")
        # No specific initialization steps needed here for ChromaDBMemory as it's done in its __init__.
        # This method can be expanded if future setup is required.
        pass

    def save(
        self,
        documents: List[str],
        metadata: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    ):
        """
        Saves documents and their metadata into ObjectBox.
        """
        if not self.db_memory:
            self.logger.error("ChromaDBMemory not initialized.")
            raise Exception("ChromaDBMemory not initialized.")

        for i, doc_content in enumerate(documents):
            doc_meta = None
            if metadata:
                doc_meta = metadata[i] if isinstance(metadata, list) else metadata

            try:
                self.db_memory.save(value=doc_content, metadata=doc_meta)
                self.logger.info(f"Saved document: {doc_content[:50]}...")
            except Exception as e:
                self.logger.error(f"Failed to save document: {doc_content[:50]}... Error: {e}")
                # Decide if to re-raise or collect errors
                raise

    def search(
        self,
        query: List[str],
        limit: int = 3,
        filter: Optional[dict] = None,
        score_threshold: float = 0.0, # Default to 0.0 to include all results above minimal similarity
    ) -> List[Dict[str, Any]]:
        """
        Searches for documents in ObjectBox based on query texts.
        """
        if not self.db_memory:
            self.logger.error("ChromaDBMemory not initialized.")
            raise Exception("ChromaDBMemory not initialized.")

        if not query:
            self.logger.warn("Search query is empty.")
            return []

        actual_query_text = query[0]
        if len(query) > 1:
            self.logger.info(f"Multiple queries provided, using the first one: '{actual_query_text}'.")

        if filter:
            self.logger.warn("Search filter parameter is provided but not currently supported by ChromaDBMemory. It will be ignored.")

        try:
            with suppress_logging(): # Suppress potential verbose logs from underlying libraries
                db_results = self.db_memory.query(
                    query_text=actual_query_text,
                    limit=limit,
                    score_threshold=score_threshold,
                )
        except Exception as e:
            self.logger.error(f"Error during similarity search in ChromaDBMemory: {e}")
            return [] # Return empty list on error

        # Adapt results to the expected format
        formatted_results = []
        for res in db_results:
            # Assuming ChromaDBMemory.query can be modified to return 'id'
            # If 'id' is not available, it might be omitted or set to a placeholder
            formatted_results.append({
                "id": res.get("id", hashlib.sha256(res['content'].encode()).hexdigest()), # Placeholder ID if not from DB
                "context": res["content"],
                "metadata": res.get("metadata", {}),
                "score": res["score"],
            })

        return formatted_results

    def reset(self):
        """
        Resets the knowledge storage by deleting the ObjectBox store directory.
        """
        if not self.db_memory or not self.db_memory._current_store_actual_path:
            self.logger.error("ChromaDBMemory instance or its store path is not available. Cannot reset.")
            # Optionally, try to compute the path again if self.collection_name is available
            # For now, just return to avoid errors with shutil.rmtree
            return

        store_path = self.db_memory._current_store_actual_path

        try:
            self.logger.info(f"Attempting to close ObjectBox store for collection: {self.collection_name}")
            # ChromaDBMemory.close_store() is a class method.
            # It closes the shared static store.
            ChromaDBMemory.close_store()
            self.logger.info(f"ObjectBox store closed for collection: {self.collection_name}")

            if os.path.exists(store_path):
                self.logger.info(f"Deleting store directory: {store_path}")
                shutil.rmtree(store_path)
                self.logger.info(f"Store directory deleted: {store_path}")
            else:
                self.logger.warn(f"Store directory not found, nothing to delete: {store_path}")

            # After deleting, re-initialize db_memory to a fresh state for the current instance
            # This uses the same path, which will be an empty directory now.
            specific_collection_path = os.path.join(base_storage_dir, self.collection_name)
            os.makedirs(specific_collection_path, exist_ok=True) # Ensure dir exists for new store
            self.db_memory = ChromaDBMemory(store_path_override=specific_collection_path)
            self.logger.info(f"KnowledgeStorage for '{self.collection_name}' has been reset and re-initialized.")

        except Exception as e:
            self.logger.error(f"Failed to reset knowledge storage for collection '{self.collection_name}'. Error: {e}")
            # Depending on the error, the state might be inconsistent.
            # Consider how to handle this - perhaps by setting self.db_memory to None or raising
            raise

    # Removed _create_default_embedding_function and _set_embedder_config
    # as ChromaDBMemory handles its own embedding mechanism via tools.embedder.
    # If KnowledgeStorage needs to influence embedding for other reasons, these might be reintroduced.
