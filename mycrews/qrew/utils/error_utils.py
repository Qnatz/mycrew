# mycrews/qrew/utils/error_utils.py
from typing import Optional # Added for Optional type hint

class ErrorSummary:
    def __init__(self, error_message: Optional[str] = None, suggestions: Optional[list[str]] = None): # Made error_message optional
        self.error_message = error_message if error_message is not None else "No summary error message." # Default if none provided
        self.suggestions = suggestions if suggestions is not None else []
        self.records = [] # Assuming ErrorSummary should collect records

    def add(self, stage: str, success: bool, message: str):
        """Adds a new error/success record."""
        self.records.append({
            "stage": stage,
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    def to_dict(self):
        """Converts the error summary (records) to a list of dictionaries."""
        return self.records

    def __str__(self):
        if not self.records:
            return "No errors or messages recorded."

        status_lines = []
        for record in self.records:
            status = "SUCCESS" if record["success"] else "FAILURE"
            ts = record.get('timestamp', 'N/A')
            status_lines.append(f"[{ts}] Stage '{record['stage']}': {status} - {record['message']}")

        # Include initial error message if it exists and is not the default placeholder
        initial_error_msg = ""
        if self.error_message and self.error_message != "No summary error message.":
            initial_error_msg = f"Initial Error: {self.error_message}\nSuggestions: {self.suggestions}\n\n"

        return initial_error_msg + "\n".join(status_lines)

from typing import Optional # Added for Optional type hint
from datetime import datetime # Added for timestamp in add method
