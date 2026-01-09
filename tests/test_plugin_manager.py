"""Tests for plugin manager models and services."""

from datetime import datetime, timedelta, UTC

import pytest
from flask import Flask

from v_flask import VFlask, db
from v_flask.models import PluginActivation, SystemStatus, User, Rolle


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'

    v_flask = VFlask()
    v_flask.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        rolle = Rolle(name='admin', beschreibung='Admin')
        db.session.add(rolle)
        db.session.commit()

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


class TestPluginActivation:
    """Tests for PluginActivation model."""

    def test_create_activation(self, app):
        """Test creating a plugin activation record."""
        with app.app_context():
            activation = PluginActivation(
                plugin_name='kontakt',
                is_active=True,
                activated_at=datetime.now(UTC)
            )
            db.session.add(activation)
            db.session.commit()

            assert activation.id is not None
            assert activation.plugin_name == 'kontakt'
            assert activation.is_active is True

    def test_get_by_name(self, app):
        """Test getting activation by plugin name."""
        with app.app_context():
            activation = PluginActivation(
                plugin_name='test-plugin',
                is_active=False
            )
            db.session.add(activation)
            db.session.commit()

            found = PluginActivation.get_by_name('test-plugin')
            assert found is not None
            assert found.plugin_name == 'test-plugin'

            not_found = PluginActivation.get_by_name('nonexistent')
            assert not_found is None

    def test_get_active_plugins(self, app):
        """Test getting list of active plugins."""
        with app.app_context():
            # Create some activations
            PluginActivation.activate('plugin-a')
            PluginActivation.activate('plugin-b')
            PluginActivation.activate('plugin-c')
            PluginActivation.deactivate('plugin-b')

            active = PluginActivation.get_active_plugins()

            assert 'plugin-a' in active
            assert 'plugin-b' not in active
            assert 'plugin-c' in active

    def test_activate_new_plugin(self, app, test_user):
        """Test activating a new plugin."""
        with app.app_context():
            activation = PluginActivation.activate('new-plugin', user_id=test_user)

            assert activation.plugin_name == 'new-plugin'
            assert activation.is_active is True
            assert activation.activated_at is not None
            assert activation.activated_by_id == test_user

    def test_activate_existing_plugin(self, app):
        """Test re-activating an existing plugin."""
        with app.app_context():
            # First activation
            PluginActivation.activate('kontakt')

            # Deactivate
            PluginActivation.deactivate('kontakt')

            # Re-activate
            activation = PluginActivation.activate('kontakt')

            assert activation.is_active is True
            assert activation.deactivated_at is None

    def test_deactivate_plugin(self, app):
        """Test deactivating a plugin."""
        with app.app_context():
            PluginActivation.activate('kontakt')
            activation = PluginActivation.deactivate('kontakt')

            assert activation.is_active is False
            assert activation.deactivated_at is not None

    def test_deactivate_nonexistent(self, app):
        """Test deactivating a non-existent plugin."""
        with app.app_context():
            result = PluginActivation.deactivate('nonexistent')
            assert result is None

    def test_to_dict(self, app):
        """Test dictionary representation."""
        with app.app_context():
            activation = PluginActivation.activate('kontakt')
            d = activation.to_dict()

            assert d['plugin_name'] == 'kontakt'
            assert d['is_active'] is True
            assert 'activated_at' in d
            assert 'deactivated_at' in d

    def test_repr(self, app):
        """Test string representation."""
        with app.app_context():
            activation = PluginActivation.activate('kontakt')
            repr_str = repr(activation)

            assert 'kontakt' in repr_str
            assert 'active' in repr_str

    def test_unique_plugin_name(self, app):
        """Test that plugin_name must be unique."""
        with app.app_context():
            PluginActivation.activate('unique-plugin')

            # Trying to create another with same name should fail
            duplicate = PluginActivation(
                plugin_name='unique-plugin',
                is_active=False
            )
            db.session.add(duplicate)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()


class TestSystemStatus:
    """Tests for SystemStatus model."""

    def test_set_and_get(self, app):
        """Test setting and getting a status."""
        with app.app_context():
            SystemStatus.set('test_key', 'test_value')

            value = SystemStatus.get('test_key')
            assert value == 'test_value'

    def test_get_default(self, app):
        """Test getting with default value."""
        with app.app_context():
            value = SystemStatus.get('nonexistent', default='default')
            assert value == 'default'

    def test_update_existing(self, app):
        """Test updating an existing status."""
        with app.app_context():
            SystemStatus.set('key', 'value1')
            SystemStatus.set('key', 'value2')

            value = SystemStatus.get('key')
            assert value == 'value2'

    def test_delete(self, app):
        """Test deleting a status."""
        with app.app_context():
            SystemStatus.set('to_delete', 'value')
            assert SystemStatus.get('to_delete') == 'value'

            deleted = SystemStatus.delete('to_delete')
            assert deleted is True
            assert SystemStatus.get('to_delete') is None

    def test_delete_nonexistent(self, app):
        """Test deleting a non-existent status."""
        with app.app_context():
            deleted = SystemStatus.delete('nonexistent')
            assert deleted is False

    def test_bool_operations(self, app):
        """Test boolean get/set operations."""
        with app.app_context():
            SystemStatus.set_bool('is_enabled', True)
            assert SystemStatus.get_bool('is_enabled') is True

            SystemStatus.set_bool('is_enabled', False)
            assert SystemStatus.get_bool('is_enabled') is False

    def test_get_bool_default(self, app):
        """Test get_bool with default value."""
        with app.app_context():
            assert SystemStatus.get_bool('nonexistent', default=True) is True
            assert SystemStatus.get_bool('nonexistent', default=False) is False

    def test_list_operations(self, app):
        """Test list get/add/remove operations."""
        with app.app_context():
            # Start with empty
            assert SystemStatus.get_list('plugins') == []

            # Add items
            SystemStatus.add_to_list('plugins', 'kontakt')
            SystemStatus.add_to_list('plugins', 'newsletter')

            plugins = SystemStatus.get_list('plugins')
            assert 'kontakt' in plugins
            assert 'newsletter' in plugins

            # Add duplicate (should not duplicate)
            SystemStatus.add_to_list('plugins', 'kontakt')
            assert len(SystemStatus.get_list('plugins')) == 2

            # Remove item
            SystemStatus.remove_from_list('plugins', 'kontakt')
            plugins = SystemStatus.get_list('plugins')
            assert 'kontakt' not in plugins
            assert 'newsletter' in plugins

            # Remove last item (should delete the key)
            SystemStatus.remove_from_list('plugins', 'newsletter')
            assert SystemStatus.get('plugins') is None

    def test_datetime_operations(self, app):
        """Test datetime get/set operations."""
        with app.app_context():
            scheduled = datetime(2025, 1, 9, 3, 0, 0, tzinfo=UTC)
            SystemStatus.set_datetime('restart_scheduled', scheduled)

            retrieved = SystemStatus.get_datetime('restart_scheduled')
            assert retrieved is not None
            assert retrieved.year == 2025
            assert retrieved.month == 1
            assert retrieved.day == 9

    def test_get_datetime_invalid(self, app):
        """Test get_datetime with invalid value."""
        with app.app_context():
            SystemStatus.set('invalid_date', 'not-a-date')
            assert SystemStatus.get_datetime('invalid_date') is None

    def test_to_dict(self, app):
        """Test dictionary representation."""
        with app.app_context():
            status = SystemStatus.set('key', 'value')
            d = status.to_dict()

            assert d['key'] == 'key'
            assert d['value'] == 'value'
            assert 'updated_at' in d

    def test_repr(self, app):
        """Test string representation."""
        with app.app_context():
            status = SystemStatus.set('test', 'value')
            repr_str = repr(status)

            assert 'test' in repr_str
            assert 'value' in repr_str

    def test_restart_required_workflow(self, app):
        """Test typical restart_required workflow."""
        with app.app_context():
            # Initially no restart required
            assert SystemStatus.get_bool(SystemStatus.KEY_RESTART_REQUIRED) is False

            # Activate a plugin -> set restart required
            SystemStatus.set_bool(SystemStatus.KEY_RESTART_REQUIRED, True)
            assert SystemStatus.get_bool(SystemStatus.KEY_RESTART_REQUIRED) is True

            # Add pending migration
            SystemStatus.add_to_list(SystemStatus.KEY_MIGRATIONS_PENDING, 'kontakt')
            assert 'kontakt' in SystemStatus.get_list(SystemStatus.KEY_MIGRATIONS_PENDING)

            # After restart -> clear flag
            SystemStatus.set_bool(SystemStatus.KEY_RESTART_REQUIRED, False)
            SystemStatus.remove_from_list(SystemStatus.KEY_MIGRATIONS_PENDING, 'kontakt')

            assert SystemStatus.get_bool(SystemStatus.KEY_RESTART_REQUIRED) is False
            assert 'kontakt' not in SystemStatus.get_list(SystemStatus.KEY_MIGRATIONS_PENDING)
