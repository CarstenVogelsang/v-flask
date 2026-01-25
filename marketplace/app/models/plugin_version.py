"""PluginVersion model for tracking plugin version history."""
from datetime import datetime, timezone

from v_flask import db


class PluginVersion(db.Model):
    """Plugin version history.

    Tracks all released versions with changelog and compatibility info.
    The current version is also stored in PluginMeta.version for quick access.
    """

    __tablename__ = 'marketplace_plugin_version'

    id = db.Column(db.Integer, primary_key=True)
    plugin_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_plugin_meta.id'),
        nullable=False,
        index=True
    )

    # Version info
    version = db.Column(db.String(20), nullable=False)  # Semantic versioning: "1.2.3"
    changelog = db.Column(db.Text, nullable=True)  # Markdown formatted
    release_notes = db.Column(db.Text, nullable=True)  # Detailed release notes

    # Compatibility
    min_v_flask_version = db.Column(db.String(20), nullable=True)  # e.g., "0.2.0"
    is_breaking_change = db.Column(db.Boolean, default=False, nullable=False)

    # Status
    is_stable = db.Column(db.Boolean, default=True, nullable=False)
    is_current = db.Column(db.Boolean, default=False, nullable=False)  # Current version marker

    # Statistics
    download_count = db.Column(db.Integer, default=0, nullable=False)

    # Audit
    released_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    released_by = db.Column(db.String(255), nullable=True)  # email of releaser

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    plugin = db.relationship('PluginMeta', back_populates='versions')

    # Unique constraint: one version number per plugin
    __table_args__ = (
        db.UniqueConstraint('plugin_id', 'version', name='uq_plugin_version'),
        db.Index('idx_version_current', 'plugin_id', 'is_current'),
    )

    def __repr__(self) -> str:
        return f'<PluginVersion {self.plugin.name if self.plugin else "?"} v{self.version}>'

    @property
    def version_tuple(self) -> tuple:
        """Parse version string to tuple for comparison.

        Returns:
            Tuple of (major, minor, patch) as integers.
        """
        try:
            parts = self.version.split('.')
            return tuple(int(p) for p in parts[:3])
        except (ValueError, AttributeError):
            return (0, 0, 0)

    def increment_download_count(self):
        """Increment download counter and save."""
        self.download_count += 1
        db.session.commit()

    @classmethod
    def get_for_plugin(
        cls,
        plugin_id: int,
        only_stable: bool = False
    ) -> list['PluginVersion']:
        """Get all versions for a plugin, newest first.

        Args:
            plugin_id: ID of the plugin
            only_stable: If True, only return stable versions

        Returns:
            List of PluginVersion objects.
        """
        query = cls.query.filter_by(plugin_id=plugin_id)
        if only_stable:
            query = query.filter_by(is_stable=True)
        return query.order_by(cls.released_at.desc()).all()

    @classmethod
    def get_current(cls, plugin_id: int) -> 'PluginVersion | None':
        """Get the current (latest stable) version for a plugin."""
        return cls.query.filter_by(
            plugin_id=plugin_id,
            is_current=True
        ).first()

    @classmethod
    def get_by_version(
        cls,
        plugin_id: int,
        version: str
    ) -> 'PluginVersion | None':
        """Get a specific version of a plugin."""
        return cls.query.filter_by(
            plugin_id=plugin_id,
            version=version
        ).first()

    @classmethod
    def create_version(
        cls,
        plugin_id: int,
        version: str,
        changelog: str | None = None,
        release_notes: str | None = None,
        min_v_flask_version: str | None = None,
        is_breaking_change: bool = False,
        is_stable: bool = True,
        released_by: str | None = None,
        set_as_current: bool = True
    ) -> 'PluginVersion':
        """Create a new version and optionally set it as current.

        Args:
            plugin_id: ID of the plugin
            version: Version string (e.g., "1.2.3")
            changelog: Markdown changelog
            release_notes: Detailed release notes
            min_v_flask_version: Minimum required v-flask version
            is_breaking_change: Whether this is a breaking change
            is_stable: Whether this is a stable release
            released_by: Email of the person releasing
            set_as_current: Whether to set this as the current version

        Returns:
            Created PluginVersion object.
        """
        # If setting as current, unset previous current version
        if set_as_current:
            cls.query.filter_by(
                plugin_id=plugin_id,
                is_current=True
            ).update({'is_current': False})

        new_version = cls(
            plugin_id=plugin_id,
            version=version,
            changelog=changelog,
            release_notes=release_notes,
            min_v_flask_version=min_v_flask_version,
            is_breaking_change=is_breaking_change,
            is_stable=is_stable,
            is_current=set_as_current,
            released_by=released_by,
        )

        db.session.add(new_version)

        # Also update the version in PluginMeta if setting as current
        if set_as_current:
            from app.models.plugin_meta import PluginMeta
            plugin = PluginMeta.query.get(plugin_id)
            if plugin:
                plugin.version = version

        db.session.commit()
        return new_version
