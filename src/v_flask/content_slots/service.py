"""Content Slot Services.

Services for managing content slots and route synchronization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from v_flask.extensions import db

if TYPE_CHECKING:
    from flask import Flask


# Patterns to exclude from route sync
DEFAULT_EXCLUDED_PATTERNS = [
    r'^static',           # Static file routes
    r'\.json$',           # JSON API endpoints
    r'/api/',             # API routes
    r'^admin\.',          # Admin routes
    r'^auth\.',           # Auth routes
    r'_admin\.',          # Plugin admin routes
    r'^v_flask_static',   # v-flask static files
]

# Blueprints to exclude by default
DEFAULT_EXCLUDED_BLUEPRINTS = [
    'admin',
    'auth',
    'two_fa',
    'plugins_admin',
    'users_admin',
    'roles_admin',
    'admin_settings',
    'plugin_settings',
    'v_flask_static',
]


@dataclass
class SyncResult:
    """Result of a route synchronization."""
    added: int = 0
    removed: int = 0
    updated: int = 0
    unchanged: int = 0

    @property
    def total_changes(self) -> int:
        return self.added + self.removed + self.updated


class RouteSyncService:
    """Service for synchronizing Flask routes with PageRoute table.

    Scans the Flask app.url_map and updates the PageRoute table
    to reflect current routes. Used by plugins to know which
    pages are available for content slot assignment.

    Usage:
        service = RouteSyncService()
        result = service.sync(app)
        print(f"Added {result.added} routes")
    """

    def __init__(
        self,
        excluded_patterns: list[str] | None = None,
        excluded_blueprints: list[str] | None = None,
    ) -> None:
        """Initialize the sync service.

        Args:
            excluded_patterns: Regex patterns to exclude endpoints.
            excluded_blueprints: Blueprint names to exclude.
        """
        self.excluded_patterns = excluded_patterns or DEFAULT_EXCLUDED_PATTERNS
        self.excluded_blueprints = excluded_blueprints or DEFAULT_EXCLUDED_BLUEPRINTS

        # Compile patterns for efficiency
        self._compiled_patterns = [
            re.compile(p) for p in self.excluded_patterns
        ]

    def sync(self, app: Flask) -> SyncResult:
        """Synchronize Flask routes with PageRoute table.

        Adds new routes, removes deleted routes, and updates
        existing route metadata.

        Args:
            app: Flask application instance.

        Returns:
            SyncResult with counts of changes.
        """
        from .models import PageRoute

        result = SyncResult()

        # Get current routes from Flask
        current_endpoints = self._get_app_endpoints(app)

        # Get existing routes from database
        existing_routes = {r.endpoint: r for r in PageRoute.query.all()}

        # Add new routes
        for endpoint, info in current_endpoints.items():
            if endpoint not in existing_routes:
                route = PageRoute(
                    endpoint=endpoint,
                    rule=info['rule'],
                    blueprint=info['blueprint'],
                    display_name=self._generate_display_name(endpoint, info['rule']),
                    route_type=self._determine_route_type(endpoint, info),
                    hero_assignable=True,  # Column name for DB compatibility
                )
                db.session.add(route)
                result.added += 1
            else:
                # Update existing route if rule changed
                existing = existing_routes[endpoint]
                if existing.rule != info['rule']:
                    existing.rule = info['rule']
                    result.updated += 1
                else:
                    result.unchanged += 1

        # Remove deleted routes
        for endpoint, route in existing_routes.items():
            if endpoint not in current_endpoints:
                db.session.delete(route)
                result.removed += 1

        db.session.commit()
        return result

    def _get_app_endpoints(self, app: Flask) -> dict[str, dict]:
        """Extract endpoints from Flask app.url_map.

        Args:
            app: Flask application.

        Returns:
            Dict mapping endpoint names to route info.
        """
        endpoints = {}

        for rule in app.url_map.iter_rules():
            endpoint = rule.endpoint

            # Skip if matches excluded pattern
            if self._is_excluded(endpoint):
                continue

            # Skip if blueprint is excluded
            blueprint = endpoint.split('.')[0] if '.' in endpoint else None
            if blueprint and blueprint in self.excluded_blueprints:
                continue

            # Only include GET routes (pages, not actions)
            if 'GET' not in rule.methods:
                continue

            endpoints[endpoint] = {
                'rule': rule.rule,
                'blueprint': blueprint,
                'methods': list(rule.methods),
            }

        return endpoints

    def _is_excluded(self, endpoint: str) -> bool:
        """Check if endpoint matches any exclusion pattern.

        Args:
            endpoint: Flask endpoint name.

        Returns:
            True if should be excluded.
        """
        for pattern in self._compiled_patterns:
            if pattern.search(endpoint):
                return True
        return False

    def _generate_display_name(self, endpoint: str, rule: str) -> str:
        """Generate a human-readable display name for a route.

        Args:
            endpoint: Flask endpoint name.
            rule: URL rule pattern.

        Returns:
            Display name string.
        """
        # Use the function name part (after the dot)
        if '.' in endpoint:
            name = endpoint.split('.')[-1]
        else:
            name = endpoint

        # Convert snake_case to Title Case
        name = name.replace('_', ' ').title()

        # Special cases
        name_map = {
            'Index': 'Startseite',
            'Detail': 'Detailseite',
            'List': 'Liste',
            'Page': 'Seite',
        }

        for old, new in name_map.items():
            if name == old:
                name = new
                break

        return name

    def _determine_route_type(self, endpoint: str, info: dict) -> str:
        """Determine the type of a route.

        Args:
            endpoint: Flask endpoint name.
            info: Route info dict.

        Returns:
            Route type string ('page', 'api', 'admin', 'auth').
        """
        endpoint_lower = endpoint.lower()

        if 'admin' in endpoint_lower:
            return 'admin'
        elif 'auth' in endpoint_lower or 'login' in endpoint_lower:
            return 'auth'
        elif 'api' in endpoint_lower or info.get('rule', '').startswith('/api'):
            return 'api'
        else:
            return 'page'

    def get_assignable_routes(
        self,
        include_types: list[str] | None = None,
        exclude_blueprints: list[str] | None = None,
    ) -> list:
        """Get routes that can have content assigned.

        Args:
            include_types: Route types to include (default: ['page']).
            exclude_blueprints: Additional blueprints to exclude.

        Returns:
            List of PageRoute instances.
        """
        from .models import PageRoute

        query = PageRoute.query.filter_by(hero_assignable=True)

        # Filter by type
        if include_types:
            query = query.filter(PageRoute.route_type.in_(include_types))
        else:
            query = query.filter(PageRoute.route_type == 'page')

        # Exclude blueprints
        if exclude_blueprints:
            query = query.filter(~PageRoute.blueprint.in_(exclude_blueprints))

        return query.order_by(PageRoute.display_name, PageRoute.endpoint).all()


# Singleton instance
route_sync_service = RouteSyncService()


__all__ = [
    'RouteSyncService',
    'SyncResult',
    'route_sync_service',
    'DEFAULT_EXCLUDED_PATTERNS',
    'DEFAULT_EXCLUDED_BLUEPRINTS',
]
