"""PluginMeta model for plugin pricing and metadata."""
from datetime import datetime, timezone

from v_flask import db


class PluginMeta(db.Model):
    """Plugin metadata for pricing and marketplace display.

    The actual plugin code lives in src/v_flask_plugins/.
    This model stores marketplace-specific info like prices.
    """

    __tablename__ = 'marketplace_plugin_meta'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    long_description = db.Column(db.Text, nullable=True)
    version = db.Column(db.String(50), default='0.1.0', nullable=False)
    price_cents = db.Column(db.Integer, default=0, nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    screenshot_url = db.Column(db.String(500), nullable=True)
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

    def __repr__(self) -> str:
        return f'<PluginMeta {self.name}>'

    @property
    def price_display(self) -> str:
        """Get formatted price for display."""
        if self.price_cents == 0:
            return 'Kostenlos'
        euros = self.price_cents / 100
        return f'{euros:.2f} €'.replace('.', ',')

    @property
    def is_free(self) -> bool:
        """Check if plugin is free."""
        return self.price_cents == 0
