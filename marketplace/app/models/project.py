"""Project model for satellite projects."""
from datetime import datetime, timezone

from v_flask import db


class Project(db.Model):
    """Satellite project that can purchase and download plugins.

    Each project has a unique API key for authentication.
    """

    __tablename__ = 'marketplace_project'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    owner_email = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
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
    licenses = db.relationship('License', back_populates='project', lazy='dynamic')
    orders = db.relationship('Order', back_populates='project', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Project {self.name}>'

    @property
    def active_licenses(self):
        """Get all active (non-expired) licenses."""
        from app.models.license import License
        now = datetime.now(timezone.utc)
        return self.licenses.filter(
            (License.expires_at.is_(None)) | (License.expires_at > now)
        ).all()

    def has_license_for(self, plugin_name: str) -> bool:
        """Check if project has an active license for a plugin.

        Args:
            plugin_name: Name of the plugin to check.

        Returns:
            True if project has active license, False otherwise.
        """
        from app.models.license import License
        now = datetime.now(timezone.utc)
        return self.licenses.filter(
            License.plugin_name == plugin_name,
            (License.expires_at.is_(None)) | (License.expires_at > now)
        ).count() > 0
