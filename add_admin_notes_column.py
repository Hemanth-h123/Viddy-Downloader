import sqlite3
import os

DB_PATH = os.path.join('instance', 'downloader.db')

def add_admin_notes_column():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(feedback)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'admin_notes' not in columns:
            cursor.execute("ALTER TABLE feedback ADD COLUMN admin_notes TEXT")
            conn.commit()
            print("Successfully added 'admin_notes' column to feedback table")
        else:
            print("Column 'admin_notes' already exists in feedback table")

    except Exception as e:
        print(f"Error updating feedback table: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_admin_notes_column()