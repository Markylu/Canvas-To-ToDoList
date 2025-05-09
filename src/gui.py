import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
import os

def create_progress_window():
    """Create a progress window to show sync status."""
    root = tk.Tk()
    root.title("Canvas to Todoist Sync")
    root.geometry("600x400")
    
    # Create a style
    style = ttk.Style()
    style.configure('TLabel', font=('Arial', 12))
    style.configure('TButton', font=('Arial', 12))
    
    # Create main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # Status label
    status_label = ttk.Label(main_frame, text="Initializing...", wraplength=500)
    status_label.grid(row=0, column=0, pady=(0, 10))
    
    # Log text area
    log_text = tk.Text(main_frame, height=15, width=60, wrap=tk.WORD)
    log_text.grid(row=1, column=0, pady=(0, 10))
    
    # Scrollbar for log
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=log_text.yview)
    scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
    log_text.configure(yscrollcommand=scrollbar.set)
    
    def update_status(message):
        """Update the status label and log."""
        status_label.config(text=message)
        log_text.insert(tk.END, message + "\n")
        log_text.see(tk.END)
        root.update()
    
    return root, update_status

def create_config_gui():
    """Create a GUI window for users to input their API keys."""
    root = tk.Tk()
    root.title("Canvas to Todoist Setup")
    root.geometry("600x800")
    
    # Create a style
    style = ttk.Style()
    style.configure('TLabel', font=('Arial', 12))
    style.configure('TEntry', font=('Arial', 12))
    style.configure('TButton', font=('Arial', 12))
    
    # Create main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # Canvas API section
    ttk.Label(main_frame, text="Canvas API Settings", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    ttk.Label(main_frame, text="Canvas API URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
    canvas_url = ttk.Entry(main_frame, width=50)
    canvas_url.grid(row=1, column=1, sticky=tk.W, pady=5)
    canvas_url.insert(0, "https://sps.instructure.com/")
    
    ttk.Label(main_frame, text="Canvas API Key:").grid(row=2, column=0, sticky=tk.W, pady=5)
    canvas_key = ttk.Entry(main_frame, width=50)
    canvas_key.grid(row=2, column=1, sticky=tk.W, pady=5)
    
    ttk.Label(main_frame, text="Canvas User ID:").grid(row=3, column=0, sticky=tk.W, pady=5)
    user_id = ttk.Entry(main_frame, width=50)
    user_id.grid(row=3, column=1, sticky=tk.W, pady=5)
    
    # Todoist API section
    ttk.Label(main_frame, text="Todoist API Settings", font=('Arial', 14, 'bold')).grid(row=4, column=0, columnspan=2, pady=(20, 20))
    
    ttk.Label(main_frame, text="Todoist API Key:").grid(row=5, column=0, sticky=tk.W, pady=5)
    todoist_key = ttk.Entry(main_frame, width=50)
    todoist_key.grid(row=5, column=1, sticky=tk.W, pady=5)
    
    # Help text
    help_text = """
    To get your Canvas API key:
    1. Log in to Canvas
    2. Go to Account > Settings
    3. Scroll down to "Approved Integrations"
    4. Click "New Access Token"
    5. Give it a name and copy the token

    To get your Todoist API key:
    1. Log in to Todoist
    2. Go to Settings > Integrations
    3. Copy your API token

    To get your Canvas User ID:
    1. Log in to Canvas
    2. Go to Account > Settings
    3. Your user ID is in the URL: /users/XXXX
    """
    help_label = ttk.Label(main_frame, text=help_text, wraplength=500, justify=tk.LEFT)
    help_label.grid(row=6, column=0, columnspan=2, pady=20)
    
    def save_config():
        """Save the configuration and close the window."""
        config = {
            "CANVAS_API_URL": canvas_url.get().strip(),
            "CANVAS_API_KEY": canvas_key.get().strip(),
            "TODOIST_API_KEY": todoist_key.get().strip(),
            "CANVAS_USER_ID": user_id.get().strip()
        }
        
        # Validate inputs
        if not all(config.values()):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        # Validate user ID is numeric
        try:
            int(config["CANVAS_USER_ID"])
        except ValueError:
            messagebox.showerror("Error", "Canvas User ID must be a number")
            return
        
        # Save to config file
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle
            application_path = os.path.dirname(sys.executable)
        else:
            # If the application is run from a Python interpreter
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        config_path = os.path.join(application_path, 'config.json')
        print(f"Saving config to: {config_path}")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print("Config saved successfully")
            messagebox.showinfo("Success", "Configuration saved successfully!")
            root.destroy()
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    # Save button
    save_button = ttk.Button(main_frame, text="Save Configuration", command=save_config)
    save_button.grid(row=7, column=0, columnspan=2, pady=20)
    
    # Center the window
    center_window(root)
    
    root.mainloop()

def center_window(window):
    """Center a window on the screen."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}') 