from canvasapi import Canvas
from canvasapi.exceptions import Forbidden
import datetime
import requests
from todoist_api_python.api import TodoistAPI
import json
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from gui import create_progress_window, center_window
from config import load_config
from integration import CanvasTodoistSync

def get_course_name(course):
    """Get the course name safely, with fallback options."""
    try:
        if hasattr(course, 'name'):
            return course.name
        elif hasattr(course, 'course_code'):
            return course.course_code
        else:
            return f"Course {course.id}"
    except Exception:
        return f"Unknown Course {course.id if hasattr(course, 'id') else 'ID Unknown'}"

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
        try:
            if root.winfo_exists():
                status_label.config(text=message)
                log_text.insert(tk.END, message + "\n")
                log_text.see(tk.END)
                root.update_idletasks()  # Use update_idletasks instead of update
        except Exception as e:
            print(f"Error updating status: {str(e)}")
    
    def clear_cache():
        """Clear the task cache file."""
        try:
            cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'task_cache.json')
            if os.path.exists(cache_path):
                os.remove(cache_path)
                update_status("\nTask cache cleared successfully!")
            else:
                update_status("\nNo task cache file found.")
        except Exception as e:
            update_status(f"\nError clearing cache: {str(e)}")
    
    def on_closing():
        """Handle window closing."""
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass
    
    # Bind Ctrl+Option+Command+Shift+Delete to clear cache
    root.bind('<Control-Alt-Command-Shift-Delete>', lambda e: clear_cache())
    
    # Add cache clear button
    clear_cache_button = ttk.Button(main_frame, text="Clear Cache (Ctrl+⌥+⌘+Shift+Delete)", command=clear_cache)
    clear_cache_button.grid(row=2, column=0, pady=(0, 10))
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    return root, update_status

def main():
    while True:  # Keep trying until we have a valid config
        try:
            # Load configuration first
            print("Loading configuration...")
            try:
                config = load_config()
                print("Configuration loaded successfully")
                break  # Exit the loop once we have a valid config
            except Exception as e:
                error_msg = f"Error loading configuration: {str(e)}"
                print(error_msg)
                # Show error in a new window
                error_root = tk.Tk()
                error_root.title("Error")
                error_label = ttk.Label(error_root, text=error_msg + "\n\nClick Close to try again.", wraplength=500)
                error_label.pack(padx=20, pady=20)
                close_button = ttk.Button(error_root, text="Close", command=error_root.destroy)
                close_button.pack(pady=10)
                error_root.mainloop()
                continue  # Try again
                
        except Exception as e:
            error_message = f"\nError: {str(e)}"
            print(error_message)
            # Show error in a new window
            error_root = tk.Tk()
            error_root.title("Error")
            error_label = ttk.Label(error_root, text=error_message + "\n\nClick Close to try again.", wraplength=500)
            error_label.pack(padx=20, pady=20)
            close_button = ttk.Button(error_root, text="Close", command=error_root.destroy)
            close_button.pack(pady=10)
            error_root.mainloop()
            continue  # Try again
    
    try:
        # Create progress window
        root, update_status = create_progress_window()
        
        # Initialize sync
        update_status("Initializing Canvas and Todoist connection...")
        try:
            sync = CanvasTodoistSync(
                canvas_api_url=config["CANVAS_API_URL"],
                canvas_api_key=config["CANVAS_API_KEY"],
                todoist_api_key=config["TODOIST_API_KEY"],
                user_id=int(config["CANVAS_USER_ID"])
            )
            update_status("Connection initialized successfully")
        except Exception as e:
            error_msg = f"Error initializing connection: {str(e)}"
            update_status(error_msg)
            print(error_msg)
            raise
        
        # Perform sync
        update_status("Starting sync process...")
        sync.sync(update_status)
        
        # Add a close button
        close_button = ttk.Button(root, text="Close", command=root.destroy)
        close_button.grid(row=2, column=0, pady=(0, 10))
        
        # Center the window
        center_window(root)
        
        root.mainloop()
        
    except Exception as e:
        error_message = f"\nError: {str(e)}"
        print(error_message)
        
        if 'root' in locals() and root.winfo_exists():
            try:
                update_status(error_message)
                # Add a close button if it doesn't exist
                if not any(isinstance(child, ttk.Button) for child in root.winfo_children()):
                    close_button = ttk.Button(root, text="Close", command=root.destroy)
                    close_button.grid(row=2, column=0, pady=(0, 10))
                root.mainloop()
            except Exception:
                # If we can't update the main window, create a new error window
                error_root = tk.Tk()
                error_root.title("Error")
                error_label = ttk.Label(error_root, text=error_message, wraplength=500)
                error_label.pack(padx=20, pady=20)
                close_button = ttk.Button(error_root, text="Close", command=error_root.destroy)
                close_button.pack(pady=10)
                error_root.mainloop()

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
    canvas_user_id = ttk.Entry(main_frame, width=50)
    canvas_user_id.grid(row=3, column=1, sticky=tk.W, pady=5)
    
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

    To get your Canvas User ID:
    1. Log in to Canvas
    2. Go to Account > Profile
    3. Your user ID is in the URL (e.g., /accounts/XXXXX)

    To get your Todoist API key:
    1. Log in to Todoist
    2. Go to Settings > Integrations
    3. Copy your API token
    """
    help_label = ttk.Label(main_frame, text=help_text, wraplength=500, justify=tk.LEFT)
    help_label.grid(row=6, column=0, columnspan=2, pady=20)
    
    config_saved = [False]  # Use a list to store the state
    
    def save_config():
        """Save the configuration and close the window."""
        config = {
            "CANVAS_API_URL": canvas_url.get().strip(),
            "CANVAS_API_KEY": canvas_key.get().strip(),
            "CANVAS_USER_ID": canvas_user_id.get().strip(),
            "TODOIST_API_KEY": todoist_key.get().strip()
        }
        
        # Validate inputs
        if not all(config.values()):
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        # Validate user ID is a number
        try:
            int(config["CANVAS_USER_ID"])
        except ValueError:
            messagebox.showerror("Error", "Canvas User ID must be a number")
            return
        
        # Save to config file
        config_path = get_config_path()
        print(f"Saving config to: {config_path}")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print("Config saved successfully")
            config_saved[0] = True  # Set the flag to True
            messagebox.showinfo("Success", "Configuration saved successfully!")
            root.destroy()
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    # Save button
    save_button = ttk.Button(main_frame, text="Save Configuration", command=save_config)
    save_button.grid(row=7, column=0, columnspan=2, pady=20)
    
    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()
    return config_saved[0]  # Return whether config was saved

def get_config_path():
    """Get the path to the configuration file."""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle
        application_path = os.path.dirname(sys.executable)
    else:
        # If the application is run from a Python interpreter
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    config_path = os.path.join(application_path, 'config.json')
    print(f"Configuration path: {config_path}")
    return config_path

def load_config():
    """Load configuration from file or create new one if it doesn't exist."""
    config_path = get_config_path()
    print(f"Looking for config file at: {config_path}")
    
    if not os.path.exists(config_path):
        print("Config file not found, launching setup GUI...")
        create_config_gui()
        # After GUI closes, check if config was created
        if not os.path.exists(config_path):
            raise Exception("Configuration was not saved. Please run the application again.")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            print("Successfully loaded config file")
            
            # Validate required fields
            required_fields = ["CANVAS_API_URL", "CANVAS_API_KEY", "TODOIST_API_KEY", "CANVAS_USER_ID"]
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                raise Exception(f"Missing required fields in config: {', '.join(missing_fields)}")
            
            # Validate user ID is a number
            try:
                int(config["CANVAS_USER_ID"])
            except ValueError:
                raise Exception("Canvas User ID must be a number")
            
            return config
            
    except json.JSONDecodeError:
        print("Config file is not valid JSON")
        raise Exception("config.json is not valid JSON. Please delete the file and run the application again.")
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        raise

if __name__ == "__main__":
    main()