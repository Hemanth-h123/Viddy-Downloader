import sqlite3
import os
from getpass import getpass

# Path to the database file
db_path = os.path.join('instance', 'downloader.db')

def make_user_admin(email):
    """Make a user an admin by their email address"""
    print(f"Connecting to database at {db_path}...")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the user exists
    cursor.execute("SELECT id, username FROM user WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"No user found with email: {email}")
        conn.close()
        return False
    
    # Update the user to be an admin
    cursor.execute("UPDATE user SET is_admin = 1 WHERE email = ?", (email,))
    conn.commit()
    
    print(f"User '{user[1]}' (ID: {user[0]}) has been made an admin!")
    
    # Close the connection
    conn.close()
    return True

if __name__ == "__main__":
    print("Make User Admin Tool")
    print("====================")
    
    email = input("Enter the email of the user to make admin: ")
    make_user_admin(email)
    print("\nDone! You can now log in with this user's credentials to access the admin dashboard.")
    print("After logging in, you should see an 'Admin Dashboard' option in the user dropdown menu.")