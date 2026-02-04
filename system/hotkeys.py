"""Global hotkey management using pynput library."""

from pynput.keyboard import GlobalHotKeys
from typing import Callable, Optional


class HotkeyManager:
    """Manages global keyboard shortcuts using pynput GlobalHotKeys."""

    def __init__(self):
        self.hotkey_callback: Optional[Callable] = None
        self._listener: Optional[GlobalHotKeys] = None

    def set_callback(self, callback: Callable):
        """Set the callback function for when hotkey is pressed."""
        self.hotkey_callback = callback

    def _on_hotkey(self):
        """Internal handler when hotkey is detected."""
        if self.hotkey_callback:
            self.hotkey_callback()

    def start(self):
        """Start listening for hotkeys."""
        if self._listener is None:
            self._listener = GlobalHotKeys({
                '<ctrl>+<alt>+b': self._on_hotkey
            })
            self._listener.daemon = True
            self._listener.start()

    def stop(self):
        """Stop listening for hotkeys."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
