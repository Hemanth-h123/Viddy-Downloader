from flask_migrate import Migrate
from app import app
from web.database import db

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True)
