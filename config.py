"""
config.py - Application configuration settings.
Centralizes all configuration for different environments.
"""

import os


class Config:
    """Base configuration class."""
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "tasks.db")
    DEBUG: bool = False
    TESTING: bool = False


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG: bool = True


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING: bool = True
    # Use a named temp file so every connection within a test run shares the
    # same database (SQLite :memory: creates a new DB per connection).
    DATABASE_PATH: str = "/tmp/test_tasks.db"


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG: bool = False
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production")


# Map string names to config classes for easy selection
config_map: dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> Config:
    """Return the appropriate config based on FLASK_ENV environment variable."""
    env = os.environ.get("FLASK_ENV", "default")
    return config_map.get(env, DevelopmentConfig)()
