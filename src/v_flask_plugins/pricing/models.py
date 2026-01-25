"""Database models for the Pricing plugin.

POC: Only customer_product rule type supported.
No tier pricing, no time limits.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from v_flask.extensions import db


class RuleType(str, PyEnum):
    """Type of pricing rule.

    POC: Only CUSTOMER_PRODUCT implemented.
    MVP will add: CUSTOMER_SERIES, CUSTOMER_BRAND, etc.
    """
    CUSTOMER_PRODUCT = 'customer_product'
    # MVP: Add more types later
    # CUSTOMER_SERIES = 'customer_series'
    # CUSTOMER_BRAND = 'customer_brand'
    # CUSTOMER_MANUFACTURER = 'customer_manufacturer'
    # CUSTOMER_PRODUCT_GROUP = 'customer_product_group'
    # CUSTOMER_PRICE_TAG = 'customer_price_tag'
    # GROUP_GLOBAL = 'group_global'


class PriceType(str, PyEnum):
    """Type of price modification."""
    FIXED = 'fixed'                      # Fixed price in EUR
    DISCOUNT_PERCENT = 'discount_percent'  # Discount percentage


class PricingRule(db.Model):
    """Pricing rule for customer-specific prices.

    POC Scope:
    - Only customer_product type (customer + product)
    - Fixed prices or percentage discounts
    - No tier pricing
    - No valid_from/valid_to

    Attributes:
        id: UUID primary key
        name: Human-readable rule name
        rule_type: Type of rule (POC: only customer_product)
        customer_id: Reference to CRM customer (String FK)
        product_id: Reference to PIM product (String FK)
        price_type: Fixed price or discount percentage
        price_value: The price in EUR or discount in %
        is_active: Whether the rule is active
        note: Optional internal note
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = 'pricing_rule'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name = db.Column(db.String(255), nullable=False)

    # Rule type (POC: only customer_product)
    rule_type = db.Column(
        db.String(50),
        nullable=False,
        default=RuleType.CUSTOMER_PRODUCT.value
    )

    # Customer reference (String FK to crm_customer.id - UUID as string)
    # No SQLAlchemy relationship to avoid cross-plugin coupling
    customer_id = db.Column(db.String(36), nullable=False, index=True)

    # Product reference (String FK to pim_product.id - UUID as string)
    # No SQLAlchemy relationship to avoid cross-plugin coupling
    product_id = db.Column(db.String(36), nullable=False, index=True)

    # Price configuration
    price_type = db.Column(
        db.String(20),
        nullable=False,
        default=PriceType.FIXED.value
    )
    price_value = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )  # EUR or percent

    # Status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    note = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Unique constraint: one rule per customer-product combination
    __table_args__ = (
        db.UniqueConstraint(
            'customer_id',
            'product_id',
            name='uq_pricing_rule_customer_product'
        ),
        db.Index('idx_pricing_rule_customer', 'customer_id'),
        db.Index('idx_pricing_rule_product', 'product_id'),
    )

    def __repr__(self):
        return f'<PricingRule {self.id}: {self.name}>'

    @property
    def is_fixed_price(self) -> bool:
        """Check if this is a fixed price rule."""
        return self.price_type == PriceType.FIXED.value

    @property
    def is_discount(self) -> bool:
        """Check if this is a discount rule."""
        return self.price_type == PriceType.DISCOUNT_PERCENT.value


__all__ = ['RuleType', 'PriceType', 'PricingRule']
