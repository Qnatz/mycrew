from datetime import datetime

from pydantic import BaseModel, Field, PrivateAttr

from crewai.utilities.printer import Printer


class Logger(BaseModel):
    verbose: bool = Field(default=False)
    _printer: Printer = PrivateAttr(default_factory=Printer)
    default_color: str = Field(default="bold_yellow")

    def log(self, level, message, color=None):
        if color is None:
            color = self.default_color

        # Log if verbose is true OR if the level is warning/error
        if self.verbose or level.lower() in ["warning", "error"]:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Determine color based on level if not provided or if default is being used
            level_to_color_map = {
                "warning": "bold_yellow",
                "error": "bold_red",
                "info": "bold_green",  # Default for info if verbose
                "debug": "bold_blue"   # Default for debug if verbose
            }

            # If a specific color was passed to the log method, use it.
            # Otherwise, if the current color is still the default_color (meaning no specific color was passed for this message),
            # then try to pick a color based on the log level.
            # If the level doesn't have a specific color in the map, it will fall back to self.default_color.
            final_color = color
            if color == self.default_color: # Check if the color is still the initial default
                final_color = level_to_color_map.get(level.lower(), self.default_color)

            self._printer.print(
                f"\n[{timestamp}][{level.upper()}]: {message}", color=final_color
            )
