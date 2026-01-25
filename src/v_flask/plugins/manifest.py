"""Plugin manifest base class.

The PluginManifest class defines the interface for v-flask plugins.
Plugins must inherit from this class and override the required attributes
and optionally implement the component methods.
"""

from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flask import Blueprint, Flask


class PluginManifest(ABC):
    """Base class for v-flask plugin definitions.

    Plugins must subclass this and provide:
        - name: Unique plugin identifier (e.g., 'kontakt', 'auth')
        - version: Semantic version string (e.g., '1.0.0')
        - description: Short description of the plugin (1-2 sentences)
        - author: Plugin author name

    Optional attributes:
        - dependencies: List of plugin names this plugin depends on
        - long_description: Extended description (Markdown supported)
        - homepage: Plugin homepage URL
        - repository: Git repository URL
        - license: License identifier (e.g., 'MIT', 'Apache-2.0')
        - categories: Categories for filtering (e.g., ['forms', 'communication'])
        - tags: Tags for search
        - min_v_flask_version: Minimum required v-flask version
        - screenshots: Relative paths to screenshot images

    Optional method overrides:
        - get_models(): Return list of SQLAlchemy model classes
        - get_blueprints(): Return list of (Blueprint, url_prefix) tuples
        - get_cli_commands(): Return list of Click command groups
        - get_template_folder(): Return path to plugin templates
        - get_static_folder(): Return path to plugin static files
        - get_readme(): Return README content as Markdown string
        - on_init(app): Called when plugin is initialized with the Flask app

    Example:
        class KontaktPlugin(PluginManifest):
            name = 'kontakt'
            version = '1.0.0'
            description = 'Contact form with email notifications'
            author = 'v-flask'

            def get_models(self):
                from .models import KontaktAnfrage
                return [KontaktAnfrage]

            def get_blueprints(self):
                from .routes import kontakt_bp, kontakt_admin_bp
                return [
                    (kontakt_bp, '/kontakt'),
                    (kontakt_admin_bp, '/admin/kontakt'),
                ]
    """

    # Required attributes (must be overridden)
    name: str
    version: str
    description: str  # Short description (1-2 sentences)
    author: str

    # Optional: List of plugin names this plugin depends on
    dependencies: list[str] = []

    # Optional: Marketplace metadata (for plugin discovery and documentation)
    long_description: str = ''       # Extended description (Markdown supported)
    homepage: str = ''               # Plugin homepage URL
    repository: str = ''             # Git repository URL
    license: str = ''                # License identifier (e.g., 'MIT', 'Apache-2.0')
    categories: list[str] = []       # Categories for filtering (e.g., ['forms', 'communication'])
    tags: list[str] = []             # Tags for search
    min_v_flask_version: str = ''    # Minimum required v-flask version
    screenshots: list[str] = []      # Relative paths to screenshot images

    # Optional: Admin navigation category
    # Determines where this plugin's admin pages appear in the sidebar.
    # Standard categories: core, directory, content, legal, communication,
    #                     marketing, users, analytics, ecommerce, system
    # Host apps can register custom categories via register_category().
    # See v_flask.plugins.categories for available categories.
    admin_category: str = 'system'

    # Optional: UI Slots for automatic template integration
    # When activated, these UI elements appear in predefined template slots.
    # When deactivated, they automatically disappear.
    #
    # Example:
    #     ui_slots = {
    #         'footer_links': [
    #             {'label': 'Contact', 'url': 'kontakt.form', 'icon': 'ti ti-mail', 'order': 100}
    #         ],
    #         'admin_dashboard_widgets': [
    #             {'name': 'Messages', 'url': 'kontakt_admin.list', 'icon': 'ti-inbox',
    #              'badge_func': 'get_unread_count', 'color_hex': '#10b981'}
    #         ]
    #     }
    #
    # Valid slots: footer_links, navbar_items, admin_sidebar, admin_dashboard_widgets
    ui_slots: dict[str, list[dict]] = {}

    def get_models(self) -> list[type]:
        """Return SQLAlchemy model classes provided by this plugin.

        Returns:
            List of model classes (not instances).

        Example:
            def get_models(self):
                from .models import KontaktAnfrage
                return [KontaktAnfrage]
        """
        return []

    def get_blueprints(self) -> list[tuple[Blueprint, str]]:
        """Return Flask blueprints with their URL prefixes.

        Returns:
            List of (Blueprint, url_prefix) tuples.

        Example:
            def get_blueprints(self):
                from .routes import my_bp
                return [(my_bp, '/my-plugin')]
        """
        return []

    def get_cli_commands(self) -> list[Any]:
        """Return Click command groups for this plugin.

        Returns:
            List of Click command groups or commands.

        Example:
            def get_cli_commands(self):
                import click

                @click.group()
                def my_commands():
                    pass

                return [my_commands]
        """
        return []

    def get_template_folder(self) -> Path | str | None:
        """Return path to plugin templates folder.

        Templates will be registered with Jinja2 under the plugin name.
        Access them as 'plugin_name/template.html'.

        Returns:
            Path to templates folder, or None if no templates.

        Example:
            def get_template_folder(self):
                return Path(__file__).parent / 'templates'
        """
        return None

    def get_static_folder(self) -> Path | str | None:
        """Return path to plugin static files folder.

        Static files will be accessible under '/static/plugin_name/'.

        Returns:
            Path to static folder, or None if no static files.

        Example:
            def get_static_folder(self):
                return Path(__file__).parent / 'static'
        """
        return None

    def on_init(self, app: Flask) -> None:
        """Called when the plugin is initialized with the Flask app.

        Use this for plugin-specific initialization like:
        - Registering custom Jinja2 filters
        - Setting up event listeners
        - Initializing plugin-specific services

        Args:
            app: The Flask application instance.

        Example:
            def on_init(self, app):
                @app.context_processor
                def inject_plugin_data():
                    return {'my_plugin_version': self.version}
        """
        pass

    def get_readme(self) -> str | None:
        """Return plugin README content as Markdown string.

        Default implementation looks for README.md in the plugin's directory.
        Falls back to long_description if no README file exists.

        This method is used by marketplace UIs to display detailed
        plugin documentation.

        Returns:
            README content as string, or None if not available.

        Example:
            # Custom README location
            def get_readme(self):
                readme_path = Path(__file__).parent / 'docs' / 'README.md'
                if readme_path.exists():
                    return readme_path.read_text()
                return None
        """
        # Try to find README.md in the same directory as the plugin class
        import inspect
        plugin_file = inspect.getfile(self.__class__)
        readme_path = Path(plugin_file).parent / 'README.md'

        if readme_path.exists():
            return readme_path.read_text(encoding='utf-8')

        # Fallback to long_description
        return self.long_description if self.long_description else None

    def get_help_texts(self) -> list[dict]:
        """Return help texts to be seeded when plugin is initialized.

        Help texts provide context-sensitive documentation for admin editors
        and other UI elements. They are stored in the database and can be
        customized by the site administrator.

        Each help text dict must have:
            - schluessel: Unique key (e.g., 'impressum.editor')
            - titel: Display title for the help modal
            - inhalt_markdown: Help content in Markdown format

        Returns:
            List of help text dictionaries.

        Example:
            def get_help_texts(self):
                return [{
                    'schluessel': 'impressum.editor',
                    'titel': 'Hilfe zum Impressum',
                    'inhalt_markdown': '''## Warum ein Impressum?

Nach § 5 TMG sind geschäftsmäßige Online-Dienste zur Angabe
eines Impressums verpflichtet.

## Disclaimer

Dieses Tool ersetzt keine Rechtsberatung.
'''
                }]
        """
        return []

    def get_settings_schema(self) -> list[dict]:
        """Define available settings for this plugin.

        Settings defined here will be automatically rendered as a form
        in the admin UI. Values are stored in PluginConfig table.

        Returns:
            List of setting definitions with the following fields:
            - key (required): Unique setting key within the plugin
            - label (required): Display label in admin UI
            - type (required): Field type ('string', 'password', 'int', 'bool',
                              'float', 'textarea', 'select')
            - description: Help text shown below the field
            - required: Whether the field is required (default: False)
            - default: Default value if not set
            - options: For 'select' type, list of {value, label} dicts

        Example:
            def get_settings_schema(self):
                return [
                    {
                        'key': 'api_key',
                        'label': 'API Key',
                        'type': 'password',
                        'description': 'Your API key from example.com',
                        'required': False,
                    },
                    {
                        'key': 'max_items',
                        'label': 'Maximum Items',
                        'type': 'int',
                        'default': 10,
                    },
                    {
                        'key': 'theme',
                        'label': 'Theme',
                        'type': 'select',
                        'options': [
                            {'value': 'light', 'label': 'Light'},
                            {'value': 'dark', 'label': 'Dark'},
                        ],
                        'default': 'light',
                    },
                ]
        """
        return []

    def get_settings_template(self) -> str | None:
        """Return custom template path for plugin settings.

        Override this method to provide a custom settings UI instead of
        the auto-generated form based on get_settings_schema().

        The template will receive:
        - plugin: The PluginManifest instance
        - schema: The settings schema from get_settings_schema()
        - settings: Dict of current setting values

        Returns:
            Template path (e.g., 'my_plugin/admin/settings.html') or None
            for auto-generated UI.

        Example:
            def get_settings_template(self):
                return 'my_plugin/admin/custom_settings.html'
        """
        return None

    def on_settings_saved(self, settings: dict) -> None:
        """Called after plugin settings are saved.

        Use this hook to perform actions when settings change, such as:
        - Clearing cached API clients
        - Validating API keys
        - Reinitializing services

        Args:
            settings: Dictionary of all current settings for this plugin.

        Example:
            def on_settings_saved(self, settings):
                # Clear cached API client so it's recreated with new key
                from .services import api_client
                api_client._client = None
        """
        pass

    def has_settings(self) -> bool:
        """Check if this plugin has configurable settings.

        Returns:
            True if the plugin defines any settings, False otherwise.
        """
        return bool(self.get_settings_schema())

    def to_marketplace_dict(self) -> dict:
        """Return plugin metadata as dictionary for marketplace APIs.

        Returns:
            Dictionary with all plugin metadata suitable for JSON serialization.
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'long_description': self.long_description,
            'homepage': self.homepage,
            'repository': self.repository,
            'license': self.license,
            'categories': self.categories,
            'tags': self.tags,
            'min_v_flask_version': self.min_v_flask_version,
            'dependencies': self.dependencies,
            'has_settings': self.has_settings(),
        }

    def __repr__(self) -> str:
        return f'<Plugin {self.name}@{self.version}>'

    def validate(self) -> None:
        """Validate that required attributes are set.

        Raises:
            ValueError: If required attributes are missing.
        """
        required = ['name', 'version', 'description', 'author']
        for attr in required:
            if not hasattr(self, attr) or not getattr(self, attr):
                raise ValueError(
                    f"Plugin class must define '{attr}' attribute"
                )
