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

    def _get_installed_plugins(self) -> list[dict]:
        """Get list of locally installed plugins with their metadata.

        Scans both:
        1. Local plugins directory (downloaded from marketplace)
        2. v_flask_plugins Python package (bundled with v-flask)

        Returns:
            List of plugin metadata dictionaries.
        """
        import pkgutil

        plugins = []
        seen_names = set()

        # 1. Check local plugins directory (downloaded from marketplace)
        try:
            from v_flask.plugins.downloader import get_plugin_downloader
            downloader = get_plugin_downloader()
            for name in downloader.get_installed_plugins():
                if name not in seen_names:
                    info = self._load_plugin_metadata(name)
                    if info:
                        plugins.append(info)
                        seen_names.add(name)
        except Exception as e:
            logger.debug(f"Could not check local plugins directory: {e}")

        # 2. Check v_flask_plugins Python package (bundled with v-flask)
        try:
            import v_flask_plugins

            package_path = getattr(v_flask_plugins, '__path__', None)
            if package_path:
                for importer, name, is_pkg in pkgutil.iter_modules(package_path):
                    if is_pkg and name not in seen_names:
                        info = self._load_plugin_metadata(name)
                        if info:
                            plugins.append(info)
                            seen_names.add(name)
        except ImportError:
            logger.debug("v_flask_plugins package not installed")
        except Exception as e:
            logger.warning(f"Could not scan v_flask_plugins package: {e}")

        return plugins

    def _load_plugin_metadata(self, name: str) -> dict | None:
        """Load plugin metadata from an installed plugin module.

        Args:
            name: The plugin name.

        Returns:
            Plugin metadata dictionary or None if not loadable.
        """
        # Try common package patterns
        package_patterns = [
            f"v_flask_plugins.{name}",
            f"v_flask_plugins_{name}",
        ]

        for package in package_patterns:
            try:
                module = importlib.import_module(package)

                # Try to get metadata from plugin class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        hasattr(attr, 'name') and
                        hasattr(attr, 'version')):
                        try:
                            # Instantiate to get metadata
                            instance = attr()
                            return {
                                'name': getattr(instance, 'name', name),
                                'version': getattr(instance, 'version', '0.0.0'),
                                'description': getattr(instance, 'description', ''),
                                'dependencies': getattr(instance, 'dependencies', []),
                                'package': package,
                                'class': attr_name,
                            }
                        except Exception:
                            continue

                # Fallback: minimal metadata
                return {
                    'name': name,
                    'version': getattr(module, '__version__', '0.0.0'),
                    'description': getattr(module, '__doc__', '') or '',
                    'dependencies': [],
                    'package': package,
                }

            except ImportError:
                continue

        return None

    def get_merged_plugin_list(self) -> tuple[list[dict], bool]:
        """Get merged list of installed + marketplace plugins.

        Combines locally installed plugins with available plugins from
        the remote marketplace. Used for the unified plugin admin view.

        Caching behavior:
        - When marketplace is ONLINE: Fetch fresh data, update local cache
        - When marketplace is OFFLINE: Use cached data for installed plugins only
        - Non-installed plugins are NOT cached (only shown when online)

        Returns:
            Tuple of (plugin_list, marketplace_available)
            - plugin_list: Merged list with status for each plugin
            - marketplace_available: True if marketplace was reachable
        """
        from pathlib import Path
        from flask import current_app
        from v_flask.plugins.plugin_cache import PluginMetaCache

        installed = self._get_installed_plugins()
        activated = set(self.get_activated_plugin_names())
        installed_names = {p['name'] for p in installed}

        # Initialize cache for installed plugins
        cache = PluginMetaCache(Path(current_app.instance_path))

        # Try to get marketplace plugins
        marketplace_available = False
        remote_plugins = []
        try:
            from v_flask.plugins.marketplace_client import get_marketplace_client
            client = get_marketplace_client()
            if client.is_configured:
                remote_plugins = client.get_available_plugins()
                # Only mark as available if we actually got data
                # (empty list means API failed or returned no plugins)
                if remote_plugins:
                    marketplace_available = True

                    # Update cache for installed plugins (only when online)
                    installed_remote = [
                        p for p in remote_plugins
                        if p.get('name') in installed_names
                    ]
                    if installed_remote:
                        cache.update_batch(installed_remote)
                        logger.debug(f"Updated cache for {len(installed_remote)} installed plugins")
                else:
                    logger.warning("Marketplace returned empty plugin list")
        except Exception as e:
            logger.debug(f"Marketplace not available: {e}")

        # Merge: Installed plugins first, then marketplace-only
        result = []
        seen_names = set()

        # 1. Installed plugins (with marketplace info OR cached info)
        for plugin in installed:
            name = plugin['name']
            seen_names.add(name)

            if marketplace_available:
                # Use fresh marketplace data
                marketplace_info = next(
                    (p for p in remote_plugins if p.get('name') == name),
                    {}
                )
            else:
                # Fallback: Use cached data
                marketplace_info = cache.get(name) or {}

            result.append({
                **plugin,  # Base data (name, version, description, dependencies)
                'icon': marketplace_info.get('icon', 'ti ti-puzzle'),
                'categories': marketplace_info.get('categories', []),
                'category_info': marketplace_info.get('category_info'),
                'phase_badge': marketplace_info.get('phase_badge'),
                'price_cents': marketplace_info.get('price_cents'),
                'price_display': marketplace_info.get('price_display'),
                'is_free': marketplace_info.get('is_free', True),
                'is_installed': True,
                'is_active': name in activated,
                'status': 'active' if name in activated else 'inactive',
            })

        # 2. Marketplace-only plugins (ONLY when online - no caching!)
        if marketplace_available:
            for plugin in remote_plugins:
                name = plugin.get('name')
                if name and name not in seen_names:
                    result.append({
                        **plugin,
                        'is_installed': False,
                        'is_active': False,
                        'status': 'installable',
                    })

        return result, marketplace_available

    def _resolve_dependency_order(self, name: str) -> list[str]:
        """Resolve dependencies and return activation order.

        Uses topological sort (depth-first) to determine the order
        in which plugins must be activated.

        Args:
            name: The target plugin name.

        Returns:
            List of plugin names in activation order (dependencies first).
        """
        order = []
        visited = set()

        def visit(plugin_name: str) -> None:
            if plugin_name in visited:
                return
            visited.add(plugin_name)

            # Get plugin info (from marketplace or installed)
            info = self.get_plugin_info(plugin_name)
            if not info:
                # Try from installed plugins
                info = self._load_plugin_metadata(plugin_name)

            if info:
                for dep in info.get('dependencies', []):
                    visit(dep)

            order.append(plugin_name)

        visit(name)
        return order

    def activate_with_dependencies(
        self, name: str, user_id: int | None = None
    ) -> list[str]:
        """Activate a plugin and all its dependencies.

        Automatically resolves and activates all required dependencies
        in the correct order before activating the target plugin.

        Args:
            name: The plugin name to activate.
            user_id: Optional user ID who is activating.

        Returns:
            List of plugin names that were activated (in order).

        Raises:
            PluginNotInstalledError: If plugin or dependency is not installed.
        """
        activation_order = self._resolve_dependency_order(name)
        activated = []
        already_active = set(self.get_activated_plugin_names())

        for plugin_name in activation_order:
            if plugin_name not in already_active:
                # Use internal activation (skips dependency check since we handle it)
                self._activate_single(plugin_name, user_id)
                activated.append(plugin_name)

        return activated

    def _activate_single(self, name: str, user_id: int | None = None) -> bool:
        """Activate a single plugin without checking dependencies.

        Internal method used by activate_with_dependencies().

        Args:
            name: The plugin name to activate.
            user_id: Optional user ID who is activating.

        Returns:
            True if activation was successful.

        Raises:
            PluginNotFoundError: If plugin is not in marketplace.
            PluginNotInstalledError: If plugin package is not installed.
        """
        from v_flask.models import PluginActivation, SystemStatus

        # Validate plugin is installed
        if not self.is_plugin_installed(name):
            # Try to get info for better error message
            info = self.get_plugin_info(name) or self._load_plugin_metadata(name)
            package = info.get('package', f'v_flask_plugins.{name}') if info else f'v_flask_plugins.{name}'
            raise PluginNotInstalledError(
                f"Plugin '{name}' package not installed: {package}"
            )

        # Activate in database
        PluginActivation.activate(name, user_id=user_id)

        # Set restart required
        SystemStatus.set_bool(SystemStatus.KEY_RESTART_REQUIRED, True)

        # Add to pending migrations
        SystemStatus.add_to_list(SystemStatus.KEY_MIGRATIONS_PENDING, name)

        logger.info(f"Plugin '{name}' activated by user {user_id}")
        return True

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
