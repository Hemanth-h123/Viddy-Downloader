from app import create_app
from web.database import db
from web.models import User, Download, Subscription

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        print("Dropped all existing tables")
        
        # Create all database tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Verify tables were created
        print("\nTables in database:")
        print(db.engine.table_names())