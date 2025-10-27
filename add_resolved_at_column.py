import sqlite3
import os

DB_PATH = os.path.join('instance', 'downloader.db')

def add_resolved_at_column():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(feedback)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'resolved_at' not in columns:
            cursor.execute("ALTER TABLE feedback ADD COLUMN resolved_at DATETIME")
            conn.commit()
            print("Successfully added 'resolved_at' column to feedback table")
        else:
            print("Column 'resolved_at' already exists in feedback table")

    except Exception as e:
        print(f"Error updating feedback table: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_resolved_at_column()