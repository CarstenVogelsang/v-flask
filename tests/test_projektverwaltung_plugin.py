"""Tests for the Projektverwaltung plugin."""

import pytest
from flask import Flask
from flask_login import login_user

from v_flask import VFlask, db
from v_flask.models import User, Rolle, Permission
from v_flask_plugins.projektverwaltung.models import (
    Projekt, Komponente, Task, TaskKommentar, ChangelogEintrag, TaskStatus
)
from v_flask_plugins.projektverwaltung.services import PromptGenerator


def create_test_rolle(session):
    """Create a test role for user fixtures."""
    rolle = Rolle.query.filter_by(name='test_rolle').first()
    if not rolle:
        rolle = Rolle(name='test_rolle', beschreibung='Test Role')
        session.add(rolle)
        session.commit()
    return rolle


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def app_with_plugin():
    """Create a test Flask application with projektverwaltung plugin."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['LOGIN_DISABLED'] = True

    # Initialize V-Flask
    v_flask = VFlask(app)

    # Register plugin blueprints
    from v_flask_plugins.projektverwaltung.routes import admin_bp, api_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

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
    """Create a test user with required role."""
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
def projekt(app_with_plugin):
    """Create a test project."""
    with app_with_plugin.app_context():
        p = Projekt(
            name='Test Projekt',
            beschreibung='Ein Testprojekt',
            typ='intern',
            aktiv=True
        )
        db.session.add(p)
        db.session.commit()
        yield p


@pytest.fixture
def komponente(app_with_plugin, projekt):
    """Create a test component."""
    with app_with_plugin.app_context():
        # Refresh projekt in session
        projekt = Projekt.query.get(projekt.id)
        k = Komponente(
            projekt_id=projekt.id,
            name='Test Modul',
            prd_nummer='001',
            typ='modul',
            aktuelle_phase='mvp',
            prd_inhalt='# PRD-001 Test Modul\n\n## Übersicht\nTestbeschreibung\n\n## Features\n- Feature 1'
        )
        db.session.add(k)
        db.session.commit()
        yield k


@pytest.fixture
def task(app_with_plugin, komponente):
    """Create a test task."""
    with app_with_plugin.app_context():
        # Refresh komponente in session
        komponente = Komponente.query.get(komponente.id)
        t = Task(
            komponente_id=komponente.id,
            titel='Test Task',
            beschreibung='Eine Testaufgabe',
            status='backlog',
            prioritaet='mittel',
            typ='feature',
            phase='mvp'
        )
        db.session.add(t)
        db.session.commit()
        yield t


# =============================================================================
# MODEL TESTS
# =============================================================================

class TestProjektModel:
    """Tests for Projekt model."""

    def test_create_projekt(self, app_with_plugin):
        """Test creating a new project."""
        with app_with_plugin.app_context():
            p = Projekt(name='Neues Projekt', typ='intern')
            db.session.add(p)
            db.session.commit()

            assert p.id is not None
            assert p.name == 'Neues Projekt'
            assert p.typ == 'intern'
            assert p.aktiv is True

    def test_projekt_ist_kundenprojekt(self, app_with_plugin):
        """Test is_kundenprojekt property."""
        with app_with_plugin.app_context():
            p_intern = Projekt(name='Intern', typ='intern')
            p_kunde = Projekt(name='Kunde', typ='kunde', kunde_id=1)
            db.session.add_all([p_intern, p_kunde])
            db.session.commit()

            assert p_intern.ist_kundenprojekt is False
            assert p_kunde.ist_kundenprojekt is True

    def test_projekt_to_dict(self, app_with_plugin, projekt):
        """Test project serialization."""
        with app_with_plugin.app_context():
            p = Projekt.query.get(projekt.id)
            result = p.to_dict()
            assert 'id' in result
            assert 'name' in result
            assert result['name'] == 'Test Projekt'


class TestKomponenteModel:
    """Tests for Komponente model."""

    def test_komponente_prd_bezeichnung(self, app_with_plugin, komponente):
        """Test PRD designation property."""
        with app_with_plugin.app_context():
            k = Komponente.query.get(komponente.id)
            assert k.prd_bezeichnung == 'PRD-001'

    def test_komponente_without_prd_nummer(self, app_with_plugin, projekt):
        """Test component without PRD number."""
        with app_with_plugin.app_context():
            projekt = Projekt.query.get(projekt.id)
            k = Komponente(
                projekt_id=projekt.id,
                name='Ohne PRD',
                typ='basisfunktion'
            )
            db.session.add(k)
            db.session.commit()

            # prd_bezeichnung returns None when no prd_nummer is set
            assert k.prd_bezeichnung is None
            assert k.name == 'Ohne PRD'


class TestTaskModel:
    """Tests for Task model."""

    def test_task_nummer(self, app_with_plugin, task):
        """Test task number generation."""
        with app_with_plugin.app_context():
            t = Task.query.get(task.id)
            # Task nummer format: PRD{prd_nummer}-T{task_id:03d}
            assert t.task_nummer.startswith('PRD001-T')

    def test_task_status_enum(self, app_with_plugin, task):
        """Test task status values."""
        with app_with_plugin.app_context():
            t = Task.query.get(task.id)

            for status in TaskStatus:
                t.status = status.value
                db.session.commit()
                assert t.status == status.value

    def test_task_erledigen(self, app_with_plugin, task):
        """Test marking task as completed."""
        with app_with_plugin.app_context():
            t = Task.query.get(task.id)
            t.erledigen()
            db.session.commit()

            assert t.status == 'erledigt'
            assert t.erledigt_am is not None
            assert t.ist_erledigt is True

    def test_task_entstanden_aus(self, app_with_plugin, komponente):
        """Test task splitting relationship."""
        with app_with_plugin.app_context():
            komponente = Komponente.query.get(komponente.id)

            # Create parent task
            parent = Task(
                komponente_id=komponente.id,
                titel='Parent Task',
                status='in_arbeit',
                typ='feature'
            )
            db.session.add(parent)
            db.session.commit()

            # Create child task
            child = Task(
                komponente_id=komponente.id,
                titel='Child Task',
                status='backlog',
                typ='feature',
                entstanden_aus_id=parent.id
            )
            db.session.add(child)
            db.session.commit()

            assert child.entstanden_aus_id == parent.id
            assert child.entstanden_aus_nummer == parent.task_nummer


class TestTaskKommentarModel:
    """Tests for TaskKommentar model."""

    def test_create_kommentar(self, app_with_plugin, task, test_user):
        """Test creating a task comment."""
        with app_with_plugin.app_context():
            task = Task.query.get(task.id)
            user = User.query.get(test_user.id)

            k = TaskKommentar(
                task_id=task.id,
                user_id=user.id,
                typ='review',
                inhalt='Test Kommentar'
            )
            db.session.add(k)
            db.session.commit()

            assert k.id is not None
            assert k.erledigt is False

    def test_kommentar_toggle_erledigt(self, app_with_plugin, task, test_user):
        """Test toggling comment completion status."""
        with app_with_plugin.app_context():
            task = Task.query.get(task.id)
            user = User.query.get(test_user.id)

            k = TaskKommentar(
                task_id=task.id,
                user_id=user.id,
                typ='review',
                inhalt='Test'
            )
            db.session.add(k)
            db.session.commit()

            # Toggle to completed
            k.erledigt = True
            db.session.commit()
            assert k.erledigt is True


class TestChangelogEintragModel:
    """Tests for ChangelogEintrag model."""

    def test_create_changelog_from_task(self, app_with_plugin, task):
        """Test creating changelog entry from task."""
        with app_with_plugin.app_context():
            task = Task.query.get(task.id)

            entry = ChangelogEintrag.create_from_task(task, kategorie='added')
            db.session.add(entry)
            db.session.commit()

            assert entry.id is not None
            assert entry.task_id == task.id
            assert entry.kategorie == 'added'
            assert entry.version == task.phase.upper()

    def test_changelog_to_markdown(self, app_with_plugin, komponente):
        """Test changelog markdown generation."""
        with app_with_plugin.app_context():
            komponente = Komponente.query.get(komponente.id)

            entry = ChangelogEintrag(
                komponente_id=komponente.id,
                version='MVP',
                kategorie='added',
                beschreibung='New feature added'
            )
            db.session.add(entry)
            db.session.commit()

            md = entry.to_markdown()
            assert 'New feature added' in md


# =============================================================================
# PROMPT GENERATOR TESTS
# =============================================================================

class TestPromptGenerator:
    """Tests for PromptGenerator service."""

    def test_generate_task_prompt(self, app_with_plugin, task):
        """Test task prompt generation."""
        with app_with_plugin.app_context():
            task = Task.query.get(task.id)
            prompt = PromptGenerator.generate_task_prompt(task)

            assert task.task_nummer in prompt
            assert task.titel in prompt
            assert 'Übersicht' in prompt
            assert 'feature' in prompt.lower()

    def test_generate_task_prompt_without_prd(self, app_with_plugin, task):
        """Test task prompt generation without PRD excerpt."""
        with app_with_plugin.app_context():
            task = Task.query.get(task.id)
            prompt = PromptGenerator.generate_task_prompt(task, include_prd=False)

            assert task.task_nummer in prompt
            assert 'PRD-Kontext' not in prompt

    def test_generate_review_prompt(self, app_with_plugin, task, test_user):
        """Test review prompt generation."""
        with app_with_plugin.app_context():
            task = Task.query.get(task.id)
            user = User.query.get(test_user.id)

            # Add review comment
            k = TaskKommentar(
                task_id=task.id,
                user_id=user.id,
                typ='review',
                inhalt='Bitte Icon anpassen'
            )
            db.session.add(k)
            db.session.commit()

            # Refresh task
            task = Task.query.get(task.id)
            prompt = PromptGenerator.generate_review_prompt(task)

            assert 'Review' in prompt
            assert 'Bitte Icon anpassen' in prompt

    def test_generate_review_prompt_no_comments(self, app_with_plugin, task):
        """Test review prompt with no comments."""
        with app_with_plugin.app_context():
            task = Task.query.get(task.id)
            prompt = PromptGenerator.generate_review_prompt(task)

            assert 'Keine offenen Review-Kommentare' in prompt


# =============================================================================
# API TESTS
# =============================================================================

class TestProjekteAPI:
    """Tests for project API endpoints."""

    def test_list_projekte(self, client, projekt):
        """Test listing all projects."""
        response = client.get('/api/projekte')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_projekt(self, client, projekt):
        """Test getting a single project."""
        response = client.get(f'/api/projekte/{projekt.id}')
        assert response.status_code == 200

        data = response.get_json()
        assert data['name'] == 'Test Projekt'


class TestKomponentenAPI:
    """Tests for component API endpoints."""

    def test_list_komponenten(self, client, komponente):
        """Test listing all components."""
        response = client.get('/api/komponenten')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)

    def test_get_komponente(self, client, komponente):
        """Test getting a single component."""
        response = client.get(f'/api/komponenten/{komponente.id}')
        assert response.status_code == 200

        data = response.get_json()
        assert data['name'] == 'Test Modul'

    def test_get_komponente_prd(self, client, komponente):
        """Test getting PRD as markdown."""
        response = client.get(f'/api/komponenten/{komponente.id}/prd')
        assert response.status_code == 200
        assert response.content_type == 'text/markdown; charset=utf-8'
        assert b'PRD-001' in response.data


class TestTasksAPI:
    """Tests for task API endpoints."""

    def test_get_task(self, client, task):
        """Test getting a single task."""
        response = client.get(f'/api/tasks/{task.id}')
        assert response.status_code == 200

        data = response.get_json()
        assert data['titel'] == 'Test Task'

    def test_get_task_by_nummer(self, client, task):
        """Test getting task by number."""
        # Get the task to find its nummer
        response = client.get(f'/api/tasks/{task.id}')
        task_nummer = response.get_json()['task_nummer']

        response = client.get(f'/api/tasks/by-nummer/{task_nummer}')
        assert response.status_code == 200

    def test_update_task(self, client, task):
        """Test updating a task."""
        response = client.patch(
            f'/api/tasks/{task.id}',
            json={'status': 'in_arbeit'}
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['task']['status'] == 'in_arbeit'

    def test_task_erledigen_endpoint(self, client, task):
        """Test completing a task via API."""
        response = client.post(
            f'/api/tasks/{task.id}/erledigen',
            json={'create_changelog': False}  # Skip changelog to simplify test
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['task']['status'] == 'erledigt'

    def test_task_prompt_endpoint(self, client, task):
        """Test generating task prompt via API."""
        response = client.get(f'/api/tasks/{task.id}/prompt')
        assert response.status_code == 200

        data = response.get_json()
        assert 'prompt' in data
        assert 'task_nummer' in data
        assert 'Test Task' in data['prompt'] or task.titel in data['prompt']


class TestKommentareAPI:
    """Tests for comment API endpoints."""

    def test_list_task_kommentare(self, client, task):
        """Test listing task comments."""
        response = client.get(f'/api/tasks/{task.id}/kommentare')
        assert response.status_code == 200

        data = response.get_json()
        assert 'kommentare' in data
        assert 'anzahl' in data


class TestAPIIndex:
    """Tests for API index endpoint."""

    def test_api_index(self, client):
        """Test API documentation endpoint."""
        response = client.get('/api/')
        assert response.status_code == 200

        data = response.get_json()
        assert data['name'] == 'Projektverwaltung API'
        assert 'endpoints' in data
