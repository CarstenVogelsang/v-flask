"""Admin routes for plugin management."""

from __future__ import annotations

from datetime import datetime, timedelta, UTC
from typing import TYPE_CHECKING

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from v_flask.auth import permission_required
from v_flask.plugins.manager import (
    DependencyNotActivatedError,
    PluginManager,
    PluginNotFoundError,
    PluginNotInstalledError,
)
from v_flask.plugins.restart import RestartManager

if TYPE_CHECKING:
    from flask import Flask

# Blueprint for plugin admin routes
plugins_admin_bp = Blueprint(
    'plugins_admin',
    __name__,
    url_prefix='/admin/plugins',
    template_folder='../templates',
)


def get_plugin_manager() -> PluginManager:
    """Get the plugin manager from the current app."""
    from flask import current_app
    return current_app.extensions['v_flask'].plugin_manager


def get_restart_manager() -> RestartManager:
    """Get the restart manager from the current app."""
    from flask import current_app
    return current_app.extensions['v_flask'].restart_manager


@plugins_admin_bp.route('/')
@permission_required('plugins.manage')
def list_plugins():
    """Display list of available plugins with their status."""
    manager = get_plugin_manager()
    restart_manager = get_restart_manager()

    plugins = manager.get_plugins_with_status()
    restart_required = manager.is_restart_required()
    scheduled_restart = restart_manager.get_scheduled_restart()
    pending_migrations = manager.get_pending_migrations()

    return render_template(
        'v_flask/admin/plugins/list.html',
        plugins=plugins,
        restart_required=restart_required,
        scheduled_restart=scheduled_restart,
        pending_migrations=pending_migrations,
    )


@plugins_admin_bp.route('/<name>/activate', methods=['POST'])
@permission_required('plugins.manage')
def activate_plugin(name: str):
    """Activate a plugin."""
    manager = get_plugin_manager()

    try:
        user_id = current_user.id if current_user.is_authenticated else None
        manager.activate_plugin(name, user_id=user_id)
        flash(f'Plugin "{name}" wurde aktiviert. Server-Neustart erforderlich.', 'success')
    except PluginNotFoundError:
        flash(f'Plugin "{name}" wurde nicht gefunden.', 'error')
    except PluginNotInstalledError as e:
        flash(f'Plugin "{name}" ist nicht installiert: {e}', 'error')
    except DependencyNotActivatedError as e:
        flash(str(e), 'warning')
    except Exception as e:
        flash(f'Fehler beim Aktivieren: {e}', 'error')

    return redirect(url_for('plugins_admin.list_plugins'))


@plugins_admin_bp.route('/<name>/deactivate', methods=['POST'])
@permission_required('plugins.manage')
def deactivate_plugin(name: str):
    """Deactivate a plugin."""
    manager = get_plugin_manager()

    try:
        if manager.deactivate_plugin(name):
            flash(f'Plugin "{name}" wurde deaktiviert. Server-Neustart erforderlich.', 'success')
        else:
            flash(f'Plugin "{name}" war nicht aktiviert.', 'warning')
    except Exception as e:
        flash(f'Fehler beim Deaktivieren: {e}', 'error')

    return redirect(url_for('plugins_admin.list_plugins'))


@plugins_admin_bp.route('/restart', methods=['POST'])
@permission_required('plugins.restart')
def restart_now():
    """Request immediate server restart."""
    restart_manager = get_restart_manager()

    try:
        restart_manager.request_restart(immediate=True)
        flash('Server-Neustart wurde initiiert.', 'info')
    except Exception as e:
        flash(f'Neustart konnte nicht initiiert werden: {e}', 'error')

    return redirect(url_for('plugins_admin.list_plugins'))


@plugins_admin_bp.route('/restart/schedule', methods=['POST'])
@permission_required('plugins.restart')
def schedule_restart():
    """Schedule a server restart."""
    restart_manager = get_restart_manager()

    # Get schedule time from form
    schedule_type = request.form.get('schedule_type', 'hours')
    schedule_value = request.form.get('schedule_value', '2')

    try:
        if schedule_type == 'datetime':
            # Specific datetime provided
            restart_at = datetime.fromisoformat(schedule_value)
            if restart_at.tzinfo is None:
                restart_at = restart_at.replace(tzinfo=UTC)
        else:
            # Hours from now
            hours = int(schedule_value)
            restart_at = datetime.now(UTC) + timedelta(hours=hours)

        restart_manager.schedule_restart(restart_at)
        flash(f'Server-Neustart geplant für {restart_at.strftime("%d.%m.%Y %H:%M")} Uhr.', 'success')
    except ValueError as e:
        flash(f'Ungültiger Zeitwert: {e}', 'error')
    except Exception as e:
        flash(f'Fehler beim Planen des Neustarts: {e}', 'error')

    return redirect(url_for('plugins_admin.list_plugins'))


@plugins_admin_bp.route('/restart/cancel', methods=['POST'])
@permission_required('plugins.restart')
def cancel_restart():
    """Cancel a scheduled restart."""
    restart_manager = get_restart_manager()

    try:
        restart_manager.cancel_scheduled_restart()
        flash('Geplanter Neustart wurde abgebrochen.', 'success')
    except Exception as e:
        flash(f'Fehler beim Abbrechen: {e}', 'error')

    return redirect(url_for('plugins_admin.list_plugins'))


@plugins_admin_bp.route('/migrations', methods=['POST'])
@permission_required('plugins.manage')
def run_migrations():
    """Run database migrations for pending plugins."""
    manager = get_plugin_manager()

    pending = manager.get_pending_migrations()
    if not pending:
        flash('Keine ausstehenden Migrationen.', 'info')
        return redirect(url_for('plugins_admin.list_plugins'))

    try:
        # Run Flask-Migrate upgrade
        from flask import current_app
        from flask_migrate import upgrade

        with current_app.app_context():
            upgrade()

        # Clear pending migrations
        manager.clear_all_pending_migrations()
        flash(f'Migrationen für {len(pending)} Plugin(s) erfolgreich ausgeführt.', 'success')
    except ImportError:
        # Flask-Migrate not installed, try direct db.create_all()
        try:
            from v_flask.extensions import db
            db.create_all()
            manager.clear_all_pending_migrations()
            flash('Datenbank-Tabellen wurden erstellt.', 'success')
        except Exception as e:
            flash(f'Fehler beim Erstellen der Tabellen: {e}', 'error')
    except Exception as e:
        flash(f'Fehler beim Ausführen der Migrationen: {e}', 'error')

    return redirect(url_for('plugins_admin.list_plugins'))


def register_plugin_admin_routes(app: Flask) -> None:
    """Register the plugin admin blueprint with the app.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(plugins_admin_bp)
