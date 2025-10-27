import sqlite3
import os

# Path to the database file
db_path = os.path.join('instance', 'downloader.db')

def add_admin_column():
    """Add is_admin column to the user table if it doesn't exist"""
    print(f"Checking database at {db_path}...")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the column exists
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'is_admin' not in column_names:
        print("Adding is_admin column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        conn.commit()
        print("Column added successfully!")
    else:
        print("is_admin column already exists.")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    add_admin_column()
    print("Database update completed.")