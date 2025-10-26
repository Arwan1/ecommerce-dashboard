#!/usr/bin/env python3
"""
Fix the supplier chart in returns dashboard by handling NULL values properly
"""

def fix_returns_dashboard():
    # Read the file
    with open('gui/returns_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find and fix the supplier chart logic
    old_chart_code = """if chart_data.get('supplier_returns') and len(chart_data['supplier_returns']) > 0:
            try:
                suppliers = [item['ready_made_supplier'][:15] + '...' if len(item['ready_made_supplier']) > 15 else item['ready_made_supplier']
                           for item in chart_data['supplier_returns']]"""
    
    new_chart_code = """if chart_data.get('supplier_returns') and len(chart_data['supplier_returns']) > 0:
            try:
                # Filter out None suppliers and handle safely
                valid_suppliers = [item for item in chart_data['supplier_returns'] if item.get('ready_made_supplier')]
                if valid_suppliers:
                    suppliers = [item['ready_made_supplier'][:15] + '...' if len(item['ready_made_supplier']) > 15 else item['ready_made_supplier']
                               for item in valid_suppliers]"""
    
    # Replace the code
    content = content.replace(old_chart_code, new_chart_code)
    
    # Also fix the counts line
    old_counts = "counts = [item['return_count'] for item in chart_data['supplier_returns']]"
    new_counts = "                    counts = [item['return_count'] for item in valid_suppliers]"
    
    content = content.replace(old_counts, new_counts)
    
    # Write back
    with open('gui/returns_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed supplier chart handling")

if __name__ == "__main__":
    fix_returns_dashboard()
