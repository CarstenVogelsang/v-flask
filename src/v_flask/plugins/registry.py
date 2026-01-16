"""Plugin registry for managing v-flask plugins.

The PluginRegistry handles plugin registration, dependency resolution,
and initialization with the Flask application.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from v_flask.plugins.manifest import PluginManifest

if TYPE_CHECKING:
    from flask import Flask


class PluginRegistryError(Exception):
    """Base exception for plugin registry errors."""

    pass


class CircularDependencyError(PluginRegistryError):
    """Raised when circular dependencies are detected."""

    pass


class MissingDependencyError(PluginRegistryError):
    """Raised when a required dependency is not registered."""

    pass


class PluginRegistry:
    """Central registry for managing v-flask plugins.

    The registry handles:
    - Plugin registration and validation
    - Dependency resolution using topological sort
    - Initialization of plugins with the Flask app

    Usage:
        registry = PluginRegistry()

        # Register plugins
        registry.register(KontaktPlugin())
        registry.register(AuthPlugin())

        # Initialize with Flask app (handles dependencies automatically)
        registry.init_plugins(app)

        # Access registered plugins
        plugin = registry.get('kontakt')
        all_plugins = registry.all()
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PluginManifest] = {}
        self._initialized = False

    def register(self, plugin: PluginManifest) -> None:
        """Register a plugin with the registry.

        Args:
            plugin: Plugin instance to register.

        Raises:
            ValueError: If plugin validation fails.
            PluginRegistryError: If plugin is already registered.
        """
        if self._initialized:
            raise PluginRegistryError(
                "Cannot register plugins after initialization"
            )

        # Validate plugin
        plugin.validate()

        # Check for duplicate registration
        if plugin.name in self._plugins:
            raise PluginRegistryError(
                f"Plugin '{plugin.name}' is already registered"
            )

        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> PluginManifest | None:
        """Get a plugin by name.

        Args:
            name: Plugin name.

        Returns:
            Plugin instance or None if not found.
        """
        return self._plugins.get(name)

    def all(self) -> list[PluginManifest]:
        """Get all registered plugins.

        Returns:
            List of all registered plugin instances.
        """
        return list(self._plugins.values())

    def resolve_dependencies(self) -> list[PluginManifest]:
        """Resolve plugin dependencies and return plugins in load order.

        Uses Kahn's algorithm for topological sorting to ensure plugins
        are loaded after their dependencies.

        Returns:
            List of plugins in dependency-resolved order.

        Raises:
            MissingDependencyError: If a dependency is not registered.
            CircularDependencyError: If circular dependencies exist.
        """
        # Validate all dependencies exist
        for plugin in self._plugins.values():
            for dep in plugin.dependencies:
                if dep not in self._plugins:
                    raise MissingDependencyError(
                        f"Plugin '{plugin.name}' requires '{dep}', "
                        f"but '{dep}' is not registered"
                    )

        return self._topological_sort()

    def _topological_sort(self) -> list[PluginManifest]:
        """Sort plugins using Kahn's algorithm.

        Returns:
            List of plugins in topologically sorted order.

        Raises:
            CircularDependencyError: If circular dependencies exist.
        """
        # Build in-degree map (how many plugins depend on each)
        in_degree: dict[str, int] = defaultdict(int)
        dependents: dict[str, list[str]] = defaultdict(list)

        for name in self._plugins:
            in_degree[name]  # Ensure all plugins are in the map

        for plugin in self._plugins.values():
            for dep in plugin.dependencies:
                in_degree[plugin.name] += 1
                dependents[dep].append(plugin.name)

        # Find all plugins with no dependencies (in_degree == 0)
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result: list[PluginManifest] = []

        while queue:
            # Sort to ensure deterministic order
            queue.sort()
            current = queue.pop(0)
            result.append(self._plugins[current])

            # Reduce in_degree for dependent plugins
            for dependent in dependents[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If not all plugins are in result, there's a cycle
        if len(result) != len(self._plugins):
            # Find plugins involved in cycles
            remaining = set(self._plugins.keys()) - {p.name for p in result}
            raise CircularDependencyError(
                f"Circular dependency detected involving: {', '.join(sorted(remaining))}"
            )

        return result

    def init_plugins(self, app: Flask) -> None:
        """Initialize all registered plugins with the Flask app.

        Plugins are initialized in dependency order. For each plugin:
        1. Models are imported (registered with SQLAlchemy)
        2. Blueprints are registered with their URL prefixes
        3. CLI commands are registered
        4. Template/static folders are registered
        5. on_init() hook is called

        Args:
            app: Flask application instance.

        Raises:
            PluginRegistryError: If already initialized.
        """
        if self._initialized:
            raise PluginRegistryError("Plugins already initialized")

        plugins = self.resolve_dependencies()

        for plugin in plugins:
            self._init_single_plugin(app, plugin)

        self._initialized = True

    def _init_single_plugin(self, app: Flask, plugin: PluginManifest) -> None:
        """Initialize a single plugin.

        Args:
            app: Flask application instance.
            plugin: Plugin to initialize.
        """
        # 1. Import models (they register themselves with SQLAlchemy)
        models = plugin.get_models()
        if models:
            app.logger.debug(
                f"Plugin '{plugin.name}': Registered {len(models)} model(s)"
            )

        # 2. Register blueprints
        for blueprint, url_prefix in plugin.get_blueprints():
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            app.logger.debug(
                f"Plugin '{plugin.name}': Registered blueprint at '{url_prefix}'"
            )

        # 3. Register CLI commands
        for cmd in plugin.get_cli_commands():
            app.cli.add_command(cmd)
            app.logger.debug(
                f"Plugin '{plugin.name}': Registered CLI command"
            )

        # 4. Register template folder
        template_folder = plugin.get_template_folder()
        if template_folder:
            # Add to Jinja2 loader
            from jinja2 import ChoiceLoader, FileSystemLoader

            plugin_loader = FileSystemLoader(str(template_folder))

            if app.jinja_loader is None:
                app.jinja_loader = plugin_loader
            elif isinstance(app.jinja_loader, ChoiceLoader):
                app.jinja_loader.loaders.append(plugin_loader)
            else:
                app.jinja_loader = ChoiceLoader([
                    app.jinja_loader,
                    plugin_loader
                ])

            app.logger.debug(
                f"Plugin '{plugin.name}': Registered templates from '{template_folder}'"
            )

        # 5. Register static folder
        static_folder = plugin.get_static_folder()
        if static_folder:
            from flask import Blueprint

            static_bp = Blueprint(
                f'{plugin.name}_static',
                plugin.name,
                static_folder=str(static_folder),
                static_url_path=f'/static/{plugin.name}'
            )
            app.register_blueprint(static_bp)
            app.logger.debug(
                f"Plugin '{plugin.name}': Registered static files at '/static/{plugin.name}'"
            )

        # 6. Call on_init hook
        plugin.on_init(app)

        # 7. Register UI slots (if slot manager is available)
        if hasattr(plugin, 'ui_slots') and plugin.ui_slots:
            slot_manager = app.extensions.get('v_flask_slots')
            if slot_manager is not None:
                slot_manager.register_plugin(plugin)
                app.logger.debug(
                    f"Plugin '{plugin.name}': Registered UI slots for "
                    f"{list(plugin.ui_slots.keys())}"
                )

        # 8. Seed help texts (if plugin provides any)
        help_texts = plugin.get_help_texts()
        if help_texts:
            self._seed_help_texts(app, plugin, help_texts)

        app.logger.info(f"Plugin initialized: {plugin}")

    def _seed_help_texts(
        self, app: Flask, plugin: PluginManifest, help_texts: list[dict]
    ) -> None:
        """Seed help texts from a plugin.

        Only creates new help texts - existing ones are not updated
        to preserve administrator customizations.

        Args:
            app: Flask application instance.
            plugin: Plugin providing the help texts.
            help_texts: List of help text dictionaries.
        """
        from v_flask.extensions import db
        from v_flask.models import HelpText

        try:
            created = 0
            for help_data in help_texts:
                schluessel = help_data.get('schluessel')
                if not schluessel:
                    continue

                # Only create if doesn't exist (preserve customizations)
                existing = HelpText.query.filter_by(schluessel=schluessel).first()
                if existing is None:
                    help_text = HelpText(
                        schluessel=schluessel,
                        titel=help_data.get('titel', schluessel),
                        inhalt_markdown=help_data.get('inhalt_markdown', ''),
                        plugin=plugin.name,
                    )
                    db.session.add(help_text)
                    created += 1

            if created > 0:
                db.session.commit()
                app.logger.debug(
                    f"Plugin '{plugin.name}': Seeded {created} help text(s)"
                )
        except Exception as e:
            # Don't fail plugin init if help text seeding fails
            # (e.g., database table might not exist yet)
            app.logger.warning(
                f"Plugin '{plugin.name}': Could not seed help texts: {e}"
            )

    @property
    def is_initialized(self) -> bool:
        """Check if plugins have been initialized."""
        return self._initialized

    def __len__(self) -> int:
        return len(self._plugins)

    def __contains__(self, name: str) -> bool:
        return name in self._plugins

    def __iter__(self):
        return iter(self._plugins.values())
