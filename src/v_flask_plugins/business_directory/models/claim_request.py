"""ClaimRequest Model.

Ownership claims for existing directory entries.
"""

from datetime import datetime, timezone

from v_flask.extensions import db


class ClaimRequest(db.Model):
    """Request to claim ownership of an existing directory entry.

    When a business owner wants to take over an existing entry,
    they submit a claim with proof of ownership. An admin reviews
    the claim and approves or rejects it.

    Usage:
        # Create claim request
        claim = ClaimRequest(
            entry_id=entry.id,
            user_id=current_user.id,
            nachweis_typ='impressum',
            nachweis_url='https://example.com/impressum'
        )
        db.session.add(claim)
        db.session.commit()

        # Admin approves claim
        claim.approve(admin_user)
        # This sets entry.owner_id = claim.user_id

        # Admin rejects claim
        claim.reject(admin_user, reason='Nachweis nicht ausreichend')
    """

    __tablename__ = 'business_directory_claim_request'

    id = db.Column(db.Integer, primary_key=True)

    # References
    entry_id = db.Column(
        db.Integer,
        db.ForeignKey('business_directory_entry.id'),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False,
        index=True
    )

    # Claim evidence
    nachweis_typ = db.Column(db.String(50))
    # Values: impressum, social_media, telefon, gewerbeanmeldung, sonstiges

    nachweis_url = db.Column(db.String(500))
    # e.g. impressum URL, Facebook page, Instagram profile

    nachweis_text = db.Column(db.Text)
    # Additional explanation or notes

    # Status: pending, approved, rejected
    status = db.Column(db.String(20), default='pending', index=True)

    # Admin response
    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    entry = db.relationship(
        'DirectoryEntry',
        back_populates='claim_requests'
    )
    user = db.relationship(
        'User',
        foreign_keys=[user_id],
        backref=db.backref('directory_claim_requests', lazy='dynamic')
    )
    reviewer = db.relationship(
        'User',
        foreign_keys=[reviewed_by]
    )

    def __repr__(self) -> str:
        return f'<ClaimRequest {self.id} entry={self.entry_id} status={self.status}>'

    @property
    def is_pending(self) -> bool:
        """Check if claim is pending review."""
        return self.status == 'pending'

    @property
    def is_approved(self) -> bool:
        """Check if claim was approved."""
        return self.status == 'approved'

    @property
    def is_rejected(self) -> bool:
        """Check if claim was rejected."""
        return self.status == 'rejected'

    def approve(self, admin_user) -> None:
        """Approve the claim and transfer ownership.

        Args:
            admin_user: The admin user approving the claim.
        """
        from .directory_entry import DirectoryEntry

        self.status = 'approved'
        self.reviewed_by = admin_user.id
        self.reviewed_at = datetime.now(timezone.utc)

        # Transfer ownership
        entry = db.session.get(DirectoryEntry, self.entry_id)
        if entry:
            entry.owner_id = self.user_id
            entry.self_managed = True

        db.session.commit()

    def reject(self, admin_user, reason: str = None) -> None:
        """Reject the claim.

        Args:
            admin_user: The admin user rejecting the claim.
            reason: Optional reason for rejection (shown to user).
        """
        self.status = 'rejected'
        self.reviewed_by = admin_user.id
        self.reviewed_at = datetime.now(timezone.utc)
        self.rejection_reason = reason
        db.session.commit()

    @classmethod
    def get_pending_count(cls) -> int:
        """Get count of pending claims."""
        return cls.query.filter_by(status='pending').count()

    @classmethod
    def get_pending(cls) -> list['ClaimRequest']:
        """Get all pending claims ordered by date."""
        return cls.query.filter_by(status='pending').order_by(
            cls.created_at.asc()
        ).all()

    @classmethod
    def get_for_entry(cls, entry_id: int) -> list['ClaimRequest']:
        """Get all claims for an entry.

        Args:
            entry_id: The DirectoryEntry ID.

        Returns:
            List of ClaimRequest instances.
        """
        return cls.query.filter_by(entry_id=entry_id).order_by(
            cls.created_at.desc()
        ).all()

    @classmethod
    def has_pending_claim(cls, entry_id: int, user_id: int) -> bool:
        """Check if user has a pending claim for an entry.

        Args:
            entry_id: The DirectoryEntry ID.
            user_id: The user ID.

        Returns:
            True if pending claim exists.
        """
        return cls.query.filter_by(
            entry_id=entry_id,
            user_id=user_id,
            status='pending'
        ).first() is not None
