"""Test script to verify hotkey detection works."""

from pynput.keyboard import GlobalHotKeys
import time

print("=" * 50)
print("BretClip Hotkey Test")
print("=" * 50)
print()
print("Press Ctrl+Alt+B to test the hotkey...")
print("Press Ctrl+C to exit")
print()

def on_hotkey():
    print(">>> SUCCESS! Hotkey Ctrl+Alt+B detected! <<<")

hotkeys = GlobalHotKeys({'<ctrl>+<alt>+b': on_hotkey})
hotkeys.daemon = True
hotkeys.start()

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nExiting...")

hotkeys.stop()
