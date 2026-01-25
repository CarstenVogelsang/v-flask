"""Bundle registry for managing v-flask bundles.

The BundleRegistry handles bundle discovery, registration, and activation.
Bundles can be registered manually or discovered via entry points.
"""

from __future__ import annotations

import importlib.metadata
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

    from v_flask.bundles.manifest import BundleManifest
    from v_flask.themes.registry import ThemeRegistry

logger = logging.getLogger(__name__)


class BundleRegistry:
    """Central registry for managing v-flask bundles.

    Bundles can be:
    1. Registered manually via register()
    2. Discovered via entry points (v_flask.bundles)

    Entry point example in pyproject.toml:
        [project.entry-points."v_flask.bundles"]
        mfr = "v_flask_bundles.mfr:MFRBundle"

    Example:
        registry = BundleRegistry(theme_registry)

        # Manual registration
        registry.register(MFRBundle())

        # Discover from entry points
        registry.discover_bundles()

        # Activate a bundle
        registry.activate('mfr', app)
    """

    def __init__(self, theme_registry: ThemeRegistry | None = None) -> None:
        """Initialize the bundle registry.

        Args:
            theme_registry: Optional ThemeRegistry for theme activation.
                           If not provided, a new one will be created.
        """
        self._bundles: dict[str, BundleManifest] = {}
        self._active_bundle: BundleManifest | None = None
        self._discovered = False

        # Import here to avoid circular imports
        if theme_registry is None:
            from v_flask.themes.registry import ThemeRegistry
            theme_registry = ThemeRegistry()
        self._theme_registry = theme_registry

    def register(self, bundle: BundleManifest) -> None:
        """Register a bundle manually.

        Args:
            bundle: BundleManifest instance to register.

        Raises:
            ValueError: If bundle validation fails.
        """
        bundle.validate()
        self._bundles[bundle.name] = bundle

        # Also register the bundle's theme if present
        theme = bundle.get_theme()
        if theme:
            self._theme_registry.register(theme)

        logger.debug(f"Registered bundle: {bundle}")

    def discover_bundles(self) -> list[BundleManifest]:
        """Discover installed bundles via entry points.

        Looks for entry points in the 'v_flask.bundles' group.

        Returns:
            List of discovered bundle instances.
        """
        if self._discovered:
            return list(self._bundles.values())

        try:
            eps = importlib.metadata.entry_points(group='v_flask.bundles')
            for ep in eps:
                try:
                    bundle_class = ep.load()
                    bundle = bundle_class()
                    bundle.validate()
                    self._bundles[bundle.name] = bundle

                    # Also register the bundle's theme
                    theme = bundle.get_theme()
                    if theme:
                        self._theme_registry.register(theme)

                    logger.info(f"Discovered bundle via entry point: {bundle}")
                except Exception as e:
                    logger.warning(f"Failed to load bundle '{ep.name}': {e}")
        except Exception as e:
            logger.debug(f"No entry points found for bundles: {e}")

        self._discovered = True
        return list(self._bundles.values())

    def get(self, name: str) -> BundleManifest | None:
        """Get a bundle by name.

        Args:
            name: Bundle name to look up.

        Returns:
            BundleManifest instance or None if not found.
        """
        self.discover_bundles()
        return self._bundles.get(name)

    def all(self) -> list[BundleManifest]:
        """Get all registered bundles.

        Returns:
            List of all registered BundleManifest instances.
        """
        self.discover_bundles()
        return list(self._bundles.values())

    def activate(
        self,
        name: str,
        app: Flask,
        plugin_registry: object | None = None
    ) -> BundleManifest:
        """Activate a bundle for the application.

        This method:
        1. Validates the bundle exists
        2. Checks that required plugins are registered
        3. Activates the bundle's theme (if present)
        4. Registers admin categories
        5. Calls bundle's on_activate hook

        Args:
            name: Name of the bundle to activate.
            app: Flask application instance.
            plugin_registry: Optional PluginRegistry for plugin checks.

        Returns:
            The activated bundle instance.

        Raises:
            ValueError: If bundle not found or required plugins missing.
        """
        bundle = self.get(name)
        if not bundle:
            available = ', '.join(self._bundles.keys()) or 'none'
            raise ValueError(
                f"Bundle '{name}' not found. Available bundles: {available}"
            )

        # Check required plugins
        if plugin_registry:
            self._check_required_plugins(bundle, plugin_registry)

        # Activate theme if present
        theme = bundle.get_theme()
        if theme:
            self._theme_registry.activate(theme.name, app)
            logger.info(f"Bundle '{name}' activated theme: {theme.name}")

        # Register admin categories
        self._register_admin_categories(app, bundle)

        # Call bundle's activation hook
        bundle.on_activate(app)

        self._active_bundle = bundle
        app.extensions['v_flask_bundle'] = bundle

        logger.info(f"Activated bundle: {bundle}")
        return bundle

    def _check_required_plugins(
        self,
        bundle: BundleManifest,
        plugin_registry: object
    ) -> None:
        """Check that all required plugins are registered.

        Args:
            bundle: Bundle to check plugins for.
            plugin_registry: PluginRegistry instance.

        Raises:
            ValueError: If required plugins are missing.
        """
        required = bundle.get_required_plugins()
        if not required:
            return

        # Get registered plugin names
        registered_names = set()
        if hasattr(plugin_registry, 'all'):
            for plugin in plugin_registry.all():
                registered_names.add(plugin.name)

        missing = [p for p in required if p not in registered_names]
        if missing:
            raise ValueError(
                f"Bundle '{bundle.name}' requires plugins that are not "
                f"registered: {', '.join(missing)}. "
                f"Please register these plugins before activating the bundle."
            )

    def _register_admin_categories(
        self,
        app: Flask,
        bundle: BundleManifest
    ) -> None:
        """Register bundle's admin categories.

        Args:
            app: Flask application instance.
            bundle: Bundle with categories to register.
        """
        categories = bundle.get_admin_categories()
        if not categories:
            return

        try:
            from v_flask.plugins.categories import register_category

            for cat_id, cat_config in categories.items():
                register_category(
                    cat_id,
                    cat_config.get('label', cat_id),
                    cat_config.get('icon', 'ti ti-folder'),
                    cat_config.get('order', 50)
                )
                logger.debug(f"Registered admin category: {cat_id}")
        except ImportError:
            logger.warning(
                "Could not import register_category, "
                "admin categories not registered"
            )

    @property
    def active_bundle(self) -> BundleManifest | None:
        """Get the currently active bundle.

        Returns:
            Active BundleManifest or None if no bundle is active.
        """
        return self._active_bundle

    @property
    def theme_registry(self) -> ThemeRegistry:
        """Get the theme registry.

        Returns:
            ThemeRegistry instance.
        """
        return self._theme_registry
