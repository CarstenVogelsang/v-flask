"""Tests for the Kontakt plugin."""

import pytest
from flask import Flask, Blueprint

from v_flask import VFlask, db
from v_flask.models import User, Rolle, Permission
from v_flask_plugins.kontakt import KontaktPlugin
from v_flask_plugins.kontakt.models import KontaktAnfrage


def create_mock_auth_blueprint():
    """Create a mock auth blueprint for testing."""
    auth_bp = Blueprint('auth', __name__)

    @auth_bp.route('/login')
    def login():
        return 'Login'

    @auth_bp.route('/logout')
    def logout():
        return 'Logout'

    return auth_bp


@pytest.fixture
def app_with_kontakt():
    """Create a Flask app with Kontakt plugin."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    # Register mock auth blueprint for template to work
    app.register_blueprint(create_mock_auth_blueprint(), url_prefix='/auth')

    v_flask = VFlask()
    v_flask.register_plugin(KontaktPlugin())
    v_flask.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app_with_kontakt):
    """Create a test client."""
    return app_with_kontakt.test_client()


@pytest.fixture
def admin_user_id(app_with_kontakt):
    """Create an admin user and return the ID for testing."""
    with app_with_kontakt.app_context():
        # Create admin permission
        perm = Permission(code='admin.*', beschreibung='Vollzugriff', modul='core')
        db.session.add(perm)

        # Create admin role
        rolle = Rolle(name='admin', beschreibung='Administrator')
        rolle.permissions.append(perm)
        db.session.add(rolle)
        db.session.commit()

        # Create admin user
        user = User(
            email='admin@test.com',
            vorname='Admin',
            nachname='User',
            rolle_id=rolle.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Return just the ID to avoid DetachedInstanceError
        return user.id


class TestKontaktPluginManifest:
    """Test KontaktPlugin manifest."""

    def test_plugin_metadata(self):
        """Test plugin has correct metadata."""
        plugin = KontaktPlugin()

        assert plugin.name == 'kontakt'
        assert plugin.version == '1.0.0'
        assert plugin.author == 'v-flask'
        assert plugin.dependencies == []

    def test_plugin_provides_models(self):
        """Test plugin provides KontaktAnfrage model."""
        plugin = KontaktPlugin()
        models = plugin.get_models()

        assert len(models) == 1
        assert models[0] == KontaktAnfrage

    def test_plugin_provides_blueprints(self):
        """Test plugin provides two blueprints."""
        plugin = KontaktPlugin()
        blueprints = plugin.get_blueprints()

        assert len(blueprints) == 2

        names = [bp.name for bp, _ in blueprints]
        assert 'kontakt' in names
        assert 'kontakt_admin' in names

    def test_plugin_has_template_folder(self):
        """Test plugin provides template folder."""
        plugin = KontaktPlugin()
        folder = plugin.get_template_folder()

        assert folder is not None
        assert folder.exists()

    def test_plugin_marketplace_metadata(self):
        """Test plugin has marketplace metadata."""
        plugin = KontaktPlugin()

        assert plugin.license == 'MIT'
        assert 'forms' in plugin.categories
        assert 'communication' in plugin.categories
        assert 'kontakt' in plugin.tags
        assert plugin.min_v_flask_version == '0.1.0'
        assert len(plugin.long_description) > 50  # Has substantial description

    def test_plugin_get_readme(self):
        """Test plugin provides README content."""
        plugin = KontaktPlugin()
        readme = plugin.get_readme()

        assert readme is not None
        assert '# Kontakt-Plugin' in readme
        assert 'Features' in readme
        assert 'Installation' in readme

    def test_plugin_to_marketplace_dict(self):
        """Test marketplace dict includes all metadata."""
        plugin = KontaktPlugin()
        d = plugin.to_marketplace_dict()

        assert d['name'] == 'kontakt'
        assert d['license'] == 'MIT'
        assert 'forms' in d['categories']
        assert len(d['tags']) >= 3


class TestKontaktAnfrageModel:
    """Test KontaktAnfrage model."""

    def test_create_anfrage(self, app_with_kontakt):
        """Test creating a contact submission."""
        with app_with_kontakt.app_context():
            anfrage = KontaktAnfrage(
                name='Test User',
                email='test@example.com',
                nachricht='Test message'
            )
            db.session.add(anfrage)
            db.session.commit()

            assert anfrage.id is not None
            assert anfrage.gelesen is False
            assert anfrage.created_at is not None

    def test_mark_as_read(self, app_with_kontakt):
        """Test marking submission as read."""
        with app_with_kontakt.app_context():
            anfrage = KontaktAnfrage(
                name='Test',
                email='test@example.com',
                nachricht='Message'
            )
            db.session.add(anfrage)
            db.session.commit()

            assert anfrage.gelesen is False

            anfrage.mark_as_read()
            db.session.commit()

            assert anfrage.gelesen is True

    def test_to_dict(self, app_with_kontakt):
        """Test dictionary representation."""
        with app_with_kontakt.app_context():
            anfrage = KontaktAnfrage(
                name='Dict Test',
                email='dict@example.com',
                nachricht='Dict message'
            )
            db.session.add(anfrage)
            db.session.commit()

            d = anfrage.to_dict()

            assert d['name'] == 'Dict Test'
            assert d['email'] == 'dict@example.com'
            assert d['nachricht'] == 'Dict message'
            assert d['gelesen'] is False
            assert 'created_at' in d

    def test_repr(self, app_with_kontakt):
        """Test string representation."""
        with app_with_kontakt.app_context():
            anfrage = KontaktAnfrage(
                name='Test',
                email='test@example.com',
                nachricht='Message'
            )
            db.session.add(anfrage)
            db.session.commit()

            assert 'neu' in repr(anfrage)

            anfrage.mark_as_read()
            assert 'gelesen' in repr(anfrage)


class TestContactFormRoute:
    """Test public contact form routes."""

    def test_form_get(self, client):
        """Test GET request to contact form."""
        response = client.get('/kontakt/')

        assert response.status_code == 200
        assert b'Kontakt' in response.data

    def test_form_post_valid(self, app_with_kontakt, client):
        """Test POST with valid data."""
        response = client.post('/kontakt/', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'nachricht': 'This is a test message.'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Vielen Dank' in response.data

        # Check database
        with app_with_kontakt.app_context():
            anfrage = db.session.query(KontaktAnfrage).first()
            assert anfrage is not None
            assert anfrage.name == 'Test User'
            assert anfrage.email == 'test@example.com'

    def test_form_post_missing_name(self, client):
        """Test POST with missing name."""
        response = client.post('/kontakt/', data={
            'name': '',
            'email': 'test@example.com',
            'nachricht': 'Message'
        })

        assert response.status_code == 200
        assert b'Namen' in response.data

    def test_form_post_invalid_email(self, client):
        """Test POST with invalid email."""
        response = client.post('/kontakt/', data={
            'name': 'Test',
            'email': 'invalid-email',
            'nachricht': 'Message'
        })

        assert response.status_code == 200
        assert b'E-Mail' in response.data

    def test_form_post_missing_message(self, client):
        """Test POST with missing message."""
        response = client.post('/kontakt/', data={
            'name': 'Test',
            'email': 'test@example.com',
            'nachricht': ''
        })

        assert response.status_code == 200
        assert b'Nachricht' in response.data


class TestAdminRoutes:
    """Test admin routes for contact submissions."""

    def test_list_requires_auth(self, client):
        """Test that admin list requires authentication."""
        response = client.get('/admin/kontakt/')

        # Should redirect to login
        assert response.status_code == 302 or response.status_code == 401

    def test_list_with_auth(self, app_with_kontakt, admin_user_id):
        """Test admin list with authenticated user."""
        client = app_with_kontakt.test_client()

        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        response = client.get('/admin/kontakt/')
        assert response.status_code == 200
        assert b'Kontaktanfragen' in response.data

    def test_detail_marks_as_read(self, app_with_kontakt, admin_user_id):
        """Test that viewing detail marks submission as read."""
        # Create a submission
        with app_with_kontakt.app_context():
            anfrage = KontaktAnfrage(
                name='Test',
                email='test@example.com',
                nachricht='Message'
            )
            db.session.add(anfrage)
            db.session.commit()
            anfrage_id = anfrage.id

        client = app_with_kontakt.test_client()

        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        # View detail
        response = client.get(f'/admin/kontakt/{anfrage_id}')
        assert response.status_code == 200

        # Check it's marked as read
        with app_with_kontakt.app_context():
            anfrage = db.session.get(KontaktAnfrage, anfrage_id)
            assert anfrage.gelesen is True

    def test_toggle_read(self, app_with_kontakt, admin_user_id):
        """Test toggling read status."""
        # Create a read submission
        with app_with_kontakt.app_context():
            anfrage = KontaktAnfrage(
                name='Test',
                email='test@example.com',
                nachricht='Message',
                gelesen=True
            )
            db.session.add(anfrage)
            db.session.commit()
            anfrage_id = anfrage.id

        client = app_with_kontakt.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        # Toggle to unread
        response = client.post(
            f'/admin/kontakt/{anfrage_id}/toggle-read',
            follow_redirects=True
        )
        assert response.status_code == 200

        with app_with_kontakt.app_context():
            anfrage = db.session.get(KontaktAnfrage, anfrage_id)
            assert anfrage.gelesen is False

    def test_delete(self, app_with_kontakt, admin_user_id):
        """Test deleting a submission."""
        # Create a submission
        with app_with_kontakt.app_context():
            anfrage = KontaktAnfrage(
                name='Test',
                email='test@example.com',
                nachricht='Message'
            )
            db.session.add(anfrage)
            db.session.commit()
            anfrage_id = anfrage.id

        client = app_with_kontakt.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        # Delete
        response = client.post(
            f'/admin/kontakt/{anfrage_id}/delete',
            follow_redirects=True
        )
        assert response.status_code == 200

        with app_with_kontakt.app_context():
            anfrage = db.session.get(KontaktAnfrage, anfrage_id)
            assert anfrage is None
