"""Screen capture module using mss for fast screenshot capture."""

import mss
import mss.tools
from PIL import Image
from typing import Optional, Tuple
import ctypes
from ctypes import wintypes


class ScreenCapture:
    """Fast screen capture using mss library."""

    def __init__(self):
        self.sct = mss.mss()

    def capture_fullscreen(self, monitor: int = 0) -> Image.Image:
        """Capture the entire screen or a specific monitor.

        Args:
            monitor: Monitor index (0 = all monitors combined, 1+ = specific monitor)

        Returns:
            PIL Image of the captured screen
        """
        monitor_info = self.sct.monitors[monitor]
        screenshot = self.sct.grab(monitor_info)
        return Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')

    def capture_region(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """Capture a specific region of the screen.

        Args:
            x: Left coordinate
            y: Top coordinate
            width: Width of region
            height: Height of region

        Returns:
            PIL Image of the captured region
        """
        region = {'left': x, 'top': y, 'width': width, 'height': height}
        screenshot = self.sct.grab(region)
        return Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')

    def capture_window(self, hwnd: int) -> Optional[Image.Image]:
        """Capture a specific window by its handle.

        Args:
            hwnd: Window handle

        Returns:
            PIL Image of the window, or None if window not found
        """
        try:
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

            x = rect.left
            y = rect.top
            width = rect.right - rect.left
            height = rect.bottom - rect.top

            if width <= 0 or height <= 0:
                return None

            return self.capture_region(x, y, width, height)
        except Exception:
            return None

    def get_monitors(self) -> list:
        """Get list of available monitors.

        Returns:
            List of monitor dictionaries with position and size info
        """
        return self.sct.monitors[1:]  # Skip the "all monitors" entry

    def get_screen_size(self) -> Tuple[int, int]:
        """Get the total screen size (all monitors combined).

        Returns:
            Tuple of (width, height)
        """
        mon = self.sct.monitors[0]  # Combined monitor
        return mon['width'], mon['height']

    def close(self):
        """Clean up resources."""
        self.sct.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
