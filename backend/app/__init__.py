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

    # Enable CORS for React frontend
    CORS(app, resources={r"/*": {"origins": "*"}})

    with app.app_context():
        from .api.routes.data_generation import bp as data_generation_bp
        from .api.routes.preprocessing import bp as preprocessing_bp
        from .api.routes.training import bp as training_bp
        from .api.routes.analytics import bp as analytics_bp

        app.register_blueprint(data_generation_bp, url_prefix='/api/data')
        app.register_blueprint(preprocessing_bp, url_prefix='/api/preprocessing')
        app.register_blueprint(training_bp, url_prefix='/api/training')
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    return app
