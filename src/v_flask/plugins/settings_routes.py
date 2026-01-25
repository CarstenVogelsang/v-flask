"""Settings routes for plugin configuration.

Provides admin UI for managing plugin-specific settings stored in the database.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from v_flask.auth import permission_required
from v_flask.models import PluginConfig

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

# Blueprint for plugin settings routes
plugin_settings_bp = Blueprint(
    'plugin_settings',
    __name__,
    url_prefix='/admin/plugins',
    template_folder='../templates',
)


def get_plugin_registry():
    """Get the plugin registry from the current app."""
    from flask import current_app
    return current_app.extensions['v_flask'].plugin_registry


def get_plugin_by_name(name: str):
    """Get a registered plugin by name.

    Args:
        name: The plugin name.

    Returns:
        The plugin manifest instance or None if not found.
    """
    registry = get_plugin_registry()
    return registry.get(name)


@plugin_settings_bp.route('/<plugin_name>/settings', methods=['GET', 'POST'])
@permission_required('plugins.settings')
def plugin_settings(plugin_name: str):
    """Display and handle plugin settings form.

    For plugins with get_settings_schema(), auto-generates a form.
    For plugins with get_settings_template(), uses custom template.

    Args:
        plugin_name: The plugin identifier.
    """
    plugin = get_plugin_by_name(plugin_name)

    if not plugin:
        flash(f'Plugin "{plugin_name}" nicht gefunden.', 'error')
        return redirect(url_for('plugins_admin.list_plugins'))

    schema = plugin.get_settings_schema()

    if not schema:
        flash(f'Plugin "{plugin_name}" hat keine konfigurierbaren Einstellungen.', 'info')
        return redirect(url_for('plugins_admin.list_plugins'))

    # Handle form submission
    if request.method == 'POST':
        try:
            user_id = current_user.id if current_user.is_authenticated else None
            saved_settings = {}

            for field in schema:
                key = field['key']
                field_type = field.get('type', 'string')

                # Get value from form
                if field_type == 'bool':
                    # Checkboxes need special handling
                    value = key in request.form
                else:
                    value = request.form.get(key, '')

                # Determine value_type for PluginConfig
                value_type = _get_value_type(field_type)

                # Determine if secret
                is_secret = field_type == 'password'

                # Save to database
                PluginConfig.set_value(
                    plugin_name=plugin_name,
                    key=key,
                    value=value,
                    value_type=value_type,
                    is_secret=is_secret,
                    description=field.get('description'),
                    user_id=user_id,
                )

                saved_settings[key] = value

            # Call plugin hook
            plugin.on_settings_saved(saved_settings)

            flash('Einstellungen gespeichert.', 'success')
            logger.info(f"Plugin settings saved for '{plugin_name}' by user {user_id}")

        except Exception as e:
            logger.error(f"Error saving settings for '{plugin_name}': {e}")
            flash(f'Fehler beim Speichern: {e}', 'error')

        return redirect(url_for('plugin_settings.plugin_settings', plugin_name=plugin_name))

    # Load current values
    current_values = {}
    for field in schema:
        key = field['key']
        default = field.get('default', '')
        current_values[key] = PluginConfig.get_value(plugin_name, key, default)

    # Check for custom template
    custom_template = plugin.get_settings_template()
    if custom_template:
        return render_template(
            custom_template,
            plugin=plugin,
            schema=schema,
            settings=current_values,
        )

    # Use auto-generated template
    return render_template(
        'v_flask/admin/plugin_settings.html',
        plugin=plugin,
        schema=schema,
        settings=current_values,
    )


def _get_value_type(field_type: str) -> str:
    """Map form field type to PluginConfig value_type.

    Args:
        field_type: The schema field type.

    Returns:
        The PluginConfig value_type string.
    """
    type_mapping = {
        'string': 'string',
        'password': 'string',
        'textarea': 'string',
        'int': 'int',
        'float': 'float',
        'bool': 'bool',
        'select': 'string',
    }
    return type_mapping.get(field_type, 'string')


# ============================================================================
# Help Routes (Placeholder for future implementation)
# ============================================================================

@plugin_settings_bp.route('/<plugin_name>/help')
@permission_required('plugins.view')
def plugin_help(plugin_name: str):
    """Display help page for a plugin.

    Args:
        plugin_name: The plugin identifier.
    """
    from v_flask.models import HelpText

    plugin = get_plugin_by_name(plugin_name)

    if not plugin:
        flash(f'Plugin "{plugin_name}" nicht gefunden.', 'error')
        return redirect(url_for('plugins_admin.list_plugins'))

    # Try to find help text for this plugin
    help_key = f'{plugin_name}.overview'
    help_text = HelpText.query.filter_by(schluessel=help_key).first()

    # Get plugin README as fallback
    readme_content = None
    if not help_text:
        readme_content = plugin.get_readme()

    can_edit = current_user.has_permission('help.edit')

    return render_template(
        'v_flask/admin/plugin_help.html',
        plugin=plugin,
        help_text=help_text,
        readme_content=readme_content,
        can_edit=can_edit,
    )


def register_settings_routes(app: Flask) -> None:
    """Register the settings blueprint with the app.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(plugin_settings_bp)
