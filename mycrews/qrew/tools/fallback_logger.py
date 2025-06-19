import os
import json
from datetime import datetime

def fallback_log(content: str, metadata: dict, log_dir="fallback_logs"):
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        "content": content,
        "metadata": metadata,
        "timestamp": timestamp
    }
    path = os.path.join(log_dir, f"log_{timestamp.replace(':', '_')}.json")
    with open(path, "w") as f:
        json.dump(log_entry, f, indent=2)
