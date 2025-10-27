#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration script to add content_type and video_quality columns to the download table
"""

import sqlite3
import os
from datetime import datetime

# Path to the SQLite database
DB_PATH = os.path.join('instance', 'downloader.db')

def add_columns():
    """Add content_type and video_quality columns to the download table"""
    print(f"Connecting to database at {DB_PATH}...")
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(download)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add content_type column if it doesn't exist
        if 'content_type' not in columns:
            print("Adding content_type column...")
            cursor.execute("ALTER TABLE download ADD COLUMN content_type TEXT DEFAULT 'video'")
            print("content_type column added successfully.")
        else:
            print("content_type column already exists.")
        
        # Add video_quality column if it doesn't exist
        if 'video_quality' not in columns:
            print("Adding video_quality column...")
            cursor.execute("ALTER TABLE download ADD COLUMN video_quality TEXT DEFAULT 'auto'")
            print("video_quality column added successfully.")
        else:
            print("video_quality column already exists.")
        
        # Commit the changes
        conn.commit()
        print("Database migration completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_columns()