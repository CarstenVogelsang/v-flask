"""Plugin activation model for tracking enabled plugins."""

from datetime import datetime, UTC

from v_flask.extensions import db


class PluginActivation(db.Model):
    """Tracks which plugins are activated in the system.

    This model stores the activation state of plugins. When a plugin is
    activated, it's recorded here. On app startup, VFlask reads this table
    to determine which plugins to load.

    Attributes:
        id: Primary key.
        plugin_name: Unique plugin identifier (from PluginManifest.name).
        is_active: Whether the plugin is currently active.
        activated_at: When the plugin was last activated.
        activated_by_id: User who activated the plugin.
        deactivated_at: When the plugin was last deactivated.

    Usage:
        # Check if a plugin is active
        activation = PluginActivation.get_by_name('kontakt')
        if activation and activation.is_active:
            # Plugin is active

        # Activate a plugin
        PluginActivation.activate('kontakt', user_id=1)

        # Deactivate a plugin
        PluginActivation.deactivate('kontakt')
    """

    __tablename__ = 'v_flask_plugin_activation'

    id = db.Column(db.Integer, primary_key=True)
    plugin_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    activated_at = db.Column(db.DateTime)
    activated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    deactivated_at = db.Column(db.DateTime)

    # Relationship to User (optional, for audit purposes)
    activated_by = db.relationship(
        'User',
        foreign_keys=[activated_by_id],
        backref=db.backref('plugin_activations', lazy='dynamic')
    )

    def __repr__(self) -> str:
        status = 'active' if self.is_active else 'inactive'
        return f'<PluginActivation {self.plugin_name} ({status})>'

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'plugin_name': self.plugin_name,
            'is_active': self.is_active,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'activated_by_id': self.activated_by_id,
            'deactivated_at': self.deactivated_at.isoformat() if self.deactivated_at else None,
        }

    @classmethod
    def get_by_name(cls, plugin_name: str) -> 'PluginActivation | None':
        """Get activation record by plugin name.

        Args:
            plugin_name: The plugin name to look up.

        Returns:
            PluginActivation instance or None if not found.
        """
        return db.session.query(cls).filter_by(plugin_name=plugin_name).first()

    @classmethod
    def get_active_plugins(cls) -> list[str]:
        """Get list of all active plugin names.

        Returns:
            List of plugin names that are currently active.
        """
        activations = db.session.query(cls).filter_by(is_active=True).all()
        return [a.plugin_name for a in activations]

    @classmethod
    def activate(cls, plugin_name: str, user_id: int | None = None) -> 'PluginActivation':
        """Activate a plugin.

        Creates or updates the activation record for the plugin.

        Args:
            plugin_name: The plugin name to activate.
            user_id: Optional user ID who is activating the plugin.

        Returns:
            The PluginActivation instance.
        """
        activation = cls.get_by_name(plugin_name)

        if activation:
            activation.is_active = True
            activation.activated_at = datetime.now(UTC)
            activation.activated_by_id = user_id
            activation.deactivated_at = None
        else:
            activation = cls(
                plugin_name=plugin_name,
                is_active=True,
                activated_at=datetime.now(UTC),
                activated_by_id=user_id,
            )
            db.session.add(activation)

        db.session.commit()
        return activation

    @classmethod
    def deactivate(cls, plugin_name: str) -> 'PluginActivation | None':
        """Deactivate a plugin.

        Args:
            plugin_name: The plugin name to deactivate.

        Returns:
            The PluginActivation instance or None if not found.
        """
        activation = cls.get_by_name(plugin_name)

        if activation:
            activation.is_active = False
            activation.deactivated_at = datetime.now(UTC)
            db.session.commit()

        return activation
