"""Theme manifest base class for v-flask themes.

Themes provide base templates and CSS frameworks for v-flask applications.
A theme defines the visual foundation (CSS framework, base templates, static assets)
that can be combined with plugins via bundles.

Example:
    class TailwindTheme(ThemeManifest):
        name = 'tailwind-modern'
        version = '1.0.0'
        description = 'Modern Tailwind CSS theme with DaisyUI'
        css_framework = 'tailwind'

        def get_template_folder(self):
            return Path(__file__).parent / 'templates'

        def get_head_includes(self):
            return [
                '<link href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css" rel="stylesheet">',
                '<script src="https://cdn.tailwindcss.com"></script>',
            ]
"""

from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


class ThemeManifest(ABC):
    """Base class for v-flask theme definitions.

    Themes must subclass this and provide:
        - name: Unique theme identifier (e.g., 'tailwind-modern', 'bootstrap-admin')
        - version: Semantic version string (e.g., '1.0.0')
        - description: Short description of the theme
        - css_framework: CSS framework identifier ('tailwind', 'bootstrap', 'bulma', 'custom')

    Optional attributes:
        - author: Theme author name
        - supports_dark_mode: Whether the theme supports dark mode toggle
        - color_schemes: Predefined color schemes as dict

    Optional method overrides:
        - get_template_folder(): Return path to theme templates
        - get_static_folder(): Return path to theme static files
        - get_head_includes(): Return HTML fragments for <head>
        - get_body_end_includes(): Return HTML fragments before </body>
        - on_init(app): Called when theme is initialized
    """

    # Required attributes (must be overridden)
    name: str
    version: str
    description: str
    css_framework: str  # 'tailwind', 'bootstrap', 'bulma', 'custom'

    # Optional attributes
    author: str = ''
    supports_dark_mode: bool = False
    color_schemes: dict[str, dict] = {}

    # Template paths relative to theme folder
    public_base_template: str = 'base.html'
    admin_base_template: str = 'admin/base.html'

    def get_template_folder(self) -> Path | str | None:
        """Return path to theme templates folder.

        Templates in this folder override v-flask defaults but can be
        overridden by the host application. Structure should mirror
        v-flask templates:

            templates/
                base.html           # Public base template
                admin/
                    base.html       # Admin base template
                components/         # Reusable template components/macros

        Returns:
            Path to templates folder, or None if no templates.
        """
        return None

    def get_static_folder(self) -> Path | str | None:
        """Return path to theme static files folder.

        Static files will be accessible under '/static/theme/{theme_name}/'.

        Returns:
            Path to static folder, or None if no static files.
        """
        return None

    def get_head_includes(self) -> list[str]:
        """Return HTML fragments to include in <head>.

        Use for:
        - CSS framework CDN links
        - Custom fonts (Google Fonts, etc.)
        - Meta tags specific to the theme
        - Inline critical CSS

        Returns:
            List of safe HTML strings to include in <head>.

        Example:
            def get_head_includes(self):
                return [
                    '<link href="https://cdn.tailwindcss.com" rel="stylesheet">',
                    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
                ]
        """
        return []

    def get_body_end_includes(self) -> list[str]:
        """Return HTML fragments to include before </body>.

        Use for:
        - JavaScript libraries loaded at end
        - Analytics scripts
        - Theme-specific JS initialization

        Returns:
            List of safe HTML strings to include before </body>.

        Example:
            def get_body_end_includes(self):
                return [
                    '<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>',
                ]
        """
        return []

    def get_component_macros(self) -> dict[str, str]:
        """Return mapping of component names to macro template paths.

        Allows themes to provide different implementations of UI components.
        Plugins and apps can use these macros for consistent styling.

        Returns:
            Dict mapping component name to template path.

        Example:
            def get_component_macros(self):
                return {
                    'button': 'components/button.html',
                    'card': 'components/card.html',
                    'form_field': 'components/form_field.html',
                }
        """
        return {}

    def on_init(self, app: Flask) -> None:
        """Called when the theme is initialized with the Flask app.

        Use for:
        - Registering Jinja2 globals or filters specific to the theme
        - Setting up theme-specific context processors
        - Configuring theme settings from app.config

        Args:
            app: The Flask application instance.

        Example:
            def on_init(self, app):
                @app.context_processor
                def theme_context():
                    return {
                        'theme_name': self.name,
                        'theme_supports_dark_mode': self.supports_dark_mode,
                    }
        """
        pass

    def validate(self) -> None:
        """Validate that required attributes are set.

        Raises:
            ValueError: If required attributes are missing or invalid.
        """
        required = ['name', 'version', 'description', 'css_framework']
        for attr in required:
            if not hasattr(self, attr) or not getattr(self, attr):
                raise ValueError(f"Theme class must define '{attr}' attribute")

        valid_frameworks = ['tailwind', 'bootstrap', 'bulma', 'custom']
        if self.css_framework not in valid_frameworks:
            raise ValueError(
                f"css_framework must be one of {valid_frameworks}, "
                f"got '{self.css_framework}'"
            )

    def to_dict(self) -> dict:
        """Return theme metadata as dictionary.

        Returns:
            Dictionary with theme metadata suitable for JSON serialization.
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'css_framework': self.css_framework,
            'author': self.author,
            'supports_dark_mode': self.supports_dark_mode,
            'color_schemes': list(self.color_schemes.keys()),
        }

    def __repr__(self) -> str:
        return f'<Theme {self.name}@{self.version} ({self.css_framework})>'
