import csv
from tkinter import filedialog


class CSVHandler:
    """Shared CSV file handling utilities for dashboard imports and exports."""

    @staticmethod
    def choose_import_file(title="Select CSV file"):
        """Open a file picker for CSV imports."""
        return filedialog.askopenfilename(
            title=title,
            filetypes=[("CSV files", "*.csv")],
        )

    @staticmethod
    def choose_export_file(title="Save CSV file", default_name="export.csv"):
        """Open a save dialog for CSV exports."""
        return filedialog.asksaveasfilename(
            title=title,
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv")],
        )

    @staticmethod
    def load_dict_rows(file_path):
        """Read a CSV file into a list of dictionaries."""
        with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                raise ValueError("The selected CSV file does not contain a header row.")
            return list(reader)

    @staticmethod
    def write_dict_rows(file_path, fieldnames, rows):
        """Write dictionaries to a CSV file using a fixed column order."""
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
