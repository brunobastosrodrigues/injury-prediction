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
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from .api.routes import data_generation, preprocessing, training, analytics
    app.register_blueprint(data_generation.bp, url_prefix='/api/data')
    app.register_blueprint(preprocessing.bp, url_prefix='/api/preprocessing')
    app.register_blueprint(training.bp, url_prefix='/api/training')
    app.register_blueprint(analytics.bp, url_prefix='/api/analytics')

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy'}

    return app
