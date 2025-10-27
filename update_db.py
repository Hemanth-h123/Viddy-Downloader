from app import app
from web.models import db

with app.app_context():
    db.create_all()
    print("Database schema updated successfully!")