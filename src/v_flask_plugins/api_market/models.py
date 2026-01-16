"""Models for the API Market plugin.

This plugin uses a minimal local database model for caching OpenAPI specs
and API metadata. User/key management is handled by the external API.
"""

from datetime import datetime

from v_flask.extensions import db


class ExternalApi(db.Model):
    """External API registration for the marketplace.

    Stores metadata about APIs that are documented in the marketplace.
    The actual OpenAPI spec is fetched from the spec_url and cached.

    Attributes:
        id: Primary key.
        name: Display name of the API.
        slug: URL-safe identifier.
        description: Short description.
        spec_url: URL to fetch OpenAPI spec (JSON/YAML).
        spec_data: Cached OpenAPI spec as JSON string.
        documentation_html: Generated documentation HTML (cached).
        base_url: API base URL for requests.
        auth_header_name: Name of auth header (e.g., 'X-API-Key').
        status: API status ('active', 'inactive', 'maintenance').
        icon_url: URL to API icon/logo.
        spec_cached_at: When spec was last fetched.
        created_at: When API was registered.
        updated_at: When API was last modified.
    """

    __tablename__ = 'api_market_external_api'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    spec_url = db.Column(db.String(500), nullable=False)
    spec_data = db.Column(db.Text)  # Cached JSON
    documentation_html = db.Column(db.Text)  # Generated docs
    base_url = db.Column(db.String(500))
    auth_header_name = db.Column(db.String(50), default='X-API-Key')
    status = db.Column(db.String(20), default='active', nullable=False)
    icon_url = db.Column(db.String(500))
    spec_cached_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<ExternalApi {self.slug} ({self.status})>'

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'spec_url': self.spec_url,
            'base_url': self.base_url,
            'auth_header_name': self.auth_header_name,
            'status': self.status,
            'icon_url': self.icon_url,
            'spec_cached_at': self.spec_cached_at.isoformat() if self.spec_cached_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def needs_refresh(self, ttl_seconds: int = 3600) -> bool:
        """Check if the cached spec needs to be refreshed.

        Args:
            ttl_seconds: Time-to-live in seconds (default: 1 hour).

        Returns:
            True if spec should be refreshed.
        """
        if not self.spec_cached_at or not self.spec_data:
            return True
        age = (datetime.utcnow() - self.spec_cached_at).total_seconds()
        return age > ttl_seconds

    def update_spec(self, spec_data: str, documentation_html: str = None) -> None:
        """Update the cached spec data.

        Args:
            spec_data: OpenAPI spec as JSON string.
            documentation_html: Generated documentation HTML (optional).
        """
        self.spec_data = spec_data
        self.spec_cached_at = datetime.utcnow()
        if documentation_html:
            self.documentation_html = documentation_html
