"""Tests for the Datenschutz plugin."""

import pytest
from flask import Flask

from v_flask.extensions import db


@pytest.fixture
def app():
    """Create test application."""
    from pathlib import Path
    from jinja2 import ChoiceLoader, FileSystemLoader

    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    db.init_app(app)

    # Set up template loaders for plugin templates
    plugin_templates = Path(__file__).parent.parent / 'src' / 'v_flask_plugins' / 'datenschutz' / 'templates'
    vflask_templates = Path(__file__).parent.parent / 'src' / 'v_flask' / 'templates'

    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        FileSystemLoader(str(plugin_templates)),
        FileSystemLoader(str(vflask_templates)),
    ])

    # Register blueprints
    from v_flask_plugins.datenschutz.routes import datenschutz_bp, datenschutz_admin_bp
    app.register_blueprint(datenschutz_bp, url_prefix='/datenschutz')
    app.register_blueprint(datenschutz_admin_bp, url_prefix='/admin/datenschutz')

    with app.app_context():
        from v_flask_plugins.datenschutz.models import DatenschutzConfig, DatenschutzVersion
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def config(app):
    """Create a test DatenschutzConfig."""
    from v_flask_plugins.datenschutz.models import DatenschutzConfig

    with app.app_context():
        config = DatenschutzConfig(
            verantwortlicher_name='Test GmbH',
            verantwortlicher_strasse='Teststraße 1',
            verantwortlicher_plz='12345',
            verantwortlicher_ort='Teststadt',
            verantwortlicher_email='test@example.de',
            aktivierte_bausteine=['server_logs', 'ssl_verschluesselung'],
        )
        db.session.add(config)
        db.session.commit()
        yield config


# =============================================================================
# Plugin Manifest Tests
# =============================================================================


class TestDatenschutzPluginManifest:
    """Tests for the plugin manifest."""

    def test_plugin_metadata(self):
        """Test plugin has required metadata."""
        from v_flask_plugins.datenschutz import DatenschutzPlugin

        plugin = DatenschutzPlugin()
        assert plugin.name == 'datenschutz'
        assert plugin.version == '1.0.0'
        assert 'DSGVO' in plugin.description

    def test_plugin_provides_models(self):
        """Test plugin provides models."""
        from v_flask_plugins.datenschutz import DatenschutzPlugin

        plugin = DatenschutzPlugin()
        models = plugin.get_models()
        assert len(models) == 2
        model_names = [m.__name__ for m in models]
        assert 'DatenschutzConfig' in model_names
        assert 'DatenschutzVersion' in model_names

    def test_plugin_provides_blueprints(self):
        """Test plugin provides blueprints."""
        from v_flask_plugins.datenschutz import DatenschutzPlugin

        plugin = DatenschutzPlugin()
        blueprints = plugin.get_blueprints()
        assert len(blueprints) == 2

    def test_plugin_has_template_folder(self):
        """Test plugin has template folder."""
        from v_flask_plugins.datenschutz import DatenschutzPlugin

        plugin = DatenschutzPlugin()
        folder = plugin.get_template_folder()
        assert folder.exists()
        assert (folder / 'datenschutz' / 'public.html').exists()

    def test_plugin_marketplace_metadata(self):
        """Test plugin has marketplace metadata."""
        from v_flask_plugins.datenschutz import DatenschutzPlugin

        plugin = DatenschutzPlugin()
        assert plugin.license == 'MIT'
        assert 'privacy' in plugin.categories
        assert 'dsgvo' in plugin.tags

    def test_plugin_ui_slots(self):
        """Test plugin defines UI slots."""
        from v_flask_plugins.datenschutz import DatenschutzPlugin

        plugin = DatenschutzPlugin()
        assert 'footer_links' in plugin.ui_slots
        assert 'admin_menu' in plugin.ui_slots

    def test_plugin_admin_category(self):
        """Test plugin defines admin category for navigation."""
        from v_flask_plugins.datenschutz import DatenschutzPlugin

        plugin = DatenschutzPlugin()
        assert plugin.admin_category == 'legal'


# =============================================================================
# Model Tests
# =============================================================================


class TestDatenschutzConfigModel:
    """Tests for DatenschutzConfig model."""

    def test_create_config(self, app):
        """Test creating a config."""
        from v_flask_plugins.datenschutz.models import DatenschutzConfig

        with app.app_context():
            config = DatenschutzConfig(
                verantwortlicher_name='Test GmbH',
                verantwortlicher_email='test@example.de',
            )
            db.session.add(config)
            db.session.commit()

            assert config.id is not None
            assert config.version == 1

    def test_get_verantwortlicher_adresse(self, app):
        """Test formatted address generation."""
        from v_flask_plugins.datenschutz.models import DatenschutzConfig

        with app.app_context():
            config = DatenschutzConfig(
                verantwortlicher_strasse='Teststraße 1',
                verantwortlicher_plz='12345',
                verantwortlicher_ort='Teststadt',
                verantwortlicher_land='Österreich',
            )
            address = config.get_verantwortlicher_adresse()
            assert 'Teststraße 1' in address
            assert '12345 Teststadt' in address
            assert 'Österreich' in address

    def test_baustein_activation(self, app):
        """Test Baustein activation/deactivation."""
        from v_flask_plugins.datenschutz.models import DatenschutzConfig

        with app.app_context():
            config = DatenschutzConfig()
            config.aktiviere_baustein('google_analytics')
            assert config.is_baustein_aktiv('google_analytics')

            config.deaktiviere_baustein('google_analytics')
            assert not config.is_baustein_aktiv('google_analytics')

    def test_baustein_config(self, app):
        """Test Baustein-specific configuration."""
        from v_flask_plugins.datenschutz.models import DatenschutzConfig

        with app.app_context():
            config = DatenschutzConfig()
            config.set_baustein_config('google_analytics', {'tracking_id': 'G-12345'})

            baustein_config = config.get_baustein_config('google_analytics')
            assert baustein_config['tracking_id'] == 'G-12345'

    def test_version_snapshot(self, app):
        """Test version snapshot creation."""
        from v_flask_plugins.datenschutz.models import DatenschutzConfig

        with app.app_context():
            config = DatenschutzConfig(
                verantwortlicher_name='Test GmbH',
            )
            db.session.add(config)
            db.session.commit()

            initial_version = config.version
            config.create_version_snapshot('test@user.de')
            db.session.commit()

            assert config.version == initial_version + 1
            assert len(config.versionen) == 1
            assert config.versionen[0].changed_by == 'test@user.de'


# =============================================================================
# Bausteine Tests
# =============================================================================


class TestBausteine:
    """Tests for Bausteine definitions."""

    def test_get_all_bausteine(self):
        """Test retrieving all Bausteine."""
        from v_flask_plugins.datenschutz.bausteine import get_all_bausteine

        bausteine = get_all_bausteine()
        assert len(bausteine) > 10  # Should have many Bausteine

    def test_get_baustein_by_id(self):
        """Test retrieving specific Baustein."""
        from v_flask_plugins.datenschutz.bausteine import get_baustein_by_id

        baustein = get_baustein_by_id('server_logs')
        assert baustein is not None
        assert baustein.name == 'Server-Logfiles'
        assert not baustein.optional  # Server logs are mandatory

    def test_get_pflicht_bausteine(self):
        """Test retrieving mandatory Bausteine."""
        from v_flask_plugins.datenschutz.bausteine import get_pflicht_bausteine

        pflicht = get_pflicht_bausteine()
        assert len(pflicht) >= 4  # At least server_logs, ssl, cookies, betroffenenrechte
        assert all(not b.optional for b in pflicht)

    def test_bausteine_have_text_templates(self):
        """Test all Bausteine have text templates."""
        from v_flask_plugins.datenschutz.bausteine import get_all_bausteine

        for baustein in get_all_bausteine():
            assert baustein.text_template
            assert len(baustein.text_template) > 50

    def test_kategorien_defined(self):
        """Test categories are defined."""
        from v_flask_plugins.datenschutz.bausteine import KATEGORIEN

        assert 'basis' in KATEGORIEN
        assert 'analytics' in KATEGORIEN
        assert 'social' in KATEGORIEN


# =============================================================================
# Generator Tests
# =============================================================================


class TestDatenschutzGenerator:
    """Tests for the privacy policy generator."""

    def test_generate_html(self, app, config):
        """Test HTML generation."""
        from v_flask_plugins.datenschutz.generator import DatenschutzGenerator

        with app.app_context():
            generator = DatenschutzGenerator(config)
            html = generator.generate_html()

            assert '<h2>Datenschutzerklärung</h2>' in html
            assert 'Test GmbH' in html
            assert 'test@example.de' in html

    def test_generate_includes_mandatory_sections(self, app, config):
        """Test mandatory sections are always included."""
        from v_flask_plugins.datenschutz.generator import DatenschutzGenerator

        with app.app_context():
            generator = DatenschutzGenerator(config)
            html = generator.generate_html()

            assert 'Verantwortlicher' in html
            assert 'Ihre Rechte als betroffene Person' in html  # From mandatory Baustein

    def test_generate_text(self, app, config):
        """Test plain text generation."""
        from v_flask_plugins.datenschutz.generator import DatenschutzGenerator

        with app.app_context():
            generator = DatenschutzGenerator(config)
            text = generator.generate_text()

            assert 'Test GmbH' in text
            assert '<' not in text or '>' not in text  # No HTML tags


# =============================================================================
# Validator Tests
# =============================================================================


class TestDatenschutzValidator:
    """Tests for the configuration validator."""

    def test_validate_complete_config(self, app, config):
        """Test validation of complete configuration."""
        from v_flask_plugins.datenschutz.validators import DatenschutzValidator

        with app.app_context():
            validator = DatenschutzValidator(config)
            result = validator.validate()

            assert result.is_valid

    def test_validate_missing_name(self, app):
        """Test validation catches missing name."""
        from v_flask_plugins.datenschutz.models import DatenschutzConfig
        from v_flask_plugins.datenschutz.validators import DatenschutzValidator

        with app.app_context():
            config = DatenschutzConfig(
                verantwortlicher_email='test@example.de',
            )
            validator = DatenschutzValidator(config)
            result = validator.validate()

            assert not result.is_valid
            assert any('Name' in e for e in result.errors)

    def test_validate_invalid_email(self, app):
        """Test validation catches invalid email."""
        from v_flask_plugins.datenschutz.models import DatenschutzConfig
        from v_flask_plugins.datenschutz.validators import DatenschutzValidator

        with app.app_context():
            config = DatenschutzConfig(
                verantwortlicher_name='Test',
                verantwortlicher_email='invalid-email',
            )
            validator = DatenschutzValidator(config)
            result = validator.validate()

            assert not result.is_valid
            assert any('ungültig' in e for e in result.errors)

    def test_validate_dsb_fields(self, app):
        """Test DSB fields required when enabled."""
        from v_flask_plugins.datenschutz.models import DatenschutzConfig
        from v_flask_plugins.datenschutz.validators import DatenschutzValidator

        with app.app_context():
            config = DatenschutzConfig(
                verantwortlicher_name='Test',
                verantwortlicher_email='test@test.de',
                dsb_vorhanden=True,
            )
            validator = DatenschutzValidator(config)
            result = validator.validate()

            assert not result.is_valid
            assert any('Datenschutzbeauftragten' in e for e in result.errors)

    def test_completeness_score(self, app, config):
        """Test completeness score calculation."""
        from v_flask_plugins.datenschutz.validators import DatenschutzValidator

        with app.app_context():
            validator = DatenschutzValidator(config)
            score = validator.get_completeness_score()

            assert 0 <= score <= 100
            assert score > 40  # Config has required fields but not all optional


# =============================================================================
# Route Tests (Unit tests without full Flask-Login setup)
# =============================================================================


class TestRouteBlueprints:
    """Tests for route blueprints registration."""

    def test_blueprints_registered(self, app):
        """Test blueprints are registered."""
        with app.app_context():
            assert 'datenschutz' in app.blueprints
            assert 'datenschutz_admin' in app.blueprints

    def test_public_route_exists(self, app):
        """Test public route is registered."""
        with app.app_context():
            rules = [r.rule for r in app.url_map.iter_rules()]
            assert '/datenschutz/' in rules

    def test_admin_route_exists(self, app):
        """Test admin route is registered."""
        with app.app_context():
            rules = [r.rule for r in app.url_map.iter_rules()]
            assert '/admin/datenschutz/' in rules

    def test_save_route_exists(self, app):
        """Test save route is registered."""
        with app.app_context():
            rules = [r.rule for r in app.url_map.iter_rules()]
            assert '/admin/datenschutz/save' in rules
