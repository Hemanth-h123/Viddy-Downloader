"""
Database configuration module to avoid circular imports
"""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()
