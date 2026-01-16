"""Plugin manager service for discovering, activating, and loading plugins."""

from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from v_flask.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginManagerError(Exception):
    """Base exception for plugin manager errors."""

    pass


class PluginNotFoundError(PluginManagerError):
    """Raised when a plugin is not found in the marketplace."""

    pass


class PluginNotInstalledError(PluginManagerError):
    """Raised when a plugin package is not installed."""

    pass


class DependencyNotActivatedError(PluginManagerError):
    """Raised when a required dependency plugin is not activated."""

    pass


class PluginManager:
    """Manages plugin discovery, activation, and loading.

    The PluginManager handles:
    - Reading available plugins from marketplace JSON
    - Activating/deactivating plugins (persists to DB)
    - Loading activated plugins at app startup
    - Tracking restart and migration requirements

    Usage:
        manager = PluginManager()

        # Get available plugins from marketplace
        available = manager.get_available_plugins()

        # Activate a plugin
        manager.activate_plugin('kontakt', user_id=1)

        # Check if restart is needed
        if manager.is_restart_required():
            # Show banner to admin

        # At app startup: load activated plugins
        manager.load_activated_plugins(registry)
    """

    # Default marketplace file location
    DEFAULT_MARKETPLACE_PATH = Path(__file__).parent.parent / 'data' / 'plugins_marketplace.json'

    def __init__(self, marketplace_file: Path | str | None = None):
        """Initialize the plugin manager.

        Args:
            marketplace_file: Path to the marketplace JSON file.
                             Defaults to v_flask/data/plugins_marketplace.json.
        """
        if marketplace_file:
            self.marketplace_file = Path(marketplace_file)
        else:
            self.marketplace_file = self.DEFAULT_MARKETPLACE_PATH

        self._marketplace_cache: list[dict] | None = None

    def get_available_plugins(self) -> list[dict]:
        """Return list of available plugins from marketplace JSON.

        Returns:
            List of plugin metadata dictionaries.
        """
        if self._marketplace_cache is not None:
            return self._marketplace_cache

        if not self.marketplace_file.exists():
            logger.warning(f"Marketplace file not found: {self.marketplace_file}")
            return []

        try:
            with open(self.marketplace_file, 'r', encoding='utf-8') as f:
                self._marketplace_cache = json.load(f)
                return self._marketplace_cache
        except json.JSONDecodeError as e:
            logger.error(f"Invalid marketplace JSON: {e}")
            return []

    def get_plugin_info(self, name: str) -> dict | None:
        """Get plugin info by name from marketplace.

        Args:
            name: The plugin name.

        Returns:
            Plugin metadata dictionary or None if not found.
        """
        for plugin in self.get_available_plugins():
            if plugin.get('name') == name:
                return plugin
        return None

    def is_plugin_installed(self, name: str) -> bool:
        """Check if a plugin package is installed.

        Args:
            name: The plugin name.

        Returns:
            True if the package can be imported.
        """
        info = self.get_plugin_info(name)
        if not info:
            return False

        package = info.get('package')
        if not package:
            return False

        try:
            importlib.import_module(package)
            return True
        except ImportError:
            return False

    def get_activated_plugin_names(self) -> list[str]:
        """Return list of activated plugin names from DB.

        Returns:
            List of plugin names that are currently active.
        """
        from v_flask.models import PluginActivation
        return PluginActivation.get_active_plugins()

    def get_plugins_with_status(self) -> list[dict]:
        """Return available plugins with their activation status.

        Returns:
            List of plugin dicts with added 'is_active' and 'is_installed' fields.
        """
        activated = set(self.get_activated_plugin_names())
        result = []

        for plugin in self.get_available_plugins():
            plugin_copy = plugin.copy()
            plugin_copy['is_active'] = plugin['name'] in activated
            plugin_copy['is_installed'] = self.is_plugin_installed(plugin['name'])
            result.append(plugin_copy)

        return result

    def _check_dependencies(self, name: str) -> None:
        """Check if all plugin dependencies are activated.

        Args:
            name: The plugin name to check dependencies for.

        Raises:
            DependencyNotActivatedError: If a dependency is not activated.
        """
        info = self.get_plugin_info(name)
        if not info:
            return  # Already validated in activate_plugin

        dependencies = info.get('dependencies', [])
        if not dependencies:
            return  # No dependencies to check

        activated = set(self.get_activated_plugin_names())

        for dep in dependencies:
            if dep not in activated:
                raise DependencyNotActivatedError(
                    f"Plugin '{name}' benötigt '{dep}', aber '{dep}' ist nicht aktiviert. "
                    f"Bitte aktiviere zuerst '{dep}'."
                )

    def activate_plugin(self, name: str, user_id: int | None = None) -> bool:
        """Activate a plugin.

        This method:
        1. Validates the plugin exists in marketplace
        2. Validates the plugin package is installed
        3. Validates all dependencies are activated
        4. Creates/updates PluginActivation record
        5. Sets restart_required flag
        6. Adds to migrations_pending list

        Args:
            name: The plugin name to activate.
            user_id: Optional user ID who is activating.

        Returns:
            True if activation was successful.

        Raises:
            PluginNotFoundError: If plugin is not in marketplace.
            PluginNotInstalledError: If plugin package is not installed.
            DependencyNotActivatedError: If a dependency is not activated.
        """
        from v_flask.models import PluginActivation, SystemStatus

        # Validate plugin exists
        info = self.get_plugin_info(name)
        if not info:
            raise PluginNotFoundError(f"Plugin '{name}' not found in marketplace")

        # Validate plugin is installed
        if not self.is_plugin_installed(name):
            raise PluginNotInstalledError(
                f"Plugin '{name}' package not installed: {info.get('package')}"
            )

        # Validate dependencies are activated
        self._check_dependencies(name)

        # Activate in database
        PluginActivation.activate(name, user_id=user_id)

        # Set restart required
        SystemStatus.set_bool(SystemStatus.KEY_RESTART_REQUIRED, True)

        # Add to pending migrations
        SystemStatus.add_to_list(SystemStatus.KEY_MIGRATIONS_PENDING, name)

        logger.info(f"Plugin '{name}' activated by user {user_id}")
        return True

    def deactivate_plugin(self, name: str) -> bool:
        """Deactivate a plugin.

        Args:
            name: The plugin name to deactivate.

        Returns:
            True if deactivation was successful.
        """
        from v_flask.models import PluginActivation, SystemStatus

        activation = PluginActivation.deactivate(name)
        if activation:
            # Set restart required
            SystemStatus.set_bool(SystemStatus.KEY_RESTART_REQUIRED, True)
            logger.info(f"Plugin '{name}' deactivated")
            return True

        return False

    def load_activated_plugins(self, registry: PluginRegistry) -> list[str]:
        """Load all activated plugins into the registry.

        This method is called at app startup to dynamically load
        plugins that have been activated via the admin interface.

        Args:
            registry: The PluginRegistry to register plugins with.

        Returns:
            List of plugin names that were successfully loaded.
        """
        loaded = []
        activated = self.get_activated_plugin_names()

        for name in activated:
            info = self.get_plugin_info(name)
            if not info:
                logger.warning(f"Activated plugin '{name}' not found in marketplace")
                continue

            package = info.get('package')
            class_name = info.get('class')

            if not package or not class_name:
                logger.warning(f"Plugin '{name}' missing package or class in marketplace")
                continue

            try:
                # Import the plugin module
                module = importlib.import_module(package)

                # Get the plugin class
                plugin_class = getattr(module, class_name)

                # Instantiate and register
                plugin_instance = plugin_class()
                registry.register(plugin_instance)

                loaded.append(name)
                logger.info(f"Loaded activated plugin: {name}")

            except ImportError as e:
                logger.error(f"Failed to import plugin '{name}': {e}")
            except AttributeError as e:
                logger.error(f"Plugin class '{class_name}' not found in '{package}': {e}")
            except Exception as e:
                logger.error(f"Failed to load plugin '{name}': {e}")

        return loaded

    def is_restart_required(self) -> bool:
        """Check if a server restart is required.

        Returns:
            True if restart is required.
        """
        from v_flask.models import SystemStatus
        return SystemStatus.get_bool(SystemStatus.KEY_RESTART_REQUIRED)

    def mark_restart_complete(self) -> None:
        """Clear the restart_required flag.

        Call this after the server has been restarted.
        """
        from v_flask.models import SystemStatus
        SystemStatus.set_bool(SystemStatus.KEY_RESTART_REQUIRED, False)

    def get_pending_migrations(self) -> list[str]:
        """Get list of plugins with pending migrations.

        Returns:
            List of plugin names needing migration.
        """
        from v_flask.models import SystemStatus
        return SystemStatus.get_list(SystemStatus.KEY_MIGRATIONS_PENDING)

    def clear_pending_migration(self, name: str) -> None:
        """Clear a plugin from pending migrations.

        Args:
            name: The plugin name to clear.
        """
        from v_flask.models import SystemStatus
        SystemStatus.remove_from_list(SystemStatus.KEY_MIGRATIONS_PENDING, name)

    def clear_all_pending_migrations(self) -> None:
        """Clear all pending migrations."""
        from v_flask.models import SystemStatus
        SystemStatus.delete(SystemStatus.KEY_MIGRATIONS_PENDING)

    def refresh_marketplace(self) -> None:
        """Refresh the marketplace cache by re-reading the JSON file."""
        self._marketplace_cache = None
        self.get_available_plugins()
