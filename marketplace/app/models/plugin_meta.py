"""PluginMeta model for plugin pricing and metadata."""
from datetime import datetime, timezone

from v_flask import db


class PluginMeta(db.Model):
    """Plugin metadata for pricing and marketplace display.

    The actual plugin code lives in src/v_flask_plugins/.
    This model stores marketplace-specific info like prices.

    For differentiated pricing (price per project type), use the
    PluginPrice model. The price_cents field here is the default/base price.
    """

    __tablename__ = 'marketplace_plugin_meta'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    long_description = db.Column(db.Text, nullable=True)
    version = db.Column(db.String(50), default='0.1.0', nullable=False)

    # Base price (fallback if no differentiated pricing configured)
    price_cents = db.Column(db.Integer, default=0, nullable=False)

    # Plugin metadata
    category = db.Column(db.String(50), nullable=True, index=True)  # Legacy, use category_id
    min_v_flask_version = db.Column(db.String(20), nullable=True)
    has_trial = db.Column(db.Boolean, default=True, nullable=False)

    # Icon (Tabler icon class, e.g. "ti ti-puzzle")
    icon = db.Column(db.String(100), default='ti ti-puzzle', nullable=False)

    # Category relationship (replaces legacy category string field)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_plugin_category.id'),
        nullable=True,
        index=True
    )

    # Development phase: alpha (POC), beta (MVP), v1, v2, etc.
    phase = db.Column(
        db.String(20),
        default='alpha',
        nullable=False,
        index=True
    )

    # Display settings
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    screenshot_url = db.Column(db.String(500), nullable=True)

    # Billing options
    allow_one_time_purchase = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    prices = db.relationship(
        'PluginPrice',
        back_populates='plugin',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    versions = db.relationship(
        'PluginVersion',
        back_populates='plugin',
        lazy='dynamic',
        order_by='desc(PluginVersion.released_at)',
        cascade='all, delete-orphan'
    )
    category_rel = db.relationship(
        'PluginCategory',
        backref='plugins',
        lazy='joined'
    )

    def __repr__(self) -> str:
        return f'<PluginMeta {self.name}>'

    @property
    def price_display(self) -> str:
        """Get formatted base price for display."""
        if self.price_cents == 0:
            return 'Kostenlos'
        euros = self.price_cents / 100
        return f'{euros:.2f} €'.replace('.', ',')

    @property
    def is_free(self) -> bool:
        """Check if plugin is free (base price is 0)."""
        return self.price_cents == 0

    @property
    def phase_display(self) -> str:
        """Get display name for development phase."""
        mapping = {
            'alpha': 'Alpha (POC)',
            'beta': 'Beta (MVP)',
        }
        return mapping.get(self.phase, self.phase.upper())

    @property
    def is_stable(self) -> bool:
        """Check if plugin is in a stable release phase (v1+)."""
        return self.phase.startswith('v')

    @property
    def phase_from_version(self) -> str:
        """Compute development phase from version string.

        Mapping:
        - 0.0-0.8 = alpha (POC)
        - 0.9-0.99 = beta (MVP)
        - 1.x = v1
        - 2.x = v2
        - etc.

        Returns:
            Phase string: 'alpha', 'beta', 'v1', 'v2', etc.
        """
        try:
            parts = self.version.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0

            if major == 0:
                if minor >= 9:
                    return 'beta'
                return 'alpha'
            return f'v{major}'
        except (ValueError, IndexError):
            return 'alpha'

    @property
    def phase_badge(self) -> dict:
        """Get badge styling data for UI display.

        Uses phase_from_version for automatic phase detection.

        Returns:
            Dict with 'label' and 'color' (DaisyUI badge class)
        """
        phase = self.phase_from_version
        badges = {
            'alpha': {'label': 'Alpha', 'color': 'badge-warning'},
            'beta': {'label': 'Beta', 'color': 'badge-info'},
        }
        if phase.startswith('v'):
            return {'label': phase.upper(), 'color': 'badge-success'}
        return badges.get(phase, {'label': phase, 'color': 'badge-neutral'})

    @property
    def current_version(self) -> 'PluginVersion | None':
        """Get the current (latest stable) version object."""
        from app.models.plugin_version import PluginVersion
        return PluginVersion.get_current(self.id)

    def get_price_for_project_type(self, project_type_id: int) -> 'PluginPrice | None':
        """Get differentiated price for a specific project type.

        Args:
            project_type_id: ID of the project type

        Returns:
            PluginPrice if configured, None to use base price
        """
        return self.prices.filter_by(
            project_type_id=project_type_id,
            is_active=True
        ).first()

    def get_effective_price_cents(self, project_type_id: int | None = None) -> int:
        """Get effective price in cents for a project type.

        Uses differentiated price if available, otherwise base price.

        Args:
            project_type_id: Optional project type ID

        Returns:
            Price in cents
        """
        if project_type_id:
            price = self.get_price_for_project_type(project_type_id)
            if price:
                return price.price_cents
        return self.price_cents

    def get_all_versions(self, only_stable: bool = False) -> list:
        """Get all versions, newest first.

        Args:
            only_stable: If True, only return stable versions

        Returns:
            List of PluginVersion objects
        """
        query = self.versions
        if only_stable:
            query = query.filter_by(is_stable=True)
        return query.all()
