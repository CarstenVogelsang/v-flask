"""License model for project-plugin relationships."""
from datetime import datetime, timezone

from v_flask import db


# License status constants (using strings for easier migration)
LICENSE_STATUS_ACTIVE = 'active'
LICENSE_STATUS_TRIAL = 'trial'
LICENSE_STATUS_SUSPENDED = 'suspended'
LICENSE_STATUS_EXPIRED = 'expired'
LICENSE_STATUS_REVOKED = 'revoked'

# Billing cycle constants
BILLING_CYCLE_ONCE = 'once'
BILLING_CYCLE_MONTHLY = 'monthly'
BILLING_CYCLE_YEARLY = 'yearly'


class License(db.Model):
    """License linking a project to a plugin.

    A license allows a project to download and use a plugin.
    Can be time-limited (expires_at) or perpetual (expires_at = None).

    Status values:
        - active: Paid and valid license
        - trial: Currently in trial period
        - suspended: Temporarily disabled (e.g., payment issue)
        - expired: Trial or subscription ended
        - revoked: Manually revoked by admin
    """

    __tablename__ = 'marketplace_license'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project.id'),
        nullable=False,
        index=True
    )
    plugin_name = db.Column(db.String(100), nullable=False, index=True)

    # License status and billing
    status = db.Column(
        db.String(20),
        default=LICENSE_STATUS_ACTIVE,
        nullable=False,
        index=True
    )
    billing_cycle = db.Column(
        db.String(20),
        default=BILLING_CYCLE_ONCE,
        nullable=False
    )
    next_billing_date = db.Column(db.DateTime, nullable=True)

    # Pricing reference (for differentiated pricing per project type)
    plugin_price_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_plugin_price.id'),
        nullable=True,
        index=True
    )

    purchased_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at = db.Column(db.DateTime, nullable=True)
    stripe_payment_id = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    project = db.relationship('Project', back_populates='licenses')
    plugin_price = db.relationship('PluginPrice', back_populates='licenses')
    history = db.relationship(
        'LicenseHistory',
        back_populates='license',
        lazy='dynamic',
        order_by='desc(LicenseHistory.created_at)'
    )

    # Unique constraint: one license per project-plugin combination
    __table_args__ = (
        db.UniqueConstraint('project_id', 'plugin_name', name='uq_project_plugin'),
    )

    def __repr__(self) -> str:
        return f'<License {self.project.name if self.project else "?"} -> {self.plugin_name}>'

    @property
    def is_active(self) -> bool:
        """Check if license is currently active and usable.

        A license is active if:
        - Status is 'active' or 'trial'
        - Not expired (expires_at is None or in the future)
        """
        if self.status not in (LICENSE_STATUS_ACTIVE, LICENSE_STATUS_TRIAL):
            return False
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc) < self.expires_at

    @property
    def is_perpetual(self) -> bool:
        """Check if license is perpetual (no expiration)."""
        return self.expires_at is None

    @property
    def is_trial(self) -> bool:
        """Check if license is in trial status."""
        return self.status == LICENSE_STATUS_TRIAL

    @property
    def status_display(self) -> str:
        """Get localized status display text."""
        status_names = {
            LICENSE_STATUS_ACTIVE: 'Aktiv',
            LICENSE_STATUS_TRIAL: 'Testphase',
            LICENSE_STATUS_SUSPENDED: 'Pausiert',
            LICENSE_STATUS_EXPIRED: 'Abgelaufen',
            LICENSE_STATUS_REVOKED: 'Widerrufen',
        }
        return status_names.get(self.status, self.status)

    def change_status(
        self,
        new_status: str,
        performed_by: str | None = None,
        reason: str | None = None
    ) -> 'License':
        """Change license status and log to history.

        Args:
            new_status: New status value
            performed_by: Email of user making change, or 'system'
            reason: Optional reason for the change

        Returns:
            Self for chaining
        """
        from app.models.license_history import LicenseHistory

        old_status = self.status
        self.status = new_status

        # Log the change
        LicenseHistory.log(
            license_id=self.id,
            action='status_changed',
            old_status=old_status,
            new_status=new_status,
            performed_by=performed_by or 'system',
            reason=reason,
        )

        return self
