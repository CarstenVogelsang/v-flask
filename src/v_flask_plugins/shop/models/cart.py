"""Cart models for Shop plugin."""

import uuid
from datetime import datetime

from v_flask.extensions import db


class Cart(db.Model):
    """Shopping cart header - one per customer."""

    __tablename__ = 'shop_cart'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    customer_id = db.Column(
        db.String(36),
        nullable=False,
        unique=True,
        index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    items = db.relationship(
        'CartItem',
        back_populates='cart',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    @property
    def item_count(self) -> int:
        """Total number of items in cart."""
        return sum(item.quantity for item in self.items)

    @property
    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return self.items.count() == 0

    def __repr__(self):
        return f'<Cart {self.id[:8]} customer={self.customer_id[:8]}>'


class CartItem(db.Model):
    """Shopping cart line item."""

    __tablename__ = 'shop_cart_item'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    cart_id = db.Column(
        db.String(36),
        db.ForeignKey('shop_cart.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.String(36),
        nullable=False,
        index=True
    )
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Unique constraint: one product per cart
    __table_args__ = (
        db.UniqueConstraint('cart_id', 'product_id', name='uq_cart_product'),
    )

    # Relationships
    cart = db.relationship('Cart', back_populates='items')

    def __repr__(self):
        return f'<CartItem {self.id[:8]} product={self.product_id[:8]} qty={self.quantity}>'
