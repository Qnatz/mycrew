# mycrews/qrew/tools/chroma_logger.py
import os
import uuid
import datetime
from ..tools.onnx_embedder import ONNXEmbedder # This is the refactored ONNXEmbedder
from ..utils.chroma_tool_wrapper import safe_add, safe_upsert # MODIFIED IMPORT
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
import chromadb.errors # Import for specific error handling

class ChromaLogger:
    def __init__(self, collection_name: str = "qrew_system_logs", persist_directory: Optional[str] = None):
        if persist_directory is None:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            # Path from mycrews/qrew/tools to project_root (assuming project_root contains 'mycrews')
            project_root_for_db = os.path.join(current_script_dir, "..", "..", "..")
            base_persist_dir = os.path.join(project_root_for_db, ".db", "chroma_storage_logger") # Using .db
        else:
            base_persist_dir = persist_directory
        self.persist_directory = os.path.abspath(base_persist_dir)
        os.makedirs(self.persist_directory, exist_ok=True)

        self.custom_embedder_instance: Optional[ONNXEmbedder] = None
        self.client: Optional[chromadb.Client] = None
        self.collection: Optional[chromadb.Collection] = None

        # Attempt to initialize ONNXEmbedder instance once
        try:
            self.custom_embedder_instance = ONNXEmbedder()
        except Exception as e_ef:
            print(f"[ChromaLogger] Error instantiating ONNXEmbedder: {e_ef}. This is unexpected if ONNXEmbedder handles its own init errors.")
            self.custom_embedder_instance = None

        embedding_func_to_use = None
        if ONNXEmbedder.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY:
            if self.custom_embedder_instance:
                embedding_func_to_use = self.custom_embedder_instance
                print(f"[ChromaLogger] Custom ONNXEmbedder initialized and will be used for collection '{collection_name}'.")
            else:
                print(f"[ChromaLogger] Warning: ONNXEmbedder.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY is True, but instance is not available. Proceeding without embeddings.")
        else:
            print(f"[ChromaLogger] Info: Semantic embedding system (ONNX) is not available or failed to initialize. Semantic search on logs will be disabled for collection '{collection_name}'. Proceeding without embedding capabilities.")

        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(allow_reset=True)
            )
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_func_to_use
            )
            if embedding_func_to_use:
                 print(f"[ChromaLogger] Collection '{collection_name}' configured WITH custom ONNXEmbedder.")
            else:
                 print(f"[ChromaLogger] Collection '{collection_name}' configured WITHOUT custom ONNXEmbedder.")
            print(f"[ChromaLogger] Initialized ChromaLogger with collection '{collection_name}' at {self.persist_directory}")

        except Exception as e:
            print(f"[ChromaLogger] CRITICAL - Failed to initialize ChromaDB client or collection: {e}")
            self.client = None
            self.collection = None

    def _reinitialize_collection_internals(self, collection_name_for_reinit: str) -> Optional[chromadb.Collection]:
        if not self.client:
            print(f"[ChromaLogger] Client not available, cannot re-initialize collection '{collection_name_for_reinit}'.")
            return None

        embedding_func_to_use = None
        if ONNXEmbedder.EMBEDDING_SYSTEM_IMPORTED_SUCCESSFULLY and self.custom_embedder_instance:
            embedding_func_to_use = self.custom_embedder_instance

        try:
            reinit_collection = self.client.get_or_create_collection(
                name=collection_name_for_reinit,
                embedding_function=embedding_func_to_use
            )
            print(f"[ChromaLogger] Collection '{collection_name_for_reinit}' re-initialized successfully.")
            return reinit_collection
        except Exception as e_coll:
            print(f"[ChromaLogger] CRITICAL - Failed to re-initialize collection '{collection_name_for_reinit}': {e_coll}")
            return None

    def log(
        self,
        content: str,
        stage: str = "unknown",
        log_type: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        if not self.collection:
            print("[ChromaLogger] Collection not available. Cannot log.")
            return None

        custom_metadata = metadata or {}
        log_id = f"{stage}_{log_type}_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.utcnow().isoformat()

        full_metadata = {
            "stage": stage,
            "type": log_type,
            "timestamp": timestamp,
            "log_content_full": content,
            **custom_metadata
        }

        safe_add(
            collection=self.collection,
            ids=[log_id],
            documents=[content],
            metadatas=[full_metadata]
        )
        return log_id

    def save_project_state(self, project_name: str, state: Dict[str, Any]) -> Optional[str]:
        if not self.collection:
            print("[ChromaLogger] Collection not available. Cannot save project state.")
            return None

        state_id = f"state_{project_name}"
        timestamp = datetime.datetime.utcnow().isoformat()

        state_metadata = {
            "type": "project_state",
            "project_name": project_name,
            "timestamp": timestamp,
            **state
        }

        document_content = f"State snapshot for project: {project_name} at {timestamp}"

        safe_upsert(
            collection=self.collection,
            ids=[state_id],
            documents=[document_content],
            metadatas=[state_metadata]
        )
        return state_id

    def get_project_state(self, project_name: str) -> Optional[Dict[str, Any]]:
        if not self.collection:
            print("[ChromaLogger] Collection not available. Cannot get project state.")
            return None
        state_id = f"state_{project_name}"
        try:
            # Ensure result["metadatas"] is not None before accessing its length or elements
            result = self.collection.get(ids=[state_id], include=['metadatas'])
            if result and result.get("metadatas") and len(result["metadatas"]) > 0:
                return result["metadatas"][0]
            return None
        except Exception as e:
            print(f"[ChromaLogger] Error during get_project_state for '{project_name}': {e}")
            return None

    def query_logs(self, query_texts: Optional[List[str]] = None, n_results: int = 5, where_filter: Optional[Dict[str, Any]] = None, include_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        if not self.collection:
            print("[ChromaLogger] Collection not available. Cannot query logs.")
            return {}
        if not query_texts and not where_filter:
             print("[ChromaLogger] Query requires either query_texts or a where_filter.")
             return {}

        if include_fields is None:
            include_fields = ['metadatas', 'documents', 'distances']

        # Check collection count only if it's not None
        if self.collection is not None and self.collection.count() == 0:
            return {}
        try:
            return self.collection.query(
                query_texts=query_texts if query_texts else None,
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=include_fields
            )
        except Exception as e:
            print(f"[ChromaLogger] Error during query_logs: {e}")
            return {}

    def clear_all_logs_and_states(self, collection_name_to_clear: Optional[str] = None) -> None:
        if not self.client:
            print("[ChromaLogger] Client not available. Cannot clear logs.")
            return

        name_to_clear = collection_name_to_clear
        is_default_collection = False

        if self.collection and self.collection.name == name_to_clear:
            is_default_collection = True

        if not name_to_clear:
            if self.collection:
                name_to_clear = self.collection.name
                is_default_collection = True
            else:
                print("[ChromaLogger] No collection name specified and no default collection available to clear.")
                return

        if not name_to_clear:
             print("[ChromaLogger] Error: Target collection name for clearing could not be determined.")
             return

        try:
            print(f"[ChromaLogger] Attempting to delete collection: '{name_to_clear}'")
            self.client.delete_collection(name=name_to_clear)
            print(f"[ChromaLogger] Collection '{name_to_clear}' deleted successfully.")

            if is_default_collection:
                print(f"[ChromaLogger] Default collection '{name_to_clear}' was deleted. Attempting to re-initialize.")
                self.collection = self._reinitialize_collection_internals(name_to_clear)
                if self.collection:
                    print(f"[ChromaLogger] Default collection '{name_to_clear}' re-initialized.")
                else:
                    print(f"[ChromaLogger] CRITICAL: Failed to re-initialize default collection '{name_to_clear}'. Logger may be inoperable.")

        except chromadb.errors.CollectionNotFoundError: # type: ignore
            print(f"[ChromaLogger] Info: Collection '{name_to_clear}' not found. Nothing to delete.")
        except Exception as e:
            print(f"[ChromaLogger] Error during clear_all_logs_and_states for '{name_to_clear}': {e}")
