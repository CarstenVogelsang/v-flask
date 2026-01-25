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

    @app.cli.command('seed-categories')
    def seed_categories():
        """Seed plugin categories with predefined data."""
        from app.models import PluginCategory

        categories = [
            {
                'code': 'essential',
                'name_de': 'Basis',
                'description_de': 'Essenzielle Plugins für rechtliche Anforderungen wie Impressum, Datenschutz und Kontakt.',
                'icon': 'ti ti-shield-check',
                'color_hex': '#22c55e',
                'sort_order': 1,
            },
            {
                'code': 'content',
                'name_de': 'Content',
                'description_de': 'Plugins für Inhalts-Erstellung und -Verwaltung wie Hero-Sections, CTAs und CMS.',
                'icon': 'ti ti-file-text',
                'color_hex': '#3b82f6',
                'sort_order': 2,
            },
            {
                'code': 'commerce',
                'name_de': 'Commerce',
                'description_de': 'E-Commerce Plugins für Shop, Produktverwaltung (PIM) und Preisgestaltung.',
                'icon': 'ti ti-shopping-cart',
                'color_hex': '#f59e0b',
                'sort_order': 3,
            },
            {
                'code': 'forms',
                'name_de': 'Formulare',
                'description_de': 'Plugins für Formulare, Umfragen und strukturierte Datenerfassung.',
                'icon': 'ti ti-forms',
                'color_hex': '#8b5cf6',
                'sort_order': 4,
            },
            {
                'code': 'tools',
                'name_de': 'Tools',
                'description_de': 'Werkzeuge und Hilfsfunktionen wie Medienverwaltung und Projektverwaltung.',
                'icon': 'ti ti-tool',
                'color_hex': '#64748b',
                'sort_order': 5,
            },
            {
                'code': 'integration',
                'name_de': 'Integration',
                'description_de': 'Plugins zur Anbindung externer Systeme und APIs.',
                'icon': 'ti ti-plug',
                'color_hex': '#ec4899',
                'sort_order': 6,
            },
        ]

        with app.app_context():
            added = 0
            for cat_data in categories:
                existing = db.session.query(PluginCategory).filter_by(
                    code=cat_data['code']
                ).first()

                if not existing:
                    cat = PluginCategory(**cat_data)
                    db.session.add(cat)
                    click.echo(f'  Added: {cat.code} ({cat.name_de})')
                    added += 1
                else:
                    click.echo(f'  Exists: {existing.code}')

            db.session.commit()
            click.echo(f'Done! {added} categories added.')

    @app.cli.command('assign-plugin-categories')
    def assign_plugin_categories():
        """Assign categories and icons to existing plugins."""
        from app.models import PluginMeta, PluginCategory

        # Plugin assignments: name -> (category_code, icon)
        assignments = {
            # Essential (legal requirements)
            'impressum': ('essential', 'ti ti-scale'),
            'datenschutz': ('essential', 'ti ti-shield-lock'),
            'kontakt': ('essential', 'ti ti-mail'),
            # Content
            'hero': ('content', 'ti ti-photo'),
            'cta': ('content', 'ti ti-click'),
            'katalog': ('content', 'ti ti-book'),
            'content': ('content', 'ti ti-layout-grid'),
            # Commerce
            'shop': ('commerce', 'ti ti-shopping-cart'),
            'pim': ('commerce', 'ti ti-package'),
            'pricing': ('commerce', 'ti ti-currency-euro'),
            'crm': ('commerce', 'ti ti-users'),
            # Forms
            'fragebogen': ('forms', 'ti ti-clipboard-list'),
            # Tools
            'media': ('tools', 'ti ti-photo-video'),
            'projektverwaltung': ('tools', 'ti ti-folder'),
            # Integration
            'api_market': ('integration', 'ti ti-api'),
            'crm_udo': ('integration', 'ti ti-database-import'),
        }

        with app.app_context():
            # Get all categories by code
            categories = {c.code: c.id for c in PluginCategory.query.all()}

            updated = 0
            for name, (cat_code, icon) in assignments.items():
                plugin = db.session.query(PluginMeta).filter_by(name=name).first()
                if plugin:
                    cat_id = categories.get(cat_code)
                    if cat_id:
                        plugin.category_id = cat_id
                        plugin.icon = icon
                        updated += 1
                        click.echo(f'  {name}: {cat_code} ({icon})')
                    else:
                        click.echo(f'  {name}: Category {cat_code} not found!')
                else:
                    click.echo(f'  {name}: Plugin not found')

            db.session.commit()
            click.echo(f'Done! {updated} plugins updated.')

    @app.cli.command('seed-plugin-prices')
    def seed_plugin_prices():
        """Seed default prices for plugins."""
        from app.models import PluginMeta, PluginPrice, ProjectType

        # Plugins with prices: (plugin_name, price_cents_monthly)
        plugin_prices = {
            'content': 99,  # 0,99 €
            'hero': 99,     # 0,99 €
        }

        with app.app_context():
            # Get all non-free project types (excludes 'intern')
            project_types = ProjectType.query.filter_by(is_free=False).all()

            if not project_types:
                click.echo('No project types found! Run: flask db upgrade && seed ProjectType.seed_defaults()')
                return

            for plugin_name, price_cents in plugin_prices.items():
                plugin = PluginMeta.query.filter_by(name=plugin_name).first()
                if not plugin:
                    click.echo(f'  {plugin_name}: Plugin not found')
                    continue

                # Set base price in PluginMeta
                plugin.price_cents = price_cents
                click.echo(f'  {plugin_name}: Base price = {price_cents} Cent')

                # Create PluginPrice entries for each project type
                for pt in project_types:
                    for cycle in ['monthly', 'yearly']:
                        existing = PluginPrice.query.filter_by(
                            plugin_id=plugin.id,
                            project_type_id=pt.id,
                            billing_cycle=cycle
                        ).first()

                        if cycle == 'yearly':
                            actual_price = int(price_cents * 12 * 0.9)  # 10% Jahresrabatt
                        else:
                            actual_price = price_cents

                        if existing:
                            existing.price_cents = actual_price
                            existing.is_active = True
                        else:
                            new_price = PluginPrice(
                                plugin_id=plugin.id,
                                project_type_id=pt.id,
                                billing_cycle=cycle,
                                price_cents=actual_price,
                                is_active=True,
                            )
                            db.session.add(new_price)

                        click.echo(f'    {pt.code}/{cycle}: {actual_price} Cent')

            db.session.commit()
            click.echo('Done!')
