"""ProjectType model for categorizing satellite projects."""
from datetime import datetime, timezone

from v_flask import db


class ProjectType(db.Model):
    """Project type classification for satellite installations.

    Determines pricing tier, trial duration, and available features.

    Types:
    - business_directory: Branchenverzeichnisse (high volume, 14-day trial)
    - einzelkunde: Normal websites (standard pricing, 30-day trial)
    - city_server: City portals (volume discount, 30-day trial)
    - intern: Internal projects (free, no trial needed)
    """

    __tablename__ = 'marketplace_project_type'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    trial_days = db.Column(db.Integer, default=0, nullable=False)
    is_free = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_base_type = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
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
    projects = db.relationship('Project', back_populates='project_type', lazy='dynamic')
    prices = db.relationship('PluginPrice', back_populates='project_type', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<ProjectType {self.code}: {self.name}>'

    @property
    def has_trial(self) -> bool:
        """Check if this project type offers a trial period."""
        return self.trial_days > 0 and not self.is_free

    @classmethod
    def get_by_code(cls, code: str) -> 'ProjectType | None':
        """Get project type by code."""
        return cls.query.filter_by(code=code).first()

    @classmethod
    def get_active_types(cls) -> list['ProjectType']:
        """Get all active project types ordered by sort_order."""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()

    @classmethod
    def seed_defaults(cls) -> list['ProjectType']:
        """Create default project types if they don't exist.

        Returns:
            List of created project types (empty if all exist).
        """
        defaults = [
            {
                'code': 'einzelkunde',
                'name': 'Einzelkunde',
                'description': 'Normale Unternehmens-Webseiten',
                'trial_days': 30,
                'is_free': False,
                'is_base_type': True,  # Base type for default pricing
                'sort_order': 1,
            },
            {
                'code': 'business_directory',
                'name': 'Branchenverzeichnis',
                'description': 'Branchenverzeichnisse mit hohem Datenvolumen',
                'trial_days': 14,
                'is_free': False,
                'is_base_type': False,
                'sort_order': 2,
            },
            {
                'code': 'city_server',
                'name': 'City Server',
                'description': 'Stadtportale und kommunale Projekte',
                'trial_days': 30,
                'is_free': False,
                'is_base_type': False,
                'sort_order': 3,
            },
            {
                'code': 'intern',
                'name': 'Intern',
                'description': 'Interne Projekte (kostenlos)',
                'trial_days': 0,
                'is_free': True,
                'is_base_type': False,
                'sort_order': 100,  # High value to visually separate from others
            },
        ]

        created = []
        for data in defaults:
            existing = cls.get_by_code(data['code'])
            if not existing:
                project_type = cls(**data)
                db.session.add(project_type)
                created.append(project_type)

        if created:
            db.session.commit()

        return created
