"""Test using tkinter instead of PyQt5."""

import tkinter as tk

print("Starting tkinter fullscreen test...")

root = tk.Tk()
root.title("BretClip")

# Make fullscreen
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.configure(bg='gray20')

# Add a label
label = tk.Label(
    root,
    text="FULLSCREEN OVERLAY - Press ESC to close",
    bg='red',
    fg='white',
    font=('Arial', 24),
    padx=20,
    pady=20
)
label.place(x=100, y=50)

# ESC to close
root.bind('<Escape>', lambda e: root.destroy())

# Click handler
def on_click(event):
    print(f"Clicked at {event.x}, {event.y}")

root.bind('<Button-1>', on_click)

print(f"Window size: {root.winfo_screenwidth()}x{root.winfo_screenheight()}")
print("Running - press ESC to close")

root.mainloop()
print("Done")
