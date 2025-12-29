import os
from flask import Flask
from flask_cors import CORS


def create_app(config_name=None):
    """Flask application factory."""
    app = Flask(__name__)

    # Load configuration
    from .config import config
    config_name = config_name or os.environ.get('FLASK_CONFIG', 'development')
    app.config.from_object(config[config_name])

    # Configure CORS with specific allowed origins (not wildcard)
    allowed_origins = os.environ.get('CORS_ORIGINS', '').split(',')
    if not allowed_origins or allowed_origins == ['']:
        # Default allowed origins for development
        allowed_origins = [
            "http://localhost:5173",      # Vite dev server
            "http://127.0.0.1:5173",
            "http://localhost:3000",      # Alternative React port
            "http://frontend:5173",       # Docker internal
        ]

    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })

    with app.app_context():
        from .api.routes.data_generation import bp as data_generation_bp
        from .api.routes.preprocessing import bp as preprocessing_bp
        from .api.routes.training import bp as training_bp
        from .api.routes.analytics import bp as analytics_bp
        from .api.routes.data_ingestion import bp as data_ingestion_bp
        from .api.routes.explainability import explainability_bp
        from .api.routes.validation import validation_bp

        app.register_blueprint(data_generation_bp, url_prefix='/api/data')
        app.register_blueprint(preprocessing_bp, url_prefix='/api/preprocessing')
        app.register_blueprint(training_bp, url_prefix='/api/training')
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
        app.register_blueprint(data_ingestion_bp, url_prefix='/api/ingestion')
        app.register_blueprint(explainability_bp)
        app.register_blueprint(validation_bp, url_prefix='/api/validation')

    return app
