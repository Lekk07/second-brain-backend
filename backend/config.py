"""
config.py

WHY a config map with classes?
  Different environments (dev, test, prod) need different settings.
  Using classes + a map lets create_app() pick the right one via
  an env variable, keeping secrets out of source code.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()  # reads .env file automatically


class BaseConfig:
    """Shared defaults for all environments."""
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-change-me-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///second_brain_dev.db"
    )


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")  # PostgreSQL in prod
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://second-brain-frontend-drab.vercel.app").split(",")


# Maps the FLASK_ENV value to a config class
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
