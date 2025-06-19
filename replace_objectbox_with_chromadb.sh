#!/bin/bash

TARGET="src/crewai/knowledge/storage/knowledge_storage.py"

echo "[INFO] Updating $TARGET..."

# 1. Remove import of ObjectBoxMemory if it exists
sed -i '/objectbox_memory/d' "$TARGET"

# 2. Add import for ChromaDBMemory if not already present
grep -q "from tools.chromadb_memory import ChromaDBMemory" "$TARGET" || \
sed -i '1i from tools.chromadb_memory import ChromaDBMemory' "$TARGET"

# 3. Replace ObjectBoxMemory with ChromaDBMemory in the file
sed -i 's/ObjectBoxMemory/ChromaDBMemory/g' "$TARGET"

echo "[DONE] Replaced ObjectBoxMemory with ChromaDBMemory in $TARGET."
