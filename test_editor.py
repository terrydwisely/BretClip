"""Test the editor window directly."""

import sys
import os
import ctypes

# DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PIL import Image
from editor.window import EditorWindow

print("Creating test image...")
# Create a test image (red square)
test_image = Image.new('RGB', (800, 600), color=(100, 150, 200))

print("Starting Qt application...")
app = QApplication(sys.argv)

print("Creating editor window...")
editor = EditorWindow()

print("Setting image...")
editor.set_image(test_image)

print("Showing editor...")
editor.show()
editor.raise_()
editor.activateWindow()

print("Editor should be visible now. Close it to exit.")
sys.exit(app.exec_())
