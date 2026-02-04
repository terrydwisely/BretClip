"""Main editor window for BretClip - Modern Dark Theme."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QAction, QActionGroup, QColorDialog,
    QFileDialog, QMessageBox, QSlider, QLabel, QStatusBar,
    QToolButton, QMenu, QSpinBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QColor, QPixmap, QPainter, QKeySequence, QPen, QBrush, QFont
from PIL import Image
from typing import Optional
import os

from .canvas import DrawingCanvas
from .tools import ToolType, AnnotationTool

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from system.clipboard import ClipboardManager


# Modern Dark Theme Colors
COLORS = {
    'bg_dark': '#1a1a1e',
    'bg_medium': '#222226',
    'bg_light': '#2a2a2e',
    'bg_hover': '#363639',
    'bg_active': '#0d5289',
    'border': '#38383c',
    'border_light': '#48484c',
    'text': '#d0d0d4',
    'text_bright': '#ffffff',
    'text_dim': '#72727a',
    'accent': '#2d7ff9',
    'accent_hover': '#4a94ff',
    'accent_pressed': '#1a6ae0',
    'success': '#34d399',
    'warning': '#fbbf24',
    'error': '#ef4444',
    'toolbar_bg': '#28282c',
    'statusbar_bg': '#2d7ff9',
}


MODERN_STYLESHEET = f"""
/* Main Window */
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

/* Central Widget */
QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text']};
    font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif;
    font-size: 13px;
}}

/* Menu Bar */
QMenuBar {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 4px 0px;
    spacing: 0px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 0px 2px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['bg_hover']};
}}

QMenuBar::item:pressed {{
    background-color: {COLORS['bg_active']};
}}

/* Dropdown Menus */
QMenu {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 0px;
}}

QMenu::item {{
    padding: 8px 32px 8px 16px;
    background-color: transparent;
}}

QMenu::item:selected {{
    background-color: {COLORS['accent']};
    color: {COLORS['text_bright']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border']};
    margin: 6px 12px;
}}

QMenu::indicator {{
    width: 16px;
    height: 16px;
    margin-left: 8px;
}}

/* Toolbar */
QToolBar {{
    background-color: {COLORS['toolbar_bg']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 8px 16px;
    spacing: 4px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {COLORS['border']};
    margin: 6px 8px;
}}

/* Tool Buttons in Toolbar */
QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 10px;
    margin: 0px 2px;
    color: {COLORS['text']};
}}

QToolButton:hover {{
    background-color: {COLORS['bg_hover']};
}}

QToolButton:pressed {{
    background-color: {COLORS['bg_active']};
}}

QToolButton:checked {{
    background-color: {COLORS['accent']};
    color: {COLORS['text_bright']};
}}

QToolButton::menu-indicator {{
    image: none;
}}

/* Action Buttons (Copy, Save) */
QToolButton#actionButton {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 500;
}}

QToolButton#actionButton:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['accent']};
}}

QToolButton#primaryButton {{
    background-color: {COLORS['accent']};
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    color: {COLORS['text_bright']};
    font-weight: 600;
}}

QToolButton#primaryButton:hover {{
    background-color: {COLORS['accent_hover']};
}}

QToolButton#primaryButton:pressed {{
    background-color: {COLORS['accent_pressed']};
}}

/* Sliders */
QSlider {{
    height: 24px;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {COLORS['bg_light']};
    border-radius: 2px;
    margin: 0px;
}}

QSlider::handle:horizontal {{
    background: {COLORS['accent']};
    border: none;
    width: 14px;
    height: 14px;
    margin: -5px 0px;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS['accent_hover']};
}}

QSlider::sub-page:horizontal {{
    background: {COLORS['accent']};
    border-radius: 2px;
}}

/* Labels */
QLabel {{
    background-color: transparent;
    color: {COLORS['text']};
    padding: 0px 4px;
}}

QLabel#sizeLabel {{
    background-color: {COLORS['bg_light']};
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 500;
    min-width: 28px;
}}

QLabel#sectionLabel {{
    color: {COLORS['text_dim']};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS['statusbar_bg']};
    color: {COLORS['text_bright']};
    border: none;
    padding: 4px 12px;
    font-size: 12px;
}}

QStatusBar::item {{
    border: none;
}}

/* Color Button */
QToolButton#colorButton {{
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px;
    min-width: 32px;
    min-height: 32px;
}}

QToolButton#colorButton:hover {{
    border-color: {COLORS['accent']};
}}

/* Tooltip */
QToolTip {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ScrollBar */
QScrollBar:vertical {{
    background-color: {COLORS['bg_dark']};
    width: 12px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['bg_hover']};
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['border_light']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_dark']};
    height: 12px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['bg_hover']};
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['border_light']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Message Box */
QMessageBox {{
    background-color: {COLORS['bg_medium']};
}}

QMessageBox QLabel {{
    color: {COLORS['text']};
    font-size: 13px;
}}

QPushButton {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 20px;
    color: {COLORS['text']};
    font-weight: 500;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['accent']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_active']};
}}

QPushButton:default {{
    background-color: {COLORS['accent']};
    border: none;
    color: {COLORS['text_bright']};
}}

QPushButton:default:hover {{
    background-color: {COLORS['accent_hover']};
}}

/* Frame separator */
QFrame#separator {{
    background-color: {COLORS['border']};
    max-width: 1px;
    margin: 6px 4px;
}}
"""


class EditorWindow(QMainWindow):
    """Main editor window with annotation tools - Modern Dark Theme."""

    closed = pyqtSignal()
    new_capture_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BretClip")
        self.setMinimumSize(800, 600)

        # Force window to stay on top and be visible
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        # Apply modern stylesheet
        self.setStyleSheet(MODERN_STYLESHEET)

        # State
        self.current_color = QColor(255, 82, 82)  # Modern red
        self.current_size = 3
        self.has_unsaved_changes = False
        self.original_capture = None  # Store original for auto-save

        self._setup_ui()
        self._create_menus()
        self._create_toolbar()
        self._setup_statusbar()

        # Center on primary screen
        self._center_on_screen()

    def _center_on_screen(self):
        """Center window on primary screen."""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        w, h = 1000, 700
        x = screen.x() + (screen.width() - w) // 2
        y = screen.y() + (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

    def _setup_ui(self):
        """Set up the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Canvas
        self.canvas = DrawingCanvas()
        self.canvas.image_modified.connect(self._on_image_modified)
        layout.addWidget(self.canvas)

    def _create_menus(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Capture", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_capture)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_image)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._save_image_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        copy_action = QAction("&Copy to Clipboard", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self._copy_to_clipboard)
        file_menu.addAction(copy_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.canvas.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.canvas.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        clear_action = QAction("&Clear Annotations", self)
        clear_action.triggered.connect(self.canvas.clear_annotations)
        edit_menu.addAction(clear_action)

    def _create_toolbar(self):
        """Create the annotation toolbar with modern styling."""
        toolbar = QToolBar("Tools")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(toolbar)

        # Tool action group (exclusive selection)
        tool_group = QActionGroup(self)
        tool_group.setExclusive(True)

        # Tool definitions with modern icons
        tools = [
            ("Pen", ToolType.PEN, "P", "Draw freehand"),
            ("Highlighter", ToolType.HIGHLIGHTER, "H", "Highlight area"),
            ("Rectangle", ToolType.RECTANGLE, "R", "Draw rectangle"),
            ("Circle", ToolType.CIRCLE, "C", "Draw circle"),
            ("Arrow", ToolType.ARROW, "A", "Draw arrow"),
            ("Text", ToolType.TEXT, "T", "Add text"),
            ("Eraser", ToolType.ERASER, "E", "Erase annotations"),
        ]

        for name, tool_type, shortcut, tooltip in tools:
            action = QAction(name, self)
            action.setCheckable(True)
            action.setShortcut(shortcut)
            action.setData(tool_type)
            action.setIcon(self._create_tool_icon(tool_type))
            action.setToolTip(f"{name} ({shortcut})\n{tooltip}")
            action.triggered.connect(lambda checked, t=tool_type: self._set_tool(t))
            tool_group.addAction(action)
            toolbar.addAction(action)

            if tool_type == ToolType.PEN:
                action.setChecked(True)

        toolbar.addSeparator()

        # Color section
        color_label = QLabel("Color")
        color_label.setObjectName("sectionLabel")
        toolbar.addWidget(color_label)

        # Color button
        self.color_btn = QToolButton()
        self.color_btn.setObjectName("colorButton")
        self.color_btn.setToolTip("Choose annotation color")
        self.color_btn.setFixedSize(36, 36)
        self._update_color_button()
        self.color_btn.clicked.connect(self._choose_color)
        toolbar.addWidget(self.color_btn)

        toolbar.addSeparator()

        # Size section
        size_label = QLabel("Size")
        size_label.setObjectName("sectionLabel")
        toolbar.addWidget(size_label)

        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(1, 30)
        self.size_slider.setValue(3)
        self.size_slider.setFixedWidth(140)
        self.size_slider.setToolTip("Brush/line size")
        self.size_slider.valueChanged.connect(self._size_changed)
        toolbar.addWidget(self.size_slider)

        self.size_label = QLabel("3")
        self.size_label.setObjectName("sizeLabel")
        self.size_label.setAlignment(Qt.AlignCenter)
        toolbar.addWidget(self.size_label)

        # Spacer
        spacer = QWidget()
        spacer.setFixedWidth(16)
        toolbar.addWidget(spacer)

        toolbar.addSeparator()

        # Undo/Redo buttons
        undo_btn = QToolButton()
        undo_btn.setIcon(self._create_undo_icon())
        undo_btn.setToolTip("Undo (Ctrl+Z)")
        undo_btn.clicked.connect(self.canvas.undo)
        toolbar.addWidget(undo_btn)

        redo_btn = QToolButton()
        redo_btn.setIcon(self._create_redo_icon())
        redo_btn.setToolTip("Redo (Ctrl+Y)")
        redo_btn.clicked.connect(self.canvas.redo)
        toolbar.addWidget(redo_btn)

        toolbar.addSeparator()

        # Action buttons (right side)
        copy_btn = QToolButton()
        copy_btn.setObjectName("actionButton")
        copy_btn.setText("Copy")
        copy_btn.setIcon(self._create_copy_icon())
        copy_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        copy_btn.setToolTip("Copy to clipboard (Ctrl+C)")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        toolbar.addWidget(copy_btn)

        spacer2 = QWidget()
        spacer2.setFixedWidth(4)
        toolbar.addWidget(spacer2)

        save_btn = QToolButton()
        save_btn.setObjectName("primaryButton")
        save_btn.setText("Save")
        save_btn.setIcon(self._create_save_icon())
        save_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        save_btn.setToolTip("Save image (Ctrl+S)")
        save_btn.clicked.connect(self._save_image_as)
        toolbar.addWidget(save_btn)

    def _create_tool_icon(self, tool_type: ToolType) -> QIcon:
        """Create a modern icon using Segoe MDL2 Assets font."""
        size = 24
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Map tool types to Segoe MDL2 Assets glyphs
        glyph_map = {
            ToolType.PEN: '\uED63',          # Edit
            ToolType.HIGHLIGHTER: '\uE7E6',  # Highlight
            ToolType.RECTANGLE: '\uE739',    # Checkbox (square outline)
            ToolType.CIRCLE: '\uEA3A',       # StatusCircleOuter
            ToolType.ARROW: '\uE72A',        # Forward arrow
            ToolType.TEXT: '\uE8D2',         # Font
            ToolType.ERASER: '\uE75C',       # Delete
        }

        glyph = glyph_map.get(tool_type, '\uE700')

        font = QFont('Segoe MDL2 Assets', 14)
        painter.setFont(font)
        painter.setPen(QColor(COLORS['text']))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, glyph)

        painter.end()
        return QIcon(pixmap)

    def _create_undo_icon(self) -> QIcon:
        """Create modern undo icon using Segoe MDL2 Assets."""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont('Segoe MDL2 Assets', 14)
        painter.setFont(font)
        painter.setPen(QColor(COLORS['text']))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, '\uE7A7')
        painter.end()
        return QIcon(pixmap)

    def _create_redo_icon(self) -> QIcon:
        """Create modern redo icon using Segoe MDL2 Assets."""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont('Segoe MDL2 Assets', 14)
        painter.setFont(font)
        painter.setPen(QColor(COLORS['text']))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, '\uE7A6')
        painter.end()
        return QIcon(pixmap)

    def _create_copy_icon(self) -> QIcon:
        """Create modern copy icon using Segoe MDL2 Assets."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont('Segoe MDL2 Assets', 10)
        painter.setFont(font)
        painter.setPen(QColor(COLORS['text']))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, '\uE8C8')
        painter.end()
        return QIcon(pixmap)

    def _create_save_icon(self) -> QIcon:
        """Create modern save icon using Segoe MDL2 Assets."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont('Segoe MDL2 Assets', 10)
        painter.setFont(font)
        painter.setPen(QColor(COLORS['text_bright']))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, '\uE74E')
        painter.end()
        return QIcon(pixmap)

    def _setup_statusbar(self):
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready  |  Ctrl+Alt+B for new capture")

    def _set_tool(self, tool_type: ToolType):
        """Set the current drawing tool."""
        tool = AnnotationTool(
            tool_type=tool_type,
            color=QColor(self.current_color),
            size=self.current_size
        )
        self.canvas.set_tool(tool)
        self.statusbar.showMessage(f"Tool: {tool_type.name.capitalize()}")

    def _choose_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(
            self.current_color,
            self,
            "Choose Color",
            QColorDialog.ShowAlphaChannel
        )
        if color.isValid():
            self.current_color = color
            self._update_color_button()
            self._update_tool()

    def _update_color_button(self):
        """Update the color button appearance with the current color."""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw rounded color swatch
        painter.setBrush(QBrush(self.current_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(2, 2, 20, 20, 4, 4)

        painter.end()
        self.color_btn.setIcon(QIcon(pixmap))

    def _size_changed(self, value: int):
        """Handle size slider change."""
        self.current_size = value
        self.size_label.setText(str(value))
        self._update_tool()

    def _update_tool(self):
        """Update the current tool with new settings."""
        current_type = self.canvas.current_tool.tool_type
        tool = AnnotationTool(
            tool_type=current_type,
            color=QColor(self.current_color),
            size=self.current_size
        )
        self.canvas.set_tool(tool)

    def _on_image_modified(self):
        """Handle image modification."""
        self.has_unsaved_changes = True
        self._update_title()

    def _update_title(self):
        """Update window title."""
        title = "BretClip"
        if self.has_unsaved_changes:
            title += " *"
        self.setWindowTitle(title)

    def set_image(self, image: Image.Image):
        """Set the captured image for editing."""
        self.original_capture = image  # Store for auto-save on close
        self.canvas.set_image(image)
        self.has_unsaved_changes = True  # Mark as needing save
        self._update_title()

        # Auto-copy to clipboard
        try:
            ClipboardManager.copy_image(image)
            self.statusbar.showMessage("Captured and copied to clipboard! Edit your image, then close to auto-save.", 5000)
        except Exception as e:
            print(f"Clipboard copy failed: {e}")
            self.statusbar.showMessage("Captured! (Clipboard copy failed). Edit your image, then close to auto-save.", 5000)

    def _new_capture(self):
        """Request a new capture."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Continue with new capture?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.new_capture_requested.emit()

    def _save_image(self):
        """Save the image (quick save)."""
        self._save_image_as()

    def _save_image_as(self):
        """Save the image with dialog."""
        image = self.canvas.get_final_image()
        if not image:
            QMessageBox.warning(self, "Error", "No image to save!")
            return

        filters = "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;GIF Image (*.gif)"
        filename, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Image", "", filters
        )

        if filename:
            # Ensure correct extension
            if "PNG" in selected_filter and not filename.lower().endswith('.png'):
                filename += '.png'
            elif "JPEG" in selected_filter and not filename.lower().endswith(('.jpg', '.jpeg')):
                filename += '.jpg'
            elif "GIF" in selected_filter and not filename.lower().endswith('.gif'):
                filename += '.gif'

            try:
                # Convert RGBA to RGB for JPEG
                if filename.lower().endswith(('.jpg', '.jpeg')) and image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background

                image.save(filename)
                self.has_unsaved_changes = False
                self._update_title()
                self.statusbar.showMessage(f"Saved to {filename}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def _copy_to_clipboard(self):
        """Copy the current image to clipboard."""
        image = self.canvas.get_final_image()
        if image:
            if ClipboardManager.copy_image(image):
                self.statusbar.showMessage("Copied to clipboard! Paste anywhere with Ctrl+V", 3000)
            else:
                QMessageBox.warning(self, "Error", "Failed to copy to clipboard")
        else:
            QMessageBox.warning(self, "Error", "No image to copy!")

    def closeEvent(self, event):
        """Handle window close - auto-save the image."""
        # Auto-save to Screenshots folder on close
        image = self.canvas.get_final_image()
        if image:
            import os
            from datetime import datetime

            screenshots_folder = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
            if not os.path.exists(screenshots_folder):
                os.makedirs(screenshots_folder)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"BretClip_{timestamp}.png"
            filepath = os.path.join(screenshots_folder, filename)

            try:
                image.save(filepath)
                print(f"Auto-saved to: {filepath}")
            except Exception as e:
                print(f"Auto-save error: {e}")

        self.closed.emit()
        event.accept()
