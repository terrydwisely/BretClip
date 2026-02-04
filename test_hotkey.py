"""Test script to verify hotkey detection works."""

import keyboard
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

keyboard.add_hotkey('ctrl+alt+b', on_hotkey)

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nExiting...")

keyboard.unhook_all()
