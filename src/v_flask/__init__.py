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
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask_login import LoginManager

from v_flask.extensions import db

if TYPE_CHECKING:
    from flask import Flask

__version__ = "0.1.0"

__all__ = [
    'VFlask',
    'db',
]


class VFlask:
    """Flask extension for v-flask core functionality.

    Provides:
        - SQLAlchemy database integration
        - Flask-Login user authentication
        - User, Role, Permission models
        - Auth decorators (@permission_required, @admin_required)
        - Betreiber (operator) for theming

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
    """

    def __init__(self, app: Flask | None = None) -> None:
        """Initialize the extension.

        Args:
            app: Flask application instance. If provided, init_app is called.
        """
        self.app = app
        self.login_manager = LoginManager()

        if app is not None:
            self.init_app(app)

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

        # Template context processor for Betreiber
        @app.context_processor
        def inject_v_flask_context():
            def get_betreiber():
                from v_flask.models import Betreiber
                return db.session.query(Betreiber).first()

            return {
                'get_betreiber': get_betreiber,
                'v_flask_version': __version__,
            }

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
