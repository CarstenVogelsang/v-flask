"""CLI commands for v-flask.

Provides Flask CLI commands for database initialization and seeding.

Usage:
    flask init-db        # Create all tables
    flask seed           # Seed core data (roles, permissions)
    flask seed-palettes  # Seed default color palettes
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
        - Roles: superadmin, admin, betreiber, mitarbeiter, kunde
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
            {'name': 'superadmin', 'beschreibung': 'Super-Administrator (V-Flask Team)'},
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
            # Superadmin wildcard (V-Flask team, sees alpha/beta plugins)
            {'code': 'superadmin.*', 'beschreibung': 'Super-Admin Vollzugriff inkl. Alpha/Beta-Plugins', 'modul': 'core'},
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
            'superadmin': ['superadmin.*', 'admin.*'],  # Inherits all admin rights + superadmin
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

    @app.cli.command('seed-palettes')
    def seed_palettes_command():
        """Seed default color palettes.

        Creates a set of predefined color palettes for theming.
        Each palette includes 8 semantic colors (DaisyUI convention).

        Categories:
        - warm: Orange, red, yellow tones
        - cool: Blue, purple, teal tones
        - neutral: Gray, black, white tones
        - vibrant: Bright, saturated colors
        """
        from .models import ColorPalette

        click.echo('Seeding color palettes...')
        click.echo('')

        palettes_data = [
            # Warm palettes
            {
                'name': 'Warm Orange',
                'slug': 'warm-orange',
                'category': 'warm',
                'is_default': True,
                'primary': '#f97316',
                'secondary': '#ea580c',
                'accent': '#fbbf24',
                'neutral': '#78716c',
                'info': '#0ea5e9',
                'success': '#22c55e',
                'warning': '#f59e0b',
                'error': '#ef4444',
            },
            {
                'name': 'Terracotta',
                'slug': 'terracotta',
                'category': 'warm',
                'primary': '#c2410c',
                'secondary': '#9a3412',
                'accent': '#d97706',
                'neutral': '#57534e',
                'info': '#0284c7',
                'success': '#16a34a',
                'warning': '#ca8a04',
                'error': '#dc2626',
            },
            # Cool palettes
            {
                'name': 'Ocean Blue',
                'slug': 'ocean-blue',
                'category': 'cool',
                'primary': '#0ea5e9',
                'secondary': '#0284c7',
                'accent': '#06b6d4',
                'neutral': '#64748b',
                'info': '#3b82f6',
                'success': '#22c55e',
                'warning': '#f59e0b',
                'error': '#ef4444',
            },
            {
                'name': 'Royal Purple',
                'slug': 'royal-purple',
                'category': 'cool',
                'primary': '#8b5cf6',
                'secondary': '#7c3aed',
                'accent': '#a855f7',
                'neutral': '#6b7280',
                'info': '#6366f1',
                'success': '#10b981',
                'warning': '#f59e0b',
                'error': '#ef4444',
            },
            # Neutral palettes
            {
                'name': 'Slate Gray',
                'slug': 'slate-gray',
                'category': 'neutral',
                'primary': '#475569',
                'secondary': '#334155',
                'accent': '#64748b',
                'neutral': '#1e293b',
                'info': '#0ea5e9',
                'success': '#22c55e',
                'warning': '#f59e0b',
                'error': '#ef4444',
            },
            # Vibrant palettes
            {
                'name': 'Neon',
                'slug': 'neon',
                'category': 'vibrant',
                'primary': '#ec4899',
                'secondary': '#f43f5e',
                'accent': '#14b8a6',
                'neutral': '#404040',
                'info': '#22d3ee',
                'success': '#4ade80',
                'warning': '#facc15',
                'error': '#f87171',
            },
        ]

        created = 0
        skipped = 0

        for palette_data in palettes_data:
            existing = ColorPalette.query.filter_by(slug=palette_data['slug']).first()
            if existing:
                click.echo(f"  Palette '{palette_data['name']}' already exists")
                skipped += 1
            else:
                palette = ColorPalette(**palette_data)
                db.session.add(palette)
                click.echo(f"  Created palette: {palette_data['name']} ({palette_data['category']})")
                created += 1

        db.session.commit()

        click.echo('')
        click.echo(click.style(
            f'Seeding complete! Created: {created}, Skipped: {skipped}',
            fg='green'
        ))

    @app.cli.command('plugins-migrate')
    def plugins_migrate_command():
        """Run database migrations for pending plugins.

        Use after activating plugins and restarting the server.
        Ideal for CI/CD pipelines and automated deployments.

        Example workflow:
            1. Activate plugin via Admin UI
            2. Restart server (flask run)
            3. Run: flask plugins-migrate
        """
        # Import here to avoid circular imports
        from flask import current_app

        # Get plugin manager from app extensions
        if 'v_flask' not in current_app.extensions:
            click.echo(click.style('Error: v_flask extension not initialized.', fg='red'))
            return

        manager = current_app.extensions['v_flask'].plugin_manager

        # Check if restart is still pending
        if manager.is_restart_required():
            click.echo(click.style(
                'Error: Server restart required before running migrations.',
                fg='red'
            ))
            click.echo('')
            click.echo('Workflow:')
            click.echo('  1. Restart server (CTRL+C, then flask run)')
            click.echo('  2. Run: flask plugins-migrate')
            return

        pending = manager.get_pending_migrations()
        if not pending:
            click.echo('No pending migrations.')
            return

        click.echo(f'Running migrations for {len(pending)} plugin(s): {", ".join(pending)}')
        click.echo('')

        try:
            from flask_migrate import upgrade
            upgrade()
            manager.clear_all_pending_migrations()
            click.echo('')
            click.echo(click.style('Migrations completed successfully!', fg='green'))
        except ImportError:
            # Flask-Migrate not installed, try direct db.create_all()
            click.echo('Flask-Migrate not installed, using db.create_all() fallback...')
            try:
                db.create_all()
                manager.clear_all_pending_migrations()
                click.echo(click.style('Database tables created.', fg='yellow'))
            except Exception as e:
                click.echo(click.style(f'Error creating tables: {e}', fg='red'))
        except Exception as e:
            click.echo(click.style(f'Error running migrations: {e}', fg='red'))
