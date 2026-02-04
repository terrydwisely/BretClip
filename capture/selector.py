"""Selection overlay for capturing screen regions with multi-monitor support."""

from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor, QPolygon, QPainterPath, QFont, QBrush
import ctypes
from ctypes import wintypes
from typing import Optional, List, Dict
from .modes import CaptureMode
from .screen import ScreenCapture


# Enable Per-Monitor DPI awareness (Windows 10+)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def get_all_monitors() -> List[Dict]:
    """Get all monitors using Windows EnumDisplayMonitors API.

    Returns:
        List of monitor dictionaries with left, top, width, height
    """
    monitors = []

    def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        rect = lprcMonitor.contents
        monitors.append({
            'left': rect.left,
            'top': rect.top,
            'width': rect.right - rect.left,
            'height': rect.bottom - rect.top,
            'right': rect.right,
            'bottom': rect.bottom
        })
        return True

    MonitorEnumProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(wintypes.RECT),
        ctypes.c_double
    )
    ctypes.windll.user32.EnumDisplayMonitors(None, None, MonitorEnumProc(callback), 0)
    return monitors


def get_virtual_screen_bounds() -> Dict:
    """Get the bounding rectangle of all monitors combined.

    Returns:
        Dictionary with left, top, width, height of virtual screen
    """
    monitors = get_all_monitors()
    if not monitors:
        # Fallback to primary screen
        return {'left': 0, 'top': 0, 'width': 1920, 'height': 1080}

    min_left = min(m['left'] for m in monitors)
    min_top = min(m['top'] for m in monitors)
    max_right = max(m['right'] for m in monitors)
    max_bottom = max(m['bottom'] for m in monitors)

    return {
        'left': min_left,
        'top': min_top,
        'width': max_right - min_left,
        'height': max_bottom - min_top,
        'right': max_right,
        'bottom': max_bottom
    }


def find_monitor_at_point(x: int, y: int) -> Optional[Dict]:
    """Find which monitor contains the given point.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        Monitor dictionary or None if not found
    """
    monitors = get_all_monitors()
    for mon in monitors:
        if (mon['left'] <= x < mon['right'] and
            mon['top'] <= y < mon['bottom']):
            return mon
    return monitors[0] if monitors else None


class SelectionOverlay(QWidget):
    """Fullscreen transparent overlay for selecting capture regions.

    Features:
    - Multi-monitor support with proper coordinate handling
    - Modern dark semi-transparent design
    - Clean selection rectangle with subtle styling
    """

    # Signals
    selection_complete = pyqtSignal(object)  # Emits PIL Image or None
    selection_cancelled = pyqtSignal()

    # Modern color scheme
    OVERLAY_COLOR = QColor(15, 15, 20, 160)  # Dark semi-transparent
    SELECTION_BORDER_COLOR = QColor(100, 180, 255, 255)  # Light blue border
    SELECTION_FILL_COLOR = QColor(100, 180, 255, 40)  # Subtle blue fill
    SELECTION_BORDER_WIDTH = 2
    TEXT_COLOR = QColor(255, 255, 255, 230)
    TEXT_BG_COLOR = QColor(30, 30, 35, 220)
    WINDOW_HIGHLIGHT_COLOR = QColor(100, 180, 255, 100)
    WINDOW_BORDER_COLOR = QColor(100, 180, 255, 255)

    def __init__(self, mode: CaptureMode = CaptureMode.RECTANGULAR, target_monitor: int = None):
        """Initialize the selection overlay.

        Args:
            mode: The capture mode to use
            target_monitor: Optional monitor index to target (None = all monitors)
        """
        super().__init__()
        self.mode = mode
        self.target_monitor_index = target_monitor
        self.screen_capture = ScreenCapture()

        # Get monitor information
        self.monitors = get_all_monitors()
        self.virtual_bounds = get_virtual_screen_bounds()

        # Store target monitor info
        self.target_monitor = None
        if target_monitor is not None and 0 <= target_monitor < len(self.monitors):
            self.target_monitor = self.monitors[target_monitor]

        # Selection state
        self.start_point: Optional[QPoint] = None
        self.end_point: Optional[QPoint] = None
        self.freeform_points: List[QPoint] = []
        self.is_selecting = False
        self.selection_rect: Optional[QRect] = None

        # Window capture state
        self.hovered_window: Optional[int] = None
        self.window_rect: Optional[QRect] = None

        self._setup_ui()

    def _setup_ui(self):
        """Configure the overlay window for multi-monitor coverage."""
        # Window flags for overlay behavior
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint  # Helps on some systems
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)

        # Position and size the overlay to cover the virtual screen (all monitors)
        # or just the target monitor
        if self.target_monitor:
            self.setGeometry(
                self.target_monitor['left'],
                self.target_monitor['top'],
                self.target_monitor['width'],
                self.target_monitor['height']
            )
            self.overlay_offset_x = self.target_monitor['left']
            self.overlay_offset_y = self.target_monitor['top']
        else:
            self.setGeometry(
                self.virtual_bounds['left'],
                self.virtual_bounds['top'],
                self.virtual_bounds['width'],
                self.virtual_bounds['height']
            )
            self.overlay_offset_x = self.virtual_bounds['left']
            self.overlay_offset_y = self.virtual_bounds['top']

        # Set cursor based on mode
        if self.mode in (CaptureMode.RECTANGULAR, CaptureMode.FREEFORM):
            self.setCursor(Qt.CrossCursor)
        elif self.mode == CaptureMode.WINDOW:
            self.setCursor(Qt.PointingHandCursor)

        # Instructions label with modern styling
        self.instructions = QLabel(self)
        self.instructions.setStyleSheet("""
            QLabel {
                background-color: rgba(26, 26, 30, 230);
                color: rgba(255, 255, 255, 230);
                padding: 14px 28px;
                border-radius: 10px;
                font-family: 'Segoe UI Variable', 'Segoe UI';
                font-size: 15px;
                font-weight: 500;
                border: 1px solid rgba(45, 127, 249, 60);
            }
        """)
        self._update_instructions()

    def _update_instructions(self):
        """Update instruction text based on mode."""
        texts = {
            CaptureMode.RECTANGULAR: "Click and drag to select area  |  ESC to cancel",
            CaptureMode.FREEFORM: "Click and draw to select area  |  ESC to cancel",
            CaptureMode.WINDOW: "Click on a window to capture  |  ESC to cancel",
            CaptureMode.FULLSCREEN: "Capturing fullscreen..."
        }
        self.instructions.setText(texts.get(self.mode, ""))
        self.instructions.adjustSize()

    def showEvent(self, event):
        """Position instructions when shown and ensure proper focus."""
        super().showEvent(event)

        # Force the window to the correct position (sometimes needed on Windows)
        if self.target_monitor:
            self.move(self.target_monitor['left'], self.target_monitor['top'])
        else:
            self.move(self.virtual_bounds['left'], self.virtual_bounds['top'])

        # Center instructions at top of the overlay
        overlay_width = self.width()
        self.instructions.move(
            (overlay_width - self.instructions.width()) // 2,
            40
        )

        # Ensure we have focus and are on top
        self.raise_()
        self.activateWindow()
        self.setFocus()

        # If fullscreen mode, capture immediately
        if self.mode == CaptureMode.FULLSCREEN:
            QTimer.singleShot(100, self._capture_fullscreen)

    def _capture_fullscreen(self):
        """Capture the full screen."""
        self.hide()
        QApplication.processEvents()

        # Determine which monitor to capture
        monitor_idx = 1  # Default to first monitor in mss (1-indexed)
        if self.target_monitor_index is not None:
            monitor_idx = self.target_monitor_index + 1  # mss is 1-indexed

        image = self.screen_capture.capture_fullscreen(monitor_idx)
        self.selection_complete.emit(image)
        self.close()

    def paintEvent(self, event):
        """Draw the overlay and selection indicators with modern styling."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw semi-transparent dark overlay
        painter.fillRect(self.rect(), self.OVERLAY_COLOR)

        # Draw rectangular selection
        if self.mode == CaptureMode.RECTANGULAR and self.selection_rect:
            # Clear the selection area (make it see-through)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.selection_rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Draw selection border
            pen = QPen(self.SELECTION_BORDER_COLOR, self.SELECTION_BORDER_WIDTH)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(self.SELECTION_FILL_COLOR)
            painter.drawRect(self.selection_rect)

            # Draw corner handles for visual feedback
            self._draw_corner_handles(painter, self.selection_rect)

            # Draw size indicator
            self._draw_size_indicator(painter, self.selection_rect)

        # Draw freeform selection path
        elif self.mode == CaptureMode.FREEFORM and self.freeform_points:
            pen = QPen(self.SELECTION_BORDER_COLOR, self.SELECTION_BORDER_WIDTH)
            painter.setPen(pen)

            path = QPainterPath()
            path.moveTo(self.freeform_points[0])
            for point in self.freeform_points[1:]:
                path.lineTo(point)

            if not self.is_selecting and len(self.freeform_points) > 2:
                path.closeSubpath()
                painter.setBrush(self.SELECTION_FILL_COLOR)

            painter.drawPath(path)

        # Draw window highlight
        elif self.mode == CaptureMode.WINDOW and self.window_rect:
            # Adjust window rect to local coordinates
            local_rect = QRect(
                self.window_rect.x() - self.overlay_offset_x,
                self.window_rect.y() - self.overlay_offset_y,
                self.window_rect.width(),
                self.window_rect.height()
            )
            painter.setPen(QPen(self.WINDOW_BORDER_COLOR, 3))
            painter.setBrush(self.WINDOW_HIGHLIGHT_COLOR)
            painter.drawRect(local_rect)

    def _draw_corner_handles(self, painter: QPainter, rect: QRect):
        """Draw corner handles on the selection rectangle."""
        handle_size = 8
        handle_color = self.SELECTION_BORDER_COLOR

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(handle_color))

        # Four corners
        corners = [
            (rect.left(), rect.top()),
            (rect.right() - handle_size, rect.top()),
            (rect.left(), rect.bottom() - handle_size),
            (rect.right() - handle_size, rect.bottom() - handle_size)
        ]

        for x, y in corners:
            painter.drawRoundedRect(x, y, handle_size, handle_size, 2, 2)

    def _draw_size_indicator(self, painter: QPainter, rect: QRect):
        """Draw a size indicator showing selection dimensions."""
        width = rect.width()
        height = rect.height()

        if width < 50 or height < 30:
            return  # Too small to show indicator

        size_text = f"{width} x {height}"

        font = QFont("Segoe UI Variable", 11)
        font.setWeight(QFont.Medium)
        painter.setFont(font)

        # Position at bottom of selection
        text_rect = painter.fontMetrics().boundingRect(size_text)
        text_x = rect.center().x() - text_rect.width() // 2
        text_y = rect.bottom() + 25

        # Draw background pill
        bg_rect = QRect(
            text_x - 10,
            text_y - text_rect.height() - 4,
            text_rect.width() + 20,
            text_rect.height() + 8
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.TEXT_BG_COLOR)
        painter.drawRoundedRect(bg_rect, 4, 4)

        # Draw text
        painter.setPen(self.TEXT_COLOR)
        painter.drawText(text_x, text_y - 4, size_text)

    def mousePressEvent(self, event):
        """Handle mouse press for selection start."""
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.is_selecting = True

            if self.mode == CaptureMode.RECTANGULAR:
                self.selection_rect = QRect(self.start_point, self.start_point)
                self.update()
            elif self.mode == CaptureMode.FREEFORM:
                self.freeform_points = [self.start_point]
            elif self.mode == CaptureMode.WINDOW:
                self._capture_window_at_cursor()

    def mouseMoveEvent(self, event):
        """Handle mouse move for selection update."""
        if self.mode == CaptureMode.RECTANGULAR and self.is_selecting:
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()

        elif self.mode == CaptureMode.FREEFORM and self.is_selecting:
            self.freeform_points.append(event.pos())
            self.update()

        elif self.mode == CaptureMode.WINDOW:
            self._update_hovered_window()

    def mouseReleaseEvent(self, event):
        """Handle mouse release for selection completion."""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.end_point = event.pos()

            if self.mode == CaptureMode.RECTANGULAR:
                self._capture_rectangular()
            elif self.mode == CaptureMode.FREEFORM:
                self._capture_freeform()

    def keyPressEvent(self, event):
        """Handle keyboard input."""
        if event.key() == Qt.Key_Escape:
            self.selection_cancelled.emit()
            self.close()

    def _local_to_screen(self, local_point: QPoint) -> QPoint:
        """Convert local overlay coordinates to screen coordinates."""
        return QPoint(
            local_point.x() + self.overlay_offset_x,
            local_point.y() + self.overlay_offset_y
        )

    def _capture_rectangular(self):
        """Capture the rectangular selection."""
        if not self.start_point or not self.end_point:
            self.selection_cancelled.emit()
            self.close()
            return

        rect = QRect(self.start_point, self.end_point).normalized()
        if rect.width() < 5 or rect.height() < 5:
            self.selection_cancelled.emit()
            self.close()
            return

        # Convert to screen coordinates
        screen_x = rect.x() + self.overlay_offset_x
        screen_y = rect.y() + self.overlay_offset_y

        self.hide()
        QApplication.processEvents()

        image = self.screen_capture.capture_region(
            screen_x, screen_y, rect.width(), rect.height()
        )
        self.selection_complete.emit(image)
        self.close()

    def _capture_freeform(self):
        """Capture the freeform selection."""
        if len(self.freeform_points) < 3:
            self.selection_cancelled.emit()
            self.close()
            return

        # Get bounding rect of freeform selection
        polygon = QPolygon([QPoint(p.x(), p.y()) for p in self.freeform_points])
        rect = polygon.boundingRect()

        if rect.width() < 5 or rect.height() < 5:
            self.selection_cancelled.emit()
            self.close()
            return

        # Convert to screen coordinates
        screen_x = rect.x() + self.overlay_offset_x
        screen_y = rect.y() + self.overlay_offset_y

        self.hide()
        QApplication.processEvents()

        # Capture bounding rectangle
        image = self.screen_capture.capture_region(
            screen_x, screen_y, rect.width(), rect.height()
        )

        # Create mask from polygon (offset to local coordinates)
        from PIL import Image, ImageDraw
        mask = Image.new('L', (rect.width(), rect.height()), 0)
        draw = ImageDraw.Draw(mask)

        # Convert points to local coordinates within the bounding rect
        local_points = [(p.x() - rect.x(), p.y() - rect.y()) for p in self.freeform_points]
        draw.polygon(local_points, fill=255)

        # Apply mask - create RGBA image
        image = image.convert('RGBA')
        image.putalpha(mask)

        self.selection_complete.emit(image)
        self.close()

    def _update_hovered_window(self):
        """Update the currently hovered window."""
        cursor_pos = QCursor.pos()
        hwnd = ctypes.windll.user32.WindowFromPoint(
            wintypes.POINT(cursor_pos.x(), cursor_pos.y())
        )

        # Get the top-level window
        hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)  # GA_ROOT

        if hwnd != self.hovered_window:
            self.hovered_window = hwnd
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            self.window_rect = QRect(
                rect.left, rect.top,
                rect.right - rect.left,
                rect.bottom - rect.top
            )
            self.update()

    def _capture_window_at_cursor(self):
        """Capture the window under the cursor."""
        if not self.hovered_window or not self.window_rect:
            self.selection_cancelled.emit()
            self.close()
            return

        self.hide()
        QApplication.processEvents()

        image = self.screen_capture.capture_window(self.hovered_window)
        if image:
            self.selection_complete.emit(image)
        else:
            self.selection_cancelled.emit()
        self.close()

    def closeEvent(self, event):
        """Clean up resources."""
        try:
            self.screen_capture.close()
        except Exception:
            pass
        super().closeEvent(event)


class MonitorSelectionOverlay(SelectionOverlay):
    """Selection overlay that targets a specific monitor by index.

    This is a convenience class for capturing from a specific monitor.
    """

    def __init__(self, monitor_index: int, mode: CaptureMode = CaptureMode.RECTANGULAR):
        """Initialize overlay for a specific monitor.

        Args:
            monitor_index: 0-based index of the monitor to target
            mode: The capture mode to use
        """
        super().__init__(mode=mode, target_monitor=monitor_index)


def get_monitor_info() -> List[Dict]:
    """Get information about all connected monitors.

    Returns:
        List of dictionaries with monitor information including:
        - index: Monitor index (0-based)
        - left, top: Position
        - width, height: Dimensions
        - is_primary: Whether this is likely the primary monitor (at 0,0)
    """
    monitors = get_all_monitors()
    result = []

    for i, mon in enumerate(monitors):
        result.append({
            'index': i,
            'left': mon['left'],
            'top': mon['top'],
            'width': mon['width'],
            'height': mon['height'],
            'is_primary': mon['left'] == 0 and mon['top'] == 0
        })

    return result
