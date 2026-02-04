"""Global hotkey management using keyboard library."""

import keyboard
from typing import Callable, Optional
import threading


class HotkeyManager:
    """Manages global keyboard shortcuts using keyboard library."""

    def __init__(self):
        self.hotkey_callback: Optional[Callable] = None
        self._running = False

    def set_callback(self, callback: Callable):
        """Set the callback function for when hotkey is pressed."""
        self.hotkey_callback = callback

    def _on_hotkey(self):
        """Internal handler when hotkey is detected."""
        if self.hotkey_callback:
            # Run callback in separate thread to not block
            threading.Thread(target=self.hotkey_callback, daemon=True).start()

    def start(self):
        """Start listening for hotkeys."""
        if not self._running:
            # Register Ctrl+Alt+B hotkey
            keyboard.add_hotkey('ctrl+alt+b', self._on_hotkey, suppress=False)
            self._running = True

    def stop(self):
        """Stop listening for hotkeys."""
        if self._running:
            keyboard.unhook_all_hotkeys()
            self._running = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
