"""Drawing canvas for image annotation."""

from PyQt5.QtWidgets import QWidget, QInputDialog
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QPixmap, QImage,
    QPainterPath, QFont, QBrush
)
from PIL import Image
from typing import Optional, List
import io

from .tools import ToolType, AnnotationTool, Annotation, AnnotationHistory


class DrawingCanvas(QWidget):
    """Canvas widget for displaying and annotating captured images."""

    image_modified = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)

        # Image state
        self.original_image: Optional[QPixmap] = None
        self.display_image: Optional[QPixmap] = None
        self.scale_factor: float = 1.0
        self.offset: QPoint = QPoint(0, 0)

        # Annotation state
        self.annotations: List[Annotation] = []
        self.current_annotation: Optional[Annotation] = None
        self.history = AnnotationHistory()

        # Current tool
        self.current_tool = AnnotationTool(ToolType.PEN, QColor(255, 0, 0), 3)

        # Drawing state
        self.is_drawing = False
        self.last_point: Optional[QPoint] = None

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_image(self, image: Image.Image):
        """Set the image to display and annotate."""
        # Convert PIL Image to QPixmap
        if image.mode == 'RGBA':
            data = image.tobytes('raw', 'RGBA')
            qimage = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        else:
            image = image.convert('RGB')
            data = image.tobytes('raw', 'RGB')
            qimage = QImage(data, image.width, image.height, QImage.Format_RGB888)

        self.original_image = QPixmap.fromImage(qimage)
        self.display_image = self.original_image.copy()

        # Clear annotations
        self.annotations = []
        self.history.clear()

        self._fit_to_window()
        self.update()

    def _fit_to_window(self):
        """Calculate scale factor to fit image in window."""
        if not self.original_image:
            return

        img_size = self.original_image.size()
        widget_size = self.size()

        # Calculate scale to fit
        scale_x = widget_size.width() / img_size.width()
        scale_y = widget_size.height() / img_size.height()
        self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't upscale

        # Center the image
        scaled_width = img_size.width() * self.scale_factor
        scaled_height = img_size.height() * self.scale_factor
        self.offset = QPoint(
            int((widget_size.width() - scaled_width) / 2),
            int((widget_size.height() - scaled_height) / 2)
        )

    def _screen_to_image(self, pos: QPoint) -> QPoint:
        """Convert screen coordinates to image coordinates."""
        return QPoint(
            int((pos.x() - self.offset.x()) / self.scale_factor),
            int((pos.y() - self.offset.y()) / self.scale_factor)
        )

    def _image_to_screen(self, pos: QPoint) -> QPoint:
        """Convert image coordinates to screen coordinates."""
        return QPoint(
            int(pos.x() * self.scale_factor + self.offset.x()),
            int(pos.y() * self.scale_factor + self.offset.y())
        )

    def set_tool(self, tool: AnnotationTool):
        """Set the current drawing tool."""
        self.current_tool = tool

    def paintEvent(self, event):
        """Draw the canvas with image and annotations."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Background
        painter.fillRect(self.rect(), QColor(45, 45, 45))

        if not self.original_image:
            # Draw placeholder
            painter.setPen(QColor(128, 128, 128))
            painter.drawText(self.rect(), Qt.AlignCenter, "No image captured")
            return

        # Draw scaled image
        scaled_size = self.original_image.size() * self.scale_factor
        target_rect = QRect(self.offset, scaled_size.toSize())
        painter.drawPixmap(target_rect, self.original_image)

        # Draw annotations
        painter.save()
        painter.translate(self.offset)
        painter.scale(self.scale_factor, self.scale_factor)

        for annotation in self.annotations + ([self.current_annotation] if self.current_annotation else []):
            self._draw_annotation(painter, annotation)

        painter.restore()

    def _draw_annotation(self, painter: QPainter, annotation: Annotation):
        """Draw a single annotation."""
        if not annotation or not annotation.points:
            return

        tool = annotation.tool

        # Set pen properties
        pen = QPen(tool.color)
        pen.setWidth(tool.size)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        if tool.tool_type == ToolType.HIGHLIGHTER:
            color = QColor(tool.color)
            color.setAlphaF(tool.opacity)
            pen.setColor(color)

        painter.setPen(pen)

        if tool.tool_type in (ToolType.PEN, ToolType.HIGHLIGHTER, ToolType.ERASER):
            # Freehand drawing
            if len(annotation.points) > 1:
                path = QPainterPath()
                path.moveTo(annotation.points[0])
                for point in annotation.points[1:]:
                    path.lineTo(point)
                painter.drawPath(path)
            elif len(annotation.points) == 1:
                painter.drawPoint(annotation.points[0])

        elif tool.tool_type == ToolType.RECTANGLE:
            if len(annotation.points) >= 2:
                rect = QRect(annotation.points[0], annotation.points[-1]).normalized()
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)

        elif tool.tool_type == ToolType.CIRCLE:
            if len(annotation.points) >= 2:
                rect = QRect(annotation.points[0], annotation.points[-1]).normalized()
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(rect)

        elif tool.tool_type == ToolType.ARROW:
            if len(annotation.points) >= 2:
                start = annotation.points[0]
                end = annotation.points[-1]

                # Draw line
                painter.drawLine(start, end)

                # Draw arrowhead
                import math
                angle = math.atan2(end.y() - start.y(), end.x() - start.x())
                arrow_size = tool.size * 4

                p1 = QPoint(
                    int(end.x() - arrow_size * math.cos(angle - math.pi / 6)),
                    int(end.y() - arrow_size * math.sin(angle - math.pi / 6))
                )
                p2 = QPoint(
                    int(end.x() - arrow_size * math.cos(angle + math.pi / 6)),
                    int(end.y() - arrow_size * math.sin(angle + math.pi / 6))
                )

                painter.drawLine(end, p1)
                painter.drawLine(end, p2)

        elif tool.tool_type == ToolType.TEXT:
            if annotation.points and annotation.text:
                font = QFont("Arial", tool.size * 4)
                painter.setFont(font)
                painter.drawText(annotation.points[0], annotation.text)

    def mousePressEvent(self, event):
        """Handle mouse press for drawing."""
        if event.button() == Qt.LeftButton and self.original_image:
            self.is_drawing = True
            pos = self._screen_to_image(event.pos())
            self.last_point = pos

            # Handle text tool differently
            if self.current_tool.tool_type == ToolType.TEXT:
                text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
                if ok and text:
                    self.current_annotation = Annotation(
                        tool=AnnotationTool(
                            tool_type=self.current_tool.tool_type,
                            color=QColor(self.current_tool.color),
                            size=self.current_tool.size,
                            opacity=self.current_tool.opacity
                        ),
                        points=[pos],
                        text=text
                    )
                    self.annotations.append(self.current_annotation)
                    self.history.add_state(self.annotations)
                    self.current_annotation = None
                    self.image_modified.emit()
                self.is_drawing = False
            else:
                self.current_annotation = Annotation(
                    tool=AnnotationTool(
                        tool_type=self.current_tool.tool_type,
                        color=QColor(self.current_tool.color),
                        size=self.current_tool.size,
                        opacity=self.current_tool.opacity
                    ),
                    points=[pos]
                )

            self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move for drawing."""
        if self.is_drawing and self.current_annotation and self.original_image:
            pos = self._screen_to_image(event.pos())

            if self.current_tool.tool_type in (ToolType.PEN, ToolType.HIGHLIGHTER, ToolType.ERASER):
                # Add point to path
                self.current_annotation.points.append(pos)
            else:
                # For shapes, just update end point
                if len(self.current_annotation.points) > 1:
                    self.current_annotation.points[-1] = pos
                else:
                    self.current_annotation.points.append(pos)

            self.last_point = pos
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finish drawing."""
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.is_drawing = False

            if self.current_annotation and len(self.current_annotation.points) > 0:
                self.annotations.append(self.current_annotation)
                self.history.add_state(self.annotations)
                self.image_modified.emit()

            self.current_annotation = None
            self.update()

    def resizeEvent(self, event):
        """Handle resize to refit image."""
        super().resizeEvent(event)
        self._fit_to_window()

    def undo(self):
        """Undo last annotation."""
        state = self.history.undo()
        if state is not None:
            self.annotations = list(state)
            self.image_modified.emit()
            self.update()

    def redo(self):
        """Redo last undone annotation."""
        state = self.history.redo()
        if state is not None:
            self.annotations = list(state)
            self.image_modified.emit()
            self.update()

    def clear_annotations(self):
        """Clear all annotations."""
        if self.annotations:
            self.annotations = []
            self.history.add_state(self.annotations)
            self.image_modified.emit()
            self.update()

    def get_final_image(self) -> Optional[Image.Image]:
        """Get the image with annotations baked in."""
        if not self.original_image:
            return None

        # Create a pixmap with annotations
        result = self.original_image.copy()
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)

        for annotation in self.annotations:
            self._draw_annotation(painter, annotation)

        painter.end()

        # Convert to PIL Image
        qimage = result.toImage()
        buffer = qimage.bits().asstring(qimage.sizeInBytes())

        if qimage.format() == QImage.Format_RGBA8888:
            return Image.frombytes('RGBA', (qimage.width(), qimage.height()), buffer, 'raw', 'RGBA')
        else:
            qimage = qimage.convertToFormat(QImage.Format_RGB888)
            buffer = qimage.bits().asstring(qimage.sizeInBytes())
            return Image.frombytes('RGB', (qimage.width(), qimage.height()), buffer, 'raw', 'RGB')
