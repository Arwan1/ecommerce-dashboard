#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from gui.returns_dashboard import ReturnsDashboard

def test_supplier_section():
    """Test if the new supplier section exists and works"""
    print("🧪 Testing supplier section visibility...")
    
    root = tk.Tk()
    root.title("Test Supplier Section")
    root.geometry("800x600")
    
    # Create returns dashboard
    dashboard = ReturnsDashboard(root)
    
    # Check if supplier section frame exists
    if hasattr(dashboard, 'supplier_section_frame'):
        print("✅ supplier_section_frame exists!")
        
        # Try to create the supplier table
        dashboard.create_supplier_chart('Last 30 Days')
        print("✅ create_supplier_chart called")
        
        # Show the window so we can see it
        root.deiconify()
        print("✅ Window should now be visible with supplier section")
        
    else:
        print("❌ supplier_section_frame NOT found!")
        
        # Check what attributes the dashboard has
        print("Available attributes:")
        for attr in dir(dashboard):
            if 'supplier' in attr.lower():
                print(f"  - {attr}")
    
    # Keep window open for inspection
    root.mainloop()

if __name__ == "__main__":
    test_supplier_section()
