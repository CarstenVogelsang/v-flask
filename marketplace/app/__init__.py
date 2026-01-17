"""V-Flask Marketplace Application Factory.

Flask application for managing plugin licenses and distribution.
Uses v-flask framework for authentication and admin UI.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from v_flask import VFlask, db

# Global instances
migrate = Migrate()
csrf = CSRFProtect()

if TYPE_CHECKING:
    pass


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Configuration name ('development', 'production', 'testing').

    Returns:
        Configured Flask application.
    """
    from app.config import get_config, config as config_map

    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
    )

    # Load configuration
    if config_name:
        app.config.from_object(config_map.get(config_name, config_map['default']))
    else:
        app.config.from_object(get_config())

    # Ensure instance directory exists
    instance_path = Path(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    instance_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize v-flask (provides db, User, Rolle, Permission, Auth)
    v_flask = VFlask()
    v_flask.init_app(app)

    # Initialize Flask-Migrate for database migrations
    migrate.init_app(app, db)

    # Initialize CSRF protection
    csrf.init_app(app)

    # Register marketplace routes
    _register_routes(app)

    # Register CLI commands
    _register_cli(app)

    return app


def _register_routes(app: Flask) -> None:
    """Register all application routes.

    Args:
        app: Flask application instance.
    """
    from flask import Blueprint, render_template, redirect, url_for

    # Main blueprint for homepage
    main_bp = Blueprint('main', __name__)

    @main_bp.route('/')
    def index():
        """Marketplace homepage - redirect to shop."""
        return redirect(url_for('shop.plugin_list'))

    app.register_blueprint(main_bp)

    # Auth routes (login/logout)
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Admin routes (project/license management)
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin/marketplace')

    # Shop routes (public plugin catalog)
    from app.routes.shop import shop_bp
    app.register_blueprint(shop_bp, url_prefix='/plugins')

    # API routes (for satellite projects)
    from app.routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')


def _register_cli(app: Flask) -> None:
    """Register CLI commands.

    Args:
        app: Flask application instance.
    """
    import click

    @app.cli.command('init-marketplace')
    def init_marketplace():
        """Initialize marketplace database and seed data."""
        from app.services.plugin_scanner import scan_plugins
        from app.models import PluginMeta

        click.echo('Scanning plugins from v_flask_plugins...')
        plugins = scan_plugins()

        with app.app_context():
            for plugin_data in plugins:
                existing = db.session.query(PluginMeta).filter_by(
                    name=plugin_data['name']
                ).first()

                if not existing:
                    plugin = PluginMeta(
                        name=plugin_data['name'],
                        display_name=plugin_data.get('display_name', plugin_data['name']),
                        description=plugin_data.get('description', ''),
                        version=plugin_data.get('version', '0.1.0'),
                        price_cents=0,  # Default: free
                        is_published=True,
                    )
                    db.session.add(plugin)
                    click.echo(f'  Added: {plugin.name}')
                else:
                    click.echo(f'  Exists: {existing.name}')

            db.session.commit()

        click.echo('Done!')

    @app.cli.command('create-project')
    @click.argument('name')
    @click.argument('owner_email')
    def create_project(name: str, owner_email: str):
        """Create a new project with API key."""
        import secrets
        from app.models import Project

        with app.app_context():
            api_key = f"vf_proj_{secrets.token_urlsafe(32)}"
            project = Project(
                name=name,
                slug=name.lower().replace(' ', '-'),
                owner_email=owner_email,
                api_key=api_key,
            )
            db.session.add(project)
            db.session.commit()

            click.echo(f'Project created: {project.name}')
            click.echo(f'API Key: {api_key}')
            click.echo('Store this key securely - it cannot be retrieved later!')
