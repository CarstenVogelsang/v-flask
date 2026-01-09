"""Tests for v-flask plugin system."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask, Blueprint

from v_flask import VFlask, db
from v_flask.plugins import PluginManifest, PluginRegistry
from v_flask.plugins.registry import (
    PluginRegistryError,
    CircularDependencyError,
    MissingDependencyError,
)


# --- Test Plugin Classes ---

class MinimalPlugin(PluginManifest):
    """Minimal valid plugin for testing."""

    name = 'minimal'
    version = '1.0.0'
    description = 'A minimal test plugin'
    author = 'Test Author'


class PluginWithDependency(PluginManifest):
    """Plugin that depends on minimal plugin."""

    name = 'dependent'
    version = '1.0.0'
    description = 'Plugin with dependency'
    author = 'Test Author'
    dependencies = ['minimal']


class PluginA(PluginManifest):
    """Plugin A for dependency chain testing."""

    name = 'plugin_a'
    version = '1.0.0'
    description = 'Plugin A'
    author = 'Test'


class PluginB(PluginManifest):
    """Plugin B depends on A."""

    name = 'plugin_b'
    version = '1.0.0'
    description = 'Plugin B'
    author = 'Test'
    dependencies = ['plugin_a']


class PluginC(PluginManifest):
    """Plugin C depends on A and B."""

    name = 'plugin_c'
    version = '1.0.0'
    description = 'Plugin C'
    author = 'Test'
    dependencies = ['plugin_a', 'plugin_b']


class CircularPluginA(PluginManifest):
    """Circular dependency A -> B."""

    name = 'circular_a'
    version = '1.0.0'
    description = 'Circular A'
    author = 'Test'
    dependencies = ['circular_b']


class CircularPluginB(PluginManifest):
    """Circular dependency B -> A."""

    name = 'circular_b'
    version = '1.0.0'
    description = 'Circular B'
    author = 'Test'
    dependencies = ['circular_a']


class PluginWithBlueprint(PluginManifest):
    """Plugin that provides a blueprint."""

    name = 'blueprint_plugin'
    version = '1.0.0'
    description = 'Plugin with blueprint'
    author = 'Test'

    def get_blueprints(self):
        bp = Blueprint('test_bp', __name__)

        @bp.route('/test')
        def test_route():
            return 'test response'

        return [(bp, '/test-plugin')]


class PluginWithOnInit(PluginManifest):
    """Plugin that uses on_init hook."""

    name = 'init_plugin'
    version = '1.0.0'
    description = 'Plugin with on_init'
    author = 'Test'
    init_called = False

    def on_init(self, app):
        PluginWithOnInit.init_called = True
        app.config['PLUGIN_INIT_CALLED'] = True


# --- Test Classes ---

class TestPluginManifest:
    """Tests for PluginManifest base class."""

    def test_minimal_plugin_valid(self):
        """Test that minimal plugin validates successfully."""
        plugin = MinimalPlugin()
        plugin.validate()  # Should not raise

        assert plugin.name == 'minimal'
        assert plugin.version == '1.0.0'
        assert plugin.description == 'A minimal test plugin'
        assert plugin.author == 'Test Author'

    def test_repr(self):
        """Test string representation."""
        plugin = MinimalPlugin()
        assert repr(plugin) == '<Plugin minimal@1.0.0>'

    def test_default_methods_return_empty(self):
        """Test that default component methods return empty lists/None."""
        plugin = MinimalPlugin()

        assert plugin.get_models() == []
        assert plugin.get_blueprints() == []
        assert plugin.get_cli_commands() == []
        assert plugin.get_template_folder() is None
        assert plugin.get_static_folder() is None

    def test_validation_missing_name(self):
        """Test validation fails without name."""
        class BadPlugin(PluginManifest):
            version = '1.0.0'
            description = 'Missing name'
            author = 'Test'

        with pytest.raises(ValueError, match="must define 'name'"):
            BadPlugin().validate()

    def test_validation_missing_version(self):
        """Test validation fails without version."""
        class BadPlugin(PluginManifest):
            name = 'bad'
            description = 'Missing version'
            author = 'Test'

        with pytest.raises(ValueError, match="must define 'version'"):
            BadPlugin().validate()

    def test_default_dependencies_empty(self):
        """Test that dependencies default to empty list."""
        plugin = MinimalPlugin()
        assert plugin.dependencies == []

    def test_marketplace_metadata_defaults(self):
        """Test that marketplace metadata fields have correct defaults."""
        plugin = MinimalPlugin()

        assert plugin.long_description == ''
        assert plugin.homepage == ''
        assert plugin.repository == ''
        assert plugin.license == ''
        assert plugin.categories == []
        assert plugin.tags == []
        assert plugin.min_v_flask_version == ''
        assert plugin.screenshots == []

    def test_to_marketplace_dict(self):
        """Test to_marketplace_dict returns correct structure."""
        plugin = MinimalPlugin()
        d = plugin.to_marketplace_dict()

        assert d['name'] == 'minimal'
        assert d['version'] == '1.0.0'
        assert d['description'] == 'A minimal test plugin'
        assert d['author'] == 'Test Author'
        assert d['long_description'] == ''
        assert d['homepage'] == ''
        assert d['repository'] == ''
        assert d['license'] == ''
        assert d['categories'] == []
        assert d['tags'] == []
        assert d['min_v_flask_version'] == ''
        assert d['dependencies'] == []

    def test_get_readme_returns_none_without_file(self):
        """Test get_readme returns None when no README exists."""
        plugin = MinimalPlugin()
        # MinimalPlugin is defined in this test file, no README.md exists
        assert plugin.get_readme() is None

    def test_get_readme_falls_back_to_long_description(self):
        """Test get_readme falls back to long_description if no file."""
        class PluginWithLongDesc(PluginManifest):
            name = 'with_long_desc'
            version = '1.0.0'
            description = 'Short desc'
            author = 'Test'
            long_description = '# Extended Description\n\nMore details here.'

        plugin = PluginWithLongDesc()
        readme = plugin.get_readme()

        assert readme == '# Extended Description\n\nMore details here.'


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_register_plugin(self):
        """Test registering a plugin."""
        registry = PluginRegistry()
        plugin = MinimalPlugin()

        registry.register(plugin)

        assert 'minimal' in registry
        assert len(registry) == 1

    def test_get_plugin(self):
        """Test getting a plugin by name."""
        registry = PluginRegistry()
        plugin = MinimalPlugin()
        registry.register(plugin)

        result = registry.get('minimal')

        assert result is plugin

    def test_get_nonexistent_plugin(self):
        """Test getting a non-existent plugin returns None."""
        registry = PluginRegistry()

        assert registry.get('nonexistent') is None

    def test_all_plugins(self):
        """Test getting all registered plugins."""
        registry = PluginRegistry()
        plugin1 = MinimalPlugin()
        plugin2 = PluginA()

        registry.register(plugin1)
        registry.register(plugin2)

        all_plugins = registry.all()

        assert len(all_plugins) == 2
        assert plugin1 in all_plugins
        assert plugin2 in all_plugins

    def test_duplicate_registration(self):
        """Test that duplicate registration raises error."""
        registry = PluginRegistry()
        registry.register(MinimalPlugin())

        with pytest.raises(PluginRegistryError, match="already registered"):
            registry.register(MinimalPlugin())

    def test_iteration(self):
        """Test iterating over registry."""
        registry = PluginRegistry()
        plugin1 = MinimalPlugin()
        plugin2 = PluginA()

        registry.register(plugin1)
        registry.register(plugin2)

        plugins = list(registry)

        assert len(plugins) == 2

    def test_contains(self):
        """Test 'in' operator."""
        registry = PluginRegistry()
        registry.register(MinimalPlugin())

        assert 'minimal' in registry
        assert 'nonexistent' not in registry


class TestDependencyResolution:
    """Tests for plugin dependency resolution."""

    def test_no_dependencies(self):
        """Test resolution with no dependencies."""
        registry = PluginRegistry()
        plugin_a = PluginA()
        plugin_b = MinimalPlugin()

        registry.register(plugin_a)
        registry.register(plugin_b)

        resolved = registry.resolve_dependencies()

        assert len(resolved) == 2
        # Both are independent, order is deterministic (alphabetical)

    def test_simple_dependency(self):
        """Test resolution with simple A <- B dependency."""
        registry = PluginRegistry()
        registry.register(PluginWithDependency())  # depends on minimal
        registry.register(MinimalPlugin())

        resolved = registry.resolve_dependencies()

        names = [p.name for p in resolved]
        assert names.index('minimal') < names.index('dependent')

    def test_chain_dependency(self):
        """Test A <- B <- C dependency chain."""
        registry = PluginRegistry()
        registry.register(PluginC())  # depends on A, B
        registry.register(PluginB())  # depends on A
        registry.register(PluginA())

        resolved = registry.resolve_dependencies()
        names = [p.name for p in resolved]

        # A must come before B, B must come before C
        assert names.index('plugin_a') < names.index('plugin_b')
        assert names.index('plugin_b') < names.index('plugin_c')

    def test_missing_dependency(self):
        """Test error when dependency is not registered."""
        registry = PluginRegistry()
        registry.register(PluginWithDependency())  # depends on 'minimal'

        with pytest.raises(MissingDependencyError, match="requires 'minimal'"):
            registry.resolve_dependencies()

    def test_circular_dependency(self):
        """Test detection of circular dependencies."""
        registry = PluginRegistry()
        registry.register(CircularPluginA())
        registry.register(CircularPluginB())

        with pytest.raises(CircularDependencyError, match="Circular dependency"):
            registry.resolve_dependencies()

    def test_self_dependency(self):
        """Test detection of self-dependency."""
        class SelfDepPlugin(PluginManifest):
            name = 'self_dep'
            version = '1.0.0'
            description = 'Self dependency'
            author = 'Test'
            dependencies = ['self_dep']

        registry = PluginRegistry()
        registry.register(SelfDepPlugin())

        with pytest.raises(CircularDependencyError):
            registry.resolve_dependencies()


class TestPluginInitialization:
    """Tests for plugin initialization with Flask app."""

    def test_init_plugins_empty(self, app):
        """Test init_plugins with no plugins."""
        # App fixture already calls init_app which calls _init_plugins
        # This should work without errors
        assert app is not None

    def test_init_plugins_with_blueprint(self):
        """Test plugin blueprint registration."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test'

        v_flask = VFlask()
        v_flask.register_plugin(PluginWithBlueprint())
        v_flask.init_app(app)

        with app.app_context():
            db.create_all()
            client = app.test_client()
            response = client.get('/test-plugin/test')

            assert response.status_code == 200
            assert response.data == b'test response'

    def test_init_plugins_on_init_hook(self):
        """Test plugin on_init hook is called."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test'

        PluginWithOnInit.init_called = False

        v_flask = VFlask()
        v_flask.register_plugin(PluginWithOnInit())
        v_flask.init_app(app)

        assert PluginWithOnInit.init_called is True
        assert app.config.get('PLUGIN_INIT_CALLED') is True

    def test_register_after_init_fails(self):
        """Test that registering plugins after init_app fails."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test'

        v_flask = VFlask()
        v_flask.init_app(app)

        with pytest.raises(PluginRegistryError, match="after initialization"):
            v_flask.register_plugin(MinimalPlugin())

    def test_double_init_fails(self):
        """Test that calling init_plugins twice fails."""
        registry = PluginRegistry()
        registry.register(MinimalPlugin())

        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test'

        registry.init_plugins(app)

        with pytest.raises(PluginRegistryError, match="already initialized"):
            registry.init_plugins(app)


class TestVFlaskPluginIntegration:
    """Tests for VFlask plugin integration."""

    def test_vflask_has_plugin_registry(self):
        """Test VFlask instance has plugin_registry attribute."""
        v_flask = VFlask()

        assert hasattr(v_flask, 'plugin_registry')
        assert isinstance(v_flask.plugin_registry, PluginRegistry)

    def test_vflask_register_plugin(self):
        """Test VFlask.register_plugin method."""
        v_flask = VFlask()
        plugin = MinimalPlugin()

        v_flask.register_plugin(plugin)

        assert 'minimal' in v_flask.plugin_registry

    def test_plugins_initialized_in_order(self):
        """Test that plugins are initialized in dependency order."""
        initialization_order = []

        class OrderTrackingPluginA(PluginManifest):
            name = 'order_a'
            version = '1.0.0'
            description = 'Order tracking A'
            author = 'Test'

            def on_init(self, app):
                initialization_order.append('order_a')

        class OrderTrackingPluginB(PluginManifest):
            name = 'order_b'
            version = '1.0.0'
            description = 'Order tracking B'
            author = 'Test'
            dependencies = ['order_a']

            def on_init(self, app):
                initialization_order.append('order_b')

        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test'

        v_flask = VFlask()
        # Register in reverse order
        v_flask.register_plugin(OrderTrackingPluginB())
        v_flask.register_plugin(OrderTrackingPluginA())
        v_flask.init_app(app)

        # A should be initialized before B despite registration order
        assert initialization_order == ['order_a', 'order_b']
