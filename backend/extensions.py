"""
extensions.py

WHY a separate extensions file?
  Flask extensions (db, jwt) must be created BEFORE the app object exists,
  then initialized with init_app() inside create_app(). This breaks the
  circular import: models.py imports db from here, not from app.py.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()
