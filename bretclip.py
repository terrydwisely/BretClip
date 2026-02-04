"""
BretClip - A custom screen capture tool
Main entry point for the application.

Hotkey: Ctrl+Alt+B to capture
"""

import sys
import os
import ctypes
from typing import Optional

# Enable DPI awareness BEFORE importing PyQt5
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QComboBox, QFrame,
                              QGraphicsDropShadowEffect, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QColor, QFont, QPainter, QPixmap
from PIL import Image

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from capture.modes import CaptureMode, DelayOption
from capture.selector import SelectionOverlay
from editor.window import EditorWindow
from system.tray import SystemTray
from system.hotkeys import HotkeyManager


class ModeCard(QFrame):
    """A clickable card for selecting capture mode."""

    clicked = pyqtSignal()

    def __init__(self, title: str, description: str, icon_char: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 150)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("modeCard")
        self._hovered = False

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 20, 16, 16)

        # Icon using Segoe MDL2 Assets
        icon_label = QLabel(icon_char)
        icon_label.setObjectName("cardIcon")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("cardDesc")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

    def enterEvent(self, event):
        self._hovered = True
        self.setProperty("hovered", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.setProperty("hovered", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CaptureDialog(QDialog):
    """Modern card-based capture mode selector."""

    capture_requested = pyqtSignal(object, object)  # mode, delay

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BretClip")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(720, 500)

        # Store selected values
        self.selected_mode = CaptureMode.RECTANGULAR
        self.selected_delay = DelayOption.NONE

        # For window dragging
        self._drag_pos = None

        # Main container with rounded corners
        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setGeometry(0, 0, 720, 500)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        # Stylesheet
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #1a1a1e;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
            }
            QLabel#dialogTitle {
                color: #2d7ff9;
                font-family: 'Segoe UI Variable', 'Segoe UI';
                font-size: 30px;
                font-weight: 700;
                background: transparent;
            }
            QLabel#dialogSubtitle {
                color: #72727a;
                font-family: 'Segoe UI Variable', 'Segoe UI';
                font-size: 14px;
                font-weight: 400;
                background: transparent;
            }
            QFrame#modeCard {
                background-color: #222226;
                border: 1.5px solid #38383c;
                border-radius: 14px;
            }
            QFrame#modeCard[hovered="true"] {
                background-color: #28282e;
                border: 2px solid #2d7ff9;
            }
            QLabel#cardIcon {
                font-family: 'Segoe MDL2 Assets';
                font-size: 32px;
                color: #d0d0d4;
                background: transparent;
            }
            QLabel#cardTitle {
                font-family: 'Segoe UI Variable', 'Segoe UI';
                font-size: 15px;
                font-weight: 600;
                color: #ffffff;
                background: transparent;
            }
            QLabel#cardDesc {
                font-family: 'Segoe UI Variable', 'Segoe UI';
                font-size: 11px;
                font-weight: 400;
                color: #72727a;
                background: transparent;
            }
            QComboBox {
                background-color: #222226;
                color: #d0d0d4;
                border: 1.5px solid #38383c;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Segoe UI Variable', 'Segoe UI';
                font-size: 13px;
                min-width: 140px;
            }
            QComboBox:hover {
                border-color: #2d7ff9;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #72727a;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #222226;
                color: #d0d0d4;
                selection-background-color: #2d7ff9;
                font-size: 13px;
                padding: 4px;
                border: 1px solid #38383c;
                border-radius: 8px;
            }
            QLabel#delayLabel {
                color: #72727a;
                font-family: 'Segoe UI Variable', 'Segoe UI';
                font-size: 13px;
                font-weight: 500;
                background: transparent;
            }
            QLabel#escHint {
                color: #48484c;
                font-family: 'Segoe UI Variable', 'Segoe UI';
                font-size: 12px;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 32, 40, 28)

        # Title
        title = QLabel("BretClip")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Select a capture mode to get started")
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        # Mode cards in 2x2 grid
        grid = QGridLayout()
        grid.setSpacing(16)

        # Card 1: Region (Rectangular)
        rect_card = ModeCard("Region", "Click and drag\nto select area", "\uE740")
        rect_card.clicked.connect(lambda: self._quick_capture(CaptureMode.RECTANGULAR))
        grid.addWidget(rect_card, 0, 0)

        # Card 2: Window
        win_card = ModeCard("Window", "Click to capture\na window", "\uE737")
        win_card.clicked.connect(lambda: self._quick_capture(CaptureMode.WINDOW))
        grid.addWidget(win_card, 0, 1)

        # Card 3: Freeform
        free_card = ModeCard("Freeform", "Draw a custom\nshape to capture", "\uED63")
        free_card.clicked.connect(lambda: self._quick_capture(CaptureMode.FREEFORM))
        grid.addWidget(free_card, 1, 0)

        # Card 4: Fullscreen
        full_card = ModeCard("Fullscreen", "Capture the\nentire screen", "\uE78B")
        full_card.clicked.connect(lambda: self._quick_capture(CaptureMode.FULLSCREEN))
        grid.addWidget(full_card, 1, 1)

        # Center the grid
        grid_container = QHBoxLayout()
        grid_container.addStretch()
        grid_container.addLayout(grid)
        grid_container.addStretch()
        layout.addLayout(grid_container)

        layout.addSpacing(8)

        # Delay row
        delay_row = QHBoxLayout()
        delay_row.setAlignment(Qt.AlignCenter)
        delay_row.setSpacing(10)

        delay_label = QLabel("Delay:")
        delay_label.setObjectName("delayLabel")
        delay_row.addWidget(delay_label)

        self.delay_combo = QComboBox()
        self.delay_combo.addItem("None", DelayOption.NONE)
        self.delay_combo.addItem("3s", DelayOption.THREE_SEC)
        self.delay_combo.addItem("5s", DelayOption.FIVE_SEC)
        self.delay_combo.addItem("10s", DelayOption.TEN_SEC)
        delay_row.addWidget(self.delay_combo)

        layout.addLayout(delay_row)

        layout.addStretch()

        # ESC hint
        esc_hint = QLabel("Press ESC to cancel")
        esc_hint.setObjectName("escHint")
        esc_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(esc_hint)

        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 720) // 2
        y = (screen.height() - 500) // 2
        self.move(x, y)

    def _quick_capture(self, mode: CaptureMode):
        """Start capture with selected mode and current delay."""
        self.selected_mode = mode
        self.selected_delay = self.delay_combo.currentData()
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class SignalBridge(QObject):
    """Bridge for thread-safe signal emission."""
    trigger_capture = pyqtSignal()
    trigger_direct_capture = pyqtSignal(object)  # Carries CaptureMode
    trigger_show = pyqtSignal()


class BretClipApp:
    """Main application controller."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Set application info
        self.app.setApplicationName("BretClip")
        self.app.setOrganizationName("BretClip")

        # Load icon
        self.icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets", "icon.ico"
        )

        if os.path.exists(self.icon_path):
            self.app.setWindowIcon(QIcon(self.icon_path))

        # Components
        self.editor: Optional[EditorWindow] = None
        self.selector: Optional[SelectionOverlay] = None
        self.capture_dialog: Optional[CaptureDialog] = None

        # Signal bridge for thread-safe operations
        self.signals = SignalBridge()
        self.signals.trigger_capture.connect(self._show_capture_dialog)
        self.signals.trigger_direct_capture.connect(self._direct_capture)
        self.signals.trigger_show.connect(self._show_editor)

        # System tray
        self.tray = SystemTray(self.icon_path if os.path.exists(self.icon_path) else None)
        self.tray.on_new_capture = self._on_tray_capture
        self.tray.on_show_window = self._on_tray_show
        self.tray.on_exit = self._on_exit

        # Hotkey manager
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.set_callback(self._on_hotkey)

        # Delay timer
        self.delay_timer: Optional[QTimer] = None
        self.pending_mode: Optional[CaptureMode] = None

    def _create_editor(self):
        """Create the editor window if not exists."""
        if self.editor is None:
            self.editor = EditorWindow()
            self.editor.new_capture_requested.connect(self._show_capture_dialog)
            self.editor.closed.connect(self._on_editor_closed)

            if os.path.exists(self.icon_path):
                self.editor.setWindowIcon(QIcon(self.icon_path))

    def _on_hotkey(self):
        """Handle global hotkey press."""
        self.signals.trigger_capture.emit()

    def _on_tray_capture(self, mode: str = None):
        """Handle capture request from tray."""
        if mode:
            mode_map = {
                'rectangular': CaptureMode.RECTANGULAR,
                'freeform': CaptureMode.FREEFORM,
                'window': CaptureMode.WINDOW,
                'fullscreen': CaptureMode.FULLSCREEN
            }
            capture_mode = mode_map.get(mode, CaptureMode.RECTANGULAR)
            self.signals.trigger_direct_capture.emit(capture_mode)
        else:
            self.signals.trigger_capture.emit()

    def _on_tray_show(self):
        """Handle show window request from tray."""
        self.signals.trigger_show.emit()

    def _show_capture_dialog(self):
        """Show the capture mode selection dialog."""
        dialog = CaptureDialog()
        if dialog.exec_() == dialog.Accepted:
            mode = dialog.selected_mode
            delay = dialog.selected_delay
            self._start_capture(mode, delay)

    def _direct_capture(self, mode: CaptureMode):
        """Start capture directly with specified mode (no dialog)."""
        self._do_capture(mode)

    def _start_capture(self, mode: CaptureMode, delay: DelayOption):
        """Start the capture process."""
        if delay.value > 0:
            self.pending_mode = mode
            self._start_delay_countdown(delay.value)
        else:
            self._do_capture(mode)

    def _start_delay_countdown(self, seconds: int):
        """Start delay countdown before capture."""
        self.delay_timer = QTimer()
        self.delay_timer.timeout.connect(self._on_delay_complete)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.start(seconds * 1000)

        self.tray.show_notification(
            "BretClip",
            f"Capturing in {seconds} seconds..."
        )

    def _on_delay_complete(self):
        """Handle delay completion."""
        if self.pending_mode:
            self._do_capture(self.pending_mode)
            self.pending_mode = None

    def _do_capture(self, mode: CaptureMode):
        """Perform the actual capture."""
        if self.editor and self.editor.isVisible():
            self.editor.hide()

        self.selector = SelectionOverlay(mode)
        self.selector.selection_complete.connect(self._on_capture_complete)
        self.selector.selection_cancelled.connect(self._on_capture_cancelled)
        self.selector.show()

    def _on_capture_complete(self, image: Image.Image):
        """Handle completed capture - open editor for editing."""
        # Don't null self.selector here — it's still mid-signal.
        # Use QTimer to clean it up safely after the signal finishes.
        if self.selector:
            QTimer.singleShot(0, self._cleanup_selector)

        if image:
            try:
                print(f"Capture complete: {image.size} {image.mode}")
                self._create_editor()
                print("Editor created")
                self.editor.set_image(image)
                print("Image set")
                self.editor.show()
                self.editor.activateWindow()
                self.editor.raise_()
                print("Editor shown and raised")
            except Exception as e:
                import traceback
                print(f"Editor error: {e}")
                traceback.print_exc()
                self._emergency_save(image)
        else:
            print("Warning: _on_capture_complete received None image")

    def _cleanup_selector(self):
        """Safely clean up the selector after signal processing completes."""
        self.selector = None

    def _emergency_save(self, image: Image.Image):
        """Emergency save if editor fails to open."""
        from datetime import datetime

        screenshots_folder = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        if not os.path.exists(screenshots_folder):
            os.makedirs(screenshots_folder)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"BretClip_{timestamp}.png"
        filepath = os.path.join(screenshots_folder, filename)

        try:
            image.save(filepath)
            self.tray.show_notification("BretClip", f"Saved to {filename}")
            print(f"Emergency save to: {filepath}")
        except Exception as e:
            print(f"Emergency save failed: {e}")

    def _on_capture_cancelled(self):
        """Handle cancelled capture."""
        self.selector = None

    def _show_editor(self):
        """Show the editor window."""
        self._create_editor()
        self.editor.show()
        self.editor.activateWindow()

    def _on_editor_closed(self):
        """Handle editor window close."""
        self.editor = None

    def _on_exit(self):
        """Handle application exit."""
        self.hotkey_manager.stop()
        self.tray.stop()
        self.app.quit()

    def run(self):
        """Run the application."""
        self.tray.start()
        self.hotkey_manager.start()

        QTimer.singleShot(1000, lambda: self.tray.show_notification(
            "BretClip",
            "Press Ctrl+Alt+B to capture screen"
        ))

        return self.app.exec_()


def main():
    """Main entry point."""
    app = BretClipApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
