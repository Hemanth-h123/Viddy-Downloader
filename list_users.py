import sqlite3
import os

# Path to the database file
db_path = os.path.join('instance', 'downloader.db')

def list_users():
    """List all users in the database"""
    print(f"Connecting to database at {db_path}...")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id, username, email, is_admin FROM user")
    users = cursor.fetchall()
    
    if not users:
        print("No users found in the database.")
    else:
        print("\nUsers in the database:")
        print("=" * 70)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin'}")
        print("-" * 70)
        for user in users:
            admin_status = "Yes" if user[3] else "No"
            print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {admin_status}")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    list_users()