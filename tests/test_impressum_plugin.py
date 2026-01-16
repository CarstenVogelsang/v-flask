"""Tests for the Impressum plugin."""

import pytest
from flask import Flask, Blueprint

from v_flask import VFlask, db
from v_flask.models import User, Rolle, Permission, Betreiber
from v_flask_plugins.impressum import ImpressumPlugin
from v_flask_plugins.impressum.generator import ImpressumGenerator
from v_flask_plugins.impressum.validators import ImpressumValidator, ValidationResult


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


def create_mock_admin_blueprint():
    """Create a mock admin blueprint for testing plugin templates."""
    admin_bp = Blueprint('admin', __name__)

    @admin_bp.route('/')
    def dashboard():
        return 'Admin Dashboard'

    return admin_bp


@pytest.fixture
def app_with_impressum():
    """Create a Flask app with Impressum plugin."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    # Register mock blueprints for template to work
    app.register_blueprint(create_mock_auth_blueprint(), url_prefix='/auth')
    app.register_blueprint(create_mock_admin_blueprint(), url_prefix='/admin')

    v_flask = VFlask()
    v_flask.register_plugin(ImpressumPlugin())
    v_flask.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app_with_impressum):
    """Create a test client."""
    return app_with_impressum.test_client()


@pytest.fixture
def betreiber_minimal(app_with_impressum):
    """Create a minimal Betreiber for testing."""
    with app_with_impressum.app_context():
        betreiber = Betreiber(name='Test GmbH')
        db.session.add(betreiber)
        db.session.commit()
        return betreiber.id


@pytest.fixture
def betreiber_complete(app_with_impressum):
    """Create a complete Betreiber with all Impressum fields."""
    with app_with_impressum.app_context():
        betreiber = Betreiber(
            name='Muster',
            rechtsform='GmbH',
            strasse='Musterstraße 1',
            plz='12345',
            ort='Musterstadt',
            land='Deutschland',
            telefon='+49 123 456789',
            fax='+49 123 456780',
            email='info@muster.de',
            geschaeftsfuehrer='Max Mustermann',
            handelsregister_gericht='Amtsgericht Musterstadt',
            handelsregister_nummer='HRB 12345',
            ust_idnr='DE123456789',
            wirtschafts_idnr='DE123456789012',
            inhaltlich_verantwortlich='Max Mustermann'
        )
        db.session.add(betreiber)
        db.session.commit()
        return betreiber.id


@pytest.fixture
def admin_user_id(app_with_impressum):
    """Create an admin user and return the ID for testing."""
    with app_with_impressum.app_context():
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

        return user.id


class TestImpressumPluginManifest:
    """Test ImpressumPlugin manifest."""

    def test_plugin_metadata(self):
        """Test plugin has correct metadata."""
        plugin = ImpressumPlugin()

        assert plugin.name == 'impressum'
        assert plugin.version == '1.0.0'
        assert plugin.author == 'v-flask'
        assert plugin.dependencies == []

    def test_plugin_provides_no_models(self):
        """Test plugin uses existing Betreiber model (no own models)."""
        plugin = ImpressumPlugin()
        models = plugin.get_models()

        assert len(models) == 0

    def test_plugin_provides_blueprints(self):
        """Test plugin provides two blueprints."""
        plugin = ImpressumPlugin()
        blueprints = plugin.get_blueprints()

        assert len(blueprints) == 2

        names = [bp.name for bp, _ in blueprints]
        assert 'impressum' in names
        assert 'impressum_admin' in names

    def test_plugin_has_template_folder(self):
        """Test plugin provides template folder."""
        plugin = ImpressumPlugin()
        folder = plugin.get_template_folder()

        assert folder is not None
        assert folder.exists()

    def test_plugin_marketplace_metadata(self):
        """Test plugin has marketplace metadata."""
        plugin = ImpressumPlugin()

        assert plugin.license == 'MIT'
        assert 'legal' in plugin.categories
        assert 'compliance' in plugin.categories
        assert 'impressum' in plugin.tags
        assert plugin.min_v_flask_version == '0.1.0'
        assert len(plugin.long_description) > 50

    def test_plugin_ui_slots(self):
        """Test plugin has UI slots configured."""
        plugin = ImpressumPlugin()

        assert 'footer_links' in plugin.ui_slots
        assert 'admin_menu' in plugin.ui_slots
        assert len(plugin.ui_slots['footer_links']) > 0

    def test_plugin_admin_category(self):
        """Test plugin defines admin category for navigation."""
        plugin = ImpressumPlugin()

        assert plugin.admin_category == 'legal'


class TestImpressumGenerator:
    """Test ImpressumGenerator class."""

    def test_generate_html_minimal(self, app_with_impressum, betreiber_minimal):
        """Test HTML generation with minimal data."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_minimal)
            generator = ImpressumGenerator(betreiber)
            html = generator.generate_html()

            assert 'Test GmbH' in html
            assert '§ 5 TMG' in html

    def test_generate_html_complete(self, app_with_impressum, betreiber_complete):
        """Test HTML generation with complete data."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_complete)
            generator = ImpressumGenerator(betreiber)
            html = generator.generate_html()

            assert 'Muster GmbH' in html
            assert 'Musterstraße 1' in html
            assert '12345 Musterstadt' in html
            assert 'Max Mustermann' in html
            assert 'HRB 12345' in html
            assert 'DE123456789' in html
            assert 'Kontakt' in html
            assert 'Registereintrag' in html

    def test_generate_html_with_visdp(self, app_with_impressum, betreiber_complete):
        """Test HTML generation with V.i.S.d.P. enabled."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_complete)
            betreiber.set_impressum_option('show_visdp', True)
            db.session.commit()

            generator = ImpressumGenerator(betreiber)
            html = generator.generate_html()

            assert 'Verantwortlich für den Inhalt' in html
            assert '§ 55 Abs. 2 RStV' in html

    def test_generate_html_with_streitschlichtung(self, app_with_impressum, betreiber_complete):
        """Test HTML generation with Streitschlichtung enabled."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_complete)
            betreiber.set_impressum_option('show_streitschlichtung', True)
            db.session.commit()

            generator = ImpressumGenerator(betreiber)
            html = generator.generate_html()

            assert 'Streitschlichtung' in html
            assert 'ec.europa.eu' in html

    def test_generate_text(self, app_with_impressum, betreiber_complete):
        """Test plain text generation."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_complete)
            generator = ImpressumGenerator(betreiber)
            text = generator.generate_text()

            # Should not contain HTML tags
            assert '<h2>' not in text
            assert '<p>' not in text
            assert '<br>' not in text

            # Should contain content
            assert 'Muster GmbH' in text

    def test_vertretung_title_gmbh(self, app_with_impressum):
        """Test correct title for GmbH."""
        with app_with_impressum.app_context():
            betreiber = Betreiber(
                name='Test',
                rechtsform='GmbH',
                geschaeftsfuehrer='Max Mustermann'
            )
            db.session.add(betreiber)
            db.session.commit()

            generator = ImpressumGenerator(betreiber)
            html = generator.generate_html()

            assert 'Geschäftsführer' in html

    def test_vertretung_title_ag(self, app_with_impressum):
        """Test correct title for AG."""
        with app_with_impressum.app_context():
            betreiber = Betreiber(
                name='Test',
                rechtsform='AG',
                geschaeftsfuehrer='Max Mustermann'
            )
            db.session.add(betreiber)
            db.session.commit()

            generator = ImpressumGenerator(betreiber)
            html = generator.generate_html()

            assert 'Vorstand' in html


class TestImpressumValidator:
    """Test ImpressumValidator class."""

    def test_validation_result_dataclass(self):
        """Test ValidationResult dataclass."""
        result = ValidationResult()

        assert result.is_valid is True
        assert result.has_warnings is False

        result.errors.append('Error')
        assert result.is_valid is False

        result.warnings.append('Warning')
        assert result.has_warnings is True

    def test_validate_minimal_betreiber(self, app_with_impressum, betreiber_minimal):
        """Test validation of minimal Betreiber."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_minimal)
            validator = ImpressumValidator(betreiber)
            result = validator.validate()

            assert result.is_valid is False
            assert len(result.errors) > 0
            assert any('Straße' in e for e in result.errors)
            assert any('E-Mail' in e for e in result.errors)

    def test_validate_complete_betreiber(self, app_with_impressum, betreiber_complete):
        """Test validation of complete Betreiber."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_complete)
            validator = ImpressumValidator(betreiber)
            result = validator.validate()

            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_kapitalgesellschaft_ohne_vertretung(self, app_with_impressum):
        """Test validation requires Geschäftsführer for GmbH."""
        with app_with_impressum.app_context():
            betreiber = Betreiber(
                name='Test',
                rechtsform='GmbH',
                strasse='Straße 1',
                plz='12345',
                ort='Stadt',
                email='test@example.com'
            )
            db.session.add(betreiber)
            db.session.commit()

            validator = ImpressumValidator(betreiber)
            result = validator.validate()

            assert any('Vertretungsberechtigter' in e for e in result.errors)

    def test_validate_ust_idnr_format(self, app_with_impressum):
        """Test USt-IdNr format validation."""
        with app_with_impressum.app_context():
            betreiber = Betreiber(
                name='Test',
                strasse='Straße 1',
                plz='12345',
                ort='Stadt',
                email='test@example.com',
                ust_idnr='INVALID'
            )
            db.session.add(betreiber)
            db.session.commit()

            validator = ImpressumValidator(betreiber)
            result = validator.validate()

            assert any('USt-IdNr' in w and 'Format' in w for w in result.warnings)

    def test_validate_plz_format(self, app_with_impressum):
        """Test PLZ format validation for Germany."""
        with app_with_impressum.app_context():
            betreiber = Betreiber(
                name='Test',
                strasse='Straße 1',
                plz='123',  # Invalid - should be 5 digits
                ort='Stadt',
                email='test@example.com',
                land='Deutschland'
            )
            db.session.add(betreiber)
            db.session.commit()

            validator = ImpressumValidator(betreiber)
            result = validator.validate()

            assert any('PLZ' in w for w in result.warnings)

    def test_completeness_score(self, app_with_impressum, betreiber_minimal):
        """Test completeness score calculation."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_minimal)
            validator = ImpressumValidator(betreiber)
            score = validator.get_completeness_score()

            assert 0 <= score <= 100
            assert score < 50  # Minimal has few fields

    def test_completeness_score_complete(self, app_with_impressum, betreiber_complete):
        """Test completeness score for complete Betreiber."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_complete)
            validator = ImpressumValidator(betreiber)
            score = validator.get_completeness_score()

            assert score >= 90  # Complete should be high


class TestPublicRoute:
    """Test public Impressum route."""

    def test_impressum_without_betreiber(self, client):
        """Test Impressum page without Betreiber."""
        response = client.get('/impressum/')

        assert response.status_code == 200
        assert b'Kein Impressum' in response.data

    def test_impressum_with_betreiber(self, app_with_impressum, betreiber_complete, client):
        """Test Impressum page with Betreiber."""
        response = client.get('/impressum/')

        assert response.status_code == 200
        assert b'Muster GmbH' in response.data
        assert b'Musterstra' in response.data  # Musterstraße (ß might be encoded)


class TestAdminRoutes:
    """Test admin routes for Impressum editor."""

    def test_editor_requires_auth(self, client):
        """Test that editor requires authentication."""
        response = client.get('/admin/impressum/')

        assert response.status_code == 302 or response.status_code == 401

    def test_editor_with_auth(self, app_with_impressum, betreiber_complete, admin_user_id):
        """Test editor with authenticated user."""
        client = app_with_impressum.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        response = client.get('/admin/impressum/')

        assert response.status_code == 200
        assert b'Editor' in response.data
        assert b'Vorschau' in response.data

    def test_save_impressum_data(self, app_with_impressum, betreiber_minimal, admin_user_id):
        """Test saving Impressum data."""
        client = app_with_impressum.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        response = client.post('/admin/impressum/', data={
            'name': 'Updated GmbH',
            'strasse': 'Neue Straße 1',
            'plz': '54321',
            'ort': 'Neustadt',
            'email': 'info@updated.de',
            'rechtsform': 'GmbH',
            'geschaeftsfuehrer': 'New Manager'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_minimal)
            assert betreiber.strasse == 'Neue Straße 1'
            assert betreiber.geschaeftsfuehrer == 'New Manager'

    def test_save_impressum_options(self, app_with_impressum, betreiber_complete, admin_user_id):
        """Test saving Impressum toggle options."""
        client = app_with_impressum.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        response = client.post('/admin/impressum/', data={
            'name': 'Muster',
            'show_visdp': 'on',
            'show_streitschlichtung': 'on'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_complete)
            assert betreiber.get_impressum_option('show_visdp') is True
            assert betreiber.get_impressum_option('show_streitschlichtung') is True


class TestBetreiberImpressumMethods:
    """Test Betreiber model Impressum methods."""

    def test_get_full_address(self, app_with_impressum, betreiber_complete):
        """Test get_full_address method."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_complete)
            address = betreiber.get_full_address()

            assert 'Musterstraße 1' in address
            assert '12345 Musterstadt' in address
            # Deutschland should not be included (default)
            assert 'Deutschland' not in address

    def test_get_full_address_foreign(self, app_with_impressum):
        """Test get_full_address for foreign countries."""
        with app_with_impressum.app_context():
            betreiber = Betreiber(
                name='Test',
                strasse='Main St 1',
                plz='10001',
                ort='New York',
                land='USA'
            )
            db.session.add(betreiber)
            db.session.commit()

            address = betreiber.get_full_address()
            assert 'USA' in address

    def test_get_company_name_with_rechtsform(self, app_with_impressum, betreiber_complete):
        """Test get_company_name_with_rechtsform method."""
        with app_with_impressum.app_context():
            betreiber = db.session.get(Betreiber, betreiber_complete)
            name = betreiber.get_company_name_with_rechtsform()

            assert name == 'Muster GmbH'

    def test_get_company_name_already_includes_rechtsform(self, app_with_impressum):
        """Test company name when it already includes rechtsform."""
        with app_with_impressum.app_context():
            betreiber = Betreiber(
                name='Test GmbH',
                rechtsform='GmbH'
            )
            db.session.add(betreiber)
            db.session.commit()

            name = betreiber.get_company_name_with_rechtsform()
            # Should not duplicate
            assert name == 'Test GmbH'
            assert 'GmbH GmbH' not in name

    def test_impressum_optionen_crud(self, app_with_impressum):
        """Test impressum_optionen get/set methods."""
        with app_with_impressum.app_context():
            betreiber = Betreiber(name='Test')
            db.session.add(betreiber)
            db.session.commit()

            # Test default
            assert betreiber.get_impressum_option('show_visdp', False) is False

            # Test set
            betreiber.set_impressum_option('show_visdp', True)
            db.session.commit()

            assert betreiber.get_impressum_option('show_visdp') is True

            # Test custom text option
            betreiber.set_impressum_option('streitschlichtung_text', 'Custom text')
            db.session.commit()

            assert betreiber.get_impressum_option('streitschlichtung_text') == 'Custom text'
