"""Bundle manifest base class for v-flask bundles.

A bundle combines a theme with a set of plugins for a complete starter kit.
This allows projects to activate a preconfigured combination of visual design
(theme) and functionality (plugins) with a single configuration.

Example:
    class MFRBundle(BundleManifest):
        name = 'mfr'
        version = '1.0.0'
        description = 'Manufacturer B2B Portal Bundle'
        theme = MFRTailwindTheme  # or instance
        required_plugins = ['crm']
        recommended_plugins = ['pim', 'pricing', 'kontakt']
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flask import Flask

    from v_flask.themes.manifest import ThemeManifest


class BundleManifest(ABC):
    """Base class for v-flask bundle definitions.

    Bundles must subclass this and provide:
        - name: Unique bundle identifier (e.g., 'mfr', 'verzeichnis')
        - version: Semantic version string (e.g., '1.0.0')
        - description: Short description of the bundle

    Optional attributes:
        - theme: ThemeManifest class or instance for this bundle
        - required_plugins: List of plugin names that must be installed
        - recommended_plugins: List of plugin names suggested for this bundle
        - plugins: Additional plugins to activate by default
        - admin_categories: Additional admin sidebar categories
        - config_presets: Default configuration values

    Optional method overrides:
        - get_theme(): Return the theme instance
        - on_activate(app): Called when bundle is activated
    """

    # Required attributes (must be overridden)
    name: str
    version: str
    description: str

    # Theme configuration (class or instance)
    theme: type[ThemeManifest] | ThemeManifest | None = None

    # Plugin configuration
    required_plugins: list[str] = []     # Must be installed and registered
    recommended_plugins: list[str] = []  # Suggested but optional
    plugins: list[str] = []              # Additional plugins to activate

    # Additional metadata
    author: str = ''
    homepage: str = ''
    license: str = ''
    tags: list[str] = []

    # Admin UI customization
    # Categories for the admin sidebar menu
    # Format: {'category_id': {'label': 'Label', 'icon': 'ti ti-icon', 'order': 10}}
    admin_categories: dict[str, dict] = {}

    # Configuration presets
    # Default values that can be applied during bundle activation
    config_presets: dict[str, Any] = {}

    def get_theme(self) -> ThemeManifest | None:
        """Return the theme instance for this bundle.

        If theme is a class, instantiate it. If already an instance,
        return it directly.

        Returns:
            ThemeManifest instance or None if no theme.
        """
        if self.theme is None:
            return None
        if isinstance(self.theme, type):
            return self.theme()
        return self.theme

    def get_required_plugins(self) -> list[str]:
        """Return list of required plugin names.

        These plugins must be installed and registered for the bundle
        to work correctly.

        Returns:
            List of plugin names.
        """
        return list(self.required_plugins)

    def get_recommended_plugins(self) -> list[str]:
        """Return list of recommended plugin names.

        These plugins are suggested for the best experience but
        are not strictly required.

        Returns:
            List of plugin names.
        """
        return list(self.recommended_plugins)

    def get_all_plugins(self) -> list[str]:
        """Return all plugins (required + recommended + explicit).

        Returns:
            List of all plugin names associated with this bundle.
        """
        all_plugins = set(self.required_plugins)
        all_plugins.update(self.recommended_plugins)
        all_plugins.update(self.plugins)
        return list(all_plugins)

    def get_admin_categories(self) -> dict[str, dict]:
        """Return additional admin categories to register.

        Categories are groups in the admin sidebar menu.
        Standard categories: core, directory, content, legal,
        communication, marketing, users, analytics, ecommerce, system

        Returns:
            Dict mapping category_id to category config.

        Example:
            def get_admin_categories(self):
                return {
                    'b2b': {
                        'label': 'B2B / Händler',
                        'icon': 'ti ti-building-store',
                        'order': 15,
                    },
                }
        """
        return dict(self.admin_categories)

    def get_config_presets(self) -> dict[str, Any]:
        """Return configuration presets for this bundle.

        These are suggested default values that can be applied
        during bundle activation or via admin UI.

        Returns:
            Dict of config key to default value.

        Example:
            def get_config_presets(self):
                return {
                    'SITE_NAME': 'Manufacturer Portal',
                    'CRM_CUSTOMER_TYPE': 'dealer',
                }
        """
        return dict(self.config_presets)

    def on_activate(self, app: Flask) -> None:
        """Called when the bundle is activated.

        Use for:
        - Registering additional admin categories
        - Applying configuration presets
        - Setting up bundle-specific services
        - Logging bundle activation

        Args:
            app: The Flask application instance.

        Example:
            def on_activate(self, app):
                # Register custom admin categories
                from v_flask.plugins.categories import register_category
                for cat_id, cat_config in self.get_admin_categories().items():
                    register_category(
                        cat_id,
                        cat_config['label'],
                        cat_config['icon'],
                        cat_config.get('order', 50)
                    )
                app.logger.info(f'Bundle {self.name} activated')
        """
        pass

    def validate(self) -> None:
        """Validate that required attributes are set.

        Raises:
            ValueError: If required attributes are missing.
        """
        required = ['name', 'version', 'description']
        for attr in required:
            if not hasattr(self, attr) or not getattr(self, attr):
                raise ValueError(f"Bundle class must define '{attr}' attribute")

    def to_dict(self) -> dict:
        """Return bundle metadata as dictionary.

        Returns:
            Dictionary with bundle metadata suitable for JSON serialization.
        """
        theme = self.get_theme()
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'homepage': self.homepage,
            'license': self.license,
            'tags': self.tags,
            'theme': theme.name if theme else None,
            'required_plugins': self.get_required_plugins(),
            'recommended_plugins': self.get_recommended_plugins(),
            'admin_categories': list(self.get_admin_categories().keys()),
        }

    def __repr__(self) -> str:
        theme = self.get_theme()
        theme_info = f", theme={theme.name}" if theme else ""
        return f'<Bundle {self.name}@{self.version}{theme_info}>'
