# mycrews/qrew/utils/error_utils.py

class ErrorSummary:
    def __init__(self, error_message: str, suggestions: list[str] = None):
        self.error_message = error_message
        self.suggestions = suggestions if suggestions is not None else []

    def __str__(self):
        return f"Error: {self.error_message}\nSuggestions: {self.suggestions}"
