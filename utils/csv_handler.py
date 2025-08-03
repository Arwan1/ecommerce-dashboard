import csv
from tkinter import filedialog, messagebox

class CSVHandler:
    """
    Handles importing and exporting data in CSV format.
    """
    def import_from_csv(self, db_insert_function):
        """
        Opens a file dialog to import a CSV and uses a provided function
        to insert each row into the database.
        
        Args:
            db_insert_function: A function that takes a single row (list) as an argument
                                and handles its insertion into the database.
        """
        file_path = filedialog.askopenfilename(
            title="Select a CSV file to import",
            filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader) # Skip header row
                
                imported_count = 0
                for row in reader:
                    try:
                        db_insert_function(row)
                        imported_count += 1
                    except Exception as e:
                        print(f"Could not import row {row}: {e}")
            
            messagebox.showinfo("Import Successful", f"Successfully imported {imported_count} records.")

        except Exception as e:
            messagebox.showerror("Import Error", f"An error occurred during CSV import: {e}")

    def export_to_csv(self, data, header):
        """
        Opens a file dialog to save data to a CSV file.
        
        Args:
            data (list of lists): The data rows to write.
            header (list): The header row.
        """
        file_path = filedialog.asksaveasfilename(
            title="Save data as CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(header)
                writer.writerows(data)
            
            messagebox.showinfo("Export Successful", f"Data successfully exported to {file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during CSV export: {e}")
