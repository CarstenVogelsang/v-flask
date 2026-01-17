"""Plugin system for v-flask.

This module provides a plugin architecture for extending v-flask applications
with reusable components including models, routes, templates, and CLI commands.

Usage:
    from v_flask.plugins import PluginManifest, PluginRegistry

    class MyPlugin(PluginManifest):
        name = 'my-plugin'
        version = '1.0.0'
        description = 'My awesome plugin'

        def get_models(self):
            from .models import MyModel
            return [MyModel]

        def get_blueprints(self):
            from .routes import my_bp
            return [(my_bp, '/my-plugin')]
"""

from v_flask.plugins.manifest import PluginManifest
from v_flask.plugins.registry import PluginRegistry
from v_flask.plugins.manager import PluginManager, PluginManagerError, PluginNotFoundError, PluginNotInstalledError
from v_flask.plugins.restart import RestartManager, RestartError
from v_flask.plugins.slots import PluginSlotManager
from v_flask.plugins.marketplace_client import (
    MarketplaceClient,
    MarketplaceError,
    MarketplaceConnectionError,
    MarketplaceAuthError,
    PluginNotLicensedError,
    get_marketplace_client,
    init_marketplace_client,
)
from v_flask.plugins.downloader import (
    PluginDownloader,
    DownloaderError,
    PluginAlreadyInstalledError,
    InvalidPluginArchiveError,
    get_plugin_downloader,
)

__all__ = [
    # Core plugin system
    'PluginManifest',
    'PluginRegistry',
    'PluginManager',
    'PluginManagerError',
    'PluginNotFoundError',
    'PluginNotInstalledError',
    'PluginSlotManager',
    'RestartManager',
    'RestartError',
    # Marketplace client
    'MarketplaceClient',
    'MarketplaceError',
    'MarketplaceConnectionError',
    'MarketplaceAuthError',
    'PluginNotLicensedError',
    'get_marketplace_client',
    'init_marketplace_client',
    # Plugin downloader
    'PluginDownloader',
    'DownloaderError',
    'PluginAlreadyInstalledError',
    'InvalidPluginArchiveError',
    'get_plugin_downloader',
]
