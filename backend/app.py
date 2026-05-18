"""
app.py — Application factory
"""
import os
from flask import Flask
from flask_cors import CORS
from extensions import db, jwt
from config import config_map


def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from routes.auth   import auth_bp
    from routes.notes  import notes_bp
    from routes.ai     import ai_bp
    from routes.search import search_bp
    from routes.graph  import graph_bp
    from routes.chat   import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(chat_bp)

    @app.route("/api/health")
    def health():
        return {"status": "ok", "env": config_name}

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
