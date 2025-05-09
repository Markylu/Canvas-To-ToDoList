import json
import sys
import os
from gui import create_config_gui

def get_application_path():
    """Get the application path based on how it's being run."""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle
        return os.path.dirname(sys.executable)
    else:
        # If the application is run from a Python interpreter
        return os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    """Get the path to the configuration file."""
    return os.path.join(get_application_path(), 'config.json')

def load_config():
    """Load configuration from file or create new one if it doesn't exist."""
    config_path = get_config_path()
    print(f"Looking for config file at: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            print("Successfully loaded config file")
            return config
    except FileNotFoundError:
        print("Config file not found, launching setup GUI...")
        create_config_gui()
        # Try loading the config again after GUI
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                print("Successfully loaded config file after setup")
                return config
        except FileNotFoundError:
            print("Error: No configuration file found. Please run the application again to set up your API keys.")
            sys.exit(1)
    except json.JSONDecodeError:
        print("Error: config.json is not valid JSON. Please delete the file and run the application again to set up your API keys.")
        sys.exit(1) 