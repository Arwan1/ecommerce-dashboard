"""
Simple test of returns dashboard supplier query
"""
import tkinter as tk
from gui.returns_dashboard import ReturnsDashboard

root = tk.Tk()
root.title("Test")
root.geometry("800x600")

print("Creating returns dashboard...")
dashboard = ReturnsDashboard(root)
print("Dashboard created. Starting main loop...")

root.mainloop()
