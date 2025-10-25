from application import create_app
from src.models.database import db
from src.models.user import *

app = create_app()
with app.app_context():
    db.create_all()
    print('Database schema updated successfully.')
