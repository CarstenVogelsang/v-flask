"""Configuration for V-Flask Marketplace application.

Environment variables can be set in .env file.
"""
import os
from pathlib import Path


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'marketplace-dev-secret-change-in-production')

    # SQLAlchemy Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + str(Path(__file__).parent.parent / 'instance' / 'marketplace.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Path to v_flask_plugins directory (for scanning and packaging)
    PLUGINS_SOURCE_DIR = os.environ.get(
        'PLUGINS_SOURCE_DIR',
        str(Path(__file__).parent.parent.parent / 'src' / 'v_flask_plugins')
    )

    # Stripe settings (Phase 4)
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

    # Marketplace settings
    MARKETPLACE_NAME = os.environ.get('MARKETPLACE_NAME', 'V-Flask Plugin Marketplace')
    MARKETPLACE_URL = os.environ.get('MARKETPLACE_URL', 'http://localhost:5000')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def get_config():
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
