"""
services/auth_service.py

WHY bcrypt for passwords?
  bcrypt is a slow, salted hash designed for passwords. Even if the DB
  leaks, brute-forcing bcrypt hashes takes years vs milliseconds for MD5/SHA.
"""
import re
from extensions import db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def register_user(data: dict) -> tuple[dict | None, str | None]:
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validation
    if not username:
        return None, "Username is required"
    if len(username) < 3:
        return None, "Username must be at least 3 characters"
    if not email or not EMAIL_RE.match(email):
        return None, "Valid email is required"
    if len(password) < 6:
        return None, "Password must be at least 6 characters"

    # Uniqueness checks
    if User.query.filter_by(username=username).first():
        return None, "Username already taken"
    if User.query.filter_by(email=email).first():
        return None, "Email already registered"

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return user.to_dict(), None


def login_user(data: dict) -> tuple[dict | None, str | None]:
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return None, "Email and password are required"

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None, "Invalid email or password"

    return user.to_dict(), None


def get_user_by_id(user_id: int) -> dict | None:
    user = User.query.get(user_id)
    return user.to_dict() if user else None
