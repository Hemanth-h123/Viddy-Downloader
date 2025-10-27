import sqlite3
import os

def add_subject_column():
    """Add the missing subject column to the feedback table"""
    # Connect to the database
    db_path = os.path.join('instance', 'downloader.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(feedback)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'subject' not in columns:
            # Add the subject column
            cursor.execute("ALTER TABLE feedback ADD COLUMN subject TEXT DEFAULT 'Feedback' NOT NULL")
            conn.commit()
            print("Successfully added 'subject' column to feedback table")
        else:
            print("Column 'subject' already exists in feedback table")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_subject_column()