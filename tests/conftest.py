"""Test fixtures for v-flask tests."""

import pytest
from flask import Flask, Blueprint

from v_flask import VFlask, db
from v_flask.models import User, Rolle, Permission, Betreiber


# Dummy admin blueprint for testing plugin templates
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
def dashboard():
    """Dummy admin dashboard for template url_for() calls."""
    return 'Admin Dashboard'


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    # Register dummy admin blueprint for template tests
    app.register_blueprint(admin_bp)

    v_flask = VFlask(app)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Provide the database session."""
    with app.app_context():
        yield db.session


@pytest.fixture
def betreiber(app):
    """Create a test Betreiber."""
    with app.app_context():
        b = Betreiber(
            name='Test Betreiber',
            primary_color='#3b82f6',
            secondary_color='#64748b'
        )
        db.session.add(b)
        db.session.commit()
        yield b


@pytest.fixture
def admin_rolle(app):
    """Create an admin role with permissions."""
    with app.app_context():
        # Create admin permission
        perm = Permission(code='admin.*', beschreibung='Vollzugriff', modul='core')
        db.session.add(perm)

        # Create admin role
        rolle = Rolle(name='admin', beschreibung='Administrator')
        rolle.permissions.append(perm)
        db.session.add(rolle)
        db.session.commit()
        yield rolle


@pytest.fixture
def mitarbeiter_rolle(app):
    """Create a mitarbeiter role with limited permissions."""
    with app.app_context():
        # Create permissions
        perm_read = Permission(code='projekt.read', beschreibung='Projekte lesen', modul='projekt')
        perm_create = Permission(code='projekt.create', beschreibung='Projekte erstellen', modul='projekt')
        db.session.add_all([perm_read, perm_create])

        # Create role
        rolle = Rolle(name='mitarbeiter', beschreibung='Mitarbeiter')
        rolle.permissions.extend([perm_read, perm_create])
        db.session.add(rolle)
        db.session.commit()
        yield rolle


@pytest.fixture
def admin_user(app, admin_rolle):
    """Create an admin user."""
    with app.app_context():
        user = User(
            email='admin@test.com',
            vorname='Admin',
            nachname='User',
            rolle_id=admin_rolle.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        yield user


@pytest.fixture
def mitarbeiter_user(app, mitarbeiter_rolle):
    """Create a mitarbeiter user."""
    with app.app_context():
        user = User(
            email='mitarbeiter@test.com',
            vorname='Mit',
            nachname='Arbeiter',
            rolle_id=mitarbeiter_rolle.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        yield user
