"""Tests for v-flask CLI commands."""

import pytest
from click.testing import CliRunner
from flask import Flask

from v_flask import VFlask, db
from v_flask.models import User, Rolle, Permission, Betreiber


@pytest.fixture
def runner(app):
    """Create a CLI test runner."""
    return app.test_cli_runner()


class TestInitDbCommand:
    """Tests for the init-db command."""

    def test_init_db_creates_tables(self, app, runner):
        """init-db should create all database tables."""
        # Drop all tables first
        with app.app_context():
            db.drop_all()

        # Run init-db
        result = runner.invoke(args=['init-db'])

        assert result.exit_code == 0
        assert 'Database initialized' in result.output

        # Verify tables exist by querying
        with app.app_context():
            # Should not raise an error
            User.query.all()
            Rolle.query.all()

    def test_init_db_idempotent(self, app, runner):
        """init-db should be safe to run multiple times."""
        result1 = runner.invoke(args=['init-db'])
        result2 = runner.invoke(args=['init-db'])

        assert result1.exit_code == 0
        assert result2.exit_code == 0


class TestSeedCommand:
    """Tests for the seed command."""

    def test_seed_creates_roles(self, app, runner):
        """seed should create admin, mitarbeiter, kunde roles."""
        result = runner.invoke(args=['seed'])

        assert result.exit_code == 0
        assert 'Seeding complete' in result.output

        with app.app_context():
            roles = Rolle.query.all()
            role_names = [r.name for r in roles]
            assert 'admin' in role_names
            assert 'mitarbeiter' in role_names
            assert 'kunde' in role_names

    def test_seed_creates_permissions(self, app, runner):
        """seed should create core permissions."""
        result = runner.invoke(args=['seed'])

        assert result.exit_code == 0

        with app.app_context():
            perms = Permission.query.all()
            perm_codes = [p.code for p in perms]
            assert 'admin.*' in perm_codes
            assert 'user.read' in perm_codes
            assert 'config.read' in perm_codes

    def test_seed_assigns_permissions_to_admin(self, app, runner):
        """seed should assign admin.* permission to admin role."""
        runner.invoke(args=['seed'])

        with app.app_context():
            admin = Rolle.query.filter_by(name='admin').first()
            assert admin is not None
            perm_codes = [p.code for p in admin.permissions]
            assert 'admin.*' in perm_codes

    def test_seed_creates_default_betreiber(self, app, runner):
        """seed should create a default Betreiber if none exists."""
        runner.invoke(args=['seed'])

        with app.app_context():
            betreiber = Betreiber.query.first()
            assert betreiber is not None
            assert betreiber.name == 'Default'

    def test_seed_idempotent(self, app, runner):
        """seed should be safe to run multiple times."""
        result1 = runner.invoke(args=['seed'])
        result2 = runner.invoke(args=['seed'])

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        # Should still have exactly 3 roles
        with app.app_context():
            roles = Rolle.query.all()
            assert len(roles) == 3

    def test_seed_does_not_duplicate_betreiber(self, app, runner):
        """seed should not create a second Betreiber if one exists."""
        # Create a Betreiber first
        with app.app_context():
            b = Betreiber(name='Existing', primary_color='#ff0000')
            db.session.add(b)
            db.session.commit()

        result = runner.invoke(args=['seed'])

        assert 'already exists' in result.output

        with app.app_context():
            count = Betreiber.query.count()
            assert count == 1


class TestCreateAdminCommand:
    """Tests for the create-admin command."""

    def test_create_admin_requires_seed(self, app, runner):
        """create-admin should fail if roles don't exist."""
        result = runner.invoke(
            args=['create-admin'],
            input='admin@test.com\nMax\nMuster\npassword123\npassword123\n'
        )

        assert result.exit_code == 0  # Command completes but shows error
        assert 'Admin role not found' in result.output

    def test_create_admin_success(self, app, runner):
        """create-admin should create an admin user."""
        # Seed roles first
        runner.invoke(args=['seed'])

        # Create admin
        result = runner.invoke(
            args=['create-admin'],
            input='admin@test.com\nMax\nMuster\npassword123\npassword123\n'
        )

        assert result.exit_code == 0
        assert 'created successfully' in result.output

        with app.app_context():
            user = User.query.filter_by(email='admin@test.com').first()
            assert user is not None
            assert user.vorname == 'Max'
            assert user.nachname == 'Muster'
            assert user.rolle_obj.name == 'admin'
            assert user.check_password('password123')

    def test_create_admin_with_options(self, app, runner):
        """create-admin should accept command line options."""
        runner.invoke(args=['seed'])

        result = runner.invoke(
            args=[
                'create-admin',
                '--email', 'cli@test.com',
                '--vorname', 'CLI',
                '--nachname', 'User',
                '--password', 'testpass123'
            ]
        )

        assert result.exit_code == 0
        assert 'created successfully' in result.output

        with app.app_context():
            user = User.query.filter_by(email='cli@test.com').first()
            assert user is not None

    def test_create_admin_duplicate_email(self, app, runner):
        """create-admin should reject duplicate email."""
        runner.invoke(args=['seed'])

        # Create first admin
        runner.invoke(
            args=['create-admin'],
            input='dup@test.com\nFirst\nUser\npassword\npassword\n'
        )

        # Try to create second with same email
        result = runner.invoke(
            args=['create-admin'],
            input='dup@test.com\nSecond\nUser\npassword\npassword\n'
        )

        assert 'already exists' in result.output

    def test_create_admin_invalid_email(self, app, runner):
        """create-admin should reject invalid email format."""
        runner.invoke(args=['seed'])

        result = runner.invoke(
            args=['create-admin'],
            input='invalid-email\nMax\nMuster\npassword\npassword\n'
        )

        assert 'Invalid email' in result.output
