"""Create desktop shortcut for BretClip."""

import os
import sys

try:
    import win32com.client
except ImportError:
    print("Installing pywin32...")
    os.system(f"{sys.executable} -m pip install pywin32")
    import win32com.client


def create_shortcut():
    """Create a desktop shortcut for BretClip."""
    # Paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(project_dir, "bretclip.py")
    icon_path = os.path.join(project_dir, "assets", "icon.ico")
    venv_python = os.path.join(project_dir, "venv", "Scripts", "pythonw.exe")

    # Use venv python if exists, otherwise system pythonw
    if os.path.exists(venv_python):
        python_path = venv_python
    else:
        python_path = sys.executable.replace("python.exe", "pythonw.exe")

    # Desktop path
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    shortcut_path = os.path.join(desktop, "BretClip.lnk")

    # Create shortcut using Windows Script Host
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)

    shortcut.TargetPath = python_path
    shortcut.Arguments = f'"{script_path}"'
    shortcut.WorkingDirectory = project_dir
    shortcut.Description = "BretClip - Screen Capture Tool (Ctrl+Alt+B)"

    # Set icon if exists
    if os.path.exists(icon_path):
        shortcut.IconLocation = icon_path
    else:
        print(f"Warning: Icon not found at {icon_path}")
        print("Run 'python assets/create_icon.py' first to generate the icon.")

    shortcut.save()

    print(f"Shortcut created: {shortcut_path}")
    print("\nTo pin to taskbar:")
    print("1. Right-click the desktop shortcut")
    print("2. Select 'Show more options' (Windows 11)")
    print("3. Click 'Pin to taskbar'")

    return shortcut_path


if __name__ == "__main__":
    create_shortcut()
