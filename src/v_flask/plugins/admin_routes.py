"""Admin routes for plugin management.

Includes:
- Local plugin activation/deactivation
- Server restart scheduling
- Marketplace integration (browse, install, update)
"""

from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)

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
    """Display list of all plugins (installed + marketplace).

    Shows a merged list of locally installed plugins and available
    plugins from the remote marketplace. Each plugin shows its status:
    - active: Installed and activated
    - inactive: Installed but not activated
    - installable: Only available in marketplace (not installed)

    Query params:
        category: Filter by category code (e.g., 'essential', 'commerce')
    """
    manager = get_plugin_manager()
    restart_manager = get_restart_manager()

    # Get merged list of installed + marketplace plugins
    plugins, marketplace_available = manager.get_merged_plugin_list()

    # Fetch categories for filter buttons and marketplace URL for status display
    categories = []
    current_category = request.args.get('category')
    current_category_info = None
    marketplace_url = None

    client = get_marketplace_client()
    if client and client.is_configured:
        marketplace_url = client.base_url
        try:
            categories = client.get_plugin_categories()
            # Find current category info
            if current_category:
                current_category_info = next(
                    (c for c in categories if c.get('code') == current_category),
                    None
                )
        except Exception:
            pass  # Categories are optional, continue without them

    # Filter plugins by category if specified
    if current_category:
        plugins = [
            p for p in plugins
            if (p.get('category_info') or {}).get('code') == current_category
            or p.get('category') == current_category  # Legacy fallback
        ]

    restart_required = manager.is_restart_required()
    scheduled_restart = restart_manager.get_scheduled_restart()
    pending_migrations = manager.get_pending_migrations()

    return render_template(
        'v_flask/admin/plugins/list.html',
        plugins=plugins,
        marketplace_available=marketplace_available,
        marketplace_url=marketplace_url,
        categories=categories,
        current_category=current_category,
        current_category_info=current_category_info,
        restart_required=restart_required,
        scheduled_restart=scheduled_restart,
        pending_migrations=pending_migrations,
    )


@plugins_admin_bp.route('/<name>/activate', methods=['POST'])
@permission_required('plugins.manage')
def activate_plugin(name: str):
    """Activate a plugin with all its dependencies.

    Automatically resolves and activates all required dependency plugins
    before activating the target plugin.
    """
    manager = get_plugin_manager()

    try:
        user_id = current_user.id if current_user.is_authenticated else None
        # Activate with all dependencies
        activated = manager.activate_with_dependencies(name, user_id=user_id)

        if len(activated) == 0:
            flash(f'Plugin "{name}" ist bereits aktiviert.', 'info')
        elif len(activated) == 1:
            flash(f'Plugin "{name}" wurde aktiviert. Server-Neustart erforderlich.', 'success')
        else:
            flash(
                f'{len(activated)} Plugins wurden aktiviert: {", ".join(activated)}. '
                'Server-Neustart erforderlich.',
                'success'
            )
    except PluginNotFoundError:
        flash(f'Plugin "{name}" wurde nicht gefunden.', 'error')
    except PluginNotInstalledError as e:
        flash(f'Plugin muss erst installiert werden: {e}', 'warning')
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
    """Run database migrations for pending plugins.

    Requires that no server restart is pending, since plugin models
    must be loaded before migrations can run successfully.
    """
    manager = get_plugin_manager()

    # Check if restart is still pending - migrations can only run after restart
    if manager.is_restart_required():
        flash(
            'Server-Neustart erforderlich bevor Migrationen ausgeführt werden können.',
            'warning'
        )
        return redirect(url_for('plugins_admin.list_plugins'))

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


# ============================================================================
# Marketplace Routes
# ============================================================================


def get_marketplace_client():
    """Get the marketplace client if configured."""
    try:
        from v_flask.plugins.marketplace_client import get_marketplace_client as get_client
        client = get_client()
        if client.is_configured:
            return client
    except ImportError:
        pass
    return None


def get_plugin_downloader():
    """Get the plugin downloader."""
    from v_flask.plugins.downloader import get_plugin_downloader as get_downloader
    return get_downloader()


@plugins_admin_bp.route('/marketplace')
@permission_required('plugins.manage')
def marketplace():
    """Display available plugins from the remote marketplace."""
    client = get_marketplace_client()

    if not client:
        flash(
            'Marketplace nicht konfiguriert. '
            'Setze VFLASK_MARKETPLACE_URL und VFLASK_PROJECT_API_KEY.',
            'warning'
        )
        return redirect(url_for('plugins_admin.list_plugins'))

    try:
        # Get remote plugins
        remote_plugins = client.get_available_plugins()

        # Get licenses
        try:
            licensed_names = client.get_licensed_plugin_names()
        except Exception:
            licensed_names = set()

        # Get local installation status
        downloader = get_plugin_downloader()
        installed_names = set(downloader.get_installed_plugins())

        # Enrich plugin data with status
        plugins = []
        for plugin in remote_plugins:
            name = plugin.get('name')
            is_free = plugin.get('is_free', False) or plugin.get('price_cents', 0) == 0
            plugins.append({
                **plugin,
                'is_installed': name in installed_names,
                'is_licensed': name in licensed_names or is_free,
                'is_free': is_free,
                'can_install': (name in licensed_names or is_free) and name not in installed_names,
            })

        # Get project info
        project_info = None
        try:
            project_info = client.get_project_info()
        except Exception:
            pass

        return render_template(
            'v_flask/admin/plugins/marketplace.html',
            plugins=plugins,
            project_info=project_info,
            marketplace_configured=True,
        )

    except Exception as e:
        logger.error(f"Marketplace error: {e}")
        flash(f'Fehler beim Laden des Marketplaces: {e}', 'error')
        return redirect(url_for('plugins_admin.list_plugins'))


@plugins_admin_bp.route('/<name>/install', methods=['POST'])
@permission_required('plugins.manage')
def install_plugin(name: str):
    """Install a plugin from the marketplace."""
    client = get_marketplace_client()

    if not client:
        flash('Marketplace nicht konfiguriert.', 'error')
        return redirect(url_for('plugins_admin.list_plugins'))

    downloader = get_plugin_downloader()

    try:
        # Check if can download (licensed or free)
        if not client.can_download_plugin(name):
            flash(f'Plugin "{name}" ist nicht lizenziert.', 'error')
            return redirect(url_for('plugins_admin.marketplace'))

        # Install the plugin
        force = request.form.get('force') == '1'
        downloader.install_plugin(name, force=force)

        flash(f'Plugin "{name}" wurde installiert.', 'success')

    except Exception as e:
        logger.error(f"Install error for {name}: {e}")
        flash(f'Fehler beim Installieren von "{name}": {e}', 'error')

    return redirect(url_for('plugins_admin.marketplace'))


@plugins_admin_bp.route('/<name>/uninstall', methods=['POST'])
@permission_required('plugins.manage')
def uninstall_plugin(name: str):
    """Uninstall a plugin (remove local files)."""
    manager = get_plugin_manager()
    downloader = get_plugin_downloader()

    try:
        # First deactivate if active
        manager.deactivate_plugin(name)

        # Then remove files
        if downloader.uninstall_plugin(name):
            flash(f'Plugin "{name}" wurde deinstalliert.', 'success')
        else:
            flash(f'Plugin "{name}" war nicht installiert.', 'warning')

    except Exception as e:
        logger.error(f"Uninstall error for {name}: {e}")
        flash(f'Fehler beim Deinstallieren von "{name}": {e}', 'error')

    return redirect(url_for('plugins_admin.marketplace'))


@plugins_admin_bp.route('/marketplace/refresh', methods=['POST'])
@permission_required('plugins.manage')
def refresh_marketplace():
    """Refresh marketplace plugin list.

    Clears the marketplace client cache and redirects back to the
    referring page (either list_plugins or marketplace).
    """
    client = get_marketplace_client()

    if client:
        client.refresh_cache()
        flash('Marketplace-Cache aktualisiert.', 'success')
    else:
        flash('Marketplace nicht konfiguriert.', 'warning')

    # Redirect back to referrer if within admin, otherwise to list
    referrer = request.referrer
    if referrer and '/admin/plugins' in referrer:
        return redirect(referrer)
    return redirect(url_for('plugins_admin.list_plugins'))


def register_plugin_admin_routes(app: Flask) -> None:
    """Register the plugin admin blueprint with the app.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(plugins_admin_bp)
