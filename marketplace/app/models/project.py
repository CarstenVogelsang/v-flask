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

    # Superadmin projects can see alpha/beta plugins (V-Flask internal projects)
    is_superadmin = db.Column(db.Boolean, default=False, nullable=False)

    # Project type (for pricing tiers)
    project_type_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project_type.id'),
        nullable=True,  # Nullable for migration of existing data
        index=True
    )

    # Trial period tracking
    trial_start_date = db.Column(db.DateTime, nullable=True)
    trial_end_date = db.Column(db.DateTime, nullable=True)

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
    project_type = db.relationship('ProjectType', back_populates='projects')

    def __repr__(self) -> str:
        return f'<Project {self.name}>'

    @property
    def can_see_dev_plugins(self) -> bool:
        """Check if project can see alpha/beta plugins.

        Superadmin projects (internal V-Flask projects) can see all phases.
        Normal projects only see stable releases (v1+).
        """
        return self.is_superadmin

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

    @property
    def is_in_trial(self) -> bool:
        """Check if project is currently in trial period."""
        if not self.trial_start_date or not self.trial_end_date:
            return False
        now = datetime.now(timezone.utc)
        return self.trial_start_date <= now <= self.trial_end_date

    @property
    def is_trial_expired(self) -> bool:
        """Check if trial period has expired."""
        if not self.trial_end_date:
            return False
        return datetime.now(timezone.utc) > self.trial_end_date

    @property
    def trial_days_remaining(self) -> int | None:
        """Get remaining trial days, or None if not in trial."""
        if not self.trial_end_date:
            return None
        now = datetime.now(timezone.utc)
        if now > self.trial_end_date:
            return 0
        delta = self.trial_end_date - now
        return max(0, delta.days)

    def start_trial(self, days: int | None = None) -> bool:
        """Start trial period for this project.

        Args:
            days: Number of trial days. If None, uses project_type.trial_days.

        Returns:
            True if trial started, False if not allowed.
        """
        from datetime import timedelta

        if days is None:
            if not self.project_type or not self.project_type.has_trial:
                return False
            days = self.project_type.trial_days

        if days <= 0:
            return False

        now = datetime.now(timezone.utc)
        self.trial_start_date = now
        self.trial_end_date = now + timedelta(days=days)
        db.session.commit()
        return True
