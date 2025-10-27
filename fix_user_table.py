from app import app
from web.models import db
import sqlite3

def add_is_admin_column():
    with app.app_context():
        # Get the database path from app config
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add column if it doesn't exist
        if 'is_admin' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()
            print("Added is_admin column to user table")
        else:
            print("is_admin column already exists")
        
        # Close connection
        conn.close()

if __name__ == "__main__":
    add_is_admin_column()