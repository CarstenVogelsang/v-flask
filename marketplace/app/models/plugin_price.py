"""PluginPrice model for differentiated pricing per project type."""
from datetime import datetime, timezone

from v_flask import db


class PluginPrice(db.Model):
    """Pricing per plugin and project type.

    Allows different prices for the same plugin based on project type.
    Example: CRM plugin costs 50 EUR/month for Einzelkunde,
             but 200 EUR/month for Business Directory.
    """

    __tablename__ = 'marketplace_plugin_price'

    id = db.Column(db.Integer, primary_key=True)
    plugin_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_plugin_meta.id'),
        nullable=False,
        index=True
    )
    project_type_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project_type.id'),
        nullable=False,
        index=True
    )

    # Pricing
    price_cents = db.Column(db.Integer, nullable=False)
    billing_cycle = db.Column(
        db.String(20),
        default='once',
        nullable=False
    )  # once, monthly, yearly, usage
    currency = db.Column(db.String(3), default='EUR', nullable=False)

    # Usage-based pricing (for future use)
    usage_unit = db.Column(db.String(50), nullable=True)  # e.g., "API calls"
    usage_price_per_unit = db.Column(db.Integer, nullable=True)  # cents per unit
    included_units = db.Column(db.Integer, nullable=True)  # free units included

    # Setup fee (optional)
    setup_fee_cents = db.Column(db.Integer, default=0, nullable=False)

    # Validity
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    valid_from = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    valid_until = db.Column(db.DateTime, nullable=True)  # NULL = unlimited

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
    plugin = db.relationship('PluginMeta', back_populates='prices')
    project_type = db.relationship('ProjectType', back_populates='prices')
    licenses = db.relationship('License', back_populates='plugin_price', lazy='dynamic')

    # Unique constraint: one price per plugin-projecttype-billingcycle combination
    __table_args__ = (
        db.UniqueConstraint(
            'plugin_id', 'project_type_id', 'billing_cycle',
            name='uq_plugin_projecttype_billing'
        ),
        db.Index('idx_price_active', 'is_active'),
    )

    def __repr__(self) -> str:
        return f'<PluginPrice {self.plugin_id}/{self.project_type_id}: {self.price_cents}c>'

    @property
    def price_display(self) -> str:
        """Get formatted price for display."""
        if self.price_cents == 0:
            return 'Kostenlos'
        euros = self.price_cents / 100
        formatted = f'{euros:.2f} €'.replace('.', ',')

        suffix_map = {
            'once': '',
            'monthly': '/Monat',
            'yearly': '/Jahr',
            'usage': ' (nutzungsbasiert)',
        }
        return formatted + suffix_map.get(self.billing_cycle, '')

    @property
    def is_free(self) -> bool:
        """Check if this price is free."""
        return self.price_cents == 0

    @property
    def is_valid(self) -> bool:
        """Check if this price is currently valid."""
        if not self.is_active:
            return False
        now = datetime.now(timezone.utc)
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True

    @classmethod
    def get_for_plugin_and_type(
        cls,
        plugin_id: int,
        project_type_id: int,
        billing_cycle: str = 'once'
    ) -> 'PluginPrice | None':
        """Get active price for a specific plugin and project type."""
        return cls.query.filter_by(
            plugin_id=plugin_id,
            project_type_id=project_type_id,
            billing_cycle=billing_cycle,
            is_active=True
        ).first()

    @classmethod
    def get_price_matrix(cls, plugin_id: int) -> dict:
        """Get all active prices for a plugin grouped by project type.

        Returns:
            Dict mapping project_type_code to list of price dicts.
        """
        prices = cls.query.filter_by(
            plugin_id=plugin_id,
            is_active=True
        ).all()

        matrix = {}
        for price in prices:
            code = price.project_type.code
            if code not in matrix:
                matrix[code] = []
            matrix[code].append({
                'billing_cycle': price.billing_cycle,
                'price_cents': price.price_cents,
                'price_display': price.price_display,
                'setup_fee_cents': price.setup_fee_cents,
            })

        return matrix
