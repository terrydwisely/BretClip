"""System tray integration using pystray."""

import pystray
from PIL import Image
from typing import Callable, Optional
import threading
import os


class SystemTray:
    """Manages the system tray icon and menu."""

    def __init__(self, icon_path: Optional[str] = None):
        self.icon: Optional[pystray.Icon] = None
        self.icon_image: Optional[Image.Image] = None

        # Callbacks
        self.on_new_capture: Optional[Callable] = None
        self.on_show_window: Optional[Callable] = None
        self.on_exit: Optional[Callable] = None

        # Load or create icon
        if icon_path and os.path.exists(icon_path):
            self.icon_image = Image.open(icon_path)
        else:
            self.icon_image = self._create_default_icon()

    def _create_default_icon(self) -> Image.Image:
        """Create a simple default icon if custom icon not found."""
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)

        # Simple razor shape
        draw.polygon([
            (10, 50), (10, 40), (20, 10), (35, 15), (25, 50)
        ], fill=(180, 190, 200, 255), outline=(100, 110, 120, 255))

        # Handle
        draw.polygon([
            (25, 48), (35, 50), (55, 55), (54, 60), (30, 58)
        ], fill=(60, 50, 45, 255), outline=(40, 35, 30, 255))

        return img

    def _create_menu(self) -> pystray.Menu:
        """Create the tray icon context menu."""
        return pystray.Menu(
            pystray.MenuItem(
                "New Capture (Ctrl+Alt+B)",
                self._menu_new_capture,
                default=True
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Rectangular",
                lambda: self._menu_capture_mode('rectangular')
            ),
            pystray.MenuItem(
                "Freeform",
                lambda: self._menu_capture_mode('freeform')
            ),
            pystray.MenuItem(
                "Window",
                lambda: self._menu_capture_mode('window')
            ),
            pystray.MenuItem(
                "Fullscreen",
                lambda: self._menu_capture_mode('fullscreen')
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Show Editor",
                self._menu_show_window
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Exit",
                self._menu_exit
            )
        )

    def _menu_new_capture(self, icon=None, item=None):
        """Handle new capture menu item."""
        if self.on_new_capture:
            threading.Thread(target=self.on_new_capture, daemon=True).start()

    def _menu_capture_mode(self, mode: str):
        """Handle capture mode selection."""
        if self.on_new_capture:
            threading.Thread(
                target=lambda: self.on_new_capture(mode),
                daemon=True
            ).start()

    def _menu_show_window(self, icon=None, item=None):
        """Handle show window menu item."""
        if self.on_show_window:
            threading.Thread(target=self.on_show_window, daemon=True).start()

    def _menu_exit(self, icon=None, item=None):
        """Handle exit menu item."""
        if self.on_exit:
            self.on_exit()
        self.stop()

    def start(self):
        """Start the system tray icon."""
        self.icon = pystray.Icon(
            name="BretClip",
            icon=self.icon_image,
            title="BretClip - Ctrl+Alt+B to capture",
            menu=self._create_menu()
        )

        # Run in separate thread
        threading.Thread(target=self.icon.run, daemon=True).start()

    def stop(self):
        """Stop the system tray icon."""
        if self.icon:
            self.icon.stop()
            self.icon = None

    def update_icon(self, image: Image.Image):
        """Update the tray icon image."""
        self.icon_image = image
        if self.icon:
            self.icon.icon = image

    def show_notification(self, title: str, message: str):
        """Show a notification from the tray."""
        if self.icon:
            self.icon.notify(message, title)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
