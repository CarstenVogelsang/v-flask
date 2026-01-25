"""Theme registry for managing v-flask themes.

The ThemeRegistry handles theme discovery, registration, and initialization.
Themes can be registered manually or discovered via entry points.
"""

from __future__ import annotations

import importlib.metadata
import logging
from typing import TYPE_CHECKING

from jinja2 import ChoiceLoader, FileSystemLoader

if TYPE_CHECKING:
    from flask import Flask

    from v_flask.themes.manifest import ThemeManifest

logger = logging.getLogger(__name__)


class ThemeRegistry:
    """Central registry for managing v-flask themes.

    Themes can be:
    1. Registered manually via register()
    2. Discovered via entry points (v_flask.themes)

    Entry point example in pyproject.toml:
        [project.entry-points."v_flask.themes"]
        my-theme = "my_package.themes:MyTheme"

    Example:
        registry = ThemeRegistry()

        # Manual registration
        registry.register(MyTheme())

        # Discover from entry points
        registry.discover_themes()

        # Activate a theme
        registry.activate('my-theme', app)
    """

    def __init__(self) -> None:
        self._themes: dict[str, ThemeManifest] = {}
        self._active_theme: ThemeManifest | None = None
        self._discovered = False

    def register(self, theme: ThemeManifest) -> None:
        """Register a theme manually.

        Args:
            theme: ThemeManifest instance to register.

        Raises:
            ValueError: If theme validation fails.
        """
        theme.validate()
        self._themes[theme.name] = theme
        logger.debug(f"Registered theme: {theme}")

    def discover_themes(self) -> list[ThemeManifest]:
        """Discover installed themes via entry points.

        Looks for entry points in the 'v_flask.themes' group.

        Returns:
            List of discovered theme instances.
        """
        if self._discovered:
            return list(self._themes.values())

        try:
            eps = importlib.metadata.entry_points(group='v_flask.themes')
            for ep in eps:
                try:
                    theme_class = ep.load()
                    theme = theme_class()
                    theme.validate()
                    self._themes[theme.name] = theme
                    logger.info(f"Discovered theme via entry point: {theme}")
                except Exception as e:
                    logger.warning(f"Failed to load theme '{ep.name}': {e}")
        except Exception as e:
            logger.debug(f"No entry points found for themes: {e}")

        self._discovered = True
        return list(self._themes.values())

    def get(self, name: str) -> ThemeManifest | None:
        """Get a theme by name.

        Args:
            name: Theme name to look up.

        Returns:
            ThemeManifest instance or None if not found.
        """
        self.discover_themes()
        return self._themes.get(name)

    def all(self) -> list[ThemeManifest]:
        """Get all registered themes.

        Returns:
            List of all registered ThemeManifest instances.
        """
        self.discover_themes()
        return list(self._themes.values())

    def activate(self, name: str, app: Flask) -> ThemeManifest:
        """Activate a theme for the application.

        This method:
        1. Validates the theme exists
        2. Registers theme templates with Jinja2 (high priority)
        3. Registers theme static files as a Blueprint
        4. Adds theme context processor
        5. Calls theme's on_init hook

        Args:
            name: Name of the theme to activate.
            app: Flask application instance.

        Returns:
            The activated theme instance.

        Raises:
            ValueError: If theme not found.
        """
        theme = self.get(name)
        if not theme:
            available = ', '.join(self._themes.keys()) or 'none'
            raise ValueError(
                f"Theme '{name}' not found. Available themes: {available}"
            )

        # Register theme templates
        self._register_templates(app, theme)

        # Register theme static files
        self._register_static(app, theme)

        # Add theme context processor
        self._register_context_processor(app, theme)

        # Call theme's init hook
        theme.on_init(app)

        self._active_theme = theme
        app.extensions['v_flask_theme'] = theme

        logger.info(f"Activated theme: {theme}")
        return theme

    def _register_templates(self, app: Flask, theme: ThemeManifest) -> None:
        """Register theme templates with Jinja2.

        Theme templates are inserted with high priority (after app templates,
        before v-flask core templates) to allow themes to override defaults
        while still being overridable by the host app.

        Args:
            app: Flask application instance.
            theme: Theme to register templates for.
        """
        template_folder = theme.get_template_folder()
        if not template_folder:
            return

        theme_loader = FileSystemLoader(str(template_folder))

        if app.jinja_loader is None:
            app.jinja_loader = theme_loader
        elif isinstance(app.jinja_loader, ChoiceLoader):
            # Insert after app templates (index 0) but before plugins/v-flask
            # Position 1 gives theme high priority
            app.jinja_loader.loaders.insert(1, theme_loader)
        else:
            # Existing loader is app's, create ChoiceLoader
            app.jinja_loader = ChoiceLoader([
                app.jinja_loader,
                theme_loader,
            ])

        logger.debug(f"Registered theme templates from: {template_folder}")

    def _register_static(self, app: Flask, theme: ThemeManifest) -> None:
        """Register theme static files as a Blueprint.

        Static files are accessible at /static/theme/{theme_name}/.

        Args:
            app: Flask application instance.
            theme: Theme to register static files for.
        """
        static_folder = theme.get_static_folder()
        if not static_folder:
            return

        from flask import Blueprint

        static_bp = Blueprint(
            f'theme_{theme.name}_static',
            theme.name,
            static_folder=str(static_folder),
            static_url_path=f'/static/theme/{theme.name}'
        )
        app.register_blueprint(static_bp)

        logger.debug(f"Registered theme static files from: {static_folder}")

    def _register_context_processor(
        self, app: Flask, theme: ThemeManifest
    ) -> None:
        """Add theme context processor for templates.

        Provides:
        - active_theme: The active ThemeManifest instance
        - theme_head_includes: HTML for <head>
        - theme_body_end_includes: HTML for before </body>
        - theme_css_framework: CSS framework name

        Args:
            app: Flask application instance.
            theme: Active theme.
        """
        @app.context_processor
        def theme_context() -> dict:
            return {
                'active_theme': theme,
                'theme_head_includes': theme.get_head_includes(),
                'theme_body_end_includes': theme.get_body_end_includes(),
                'theme_css_framework': theme.css_framework,
                'theme_supports_dark_mode': theme.supports_dark_mode,
                'theme_component_macros': theme.get_component_macros(),
            }

    @property
    def active_theme(self) -> ThemeManifest | None:
        """Get the currently active theme.

        Returns:
            Active ThemeManifest or None if no theme is active.
        """
        return self._active_theme
