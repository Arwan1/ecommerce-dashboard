"""
Test the specific get_returns_chart_data method
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import importlib

# Force reload the module
if 'gui.returns_dashboard' in sys.modules:
    del sys.modules['gui.returns_dashboard']

from gui.returns_dashboard import ReturnsDashboard
import tkinter as tk

def test_chart_data_method():
    print("🔍 Testing get_returns_chart_data method directly...")
    
    # Create a minimal dashboard instance
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        dashboard = ReturnsDashboard(root)
        
        # Call the method directly
        chart_data = dashboard.get_returns_chart_data("All Time")
        
        print(f"📊 Chart data keys: {chart_data.keys()}")
        
        if 'supplier_returns' in chart_data:
            supplier_data = chart_data['supplier_returns']
            print(f"📊 Supplier returns: {len(supplier_data)} items")
            for item in supplier_data[:3]:  # Show first 3
                print(f"   • {item}")
        else:
            print("❌ No supplier_returns key found in chart data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        root.destroy()

if __name__ == "__main__":
    test_chart_data_method()
