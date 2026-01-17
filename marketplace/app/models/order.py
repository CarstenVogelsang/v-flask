"""Order model for purchase tracking."""
from datetime import datetime, timezone

from v_flask import db


class Order(db.Model):
    """Order for tracking plugin purchases.

    Used for audit trail and Stripe integration.
    """

    __tablename__ = 'marketplace_order'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project.id'),
        nullable=False,
        index=True
    )
    plugin_name = db.Column(db.String(100), nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.String(20),
        default='pending',
        nullable=False
    )  # pending, completed, failed, refunded
    stripe_session_id = db.Column(db.String(255), nullable=True, unique=True)
    stripe_payment_intent_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    project = db.relationship('Project', back_populates='orders')

    def __repr__(self) -> str:
        return f'<Order {self.id}: {self.plugin_name} ({self.status})>'

    @property
    def amount_display(self) -> str:
        """Get formatted amount for display."""
        if self.amount_cents == 0:
            return 'Kostenlos'
        euros = self.amount_cents / 100
        return f'{euros:.2f} €'.replace('.', ',')

    def mark_completed(self) -> None:
        """Mark order as completed and set timestamp."""
        self.status = 'completed'
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self) -> None:
        """Mark order as failed."""
        self.status = 'failed'
