"""Route Sync Service for the Hero plugin.

Provides functionality to scan Flask routes and populate the
PageRoute table for hero section assignment.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from v_flask.extensions import db

if TYPE_CHECKING:
    from flask import Flask

from v_flask_plugins.hero.models import PageRoute


class RouteSyncService:
    """Service for synchronizing Flask routes with PageRoute table.

    Scans app.url_map and maintains the PageRoute database table,
    allowing admins to assign hero sections to specific pages.

    Usage:
        from v_flask_plugins.hero.services.route_sync_service import route_sync_service

        # Sync routes (call from admin UI or CLI)
        stats = route_sync_service.sync_routes(current_app)
        print(f"Added: {stats['added']}, Removed: {stats['removed']}")

        # Get assignable routes
        routes = route_sync_service.get_assignable_routes()
    """

    # Routes to exclude from hero assignment
    EXCLUDED_PATTERNS = [
        r'^static',           # Static files
        r'^_',                # Internal routes
        r'\.json$',           # JSON endpoints
        r'\.xml$',            # XML endpoints
        r'/api/',             # API routes
        r'^admin\.',          # All admin routes (admin.*)
        r'^admin_',           # Admin blueprints (admin_content.*, etc.)
        r'_admin\.',          # All *_admin blueprints (fragebogen_admin.*, hero_admin.*, etc.)
        r'^anbieter\.',       # Provider dashboard routes
        r'^mein_bereich\.',   # "My area" routes
        r'^media\.',          # Media management routes
        r'^two_fa\.',         # 2FA routes
        r'^auth\.',           # Auth routes (login, logout)
        r'^users_admin\.',    # User admin routes
        r'^roles_admin\.',    # Role admin routes
        r'^plugins_admin\.',  # Plugin admin routes
        r'^plugin_settings\.',  # Plugin settings routes
        r'^v_flask_static\.',  # v-flask static files
        r'^serve_media$',     # Direct media serve route
    ]

    # Endpoints that are clearly not pages
    EXCLUDED_ENDPOINTS = [
        'static',
        'send_static_file',
    ]

    # Route types based on blueprint (exact matches)
    ROUTE_TYPES = {
        'admin': 'admin',
        'public': 'page',
        'auth': 'auth',
        'api': 'api',
    }

    # Patterns for admin-type blueprints (partial matches)
    ADMIN_BLUEPRINT_PATTERNS = [
        r'^admin',      # admin, admin_content, etc.
        r'_admin$',     # *_admin (fragebogen_admin, hero_admin, etc.)
    ]

    def sync_routes(self, app: Flask) -> dict[str, int]:
        """Scan Flask routes and sync with PageRoute table.

        Compares current Flask routes with database entries:
        - Adds new routes that don't exist in DB
        - Removes routes that no longer exist in Flask
        - Keeps existing routes unchanged

        Args:
            app: Flask application instance.

        Returns:
            Statistics dict with 'added', 'removed', 'unchanged' counts.
        """
        stats = {'added': 0, 'removed': 0, 'unchanged': 0}

        # Get current routes from Flask
        current_routes = self._get_flask_routes(app)
        current_endpoints = {r['endpoint'] for r in current_routes}

        # Get existing routes from database
        existing_routes = {r.endpoint: r for r in PageRoute.query.all()}
        existing_endpoints = set(existing_routes.keys())

        # Add new routes
        for route_data in current_routes:
            endpoint = route_data['endpoint']
            if endpoint not in existing_endpoints:
                page_route = PageRoute(
                    endpoint=endpoint,
                    rule=route_data['rule'],
                    blueprint=route_data['blueprint'],
                    display_name=route_data['display_name'],
                    route_type=route_data['route_type'],
                    hero_assignable=route_data['hero_assignable'],
                )
                db.session.add(page_route)
                stats['added'] += 1
            else:
                # Update existing route if rule changed
                existing = existing_routes[endpoint]
                if existing.rule != route_data['rule']:
                    existing.rule = route_data['rule']
                stats['unchanged'] += 1

        # Remove routes that no longer exist
        for endpoint in existing_endpoints - current_endpoints:
            route = existing_routes[endpoint]
            db.session.delete(route)
            stats['removed'] += 1

        db.session.commit()
        return stats

    def get_assignable_routes(self) -> list[PageRoute]:
        """Get all routes available for hero assignment.

        Applies filtering based on plugin settings:
        - excluded_blueprints: Comma-separated list of blueprints to exclude
        - show_only_public: If true, only show routes with route_type='page'

        Returns:
            List of PageRoute instances that can have hero sections.
        """
        from v_flask.models import PluginConfig

        query = PageRoute.query.filter_by(hero_assignable=True)

        # Apply blueprint exclusions from plugin settings
        excluded_str = PluginConfig.get_value('hero', 'excluded_blueprints', '')
        if excluded_str:
            excluded_blueprints = [
                bp.strip() for bp in excluded_str.split('\n') if bp.strip()
            ]
            for bp in excluded_blueprints:
                query = query.filter(PageRoute.blueprint != bp)

        # Optionally filter to only public pages
        show_only_public = PluginConfig.get_value('hero', 'show_only_public', True)
        if show_only_public:
            query = query.filter(PageRoute.route_type == 'page')

        return query.order_by(
            PageRoute.blueprint,
            PageRoute.display_name
        ).all()

    def get_public_routes(self) -> list[PageRoute]:
        """Get only public (non-admin) routes.

        Note: This is a legacy method. Consider using get_assignable_routes()
        which applies all plugin settings.

        Returns:
            List of PageRoute instances for public pages.
        """
        from v_flask.models import PluginConfig

        query = PageRoute.query.filter(
            PageRoute.hero_assignable == True,  # noqa: E712
            PageRoute.route_type == 'page'
        )

        # Apply blueprint exclusions from plugin settings
        excluded_str = PluginConfig.get_value('hero', 'excluded_blueprints', '')
        if excluded_str:
            excluded_blueprints = [
                bp.strip() for bp in excluded_str.split('\n') if bp.strip()
            ]
            for bp in excluded_blueprints:
                query = query.filter(PageRoute.blueprint != bp)

        return query.order_by(PageRoute.display_name).all()

    def _get_flask_routes(self, app: Flask) -> list[dict]:
        """Extract routes from Flask application.

        Args:
            app: Flask application instance.

        Returns:
            List of route dictionaries with endpoint, rule, etc.
        """
        routes = []

        for rule in app.url_map.iter_rules():
            # Skip if not GET method (pages should be GET)
            if 'GET' not in rule.methods:
                continue

            endpoint = rule.endpoint

            # Skip excluded endpoints
            if endpoint in self.EXCLUDED_ENDPOINTS:
                continue

            # Skip if matches excluded patterns
            if self._should_exclude(endpoint):
                continue

            # Determine blueprint and route type
            blueprint = endpoint.split('.')[0] if '.' in endpoint else None
            route_type = self._get_route_type(blueprint)

            # Generate display name
            display_name = self._generate_display_name(endpoint, str(rule))

            # Determine if hero-assignable (public pages only by default)
            hero_assignable = route_type == 'page'

            routes.append({
                'endpoint': endpoint,
                'rule': str(rule),
                'blueprint': blueprint,
                'display_name': display_name,
                'route_type': route_type,
                'hero_assignable': hero_assignable,
            })

        return routes

    def _get_route_type(self, blueprint: str | None) -> str:
        """Determine route type from blueprint name.

        Args:
            blueprint: Blueprint name or None.

        Returns:
            Route type string ('page', 'admin', 'auth', 'api').
        """
        if blueprint is None:
            return 'page'

        # Check exact match first
        if blueprint in self.ROUTE_TYPES:
            return self.ROUTE_TYPES[blueprint]

        # Check admin patterns
        for pattern in self.ADMIN_BLUEPRINT_PATTERNS:
            if re.search(pattern, blueprint):
                return 'admin'

        return 'page'

    def _should_exclude(self, endpoint: str) -> bool:
        """Check if endpoint should be excluded from sync.

        Args:
            endpoint: Flask endpoint name.

        Returns:
            True if endpoint should be excluded.
        """
        for pattern in self.EXCLUDED_PATTERNS:
            if re.search(pattern, endpoint):
                return True
        return False

    def _generate_display_name(self, endpoint: str, rule: str) -> str:
        """Generate human-readable display name for route.

        Args:
            endpoint: Flask endpoint name.
            rule: URL rule pattern.

        Returns:
            Human-readable name for admin UI.
        """
        # Special cases
        display_names = {
            'public.index': 'Startseite',
            'public.slug_handler': 'Inhaltsseiten (Slug)',
        }

        if endpoint in display_names:
            return display_names[endpoint]

        # Extract meaningful part
        if '.' in endpoint:
            _, name = endpoint.rsplit('.', 1)
        else:
            name = endpoint

        # Convert snake_case to title case
        name = name.replace('_', ' ').title()

        # Add context from rule if dynamic
        if '<' in rule:
            # Extract parameter names
            params = re.findall(r'<(?:[\w:]+:)?(\w+)>', rule)
            if params:
                param_str = ', '.join(p.title() for p in params[:2])
                name = f'{name} ({param_str})'

        return name


# Singleton instance for convenience
route_sync_service = RouteSyncService()
