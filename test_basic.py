"""Basic window test - positioned on the larger monitor."""

import tkinter as tk
from tkinter import messagebox

print("Creating window on DISPLAY1 (2560x1440 monitor)...")

root = tk.Tk()
root.title("BretClip Test")
root.geometry("400x300+100-1300")  # +100 from left, -1300 which is Y=-1300 (on the upper monitor)

label = tk.Label(root, text="Can you see this window?\n(On 2560x1440 monitor)", font=('Arial', 16))
label.pack(pady=50)

btn = tk.Button(root, text="Click Me", command=lambda: messagebox.showinfo("Test", "Button works!"))
btn.pack(pady=20)

btn2 = tk.Button(root, text="Close", command=root.destroy)
btn2.pack(pady=20)

print("Window created at position 100, -1300")
root.mainloop()
print("Done")
