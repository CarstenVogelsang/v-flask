"""Plugin downloader and installer.

This module handles downloading plugins from the marketplace
and installing them into the project's plugins directory.
"""
from __future__ import annotations

import io
import logging
import shutil
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from v_flask.plugins.marketplace_client import MarketplaceClient

logger = logging.getLogger(__name__)


class DownloaderError(Exception):
    """Base exception for downloader errors."""
    pass


class PluginAlreadyInstalledError(DownloaderError):
    """Raised when plugin is already installed."""
    pass


class InvalidPluginArchiveError(DownloaderError):
    """Raised when the downloaded archive is invalid."""
    pass


class PluginDownloader:
    """Downloads and installs plugins from the marketplace.

    Usage:
        from v_flask.plugins.marketplace_client import get_marketplace_client

        client = get_marketplace_client()
        downloader = PluginDownloader(client)

        # Install a plugin
        downloader.install_plugin('kontakt')

        # Check if installed
        if downloader.is_plugin_installed('kontakt'):
            print("Plugin installed!")

        # Uninstall
        downloader.uninstall_plugin('kontakt')
    """

    # Default plugins directory (relative to project root)
    DEFAULT_PLUGINS_DIR = 'v_flask_plugins'

    def __init__(
        self,
        client: MarketplaceClient | None = None,
        plugins_dir: Path | str | None = None,
    ):
        """Initialize the plugin downloader.

        Args:
            client: MarketplaceClient instance. If None, gets from singleton.
            plugins_dir: Directory where plugins are installed.
                         Can be set via VFLASK_PLUGINS_DIR config.
        """
        self._client = client
        self._plugins_dir = Path(plugins_dir) if plugins_dir else None

    @property
    def client(self) -> MarketplaceClient:
        """Get the marketplace client."""
        if self._client is None:
            from v_flask.plugins.marketplace_client import get_marketplace_client
            self._client = get_marketplace_client()
        return self._client

    @property
    def plugins_dir(self) -> Path:
        """Get the plugins installation directory.

        Resolution order:
        1. Explicitly set via constructor
        2. VFLASK_PLUGINS_DIR config
        3. Default: ./v_flask_plugins/

        Returns:
            Path to plugins directory.
        """
        if self._plugins_dir:
            return self._plugins_dir

        # Try to get from Flask config
        try:
            from flask import current_app
            config_dir = current_app.config.get('VFLASK_PLUGINS_DIR')
            if config_dir:
                return Path(config_dir)

            # Default: relative to instance path's parent (project root)
            # instance_path is typically /project/instance/
            project_root = Path(current_app.instance_path).parent
            return project_root / self.DEFAULT_PLUGINS_DIR
        except RuntimeError:
            # Outside of app context, use current directory
            return Path.cwd() / self.DEFAULT_PLUGINS_DIR

    def get_plugin_path(self, name: str) -> Path:
        """Get the path where a plugin would be installed.

        Args:
            name: Plugin name.

        Returns:
            Path to plugin directory.
        """
        return self.plugins_dir / name

    def is_plugin_installed(self, name: str) -> bool:
        """Check if a plugin is installed locally.

        Args:
            name: Plugin name.

        Returns:
            True if the plugin directory exists with __init__.py.
        """
        plugin_path = self.get_plugin_path(name)
        init_file = plugin_path / '__init__.py'
        return plugin_path.is_dir() and init_file.exists()

    def get_installed_plugins(self) -> list[str]:
        """Get list of installed plugin names.

        Returns:
            List of plugin names that are installed.
        """
        if not self.plugins_dir.exists():
            return []

        installed = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / '__init__.py').exists():
                installed.append(item.name)

        return sorted(installed)

    def install_plugin(
        self,
        name: str,
        force: bool = False,
    ) -> Path:
        """Download and install a plugin from the marketplace.

        Args:
            name: Plugin name to install.
            force: If True, reinstall even if already installed.

        Returns:
            Path to the installed plugin directory.

        Raises:
            PluginAlreadyInstalledError: If plugin exists and force=False.
            InvalidPluginArchiveError: If downloaded archive is invalid.
            MarketplaceError: On download errors.
        """
        plugin_path = self.get_plugin_path(name)

        # Check if already installed
        if self.is_plugin_installed(name) and not force:
            raise PluginAlreadyInstalledError(
                f"Plugin '{name}' ist bereits installiert. "
                f"Verwende force=True zum Überschreiben."
            )

        # Download the plugin
        logger.info(f"Downloading plugin: {name}")
        try:
            zip_content = self.client.download_plugin(name)
        except Exception as e:
            logger.error(f"Failed to download plugin '{name}': {e}")
            raise

        # Extract the plugin
        logger.info(f"Installing plugin: {name} -> {plugin_path}")
        try:
            self._extract_plugin(zip_content, name, plugin_path, force)
        except Exception as e:
            logger.error(f"Failed to install plugin '{name}': {e}")
            raise

        logger.info(f"Plugin '{name}' successfully installed")
        return plugin_path

    def _extract_plugin(
        self,
        zip_content: bytes,
        expected_name: str,
        target_path: Path,
        force: bool,
    ) -> None:
        """Extract plugin from ZIP content.

        The ZIP is expected to contain a directory named after the plugin.
        Example: kontakt.zip contains kontakt/__init__.py, kontakt/routes.py, etc.

        Args:
            zip_content: ZIP file content as bytes.
            expected_name: Expected plugin name (directory name in ZIP).
            target_path: Where to extract the plugin.
            force: If True, remove existing directory first.
        """
        try:
            zip_buffer = io.BytesIO(zip_content)
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                # Validate archive structure
                names = zf.namelist()
                if not names:
                    raise InvalidPluginArchiveError("ZIP-Archiv ist leer.")

                # Check for expected directory structure
                # Files should be prefixed with plugin name
                has_init = False
                for name in names:
                    if name.startswith(f'{expected_name}/'):
                        if name == f'{expected_name}/__init__.py':
                            has_init = True

                if not has_init:
                    raise InvalidPluginArchiveError(
                        f"Ungültiges Plugin-Archiv: {expected_name}/__init__.py fehlt."
                    )

                # Remove existing if force
                if target_path.exists() and force:
                    shutil.rmtree(target_path)

                # Ensure parent directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Extract files
                for member in names:
                    # Skip directories (they're created automatically)
                    if member.endswith('/'):
                        continue

                    # Get relative path within the plugin
                    if member.startswith(f'{expected_name}/'):
                        relative_path = member[len(expected_name) + 1:]
                        if relative_path:
                            dest_file = target_path / relative_path
                            dest_file.parent.mkdir(parents=True, exist_ok=True)

                            with zf.open(member) as src, open(dest_file, 'wb') as dst:
                                dst.write(src.read())

        except zipfile.BadZipFile as e:
            raise InvalidPluginArchiveError(f"Ungültiges ZIP-Archiv: {e}") from e

    def uninstall_plugin(self, name: str) -> bool:
        """Remove an installed plugin.

        Args:
            name: Plugin name to uninstall.

        Returns:
            True if plugin was removed, False if not installed.
        """
        plugin_path = self.get_plugin_path(name)

        if not plugin_path.exists():
            logger.warning(f"Plugin '{name}' not installed, nothing to remove")
            return False

        try:
            shutil.rmtree(plugin_path)
            logger.info(f"Plugin '{name}' uninstalled from {plugin_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to uninstall plugin '{name}': {e}")
            raise DownloaderError(f"Fehler beim Deinstallieren: {e}") from e

    def get_plugin_status(self, name: str) -> dict:
        """Get comprehensive status of a plugin.

        Args:
            name: Plugin name.

        Returns:
            Status dictionary with keys:
            - name: Plugin name
            - is_installed: Whether locally installed
            - is_licensed: Whether licensed (or free)
            - can_download: Whether download is allowed
            - marketplace_info: Plugin info from marketplace (if available)
        """
        marketplace_info = self.client.get_plugin_info(name)

        return {
            'name': name,
            'is_installed': self.is_plugin_installed(name),
            'is_licensed': self.client.can_download_plugin(name),
            'can_download': self.client.can_download_plugin(name),
            'marketplace_info': marketplace_info,
        }


# Singleton instance
_downloader_instance: PluginDownloader | None = None


def get_plugin_downloader() -> PluginDownloader:
    """Get the plugin downloader instance.

    Returns:
        PluginDownloader instance.
    """
    global _downloader_instance
    if _downloader_instance is None:
        _downloader_instance = PluginDownloader()
    return _downloader_instance
