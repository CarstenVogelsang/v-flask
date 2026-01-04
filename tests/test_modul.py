"""Tests for Modul model."""

import pytest

from v_flask import db
from v_flask.models import Modul, User, Rolle, Permission


class TestModul:
    """Test cases for Modul model."""

    def test_create_modul(self, app):
        """Test creating a module."""
        with app.app_context():
            modul = Modul(
                code='projektverwaltung',
                name='Projektverwaltung',
                beschreibung='Projekte und Tasks verwalten',
                icon='folder',
                endpoint='admin.projekte',
                min_permission='projekt.read',
                sort_order=1
            )
            db.session.add(modul)
            db.session.commit()

            assert modul.id is not None
            assert modul.code == 'projektverwaltung'
            assert modul.aktiv is True

    def test_get_by_code(self, app):
        """Test getting a module by code."""
        with app.app_context():
            modul = Modul(
                code='settings',
                name='Einstellungen',
                min_permission='config.read'
            )
            db.session.add(modul)
            db.session.commit()

            result = Modul.get_by_code('settings')
            assert result is not None
            assert result.name == 'Einstellungen'

            # Non-existent code
            assert Modul.get_by_code('nonexistent') is None

    def test_get_all_active(self, app):
        """Test getting all active modules."""
        with app.app_context():
            db.session.add(Modul(code='m1', name='Module 1', min_permission='p1', aktiv=True))
            db.session.add(Modul(code='m2', name='Module 2', min_permission='p2', aktiv=True))
            db.session.add(Modul(code='m3', name='Module 3', min_permission='p3', aktiv=False))
            db.session.commit()

            results = Modul.get_all_active()
            assert len(results) == 2
            assert all(m.aktiv for m in results)

    def test_get_for_user_with_permission(self, app, admin_user):
        """Test getting modules for a user with wildcard permission."""
        with app.app_context():
            # Admin has admin.* permission
            db.session.add(Modul(code='users', name='Users', min_permission='admin.users'))
            db.session.add(Modul(code='config', name='Config', min_permission='admin.config'))
            db.session.commit()

            # Reload user in this context
            user = db.session.get(User, admin_user.id)
            results = Modul.get_for_user(user)

            # Admin should see both (admin.* matches admin.users and admin.config)
            assert len(results) == 2

    def test_get_for_user_without_permission(self, app, mitarbeiter_user):
        """Test that modules without permission are hidden."""
        with app.app_context():
            # Module requiring admin permission
            db.session.add(Modul(code='admin_only', name='Admin Only', min_permission='admin.panel'))
            # Module requiring projekt.read (mitarbeiter has this)
            db.session.add(Modul(code='projekte', name='Projekte', min_permission='projekt.read'))
            db.session.commit()

            # Reload user in this context
            user = db.session.get(User, mitarbeiter_user.id)
            results = Modul.get_for_user(user)

            # Mitarbeiter should only see projekte
            assert len(results) == 1
            assert results[0].code == 'projekte'

    def test_get_for_user_anonymous(self, app):
        """Test that anonymous users see no modules."""
        with app.app_context():
            db.session.add(Modul(code='m1', name='M1', min_permission='some.perm'))
            db.session.commit()

            # Create a mock anonymous user
            class AnonymousUser:
                is_authenticated = False

            results = Modul.get_for_user(AnonymousUser())
            assert results == []

    def test_user_can_access(self, app, admin_user, mitarbeiter_user):
        """Test user_can_access method."""
        with app.app_context():
            modul = Modul(code='admin_panel', name='Admin', min_permission='admin.panel')
            db.session.add(modul)
            db.session.commit()

            admin = db.session.get(User, admin_user.id)
            mitarbeiter = db.session.get(User, mitarbeiter_user.id)

            assert modul.user_can_access(admin) is True  # admin.* matches
            assert modul.user_can_access(mitarbeiter) is False

    def test_sort_order(self, app):
        """Test that modules are sorted by sort_order."""
        with app.app_context():
            db.session.add(Modul(code='c', name='Third', min_permission='p', sort_order=3))
            db.session.add(Modul(code='a', name='First', min_permission='p', sort_order=1))
            db.session.add(Modul(code='b', name='Second', min_permission='p', sort_order=2))
            db.session.commit()

            results = Modul.get_all_active()
            codes = [m.code for m in results]

            assert codes == ['a', 'b', 'c']

    def test_to_dict(self, app):
        """Test dictionary representation."""
        with app.app_context():
            modul = Modul(
                code='test',
                name='Test Module',
                beschreibung='A test module',
                icon='test-icon',
                endpoint='test.index',
                min_permission='test.read',
                sort_order=42
            )
            db.session.add(modul)
            db.session.commit()

            d = modul.to_dict()
            assert d['code'] == 'test'
            assert d['name'] == 'Test Module'
            assert d['beschreibung'] == 'A test module'
            assert d['icon'] == 'test-icon'
            assert d['endpoint'] == 'test.index'
            assert d['min_permission'] == 'test.read'
            assert d['sort_order'] == 42
            assert d['aktiv'] is True

    def test_unique_code(self, app):
        """Test that module codes are unique."""
        with app.app_context():
            db.session.add(Modul(code='unique', name='First', min_permission='p'))
            db.session.commit()

            db.session.add(Modul(code='unique', name='Second', min_permission='p'))
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()
