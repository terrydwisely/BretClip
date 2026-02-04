"""DEPRECATED: Use bretclip.py instead. This file is kept for reference only."""

import warnings
warnings.warn("bretclip_simple.py is deprecated. Use bretclip.py instead.", DeprecationWarning)

import sys
import os
import ctypes
from datetime import datetime

# DPI awareness FIRST
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    ctypes.windll.user32.SetProcessDPIAware()

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QComboBox, QDialog)
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QCursor
from PIL import Image
import mss
from pynput.keyboard import GlobalHotKeys

# ============ SCREEN CAPTURE ============
class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()

    def capture_region(self, x, y, w, h):
        region = {'left': x, 'top': y, 'width': w, 'height': h}
        shot = self.sct.grab(region)
        return Image.frombytes('RGB', shot.size, shot.bgra, 'raw', 'BGRX')

    def capture_fullscreen(self):
        mon = self.sct.monitors[1]
        shot = self.sct.grab(mon)
        return Image.frombytes('RGB', shot.size, shot.bgra, 'raw', 'BGRX')

# ============ SELECTION OVERLAY ============
class SelectionOverlay(QWidget):
    captured = pyqtSignal(object)
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)

        # Cover entire screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self.start_point = None
        self.end_point = None
        self.is_selecting = False
        self.capture = ScreenCapture()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self.start_point and self.end_point:
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QColor(0, 120, 215))
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.is_selecting = True

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.end_point = event.pos()
            self.is_selecting = False
            self._do_capture()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancelled.emit()
            self.close()

    def _do_capture(self):
        if not self.start_point or not self.end_point:
            self.cancelled.emit()
            self.close()
            return

        rect = QRect(self.start_point, self.end_point).normalized()
        if rect.width() < 10 or rect.height() < 10:
            self.cancelled.emit()
            self.close()
            return

        self.hide()
        QApplication.processEvents()

        screen = QApplication.primaryScreen().geometry()
        x = screen.x() + rect.x()
        y = screen.y() + rect.y()

        img = self.capture.capture_region(x, y, rect.width(), rect.height())
        self.captured.emit(img)
        self.close()

# ============ EDITOR WINDOW ============
class EditorWindow(QMainWindow):
    def __init__(self, image):
        super().__init__()
        self.image = image
        self.setWindowTitle("BretClip Editor")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #1e1e1e;")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("BretClip Editor")
        title.setStyleSheet("color: #0078d4; font-size: 28px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Image
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet("background-color: #2d2d2d; border: 2px solid #3c3c3c; padding: 10px;")

        if image.mode == 'RGBA':
            data = image.tobytes('raw', 'RGBA')
            qimg = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        else:
            rgb = image.convert('RGB')
            data = rgb.tobytes('raw', 'RGB')
            qimg = QImage(data, rgb.width, rgb.height, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(800, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_label.setPixmap(scaled)
        layout.addWidget(img_label)

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save & Close")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4; color: white;
                font-size: 20px; padding: 15px 30px;
                border: none; border-radius: 8px;
            }
            QPushButton:hover { background-color: #1084d8; }
        """)
        save_btn.clicked.connect(self.save_and_close)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Discard")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c; color: white;
                font-size: 20px; padding: 15px 30px;
                border: none; border-radius: 8px;
            }
            QPushButton:hover { background-color: #4c4c4c; }
        """)
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        # Status
        self.status = QLabel("Close window to auto-save")
        self.status.setStyleSheet("color: #888; font-size: 14px;")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        w, h = 900, 700
        x = (screen.width() - w) // 2
        y = (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

    def save_and_close(self):
        self._save_image()
        self.close()

    def _save_image(self):
        folder = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        os.makedirs(folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(folder, f"BretClip_{timestamp}.png")

        self.image.save(filepath)
        print(f"Saved: {filepath}")

        # Open folder
        os.startfile(folder)

    def closeEvent(self, event):
        self._save_image()
        event.accept()

# ============ CAPTURE DIALOG ============
class CaptureDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BretClip")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(600, 400)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; border: 2px solid #3c3c3c; border-radius: 12px; }
            QLabel { color: white; font-size: 20px; }
            QPushButton {
                background-color: #2d2d2d; color: white;
                font-size: 20px; padding: 20px 40px;
                border: 2px solid #3c3c3c; border-radius: 10px;
            }
            QPushButton:hover { background-color: #0078d4; border-color: #0078d4; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("BretClip")
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #0078d4;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Select capture mode")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()

        rect_btn = QPushButton("Rectangle")
        rect_btn.clicked.connect(lambda: self.done(1))
        btn_layout.addWidget(rect_btn)

        full_btn = QPushButton("Fullscreen")
        full_btn.clicked.connect(lambda: self.done(2))
        btn_layout.addWidget(full_btn)

        layout.addLayout(btn_layout)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: 2px solid #5c5c5c; }
            QPushButton:hover { border-color: #ff6b6b; color: #ff6b6b; }
        """)
        cancel_btn.clicked.connect(lambda: self.done(0))
        layout.addWidget(cancel_btn)

        # Center
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 600) // 2
        y = (screen.height() - 400) // 2
        self.move(x, y)

# ============ MAIN APP ============
class BretClipApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.editor = None
        self.overlay = None

        # Register hotkey with pynput
        self._hotkeys = GlobalHotKeys({'<ctrl>+<alt>+b': self.on_hotkey})
        self._hotkeys.daemon = True
        self._hotkeys.start()
        print("BretClip running. Press Ctrl+Alt+B to capture.")

    def on_hotkey(self):
        QTimer.singleShot(0, self.show_dialog)

    def show_dialog(self):
        dialog = CaptureDialog()
        result = dialog.exec_()

        if result == 1:  # Rectangle
            self.start_rectangle_capture()
        elif result == 2:  # Fullscreen
            self.capture_fullscreen()

    def start_rectangle_capture(self):
        self.overlay = SelectionOverlay()
        self.overlay.captured.connect(self.on_captured)
        self.overlay.cancelled.connect(self.on_cancelled)
        self.overlay.show()

    def capture_fullscreen(self):
        cap = ScreenCapture()
        img = cap.capture_fullscreen()
        self.on_captured(img)

    def on_captured(self, image):
        print(f"Captured image: {image.size}")
        self.editor = EditorWindow(image)
        self.editor.show()
        self.editor.raise_()
        self.editor.activateWindow()

    def on_cancelled(self):
        print("Capture cancelled")

    def run(self):
        return self.app.exec_()

if __name__ == "__main__":
    app = BretClipApp()
    sys.exit(app.run())
