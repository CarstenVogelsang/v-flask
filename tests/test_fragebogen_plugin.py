"""Tests for the Fragebogen plugin."""

import pytest
import secrets
from datetime import datetime, timedelta
from flask import Flask
from flask_login import login_user

from v_flask import VFlask, db
from v_flask.models import User, Rolle
from v_flask_plugins.fragebogen.models import (
    Fragebogen, FragebogenTeilnahme, FragebogenAntwort,
    FragebogenStatus, TeilnahmeStatus
)
from v_flask_plugins.fragebogen.services import (
    FragebogenService, ValidationResult, get_fragebogen_service
)


def create_test_rolle(session):
    """Create a test role for user fixtures."""
    rolle = Rolle.query.filter_by(name='test_rolle').first()
    if not rolle:
        rolle = Rolle(name='test_rolle', beschreibung='Test Role')
        session.add(rolle)
        session.commit()
    return rolle


# =============================================================================
# SAMPLE DATA
# =============================================================================

VALID_V2_SCHEMA = {
    "version": 2,  # Integer, not string!
    "seiten": [
        {
            "id": "seite1",
            "titel": "Grunddaten",
            "fragen": [
                {
                    "id": "name",
                    "typ": "text",
                    "frage": "Ihr Name",
                    "pflicht": True
                },
                {
                    "id": "zufriedenheit",
                    "typ": "skala",
                    "frage": "Wie zufrieden sind Sie?",
                    "min": 1,
                    "max": 5,
                    "pflicht": True
                }
            ]
        },
        {
            "id": "seite2",
            "titel": "Details",
            "fragen": [
                {
                    "id": "feedback",
                    "typ": "text",
                    "frage": "Ihr Feedback",
                    "multiline": True,
                    "pflicht": False
                },
                {
                    "id": "empfehlung",
                    "typ": "ja_nein",
                    "frage": "Würden Sie uns weiterempfehlen?",
                    "pflicht": True
                }
            ]
        }
    ]
}

INVALID_SCHEMA_NO_VERSION = {
    "seiten": [{"id": "s1", "titel": "Test", "fragen": []}]
}

INVALID_SCHEMA_EMPTY_PAGES = {
    "version": 2,
    "seiten": []
}


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def app_with_plugin():
    """Create a test Flask application with fragebogen plugin."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['LOGIN_DISABLED'] = True

    # Initialize V-Flask
    v_flask = VFlask(app)

    # Register plugin blueprints with URL prefixes
    from v_flask_plugins.fragebogen.routes import admin_bp, public_bp
    app.register_blueprint(admin_bp, url_prefix='/admin/fragebogen')
    app.register_blueprint(public_bp, url_prefix='/fragebogen')

    # Dummy admin dashboard route
    @app.route('/admin/')
    def admin_dashboard():
        return 'Admin Dashboard'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app_with_plugin):
    """Create a test client."""
    return app_with_plugin.test_client()


@pytest.fixture
def test_user(app_with_plugin):
    """Create a test user."""
    with app_with_plugin.app_context():
        rolle = create_test_rolle(db.session)
        user = User(
            email='test@example.com',
            vorname='Test',
            nachname='User',
            rolle_id=rolle.id,
            aktiv=True
        )
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        yield user


@pytest.fixture
def fragebogen_service(app_with_plugin):
    """Create a FragebogenService instance."""
    with app_with_plugin.app_context():
        yield FragebogenService()


@pytest.fixture
def fragebogen(app_with_plugin, test_user):
    """Create a test questionnaire."""
    with app_with_plugin.app_context():
        user = User.query.get(test_user.id)
        fb = Fragebogen(
            titel='Test Fragebogen',
            beschreibung='Ein Testfragebogen',
            definition_json=VALID_V2_SCHEMA,
            status=FragebogenStatus.ENTWURF.value,
            erstellt_von_id=user.id,
            erlaubt_anonym=True
        )
        db.session.add(fb)
        db.session.commit()
        yield fb


@pytest.fixture
def active_fragebogen(app_with_plugin, test_user):
    """Create an active questionnaire."""
    with app_with_plugin.app_context():
        user = User.query.get(test_user.id)
        fb = Fragebogen(
            titel='Aktiver Fragebogen',
            beschreibung='Ein aktiver Testfragebogen',
            definition_json=VALID_V2_SCHEMA,
            status=FragebogenStatus.AKTIV.value,
            erstellt_von_id=user.id,
            aktiviert_am=datetime.utcnow(),
            erlaubt_anonym=True
        )
        db.session.add(fb)
        db.session.commit()
        yield fb


@pytest.fixture
def teilnahme(app_with_plugin, active_fragebogen):
    """Create a test participation."""
    with app_with_plugin.app_context():
        fb = Fragebogen.query.get(active_fragebogen.id)
        t = FragebogenTeilnahme(
            fragebogen_id=fb.id,
            teilnehmer_id=42,
            teilnehmer_typ='kunde',
            token=secrets.token_urlsafe(48),
            status=TeilnahmeStatus.EINGELADEN.value
        )
        db.session.add(t)
        db.session.commit()
        yield t


# =============================================================================
# MODEL TESTS
# =============================================================================

class TestFragebogenModel:
    """Tests for Fragebogen model."""

    def test_create_fragebogen(self, app_with_plugin, test_user):
        """Test creating a new questionnaire."""
        with app_with_plugin.app_context():
            user = User.query.get(test_user.id)
            fb = Fragebogen(
                titel='Neuer Fragebogen',
                definition_json=VALID_V2_SCHEMA,
                erstellt_von_id=user.id
            )
            db.session.add(fb)
            db.session.commit()

            assert fb.id is not None
            assert fb.titel == 'Neuer Fragebogen'
            assert fb.status == FragebogenStatus.ENTWURF.value
            assert fb.version_nummer == 1
            assert fb.archiviert is False

    def test_fragebogen_seiten_property(self, app_with_plugin, fragebogen):
        """Test seiten property returns pages from schema."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            seiten = fb.seiten

            assert len(seiten) == 2
            assert seiten[0]['titel'] == 'Grunddaten'
            assert seiten[1]['titel'] == 'Details'

    def test_fragebogen_anzahl_seiten(self, app_with_plugin, fragebogen):
        """Test page count property."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            assert fb.anzahl_seiten == 2

    def test_fragebogen_fragen_property(self, app_with_plugin, fragebogen):
        """Test fragen returns all questions from all pages."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            fragen = fb.fragen

            assert len(fragen) == 4
            frage_ids = [f['id'] for f in fragen]
            assert 'name' in frage_ids
            assert 'zufriedenheit' in frage_ids
            assert 'feedback' in frage_ids
            assert 'empfehlung' in frage_ids

    def test_fragebogen_anzahl_fragen(self, app_with_plugin, fragebogen):
        """Test question count property."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            assert fb.anzahl_fragen == 4

    def test_fragebogen_status_transitions(self, app_with_plugin, fragebogen):
        """Test status change methods."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(fragebogen.id)

            # Draft -> Active
            assert fb.is_entwurf is True
            fb.aktivieren()
            db.session.commit()
            assert fb.status == FragebogenStatus.AKTIV.value
            assert fb.aktiviert_am is not None
            assert fb.is_aktiv is True

            # Active -> Closed
            fb.schliessen()
            db.session.commit()
            assert fb.status == FragebogenStatus.GESCHLOSSEN.value
            assert fb.geschlossen_am is not None
            assert fb.is_geschlossen is True

    def test_fragebogen_to_dict(self, app_with_plugin, fragebogen):
        """Test serialization."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            data = fb.to_dict()

            assert 'id' in data
            assert 'titel' in data
            assert 'status' in data
            assert data['titel'] == 'Test Fragebogen'

    def test_fragebogen_is_v2(self, app_with_plugin, fragebogen):
        """Test V2 schema detection."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            assert fb.is_v2 is True


class TestFragebogenTeilnahmeModel:
    """Tests for FragebogenTeilnahme model."""

    def test_create_teilnahme(self, app_with_plugin, active_fragebogen):
        """Test creating a participation."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(active_fragebogen.id)
            t = FragebogenTeilnahme.create_for_teilnehmer(
                fragebogen_id=fb.id,
                teilnehmer_id=123,
                teilnehmer_typ='user'
            )
            db.session.add(t)
            db.session.commit()

            assert t.id is not None
            assert t.token is not None
            assert len(t.token) == 64  # URL-safe token length
            assert t.status == TeilnahmeStatus.EINGELADEN.value

    def test_teilnahme_token_unique(self, app_with_plugin, active_fragebogen):
        """Test that tokens are unique."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(active_fragebogen.id)

            t1 = FragebogenTeilnahme.create_for_teilnehmer(
                fragebogen_id=fb.id,
                teilnehmer_id=1,
                teilnehmer_typ='user'
            )
            t2 = FragebogenTeilnahme.create_for_teilnehmer(
                fragebogen_id=fb.id,
                teilnehmer_id=2,
                teilnehmer_typ='user'
            )
            db.session.add_all([t1, t2])
            db.session.commit()

            assert t1.token != t2.token

    def test_teilnahme_starten(self, app_with_plugin, teilnahme):
        """Test starting participation."""
        with app_with_plugin.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            t.starten()
            db.session.commit()

            assert t.status == TeilnahmeStatus.GESTARTET.value
            assert t.gestartet_am is not None

    def test_teilnahme_abschliessen(self, app_with_plugin, teilnahme):
        """Test completing participation."""
        with app_with_plugin.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            t.starten()
            t.abschliessen()
            db.session.commit()

            assert t.status == TeilnahmeStatus.ABGESCHLOSSEN.value
            assert t.abgeschlossen_am is not None

    def test_teilnahme_get_by_token(self, app_with_plugin, teilnahme):
        """Test finding participation by token."""
        with app_with_plugin.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            token = t.token

            found = FragebogenTeilnahme.get_by_token(token)
            assert found is not None
            assert found.id == t.id

    def test_teilnahme_anonymous(self, app_with_plugin, active_fragebogen):
        """Test anonymous participation with contact data."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(active_fragebogen.id)
            t = FragebogenTeilnahme.create_anonymous(fb.id)
            t.kontakt_name = 'Max Mustermann'
            t.kontakt_email = 'max@example.com'
            t.kontakt_zusatz = {'firma': 'Test GmbH'}
            db.session.add(t)
            db.session.commit()

            assert t.teilnehmer_id is None
            assert t.is_anonym is True
            assert t.kontakt_name == 'Max Mustermann'
            assert t.kontakt_email == 'max@example.com'

    def test_teilnahme_display_name(self, app_with_plugin, active_fragebogen):
        """Test display_name property."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(active_fragebogen.id)

            # Anonymous without contact
            t1 = FragebogenTeilnahme.create_anonymous(fb.id)
            db.session.add(t1)
            db.session.commit()
            assert t1.display_name == 'Anonym'

            # Anonymous with name
            t2 = FragebogenTeilnahme.create_anonymous(fb.id)
            t2.kontakt_name = 'Max'
            db.session.add(t2)
            db.session.commit()
            assert t2.display_name == 'Max'


class TestFragebogenAntwortModel:
    """Tests for FragebogenAntwort model."""

    def test_create_antwort(self, app_with_plugin, teilnahme):
        """Test creating an answer."""
        with app_with_plugin.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            a = FragebogenAntwort(
                teilnahme_id=t.id,
                frage_id='zufriedenheit',
                antwort_json={'value': 4}
            )
            db.session.add(a)
            db.session.commit()

            assert a.id is not None
            assert a.antwort_json['value'] == 4
            assert a.value == 4

    def test_antwort_update(self, app_with_plugin, teilnahme):
        """Test updating an answer."""
        with app_with_plugin.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            a = FragebogenAntwort(
                teilnahme_id=t.id,
                frage_id='name',
                antwort_json={'value': 'Original'}
            )
            db.session.add(a)
            db.session.commit()

            # Update
            a.antwort_json = {'value': 'Updated'}
            db.session.commit()

            # Verify
            db.session.refresh(a)
            assert a.antwort_json['value'] == 'Updated'
            assert a.value == 'Updated'

    def test_antwort_multiple_choice(self, app_with_plugin, teilnahme):
        """Test multiple choice answer structure."""
        with app_with_plugin.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            a = FragebogenAntwort(
                teilnahme_id=t.id,
                frage_id='multi_q',
                antwort_json={'values': ['Option A', 'Option C']}
            )
            db.session.add(a)
            db.session.commit()

            assert a.value == ['Option A', 'Option C']


# =============================================================================
# SERVICE TESTS
# =============================================================================

class TestFragebogenServiceValidation:
    """Tests for FragebogenService validation."""

    def test_validate_valid_schema(self, fragebogen_service):
        """Test validation of valid schema."""
        result = fragebogen_service.validate_definition(VALID_V2_SCHEMA)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_missing_version(self, fragebogen_service):
        """Test validation rejects wrong version."""
        schema_no_version = {
            "version": 1,  # Wrong version
            "seiten": [{"id": "s1", "titel": "Test", "fragen": []}]
        }
        result = fragebogen_service.validate_definition(schema_no_version)
        assert result.valid is False
        assert any('V2' in e for e in result.errors)

    def test_validate_empty_pages(self, fragebogen_service):
        """Test validation rejects empty pages."""
        result = fragebogen_service.validate_definition(INVALID_SCHEMA_EMPTY_PAGES)
        assert result.valid is False
        assert any('seite' in e.lower() for e in result.errors)

    def test_validate_duplicate_frage_ids(self, fragebogen_service):
        """Test validation detects duplicate question IDs."""
        schema = {
            "version": 2,
            "seiten": [
                {
                    "id": "s1",
                    "titel": "Page 1",
                    "fragen": [
                        {"id": "q1", "typ": "text", "frage": "First"},
                        {"id": "q1", "typ": "text", "frage": "Duplicate"}
                    ]
                }
            ]
        }
        result = fragebogen_service.validate_definition(schema)
        assert result.valid is False
        assert any('doppelt' in e.lower() or 'q1' in e for e in result.errors)

    def test_validate_missing_optionen(self, fragebogen_service):
        """Test validation requires optionen for choice types."""
        schema = {
            "version": 2,
            "seiten": [
                {
                    "id": "s1",
                    "titel": "Page 1",
                    "fragen": [
                        {"id": "q1", "typ": "single_choice", "frage": "Choose one"}
                    ]
                }
            ]
        }
        result = fragebogen_service.validate_definition(schema)
        assert result.valid is False
        assert any('optionen' in e.lower() for e in result.errors)


class TestFragebogenServiceCRUD:
    """Tests for FragebogenService CRUD operations."""

    def test_create_fragebogen(self, app_with_plugin, fragebogen_service, test_user):
        """Test creating a questionnaire via service."""
        with app_with_plugin.app_context():
            user = User.query.get(test_user.id)
            fb = fragebogen_service.create_fragebogen(
                titel='Service Created',
                beschreibung='Created via service',
                definition=VALID_V2_SCHEMA,
                erstellt_von_id=user.id
            )

            assert fb.id is not None
            assert fb.titel == 'Service Created'
            assert fb.erstellt_von_id == user.id
            assert fb.status == FragebogenStatus.ENTWURF.value

    def test_update_fragebogen(self, app_with_plugin, fragebogen_service, fragebogen):
        """Test updating a questionnaire."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            updated = fragebogen_service.update_fragebogen(
                fragebogen=fb,
                titel='Updated Title'
            )

            assert updated.titel == 'Updated Title'

    def test_update_active_fragebogen_fails(self, app_with_plugin, fragebogen_service, active_fragebogen):
        """Test that active questionnaire cannot be updated."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(active_fragebogen.id)

            with pytest.raises(ValueError, match='Entwurf'):
                fragebogen_service.update_fragebogen(fragebogen=fb, titel='New')

    def test_duplicate_fragebogen(self, app_with_plugin, fragebogen_service, fragebogen, test_user):
        """Test creating a new version."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            user = User.query.get(test_user.id)

            new_fb = fragebogen_service.duplicate_fragebogen(
                fragebogen=fb,
                user_id=user.id,
                new_titel='Version 2'
            )

            assert new_fb.id != fb.id
            assert new_fb.version_nummer == 2
            assert new_fb.vorgaenger_id == fb.id
            assert new_fb.status == FragebogenStatus.ENTWURF.value


class TestFragebogenServiceTeilnahme:
    """Tests for FragebogenService participation management."""

    def test_create_anonymous_teilnahme(self, app_with_plugin, fragebogen_service, active_fragebogen):
        """Test creating anonymous participation."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(active_fragebogen.id)
            teilnahme = fragebogen_service.create_anonymous_teilnahme(fb)

            assert teilnahme.id is not None
            assert teilnahme.is_anonym is True
            assert teilnahme.token is not None

    def test_get_teilnahme_by_token(self, app_with_plugin, fragebogen_service, teilnahme):
        """Test finding participation by token."""
        with app_with_plugin.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            found = fragebogen_service.get_teilnahme_by_token(t.token)

            assert found is not None
            assert found.id == t.id

    def test_save_antwort(self, app_with_plugin, fragebogen_service, teilnahme):
        """Test saving an answer."""
        with app_with_plugin.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            antwort = fragebogen_service.save_antwort(
                teilnahme=t,
                frage_id='name',
                antwort_json={'value': 'Test Name'}
            )

            assert antwort.id is not None
            assert antwort.antwort_json['value'] == 'Test Name'

    def test_save_antwort_updates_existing(self, app_with_plugin, fragebogen_service, teilnahme):
        """Test saving overwrites existing answer."""
        with app_with_plugin.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)

            # First save
            fragebogen_service.save_antwort(t, 'name', {'value': 'First'})

            # Second save (update)
            fragebogen_service.save_antwort(t, 'name', {'value': 'Second'})

            # Only one answer should exist
            antworten = FragebogenAntwort.query.filter_by(
                teilnahme_id=t.id,
                frage_id='name'
            ).all()
            assert len(antworten) == 1
            assert antworten[0].antwort_json['value'] == 'Second'

    def test_save_kontakt_daten(self, app_with_plugin, fragebogen_service, active_fragebogen):
        """Test saving contact data for anonymous participation."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(active_fragebogen.id)
            t = fragebogen_service.create_anonymous_teilnahme(fb)

            fragebogen_service.save_kontakt_daten(
                teilnahme=t,
                email='test@example.com',
                name='Test User',
                zusatz={'firma': 'Test GmbH'}
            )

            assert t.kontakt_email == 'test@example.com'
            assert t.kontakt_name == 'Test User'
            assert t.kontakt_zusatz['firma'] == 'Test GmbH'


class TestFragebogenServiceStatistics:
    """Tests for FragebogenService statistics."""

    def test_get_auswertung(self, app_with_plugin, fragebogen_service, active_fragebogen, teilnahme):
        """Test getting questionnaire statistics."""
        with app_with_plugin.app_context():
            fb = Fragebogen.query.get(active_fragebogen.id)
            t = FragebogenTeilnahme.query.get(teilnahme.id)

            # Add some answers and complete
            t.starten()
            fragebogen_service.save_antwort(t, 'name', {'value': 'Test'})
            fragebogen_service.save_antwort(t, 'zufriedenheit', {'value': 4})
            fragebogen_service.save_antwort(t, 'empfehlung', {'value': True})
            t.abschliessen()
            db.session.commit()

            stats = fragebogen_service.get_auswertung(fb)

            assert 'fragebogen_id' in stats
            assert 'teilnehmer_gesamt' in stats
            assert 'teilnehmer_abgeschlossen' in stats
            assert 'fragen' in stats
            assert stats['teilnehmer_abgeschlossen'] >= 1


# =============================================================================
# PUBLIC ROUTE TESTS
# =============================================================================

class TestPublicRoutes:
    """Tests for public questionnaire routes."""

    def test_wizard_valid_token(self, client, teilnahme, active_fragebogen):
        """Test wizard page with valid token."""
        with client.application.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            token = t.token

        response = client.get(f'/fragebogen/t/{token}')
        assert response.status_code == 200
        assert b'Aktiver Fragebogen' in response.data

    def test_wizard_invalid_token(self, client):
        """Test wizard page with invalid token returns 404."""
        response = client.get('/fragebogen/t/invalid-token-12345-does-not-exist')
        # Invalid token renders invalid.html with 404 status
        assert response.status_code == 404

    def test_wizard_starts_teilnahme(self, client, teilnahme, active_fragebogen):
        """Test that accessing wizard starts the participation."""
        with client.application.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            token = t.token
            assert t.status == TeilnahmeStatus.EINGELADEN.value

        response = client.get(f'/fragebogen/t/{token}')
        assert response.status_code == 200

        with client.application.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            assert t.status == TeilnahmeStatus.GESTARTET.value

    def test_save_antwort_endpoint(self, client, teilnahme):
        """Test auto-save endpoint."""
        with client.application.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            token = t.token

        response = client.post(
            f'/fragebogen/t/{token}/antwort',
            json={'frage_id': 'name', 'antwort': {'value': 'Test'}},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_danke_page(self, client, teilnahme):
        """Test thank you page."""
        with client.application.app_context():
            t = FragebogenTeilnahme.query.get(teilnahme.id)
            t.starten()
            t.abschliessen()
            db.session.commit()
            token = t.token

        response = client.get(f'/fragebogen/t/{token}/danke')
        assert response.status_code == 200
        assert b'Vielen Dank' in response.data


class TestAnonymousParticipation:
    """Tests for anonymous questionnaire participation."""

    def test_start_anonymous(self, client, active_fragebogen):
        """Test starting anonymous participation."""
        with client.application.app_context():
            fb = Fragebogen.query.get(active_fragebogen.id)
            fb_id = fb.id

        response = client.get(f'/fragebogen/anonym/{fb_id}')
        # Should redirect to wizard with new token
        assert response.status_code == 302


# =============================================================================
# ADMIN ROUTE TESTS
# =============================================================================
# Note: Admin routes require authentication and permission setup.
# These tests are skipped in the plugin test suite - admin routes should
# be tested via integration tests with full V-Flask app setup.

@pytest.mark.skip(reason="Requires full auth setup with auth.login route")
class TestAdminRoutes:
    """Tests for admin routes.

    Skipped because admin routes require:
    - Flask-Login setup with auth.login route
    - User with admin permissions
    - Full V-Flask app initialization

    These should be tested in integration tests.
    """

    def test_admin_index(self, client, fragebogen):
        """Test admin index page."""
        response = client.get('/admin/fragebogen/')
        assert response.status_code == 200

    def test_admin_detail(self, client, fragebogen):
        """Test admin detail page."""
        with client.application.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            fb_id = fb.id

        response = client.get(f'/admin/fragebogen/{fb_id}')
        assert response.status_code == 200

    def test_admin_new(self, client):
        """Test new questionnaire page."""
        response = client.get('/admin/fragebogen/neu')
        assert response.status_code == 200

    def test_admin_teilnehmer(self, client, fragebogen):
        """Test participant management page."""
        with client.application.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            fb_id = fb.id

        response = client.get(f'/admin/fragebogen/{fb_id}/teilnehmer')
        assert response.status_code == 200

    def test_admin_change_status(self, client, fragebogen):
        """Test status change endpoint."""
        with client.application.app_context():
            fb = Fragebogen.query.get(fragebogen.id)
            fb_id = fb.id

        response = client.post(
            f'/admin/fragebogen/{fb_id}/status',
            data={'action': 'aktivieren'}
        )
        # Should redirect after status change
        assert response.status_code in [200, 302]
