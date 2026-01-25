"""CustomerGroup model for CRM plugin.

Customer groups for pricing tiers and customer segmentation.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID

from v_flask.extensions import db


class CustomerGroup(db.Model):
    """Customer group for pricing tiers and segmentation.

    Groups customers for applying discount tiers, special conditions,
    or customer classification. The actual pricing logic is handled
    by the Pricing plugin.

    Attributes:
        id: UUID primary key.
        name: Unique group name (e.g., 'Premium', 'Standard', 'VIP').
        description: Optional description of the group.
        discount_percent: Default discount percentage for this group.
        sort_order: Display order in lists and dropdowns.
        is_default: Whether this is the default group for new customers.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.

    Relationships:
        customers: List of customers in this group.

    Example:
        >>> group = CustomerGroup(name='Premium', discount_percent=10.0)
        >>> db.session.add(group)
        >>> db.session.commit()
    """

    __tablename__ = 'crm_customer_group'

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )
    description = db.Column(db.Text, nullable=True)
    discount_percent = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0.00
    )
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationship defined in Customer model via back_populates
    customers = db.relationship(
        'Customer',
        back_populates='group',
        lazy='dynamic'
    )

    def __repr__(self) -> str:
        return f'<CustomerGroup {self.name}>'

    @property
    def customer_count(self) -> int:
        """Get the number of customers in this group."""
        return self.customers.count()

    @classmethod
    def get_default(cls) -> 'CustomerGroup | None':
        """Get the default customer group.

        Returns:
            Default CustomerGroup or None if not set.
        """
        return cls.query.filter_by(is_default=True).first()

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Return list of (id, name) tuples for form selects.

        Returns:
            List of tuples with UUID string and group name.
        """
        groups = cls.query.order_by(cls.sort_order, cls.name).all()
        return [(str(g.id), g.name) for g in groups]

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'discount_percent': float(self.discount_percent) if self.discount_percent else 0.0,
            'sort_order': self.sort_order,
            'is_default': self.is_default,
            'customer_count': self.customer_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
