#!/usr/bin/env python3

"""
Minimal test to check if the dashboard loads
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_load():
    """Test if the dashboard loads without crashing"""
    try:
        print("Creating main window...")
        root = tk.Tk()
        root.title("Test Dashboard")
        root.geometry("800x600")
        
        print("Importing ReturnsDashboard...")
        from gui.returns_dashboard import ReturnsDashboard
        
        print("Creating dashboard...")
        dashboard = ReturnsDashboard(root)
        
        print("Dashboard created successfully!")
        print("Starting mainloop for 3 seconds...")
        
        # Run for a short time and then close
        def close_after_delay():
            print("Closing dashboard...")
            root.quit()
            
        root.after(3000, close_after_delay)  # Close after 3 seconds
        root.mainloop()
        
        print("✅ Dashboard test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dashboard_load()
    exit(0 if success else 1)
