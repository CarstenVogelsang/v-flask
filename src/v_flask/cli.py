"""CLI commands for v-flask.

Provides Flask CLI commands for database initialization and seeding.

Usage:
    flask init-db        # Create all tables
    flask seed           # Seed core data (roles, permissions)
    flask create-admin   # Create an admin user interactively
"""

import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def register_commands(app: Flask, db: SQLAlchemy) -> None:
    """Register CLI commands with the Flask app.

    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
    """

    @app.cli.command('init-db')
    def init_db_command():
        """Initialize database tables.

        Creates all tables defined by SQLAlchemy models.
        Use this for initial setup or when not using Flask-Migrate.
        """
        db.create_all()
        click.echo(click.style('Database initialized!', fg='green'))

    @app.cli.command('seed')
    def seed_command():
        """Seed database with core data.

        Creates:
        - Roles: admin, mitarbeiter, kunde
        - Core permissions for user and config management
        - Role-permission assignments
        - Default Betreiber (if none exists)
        """
        from .models import Rolle, Permission, Betreiber

        click.echo('Seeding core data...')
        click.echo('')

        # 1. Create roles
        click.echo('Creating roles...')
        roles_data = [
            {'name': 'admin', 'beschreibung': 'Administrator mit Vollzugriff'},
            {'name': 'betreiber', 'beschreibung': 'Betreiber mit Plugin-Verwaltung'},
            {'name': 'mitarbeiter', 'beschreibung': 'Mitarbeiter mit eingeschränkten Rechten'},
            {'name': 'kunde', 'beschreibung': 'Kunde mit Lesezugriff'},
        ]

        roles = {}
        for role_data in roles_data:
            existing = Rolle.query.filter_by(name=role_data['name']).first()
            if existing:
                roles[role_data['name']] = existing
                click.echo(f"  Role '{role_data['name']}' already exists")
            else:
                role = Rolle(**role_data)
                db.session.add(role)
                roles[role_data['name']] = role
                click.echo(f"  Created role: {role_data['name']}")

        db.session.flush()  # Get IDs for new roles

        # 2. Create core permissions
        click.echo('')
        click.echo('Creating permissions...')
        permissions_data = [
            # Admin wildcard
            {'code': 'admin.*', 'beschreibung': 'Vollzugriff auf alle Funktionen', 'modul': 'core'},
            # User management
            {'code': 'user.read', 'beschreibung': 'Benutzer anzeigen', 'modul': 'core'},
            {'code': 'user.create', 'beschreibung': 'Benutzer erstellen', 'modul': 'core'},
            {'code': 'user.update', 'beschreibung': 'Benutzer bearbeiten', 'modul': 'core'},
            {'code': 'user.delete', 'beschreibung': 'Benutzer löschen', 'modul': 'core'},
            # Config management
            {'code': 'config.read', 'beschreibung': 'Konfiguration lesen', 'modul': 'core'},
            {'code': 'config.update', 'beschreibung': 'Konfiguration ändern', 'modul': 'core'},
            # Plugin management
            {'code': 'plugins.manage', 'beschreibung': 'Plugins aktivieren und deaktivieren', 'modul': 'core'},
            {'code': 'plugins.restart', 'beschreibung': 'Server-Neustart initiieren', 'modul': 'core'},
        ]

        permissions = {}
        for perm_data in permissions_data:
            existing = Permission.query.filter_by(code=perm_data['code']).first()
            if existing:
                permissions[perm_data['code']] = existing
                click.echo(f"  Permission '{perm_data['code']}' already exists")
            else:
                perm = Permission(**perm_data)
                db.session.add(perm)
                permissions[perm_data['code']] = perm
                click.echo(f"  Created permission: {perm_data['code']}")

        db.session.flush()

        # 3. Assign permissions to roles
        click.echo('')
        click.echo('Assigning permissions to roles...')

        role_permissions = {
            'admin': ['admin.*'],
            'betreiber': ['user.read', 'config.read', 'plugins.manage', 'plugins.restart'],
            'mitarbeiter': ['user.read', 'config.read'],
            'kunde': [],  # No core permissions
        }

        for role_name, perm_codes in role_permissions.items():
            role = roles.get(role_name)
            if not role:
                continue

            for code in perm_codes:
                perm = permissions.get(code)
                if perm and perm not in role.permissions:
                    role.permissions.append(perm)
                    click.echo(f"  Assigned '{code}' to '{role_name}'")

        # 4. Create default Betreiber if none exists
        click.echo('')
        click.echo('Checking Betreiber...')
        if Betreiber.query.count() == 0:
            betreiber = Betreiber(
                name='Default',
                primary_color='#3b82f6',
                secondary_color='#64748b'
            )
            db.session.add(betreiber)
            click.echo('  Created default Betreiber')
        else:
            click.echo('  Betreiber already exists')

        db.session.commit()

        click.echo('')
        click.echo(click.style('Seeding complete!', fg='green'))

    @app.cli.command('create-admin')
    @click.option('--email', prompt='E-Mail', help='Admin email address')
    @click.option('--vorname', prompt='Vorname', help='First name')
    @click.option('--nachname', prompt='Nachname', help='Last name')
    @click.option('--password', prompt='Passwort', hide_input=True,
                  confirmation_prompt=True, help='Password')
    def create_admin_command(email: str, vorname: str, nachname: str, password: str):
        """Create an admin user.

        Creates a new user with the admin role. If the admin role doesn't exist,
        run 'flask seed' first.

        Can be used interactively (with prompts) or with options:
            flask create-admin --email admin@example.com --vorname Max ...
        """
        from .models import User, Rolle

        # Check if admin role exists
        admin_rolle = Rolle.query.filter_by(name='admin').first()
        if not admin_rolle:
            click.echo(click.style(
                "Error: Admin role not found. Run 'flask seed' first.",
                fg='red'
            ))
            return

        # Check if user already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            click.echo(click.style(
                f"Error: User with email '{email}' already exists.",
                fg='red'
            ))
            return

        # Validate email format (basic check)
        if '@' not in email or '.' not in email:
            click.echo(click.style(
                "Error: Invalid email format.",
                fg='red'
            ))
            return

        # Create user
        user = User(
            email=email,
            vorname=vorname,
            nachname=nachname,
            rolle_id=admin_rolle.id,
            aktiv=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        click.echo('')
        click.echo(click.style(f"Admin user '{email}' created successfully!", fg='green'))
