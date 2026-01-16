"""Plugin UI Slot System.

Manages UI elements that plugins can inject into predefined template slots.
When a plugin is deactivated, its UI elements automatically disappear.

Usage in plugins:
    class MyPlugin(PluginManifest):
        ui_slots = {
            'footer_links': [
                {'label': 'Contact', 'url': 'my_plugin.contact', 'icon': 'ti ti-mail'}
            ]
        }

Usage in templates:
    {% for item in get_plugin_slots('footer_links') %}
        <a href="{{ url_for(item.url) }}">{{ item.label }}</a>
    {% endfor %}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flask import Flask
    from v_flask.plugins.manifest import PluginManifest


# Valid slot names that plugins can use
VALID_SLOTS = [
    'footer_links',              # Links in the footer
    'navbar_items',              # Items in the navigation bar
    'admin_sidebar',             # Admin sidebar navigation (deprecated, use admin_menu)
    'admin_menu',                # Admin menu items (grouped by category)
    'admin_dashboard_widgets',   # Dashboard widget tiles
]


@dataclass
class SlotItem:
    """A single UI element in a slot."""

    plugin_name: str
    label: str
    url: str
    icon: str = ''
    order: int = 100
    permission: str | None = None
    badge: int | str | None = None
    badge_func: str | None = None
    # Additional fields for dashboard widgets
    name: str | None = None
    description: str | None = None
    color_hex: str = '#3b82f6'
    settings_url: str | None = None
    extra: dict = field(default_factory=dict)


class PluginSlotManager:
    """Aggregates and manages UI slots from active plugins.

    The slot manager collects UI element declarations from all registered
    plugins and provides them to templates via the get_items() method.

    Key features:
        - Automatic filtering based on user permissions
        - Badge value resolution via plugin methods
        - Endpoint validation to prevent broken links
        - Ordering support for consistent UI placement
    """

    def __init__(self) -> None:
        self._plugins: list[PluginManifest] = []
        self._cache: dict[str, list[dict]] = {}

    def register_plugin(self, plugin: PluginManifest) -> None:
        """Register a plugin for slot extraction.

        Args:
            plugin: Plugin instance with optional ui_slots attribute.
        """
        self._plugins.append(plugin)
        self._cache.clear()  # Invalidate cache

    def clear(self) -> None:
        """Clear all registered plugins and cache."""
        self._plugins.clear()
        self._cache.clear()

    def get_items(
        self,
        slot_name: str,
        user: Any = None,
        app: Flask | None = None,
    ) -> list[dict]:
        """Get all items for a slot, filtered and sorted.

        Args:
            slot_name: Name of the slot (e.g., 'footer_links')
            user: Current user for permission filtering (optional)
            app: Flask app for endpoint validation (optional)

        Returns:
            List of slot items as dictionaries, sorted by order.
        """
        if slot_name not in VALID_SLOTS:
            return []

        items: list[SlotItem] = []

        for plugin in self._plugins:
            # Skip plugins without ui_slots
            ui_slots = getattr(plugin, 'ui_slots', None)
            if not ui_slots:
                continue

            slot_items = ui_slots.get(slot_name, [])

            for item_def in slot_items:
                item = self._create_slot_item(plugin, item_def)

                # Permission check
                if item.permission and user:
                    if not self._check_permission(user, item.permission):
                        continue

                # Endpoint validation (skip items pointing to non-existent routes)
                if app and not self._validate_endpoint(app, item.url):
                    continue

                # Resolve badge function to actual value
                if item.badge_func:
                    item.badge = self._resolve_badge(plugin, item.badge_func)

                items.append(item)

        # Sort by order
        items.sort(key=lambda x: x.order)

        # Convert to dicts for templates
        return [self._to_dict(item) for item in items]

    def _create_slot_item(
        self,
        plugin: PluginManifest,
        item_def: dict,
    ) -> SlotItem:
        """Create a SlotItem from a dictionary definition."""
        return SlotItem(
            plugin_name=plugin.name,
            label=item_def.get('label', ''),
            url=item_def.get('url', ''),
            icon=item_def.get('icon', ''),
            order=item_def.get('order', 100),
            permission=item_def.get('permission'),
            badge=item_def.get('badge'),
            badge_func=item_def.get('badge_func'),
            name=item_def.get('name'),
            description=item_def.get('description'),
            color_hex=item_def.get('color_hex', '#3b82f6'),
            settings_url=item_def.get('settings_url'),
            extra=item_def.get('extra', {}),
        )

    def _check_permission(self, user: Any, permission: str) -> bool:
        """Check if user has the required permission.

        Supports wildcard permissions (e.g., 'admin.*' grants all admin permissions).
        """
        if hasattr(user, 'is_admin') and user.is_admin:
            return True

        if hasattr(user, 'has_permission'):
            return user.has_permission(permission)

        return True  # No permission system, allow all

    def _validate_endpoint(self, app: Flask, endpoint: str) -> bool:
        """Validate that a Flask endpoint exists.

        Args:
            app: Flask application
            endpoint: Flask endpoint name (e.g., 'kontakt.form')

        Returns:
            True if endpoint exists, False otherwise.
        """
        # Block suspicious patterns
        if '..' in endpoint or endpoint.startswith('_'):
            return False

        try:
            # Check if endpoint is registered
            for rule in app.url_map.iter_rules():
                if rule.endpoint == endpoint:
                    return True
            return False
        except Exception:
            return False

    def _resolve_badge(
        self,
        plugin: PluginManifest,
        func_name: str,
    ) -> int | str | None:
        """Resolve a badge function to its value.

        Args:
            plugin: Plugin instance
            func_name: Name of the method to call on the plugin

        Returns:
            Badge value (int or str) or None if resolution fails.
        """
        if hasattr(plugin, func_name):
            func = getattr(plugin, func_name)
            if callable(func):
                try:
                    result = func()
                    # Only return non-zero values
                    if result and result != 0:
                        return result
                except Exception:
                    return None
        return None

    def _to_dict(self, item: SlotItem) -> dict:
        """Convert SlotItem to dictionary for templates."""
        return {
            'plugin_name': item.plugin_name,
            'label': item.label or item.name or '',
            'url': item.url,
            'icon': item.icon,
            'order': item.order,
            'permission': item.permission,
            'badge': item.badge,
            'name': item.name or item.label or '',
            'description': item.description or '',
            'color_hex': item.color_hex,
            'settings_url': item.settings_url,
            **item.extra,
        }

    def get_admin_menu(
        self,
        user: Any = None,
        app: Flask | None = None,
    ) -> dict[str, list[dict]]:
        """Get admin menu items grouped by category.

        Plugins define their category via `admin_category` attribute.
        Menu items come from the `admin_menu` slot (or legacy `admin_sidebar`).

        Args:
            user: Current user for permission filtering (optional)
            app: Flask app for endpoint validation (optional)

        Returns:
            Dictionary mapping category IDs to lists of menu items.
            Example: {'legal': [{'label': 'Impressum', ...}, ...]}
        """
        from v_flask.plugins.categories import ADMIN_CATEGORIES

        grouped: dict[str, list[SlotItem]] = {}

        for plugin in self._plugins:
            # Get plugin's category (defaults to 'system')
            category = getattr(plugin, 'admin_category', 'system')

            # Validate category exists
            if category not in ADMIN_CATEGORIES:
                category = 'system'

            # Get menu items (support both new 'admin_menu' and legacy 'admin_sidebar')
            ui_slots = getattr(plugin, 'ui_slots', None)
            if not ui_slots:
                continue

            menu_items = ui_slots.get('admin_menu', []) or ui_slots.get('admin_sidebar', [])

            for item_def in menu_items:
                item = self._create_slot_item(plugin, item_def)

                # Permission check
                if item.permission and user:
                    if not self._check_permission(user, item.permission):
                        continue

                # Endpoint validation
                if app and not self._validate_endpoint(app, item.url):
                    continue

                # Resolve badge function
                if item.badge_func:
                    item.badge = self._resolve_badge(plugin, item.badge_func)

                # Add to category group
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(item)

        # Sort items within each category by order
        result: dict[str, list[dict]] = {}
        for cat_id, items in grouped.items():
            items.sort(key=lambda x: x.order)
            result[cat_id] = [self._to_dict(item) for item in items]

        # Add core v-flask admin menu items (Plugin Management)
        # These are framework features, not plugins, so they're added here
        if self._should_show_plugins_menu(user, app):
            system_items = result.get('system', [])
            system_items.append({
                'label': 'Plugins',
                'url': 'plugins_admin.list_plugins',
                'icon': 'ti ti-puzzle',
                'order': 100,
            })
            result['system'] = system_items

        return result

    def _should_show_plugins_menu(self, user: Any, app: Flask | None) -> bool:
        """Check if the Plugins menu should be shown.

        Args:
            user: Current user for permission check
            app: Flask app for endpoint validation

        Returns:
            True if the Plugins menu should be displayed.
        """
        # Check if endpoint exists
        if app and not self._validate_endpoint(app, 'plugins_admin.list_plugins'):
            return False

        # Check user permission (admins always have access)
        if user:
            if hasattr(user, 'is_admin') and user.is_admin:
                return True
            if hasattr(user, 'has_permission'):
                return user.has_permission('plugins.manage')

        # If no user check needed, show the menu
        return True

    @property
    def registered_plugins(self) -> list[str]:
        """Get names of all registered plugins."""
        return [p.name for p in self._plugins]

    def __len__(self) -> int:
        return len(self._plugins)
