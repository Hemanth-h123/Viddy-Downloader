from app import app
from web.models import db
import os

def reset_database():
    with app.app_context():
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Remove existing database if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database at {db_path}")
        
        # Create all tables with updated schema
        db.create_all()
        print("Database recreated with updated schema")

if __name__ == "__main__":
    reset_database()