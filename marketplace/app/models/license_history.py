"""LicenseHistory model for audit trail of license changes."""
from datetime import datetime, timezone

from v_flask import db


class LicenseHistory(db.Model):
    """Audit trail for license status changes.

    Records all status transitions for compliance, debugging,
    and customer support purposes.
    """

    __tablename__ = 'marketplace_license_history'

    id = db.Column(db.Integer, primary_key=True)
    license_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_license.id'),
        nullable=False,
        index=True
    )

    # Action type
    action = db.Column(
        db.String(30),
        nullable=False
    )  # created, activated, renewed, expired, suspended, revoked, upgraded, downgraded, trial_started, trial_converted

    # Status change tracking
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=True)

    # Date change tracking
    old_expires_at = db.Column(db.DateTime, nullable=True)
    new_expires_at = db.Column(db.DateTime, nullable=True)

    # Billing info (for renewals/upgrades)
    old_billing_cycle = db.Column(db.String(20), nullable=True)
    new_billing_cycle = db.Column(db.String(20), nullable=True)

    # Audit info
    performed_by = db.Column(db.String(255), nullable=True)  # email or "system"
    performed_by_type = db.Column(
        db.String(20),
        default='system',
        nullable=False
    )  # system, admin, api, customer
    reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Additional metadata
    metadata_json = db.Column(db.Text, nullable=True)  # JSON string for extra data

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    license = db.relationship('License', back_populates='history')

    __table_args__ = (
        db.Index('idx_history_action', 'action'),
    )

    def __repr__(self) -> str:
        return f'<LicenseHistory {self.license_id}: {self.action}>'

    @property
    def extra_data(self) -> dict:
        """Parse metadata JSON to dict."""
        if not self.metadata_json:
            return {}
        import json
        try:
            return json.loads(self.metadata_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    @extra_data.setter
    def extra_data(self, value: dict):
        """Serialize dict to JSON for storage."""
        import json
        self.metadata_json = json.dumps(value) if value else None

    @classmethod
    def log(
        cls,
        license_id: int,
        action: str,
        old_status: str | None = None,
        new_status: str | None = None,
        old_expires_at: datetime | None = None,
        new_expires_at: datetime | None = None,
        performed_by: str | None = None,
        performed_by_type: str = 'system',
        reason: str | None = None,
        notes: str | None = None,
        extra_data: dict | None = None,
        **kwargs
    ) -> 'LicenseHistory':
        """Create a new history entry.

        Args:
            license_id: ID of the license
            action: Action type (created, activated, etc.)
            old_status: Previous status (if applicable)
            new_status: New status (if applicable)
            old_expires_at: Previous expiration date
            new_expires_at: New expiration date
            performed_by: Email or identifier of who performed the action
            performed_by_type: Type of performer (system, admin, api, customer)
            reason: Reason for the change
            notes: Additional notes
            extra_data: Extra data as dict (stored as JSON)

        Returns:
            Created LicenseHistory entry.
        """
        entry = cls(
            license_id=license_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            old_expires_at=old_expires_at,
            new_expires_at=new_expires_at,
            old_billing_cycle=kwargs.get('old_billing_cycle'),
            new_billing_cycle=kwargs.get('new_billing_cycle'),
            performed_by=performed_by,
            performed_by_type=performed_by_type,
            reason=reason,
            notes=notes,
        )
        if extra_data:
            entry.extra_data = extra_data

        db.session.add(entry)
        db.session.commit()
        return entry

    @classmethod
    def get_for_license(
        cls,
        license_id: int,
        limit: int = 50
    ) -> list['LicenseHistory']:
        """Get history entries for a license, newest first."""
        return cls.query.filter_by(
            license_id=license_id
        ).order_by(
            cls.created_at.desc()
        ).limit(limit).all()
