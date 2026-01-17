"""License model for project-plugin relationships."""
from datetime import datetime, timezone

from v_flask import db


class License(db.Model):
    """License linking a project to a plugin.

    A license allows a project to download and use a plugin.
    Can be time-limited (expires_at) or perpetual (expires_at = None).
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

    # Unique constraint: one license per project-plugin combination
    __table_args__ = (
        db.UniqueConstraint('project_id', 'plugin_name', name='uq_project_plugin'),
    )

    def __repr__(self) -> str:
        return f'<License {self.project.name if self.project else "?"} -> {self.plugin_name}>'

    @property
    def is_active(self) -> bool:
        """Check if license is currently active (not expired)."""
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc) < self.expires_at

    @property
    def is_perpetual(self) -> bool:
        """Check if license is perpetual (no expiration)."""
        return self.expires_at is None
