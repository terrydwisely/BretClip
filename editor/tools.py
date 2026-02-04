"""Annotation tools for the editor canvas."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Tuple, Optional
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor


class ToolType(Enum):
    """Available annotation tools."""
    SELECT = auto()      # Selection/move tool
    PEN = auto()         # Freehand drawing
    HIGHLIGHTER = auto() # Semi-transparent marker
    RECTANGLE = auto()   # Rectangle shape
    CIRCLE = auto()      # Ellipse shape
    ARROW = auto()       # Arrow line
    TEXT = auto()        # Text insertion
    ERASER = auto()      # Erase annotations


@dataclass
class AnnotationTool:
    """Configuration for an annotation tool."""
    tool_type: ToolType
    color: QColor = None
    size: int = 3
    opacity: float = 1.0

    def __post_init__(self):
        if self.color is None:
            self.color = QColor(255, 0, 0)  # Default red

        # Highlighter specific settings
        if self.tool_type == ToolType.HIGHLIGHTER:
            self.opacity = 0.4
            self.size = 20
            if self.color == QColor(255, 0, 0):
                self.color = QColor(255, 255, 0)  # Default yellow


@dataclass
class Annotation:
    """Represents a single annotation on the canvas."""
    tool: AnnotationTool
    points: List[QPoint]
    text: str = ""  # For text annotations


class AnnotationHistory:
    """Manages undo/redo history for annotations."""

    def __init__(self, max_history: int = 50):
        self.history: List[List[Annotation]] = [[]]
        self.current_index: int = 0
        self.max_history = max_history

    def add_state(self, annotations: List[Annotation]):
        """Add a new state to history."""
        # Remove any redo states
        self.history = self.history[:self.current_index + 1]

        # Add new state (deep copy)
        new_state = [Annotation(
            tool=AnnotationTool(
                tool_type=a.tool.tool_type,
                color=QColor(a.tool.color),
                size=a.tool.size,
                opacity=a.tool.opacity
            ),
            points=list(a.points),
            text=a.text
        ) for a in annotations]

        self.history.append(new_state)
        self.current_index += 1

        # Trim old history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.current_index = len(self.history) - 1

    def undo(self) -> Optional[List[Annotation]]:
        """Undo to previous state."""
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]
        return None

    def redo(self) -> Optional[List[Annotation]]:
        """Redo to next state."""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        return None

    def can_undo(self) -> bool:
        return self.current_index > 0

    def can_redo(self) -> bool:
        return self.current_index < len(self.history) - 1

    def clear(self):
        """Clear all history."""
        self.history = [[]]
        self.current_index = 0
