"""
app.py - Flask application factory and entry-point.

Usage:
    python app.py                  # Development server
    gunicorn app:app               # Production (Railway / Heroku)
"""

import os

from flask import Flask

from config import get_config
from database.db import init_db
from routes.task_routes import task_bp


def create_app() -> Flask:
    """
    Application factory.

    Returns a fully configured Flask application instance with:
      - Config values loaded from config.py
      - Database initialised
      - Blueprints registered
    """
    app = Flask(__name__)
    cfg = get_config()
    app.config["SECRET_KEY"] = cfg.SECRET_KEY
    app.config["DEBUG"] = cfg.DEBUG
    app.config["TESTING"] = cfg.TESTING

    # Initialise the SQLite schema on first run
    init_db()

    # Register blueprints
    app.register_blueprint(task_bp)

    return app


# Create the module-level app instance (used by gunicorn via `app:app`)
app = create_app()

if __name__ == "__main__":
    # Respect Railway's PORT env var; fall back to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
