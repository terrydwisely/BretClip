"""Capture mode definitions and handlers."""

from enum import Enum, auto


class CaptureMode(Enum):
    """Available screen capture modes."""
    RECTANGULAR = auto()  # Click and drag to select rectangle
    FREEFORM = auto()     # Draw freeform shape
    WINDOW = auto()       # Click to select window
    FULLSCREEN = auto()   # Capture entire screen immediately


class DelayOption(Enum):
    """Delay options before capture."""
    NONE = 0
    THREE_SEC = 3
    FIVE_SEC = 5
    TEN_SEC = 10
