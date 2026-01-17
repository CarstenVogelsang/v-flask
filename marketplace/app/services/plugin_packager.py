"""Plugin packager service.

Creates ZIP archives of plugins from v_flask_plugins directory.
"""
import os
import tempfile
import zipfile
from pathlib import Path

from flask import current_app


def package_plugin(plugin_name: str) -> Path:
    """Package a plugin as a ZIP archive.

    Creates a ZIP file containing the plugin directory
    with proper structure for installation.

    Args:
        plugin_name: Name of the plugin to package.

    Returns:
        Path to the created ZIP file.

    Raises:
        FileNotFoundError: If plugin directory doesn't exist.
    """
    plugins_dir = Path(current_app.config.get(
        'PLUGINS_SOURCE_DIR',
        Path(__file__).parent.parent.parent.parent / 'src' / 'v_flask_plugins'
    ))

    plugin_path = plugins_dir / plugin_name

    if not plugin_path.exists() or not plugin_path.is_dir():
        raise FileNotFoundError(f'Plugin not found: {plugin_name}')

    # Create temporary ZIP file
    temp_dir = tempfile.mkdtemp()
    zip_path = Path(temp_dir) / f'{plugin_name}.zip'

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(plugin_path):
            # Skip __pycache__ and other unwanted directories
            dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]

            for file in files:
                # Skip .pyc files and other unwanted files
                if file.endswith('.pyc') or file.startswith('.'):
                    continue

                file_path = Path(root) / file
                # Archive path: plugin_name/relative_path
                archive_path = plugin_name / file_path.relative_to(plugin_path)
                zf.write(file_path, archive_path)

    current_app.logger.info(f'Packaged plugin: {plugin_name} -> {zip_path}')
    return zip_path


def get_plugin_size(plugin_name: str) -> int:
    """Get the total size of a plugin in bytes.

    Args:
        plugin_name: Name of the plugin.

    Returns:
        Size in bytes.
    """
    plugins_dir = Path(current_app.config.get(
        'PLUGINS_SOURCE_DIR',
        Path(__file__).parent.parent.parent.parent / 'src' / 'v_flask_plugins'
    ))

    plugin_path = plugins_dir / plugin_name

    if not plugin_path.exists():
        return 0

    total_size = 0
    for root, dirs, files in os.walk(plugin_path):
        for file in files:
            file_path = Path(root) / file
            total_size += file_path.stat().st_size

    return total_size
