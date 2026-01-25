"""Order models for Shop plugin."""

import uuid
from datetime import datetime
from enum import Enum

from v_flask.extensions import db


class OrderStatus(str, Enum):
    """Order status values."""

    NEW = 'new'
    CONFIRMED = 'confirmed'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for forms."""
        labels = {
            'new': 'Neu',
            'confirmed': 'Bestätigt',
            'processing': 'In Bearbeitung',
            'shipped': 'Versendet',
            'completed': 'Abgeschlossen',
            'cancelled': 'Storniert',
        }
        return [(s.value, labels.get(s.value, s.value)) for s in cls]


class Order(db.Model):
    """Order header with customer and totals."""

    __tablename__ = 'shop_order'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    order_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )
    customer_id = db.Column(
        db.String(36),
        nullable=True,
        index=True
    )
    status = db.Column(
        db.String(20),
        default=OrderStatus.NEW.value,
        nullable=False
    )

    # Address snapshots as JSON
    shipping_address = db.Column(db.JSON, nullable=False)
    billing_address = db.Column(db.JSON, nullable=True)

    # Amounts
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=19.0)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    # Notes
    notes = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    items = db.relationship(
        'OrderItem',
        back_populates='order',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    history = db.relationship(
        'OrderStatusHistory',
        back_populates='order',
        cascade='all, delete-orphan',
        order_by='OrderStatusHistory.created_at.desc()',
        lazy='dynamic'
    )

    @property
    def status_label(self) -> str:
        """Get human-readable status label."""
        labels = dict(OrderStatus.choices())
        return labels.get(self.status, self.status)

    @property
    def item_count(self) -> int:
        """Total number of items in order."""
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f'<Order {self.order_number} status={self.status}>'


class OrderItem(db.Model):
    """Order line item with product snapshot."""

    __tablename__ = 'shop_order_item'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    order_id = db.Column(
        db.String(36),
        db.ForeignKey('shop_order.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.String(36),
        nullable=True,
        index=True
    )

    # Snapshots at order time
    sku = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationships
    order = db.relationship('Order', back_populates='items')

    def __repr__(self):
        return f'<OrderItem {self.sku} qty={self.quantity}>'


class OrderStatusHistory(db.Model):
    """Order status change audit trail."""

    __tablename__ = 'shop_order_status_history'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    order_id = db.Column(
        db.String(36),
        db.ForeignKey('shop_order.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.String(100), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    order = db.relationship('Order', back_populates='history')

    @property
    def old_status_label(self) -> str:
        """Get human-readable old status label."""
        if not self.old_status:
            return '-'
        labels = dict(OrderStatus.choices())
        return labels.get(self.old_status, self.old_status)

    @property
    def new_status_label(self) -> str:
        """Get human-readable new status label."""
        labels = dict(OrderStatus.choices())
        return labels.get(self.new_status, self.new_status)

    def __repr__(self):
        return f'<OrderStatusHistory {self.old_status} -> {self.new_status}>'
