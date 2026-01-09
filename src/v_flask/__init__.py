"""
v-flask - Flask Core Extension Package

Reusable base package with User, Config, Logging, Auth for Flask applications.

Usage:
    from flask import Flask
    from v_flask import VFlask, db

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SECRET_KEY'] = 'your-secret-key'

    v_flask = VFlask(app)

    # Models available after init:
    from v_flask.models import User, Rolle, Permission, Config, Betreiber, AuditLog

    # Auth decorators:
    from v_flask.auth import permission_required, admin_required

    # Plugin system:
    from v_flask.plugins import PluginManifest, PluginRegistry

    class MyPlugin(PluginManifest):
        name = 'my-plugin'
        version = '1.0.0'
        ...

    v_flask.register_plugin(MyPlugin())
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import jinja2
from flask import Blueprint
from flask_login import LoginManager

from v_flask.extensions import db
from v_flask.plugins import PluginManifest, PluginRegistry, PluginManager, RestartManager
from v_flask.plugins.slots import PluginSlotManager

if TYPE_CHECKING:
    from flask import Flask

__version__ = "0.1.0"

__all__ = [
    'VFlask',
    'db',
    'PluginManifest',
    'PluginRegistry',
    'PluginManager',
    'PluginSlotManager',
    'RestartManager',
]


class VFlask:
    """Flask extension for v-flask core functionality.

    Provides:
        - SQLAlchemy database integration
        - Flask-Login user authentication
        - User, Role, Permission models
        - Auth decorators (@permission_required, @admin_required)
        - Betreiber (operator) for theming
        - Plugin system for extensibility

    Usage:
        # Simple initialization
        app = Flask(__name__)
        v_flask = VFlask(app)

        # Factory pattern
        v_flask = VFlask()
        v_flask.init_app(app)

        # With custom login settings
        v_flask = VFlask(app)
        v_flask.login_manager.login_view = 'auth.login'

        # With plugins
        from my_plugins import KontaktPlugin

        v_flask = VFlask()
        v_flask.register_plugin(KontaktPlugin())
        v_flask.init_app(app)
    """

    def __init__(self, app: Flask | None = None) -> None:
        """Initialize the extension.

        Args:
            app: Flask application instance. If provided, init_app is called.
        """
        self.app = app
        self.login_manager = LoginManager()
        self.plugin_registry = PluginRegistry()
        self.plugin_manager = PluginManager()
        self.restart_manager = RestartManager()
        self.slot_manager = PluginSlotManager()
        self._initialized = False

        if app is not None:
            self.init_app(app)

    def register_plugin(self, plugin: PluginManifest) -> None:
        """Register a plugin before initialization.

        Plugins must be registered before calling init_app().

        Args:
            plugin: Plugin instance to register.

        Raises:
            PluginRegistryError: If init_app() was already called.

        Example:
            v_flask = VFlask()
            v_flask.register_plugin(KontaktPlugin())
            v_flask.init_app(app)
        """
        from v_flask.plugins.registry import PluginRegistryError

        if self._initialized:
            raise PluginRegistryError(
                "Cannot register plugins after initialization"
            )
        self.plugin_registry.register(plugin)

    def init_app(self, app: Flask) -> None:
        """Initialize the extension with a Flask app.

        This method:
            - Initializes SQLAlchemy with the app
            - Configures Flask-Login
            - Registers the user loader
            - Adds template context processors
            - Stores the extension in app.extensions

        Args:
            app: Flask application instance.
        """
        self.app = app

        # Initialize SQLAlchemy
        db.init_app(app)

        # Configure Flask-Login
        self.login_manager.init_app(app)
        self.login_manager.login_view = 'auth.login'
        self.login_manager.login_message = 'Bitte melde dich an.'
        self.login_manager.login_message_category = 'info'

        # Register user loader
        @self.login_manager.user_loader
        def load_user(user_id: str):
            from v_flask.models import User
            return db.session.get(User, int(user_id))

        # Template context processor for Betreiber and system status
        @app.context_processor
        def inject_v_flask_context():
            def get_betreiber():
                from v_flask.models import Betreiber
                return db.session.query(Betreiber).first()

            def get_restart_required():
                """Check if a server restart is required."""
                try:
                    return self.plugin_manager.is_restart_required()
                except Exception:
                    return False

            def get_scheduled_restart():
                """Get scheduled restart time, if any."""
                try:
                    return self.restart_manager.get_scheduled_restart()
                except Exception:
                    return None

            def get_plugin_slots(slot_name: str) -> list[dict]:
                """Get UI elements for a template slot.

                Args:
                    slot_name: Name of the slot (footer_links, navbar_items, etc.)

                Returns:
                    List of slot items from active plugins.
                """
                from flask_login import current_user
                user = current_user if current_user.is_authenticated else None
                return self.slot_manager.get_items(slot_name, user=user, app=app)

            return {
                'get_betreiber': get_betreiber,
                'get_plugin_slots': get_plugin_slots,
                'v_flask_version': __version__,
                'restart_required': get_restart_required,
                'scheduled_restart': get_scheduled_restart,
            }

        # Register templates and static files
        self._register_templates(app)
        self._register_static_blueprint(app)
        self._register_jinja_filters(app)
        self._register_cli_commands(app)
        self._register_plugin_admin_routes(app)

        # Register slot manager in extensions (must be before plugin init)
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['v_flask_slots'] = self.slot_manager

        # Initialize registered plugins
        self._init_plugins(app)

        # Mark as initialized (prevents further plugin registration)
        self._initialized = True

        # Store extension in app
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['v_flask'] = self

    def create_tables(self) -> None:
        """Create all database tables.

        Call this after all models are imported.

        Usage:
            with app.app_context():
                v_flask.create_tables()
        """
        db.create_all()

    def seed_roles(self) -> None:
        """Seed default roles (admin, mitarbeiter, kunde) with permissions.

        Creates three standard roles and assigns appropriate permissions.

        Usage:
            with app.app_context():
                v_flask.seed_roles()
        """
        from v_flask.models import Permission, Rolle

        # Create default permissions
        default_permissions = [
            ('admin.*', 'Vollzugriff auf alle Admin-Funktionen'),
            ('user.read', 'Benutzer ansehen'),
            ('user.create', 'Benutzer erstellen'),
            ('user.update', 'Benutzer bearbeiten'),
            ('user.delete', 'Benutzer löschen'),
            ('config.read', 'Konfiguration ansehen'),
            ('config.update', 'Konfiguration bearbeiten'),
            ('plugins.manage', 'Plugins aktivieren und deaktivieren'),
            ('plugins.restart', 'Server-Neustart initiieren'),
        ]

        permissions = {}
        for code, beschreibung in default_permissions:
            perm = db.session.query(Permission).filter_by(code=code).first()
            if not perm:
                perm = Permission(code=code, beschreibung=beschreibung, modul='core')
                db.session.add(perm)
            permissions[code] = perm

        db.session.flush()

        # Create default roles
        default_roles = [
            ('admin', 'Administrator mit vollem Zugriff', ['admin.*']),
            ('betreiber', 'Betreiber mit Plugin-Verwaltung', [
                'user.read', 'config.read', 'plugins.manage', 'plugins.restart'
            ]),
            ('mitarbeiter', 'Interner Mitarbeiter', ['user.read', 'config.read']),
            ('kunde', 'Externer Kunde', []),
        ]

        for name, beschreibung, perm_codes in default_roles:
            rolle = db.session.query(Rolle).filter_by(name=name).first()
            if not rolle:
                rolle = Rolle(name=name, beschreibung=beschreibung)
                db.session.add(rolle)
                db.session.flush()

            # Add permissions to role
            for code in perm_codes:
                if code in permissions:
                    if permissions[code] not in rolle.permissions.all():
                        rolle.permissions.append(permissions[code])

        db.session.commit()

    def seed_betreiber(
        self,
        name: str = 'V-Flask App',
        primary_color: str = '#3b82f6',
        secondary_color: str = '#64748b',
    ) -> None:
        """Seed a default Betreiber if none exists.

        Args:
            name: Company/app name.
            primary_color: Primary CI color (hex).
            secondary_color: Secondary CI color (hex).

        Usage:
            with app.app_context():
                v_flask.seed_betreiber(name='My Company', primary_color='#10b981')
        """
        from v_flask.models import Betreiber

        if not db.session.query(Betreiber).first():
            betreiber = Betreiber(
                name=name,
                primary_color=primary_color,
                secondary_color=secondary_color,
                font_family='Inter',
            )
            db.session.add(betreiber)
            db.session.commit()

    def _register_templates(self, app: Flask) -> None:
        """Add v_flask templates to Jinja search path.

        Templates are namespaced under 'v_flask/' to avoid conflicts.
        Host apps can extend: {% extends "v_flask/base.html" %}
        """
        template_folder = os.path.join(os.path.dirname(__file__), 'templates')

        # Use ChoiceLoader to add v_flask templates while preserving app templates
        app.jinja_loader = jinja2.ChoiceLoader([
            app.jinja_loader,  # App templates first (allows overrides)
            jinja2.FileSystemLoader(template_folder),
        ])

    def _register_static_blueprint(self, app: Flask) -> None:
        """Register blueprint for serving v_flask static files.

        Files are served under /v_flask_static/ URL prefix.
        Usage in templates: {{ url_for('v_flask_static.static', filename='css/v-flask.css') }}
        """
        static_folder = os.path.join(os.path.dirname(__file__), 'static')

        v_flask_static = Blueprint(
            'v_flask_static',
            __name__,
            static_folder=static_folder,
            static_url_path='/v_flask_static'
        )

        app.register_blueprint(v_flask_static)

    def _register_jinja_filters(self, app: Flask) -> None:
        """Register custom Jinja filters for templates.

        Filters:
            - markdown: Convert markdown text to HTML (requires markdown package)
        """
        try:
            import markdown as md

            @app.template_filter('markdown')
            def markdown_filter(text: str) -> str:
                """Convert markdown to HTML with common extensions."""
                if not text:
                    return ''
                return md.markdown(
                    text,
                    extensions=['extra', 'nl2br', 'sane_lists']
                )
        except ImportError:
            # markdown package not installed - filter returns escaped text
            from markupsafe import escape

            @app.template_filter('markdown')
            def markdown_filter(text: str) -> str:
                """Fallback: return escaped text when markdown not installed."""
                return escape(text) if text else ''

    def _register_cli_commands(self, app: Flask) -> None:
        """Register Flask CLI commands.

        Commands:
            - flask init-db: Create all database tables
            - flask seed: Seed core data (roles, permissions, betreiber)
            - flask create-admin: Create an admin user interactively
        """
        from .cli import register_commands
        register_commands(app, db)

    def _register_plugin_admin_routes(self, app: Flask) -> None:
        """Register admin routes for plugin management.

        Routes are available under /admin/plugins/ and require
        'plugins.manage' or 'plugins.restart' permissions.
        """
        from v_flask.plugins.admin_routes import register_plugin_admin_routes
        register_plugin_admin_routes(app)

    def _init_plugins(self, app: Flask) -> None:
        """Initialize all registered plugins.

        This method:
        1. Loads activated plugins from the database (dynamic activation)
        2. Initializes all registered plugins in dependency-resolved order

        This method is called automatically at the end of init_app().
        """
        # Load activated plugins from database
        try:
            loaded = self.plugin_manager.load_activated_plugins(self.plugin_registry)
            if loaded:
                app.logger.info(
                    f"Loaded {len(loaded)} activated plugin(s) from database: {', '.join(loaded)}"
                )
        except Exception as e:
            # Don't fail startup if plugin loading fails (DB might not exist yet)
            app.logger.warning(f"Could not load activated plugins: {e}")

        # Initialize all registered plugins (both manual and DB-activated)
        if len(self.plugin_registry) > 0:
            app.logger.info(
                f"Initializing {len(self.plugin_registry)} plugin(s)..."
            )
            self.plugin_registry.init_plugins(app)
            app.logger.info("Plugin initialization complete")

        # Clear restart flag after successful startup
        try:
            self.restart_manager.clear_restart_flag()
        except Exception:
            pass  # Ignore if DB not ready
