from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy()
admin = Admin(name='Beauty Clinic Admin', template_mode='bootstrap4', url='/flask-admin')