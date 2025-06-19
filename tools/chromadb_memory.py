# tools/chromadb_memory.py

class ChromaDBMemory:
    def __init__(self):
        print("[ChromaDBMemory] Initialized")

    def add(self, item):
        print(f"[ChromaDBMemory] Add called with: {item}")

    def query(self, query_text):
        print(f"[ChromaDBMemory] Query called with: {query_text}")
        return ["Simulated ChromaDB result"]
