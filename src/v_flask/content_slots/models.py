"""Content Slot Models.

Database models for the content slot system.
PageRoute is the central model that stores Flask routes for slot assignment.
"""

from datetime import datetime

from v_flask.extensions import db


class PageRoute(db.Model):
    """Flask Routes available for content slot assignment.

    This model stores Flask routes (endpoints) that can have content
    assigned to slots. Routes are synchronized from app.url_map via
    the route sync service.

    Used by plugins like Hero and CTA to assign content to specific pages.

    Attributes:
        id: Primary key.
        endpoint: Flask endpoint name (e.g., 'public.index', 'kreis.detail').
        rule: URL rule pattern (e.g., '/', '/<bundesland>/<region>/<kreis>/').
        blueprint: Blueprint name (e.g., 'public', 'kreis').
        display_name: Human-readable name (editable in admin).
        route_type: Type classification ('page', 'api', 'admin', 'auth').
        slot_assignable: Whether content can be assigned to slots on this route.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.

    Example:
        route = PageRoute.query.filter_by(endpoint='public.index').first()
        print(route.display_name)  # 'Startseite'
    """

    __tablename__ = 'page_route'

    id = db.Column(db.Integer, primary_key=True)

    # Route identification
    endpoint = db.Column(db.String(200), unique=True, nullable=False, index=True)
    rule = db.Column(db.String(500), nullable=False)
    blueprint = db.Column(db.String(100), index=True)

    # Display name (editable by admin)
    display_name = db.Column(db.String(200))

    # Route type for grouping/filtering
    route_type = db.Column(db.String(50), default='page', index=True)

    # Whether content slots can be assigned to this route
    # Note: Column named 'hero_assignable' for backwards compatibility with Hero plugin
    # Alias 'slot_assignable' provided for generic content slot usage
    hero_assignable = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def slot_assignable(self) -> bool:
        """Alias for hero_assignable (generic content slot naming).

        This alias allows generic code to use 'slot_assignable' while
        maintaining the column name 'hero_assignable' for DB compatibility.
        """
        return self.hero_assignable

    @slot_assignable.setter
    def slot_assignable(self, value: bool) -> None:
        """Setter for slot_assignable (forwards to hero_assignable)."""
        self.hero_assignable = value

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f'<PageRoute {self.endpoint}>'

    @property
    def name(self) -> str:
        """Return display name or endpoint as fallback."""
        return self.display_name or self.endpoint

    @classmethod
    def get_by_endpoint(cls, endpoint: str) -> 'PageRoute | None':
        """Get a route by its endpoint name.

        Args:
            endpoint: Flask endpoint name.

        Returns:
            PageRoute instance or None if not found.
        """
        return cls.query.filter_by(endpoint=endpoint).first()

    @classmethod
    def get_assignable(cls, blueprint: str | None = None) -> list['PageRoute']:
        """Get all routes that can have content assigned.

        Args:
            blueprint: Optional blueprint filter.

        Returns:
            List of assignable PageRoute instances.
        """
        # Use hero_assignable (the actual column name) for queries
        query = cls.query.filter_by(hero_assignable=True)

        if blueprint:
            query = query.filter_by(blueprint=blueprint)

        return query.order_by(cls.display_name, cls.endpoint).all()

    @classmethod
    def get_by_type(cls, route_type: str) -> list['PageRoute']:
        """Get all routes of a specific type.

        Args:
            route_type: Route type ('page', 'api', 'admin', 'auth').

        Returns:
            List of PageRoute instances.
        """
        return cls.query.filter_by(route_type=route_type).order_by(
            cls.display_name, cls.endpoint
        ).all()


# Export models
__all__ = ['PageRoute']
