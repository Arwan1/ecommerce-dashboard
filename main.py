import tkinter as tk
import sys
import os

# Add V2 root directly to sys.path (for alll imports: Was causing errors earlier)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Import GUI stuff
from gui.login_window import LoginWindow
from gui.main_window import MainWindow  # Import   MainWindow class

class MainApplication(tk.Tk):
    """
    Main Tkinter application class.
    """
    def __init__(self):
        super().__init__()
        self.title("eCommerce System")
        self.geometry("800x600")

        self.show_login_window()

    def show_login_window(self):
        self.login_window = LoginWindow(self)
        self.login_window.pack(fill="both", expand=True)

    def show_main_gui(self, user):
        # Clear the login window
        self.login_window.destroy()

        # Create and display the main GUI
        main_window = MainWindow(self, user)
        main_window.pack(fill="both", expand=True)

# Launch the app
if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
