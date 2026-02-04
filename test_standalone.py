"""Standalone test - minimal editor window - FORCED TO SCREEN CENTER."""

import sys
import ctypes

# DPI
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    pass

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
import os
from datetime import datetime

class SimpleEditor(QMainWindow):
    def __init__(self, image):
        super().__init__()
        self.image = image
        self.setWindowTitle("BretClip Editor")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #1e1e1e;")

        # FORCE WINDOW TO CENTER OF PRIMARY SCREEN
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Title
        title = QLabel("BretClip Editor")
        title.setStyleSheet("color: #0078d4; font-size: 32px; font-weight: bold; padding: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2d2d2d; border: 2px solid #3c3c3c;")

        # Convert PIL to QPixmap
        if image.mode == 'RGBA':
            data = image.tobytes('raw', 'RGBA')
            qimage = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        else:
            img_rgb = image.convert('RGB')
            data = img_rgb.tobytes('raw', 'RGB')
            qimage = QImage(data, img_rgb.width, img_rgb.height, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qimage)
        scaled = pixmap.scaled(700, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        layout.addWidget(self.image_label)

        # Save button
        save_btn = QPushButton("SAVE AND CLOSE")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-size: 24px;
                padding: 20px 40px;
                border: none;
                border-radius: 10px;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
        """)
        save_btn.clicked.connect(self.save_and_close)
        layout.addWidget(save_btn)

        # Status
        self.status = QLabel("Click SAVE AND CLOSE when done editing")
        self.status.setStyleSheet("color: #cccccc; font-size: 16px; padding: 10px;")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

    def showEvent(self, event):
        super().showEvent(event)
        # Center on screen AFTER showing
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        print(f"Window moved to: {x}, {y}")
        print(f"Screen size: {screen.width()}x{screen.height()}")

    def save_and_close(self):
        screenshots = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        if not os.path.exists(screenshots):
            os.makedirs(screenshots)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(screenshots, f"BretClip_{timestamp}.png")

        self.image.save(filepath)
        print(f"Saved to: {filepath}")

        # Open folder with file selected
        os.system(f'explorer /select,"{filepath}"')

        self.close()

    def closeEvent(self, event):
        screenshots = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        if not os.path.exists(screenshots):
            os.makedirs(screenshots)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(screenshots, f"BretClip_{timestamp}.png")

        try:
            self.image.save(filepath)
            print(f"Auto-saved to: {filepath}")
        except Exception as e:
            print(f"Save error: {e}")

        event.accept()


if __name__ == "__main__":
    print("="*50)
    print("BRETTCLIP EDITOR TEST")
    print("="*50)

    # Create test image - BLUE so it's obvious
    test_img = Image.new('RGB', (800, 600), color=(70, 130, 180))

    app = QApplication(sys.argv)

    # Get screen info
    screen = app.primaryScreen().geometry()
    print(f"Primary screen: {screen.width()}x{screen.height()} at ({screen.x()}, {screen.y()})")

    editor = SimpleEditor(test_img)

    # Force geometry to center of screen
    w, h = 900, 700
    x = screen.x() + (screen.width() - w) // 2
    y = screen.y() + (screen.height() - h) // 2
    editor.setGeometry(x, y, w, h)
    print(f"Setting window geometry to: {x}, {y}, {w}, {h}")

    editor.show()
    editor.raise_()
    editor.activateWindow()

    print("Editor window should now be visible on your screen")
    print("="*50)

    sys.exit(app.exec_())
