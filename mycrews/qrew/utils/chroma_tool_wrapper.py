# mycrews/qrew/utils/chroma_tool_wrapper.py
from .sanitizers import sanitize_metadata # Import from new utils location
from typing import List, Dict, Any
import chromadb # For type hinting chromadb.Collection

# This wrapper will contain functions that operate on a passed-in ChromaDB collection object.
# It does not initialize its own client or collection.

def safe_add(
    collection: chromadb.Collection,
    ids: List[str],
    documents: List[str],
    metadatas: List[Dict[str, Any]]
):
    """
    Sanitize metadata, then add to the provided ChromaDB collection.
    Logs and suppresses exceptions for resilience (basic logging here).
    """
    if not collection:
        print("[ChromaToolWrapper-SafeAdd] Add failed: ChromaDB collection object not provided.")
        # Consider raising an error or returning a status
        return

    if not (len(ids) == len(documents) == len(metadatas)):
        print("[ChromaToolWrapper-SafeAdd] Add failed: Mismatch in lengths of ids, documents, or metadatas.")
        # Consider raising an error
        return

    sanitized_metadatas = [sanitize_metadata(m) for m in metadatas]

    try:
        # print(f"[ChromaToolWrapper-SafeAdd] Adding {len(documents)} documents to collection '{collection.name}'.")
        collection.add(ids=ids, documents=documents, metadatas=sanitized_metadatas)
        # print(f"[ChromaToolWrapper-SafeAdd] Add successful for {len(documents)} documents to collection '{collection.name}'.")
    except Exception as e:
        # Enhanced logging could be beneficial here
        print(f"[ChromaToolWrapper-SafeAdd] Add to collection '{collection.name}' failed: {e}")
        # Depending on desired resilience, may re-raise or handle
        # raise # Optionally re-raise

def safe_upsert(
    collection: chromadb.Collection,
    ids: List[str],
    documents: List[str],
    metadatas: List[Dict[str, Any]]
):
    """
    Sanitize metadata, then upsert to the provided ChromaDB collection.
    Logs and suppresses exceptions for resilience (basic logging here).
    """
    if not collection:
        print("[ChromaToolWrapper-SafeUpsert] Upsert failed: ChromaDB collection object not provided.")
        # Consider raising an error
        return

    if not (len(ids) == len(documents) == len(metadatas)):
        print("[ChromaToolWrapper-SafeUpsert] Upsert failed: Mismatch in lengths of ids, documents, or metadatas.")
        # Consider raising an error
        return

    sanitized_metadatas = [sanitize_metadata(m) for m in metadatas]

    try:
        # print(f"[ChromaToolWrapper-SafeUpsert] Upserting {len(documents)} documents to collection '{collection.name}'.")
        collection.upsert(ids=ids, documents=documents, metadatas=sanitized_metadatas)
        # print(f"[ChromaToolWrapper-SafeUpsert] Upsert successful for {len(documents)} documents to collection '{collection.name}'.")
    except Exception as e:
        print(f"[ChromaToolWrapper-SafeUpsert] Upsert to collection '{collection.name}' failed: {e}")
        # raise # Optionally re-raise
