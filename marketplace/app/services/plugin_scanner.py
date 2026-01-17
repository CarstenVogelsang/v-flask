"""Plugin scanner service.

Scans the v_flask_plugins directory for available plugins
and extracts their metadata from the PluginManifest.
"""
import importlib
import sys
from pathlib import Path
from typing import Any

from flask import current_app


def scan_plugins() -> list[dict[str, Any]]:
    """Scan v_flask_plugins directory for available plugins.

    Returns:
        List of plugin metadata dictionaries.
    """
    plugins_dir = Path(current_app.config.get(
        'PLUGINS_SOURCE_DIR',
        Path(__file__).parent.parent.parent.parent / 'src' / 'v_flask_plugins'
    ))

    if not plugins_dir.exists():
        current_app.logger.warning(f'Plugins directory not found: {plugins_dir}')
        return []

    plugins = []

    for plugin_path in plugins_dir.iterdir():
        if not plugin_path.is_dir():
            continue

        if plugin_path.name.startswith('_'):
            continue

        init_file = plugin_path / '__init__.py'
        if not init_file.exists():
            continue

        try:
            plugin_data = _extract_plugin_metadata(plugin_path)
            if plugin_data:
                plugins.append(plugin_data)
        except Exception as e:
            current_app.logger.warning(
                f'Failed to extract metadata from {plugin_path.name}: {e}'
            )

    return plugins


def _extract_plugin_metadata(plugin_path: Path) -> dict[str, Any] | None:
    """Extract metadata from a plugin directory.

    Tries to import the plugin module and read its PluginManifest.
    Falls back to basic info if import fails.

    Args:
        plugin_path: Path to the plugin directory.

    Returns:
        Plugin metadata dictionary or None if extraction fails.
    """
    plugin_name = plugin_path.name

    # Try to import and get manifest
    try:
        # Add parent to path temporarily
        parent_path = str(plugin_path.parent.parent)
        if parent_path not in sys.path:
            sys.path.insert(0, parent_path)

        module = importlib.import_module(f'v_flask_plugins.{plugin_name}')

        # Look for PluginManifest subclass
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type) and
                hasattr(attr, 'name') and
                hasattr(attr, 'version') and
                attr_name.endswith('Plugin')
            ):
                # Found a plugin class, extract metadata
                return {
                    'name': getattr(attr, 'name', plugin_name),
                    'display_name': getattr(attr, 'display_name', plugin_name.title()),
                    'description': getattr(attr, 'description', ''),
                    'version': getattr(attr, 'version', '0.1.0'),
                }

    except Exception as e:
        current_app.logger.debug(f'Could not import {plugin_name}: {e}')

    # Fallback: just use directory name
    return {
        'name': plugin_name,
        'display_name': plugin_name.replace('_', ' ').title(),
        'description': '',
        'version': '0.1.0',
    }
