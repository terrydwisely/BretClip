"""Test the full BretClip application."""

import sys
import os
import ctypes

# Set DPI awareness BEFORE importing PyQt5
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    ctypes.windll.user32.SetProcessDPIAware()

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now run the actual app
from bretclip import main

if __name__ == "__main__":
    main()
