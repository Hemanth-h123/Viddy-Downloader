#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility functions for the web application
"""

import os
import json
import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    """Setup and configure the application logger
    
    Returns:
        logging.Logger: The configured logger
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logger
    logger = logging.getLogger('downloader')
    logger.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'downloader.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def load_config():
    """Load the application configuration
    
    Returns:
        dict: The application configuration
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        return create_default_config()


def create_default_config():
    """Create a default configuration file
    
    Returns:
        dict: The default configuration
    """
    config = {
        "save_path": os.path.join(os.path.expanduser("~"), "Downloads"),
        "max_concurrent_downloads": 3,
        "theme": "system",
        "auto_update": True,
        "analytics": True,
        "ad_frequency": "normal",
        "auth": {
            # Optional: path to cookies.txt (Netscape format). Leave empty to auto-detect.
            "cookies_file": "",
            # Optional: set to a browser name supported by yt-dlp (e.g., "chrome", "chromium", "edge", "firefox").
            # Leave empty to disable. Recommended for Pinterest and Instagram.
            "cookies_from_browser": "",
            # Optional: per-site credentials for yt-dlp. Use only if you understand the security implications.
            "username": "",
            "password": ""
        },
        "monetization": {
            "subscription_status": "free",
            "subscription_expiry": None,
            "paypal": {
                "mode": "sandbox",
                "client_id": "",
                "client_secret": ""
            },
            "stripe": {
                "api_key": ""
            }
        }
    }
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logging.error(f"Error creating default configuration: {str(e)}")
    
    return config


def save_config(config):
    """Save the application configuration
    
    Args:
        config (dict): The configuration to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving configuration: {str(e)}")
        return False


def get_file_size(file_path):
    """Get the size of a file in human-readable format
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Human-readable file size
    """
    try:
        size_bytes = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    except Exception:
        return "Unknown"


def format_duration(seconds):
    """Format duration in seconds to human-readable format
    
    Args:
        seconds (int): Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if not seconds:
        return "Unknown"
        
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"