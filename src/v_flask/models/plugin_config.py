"""PluginConfig model for plugin-specific settings.

Provides database-backed configuration storage for plugins,
allowing settings to be managed via admin UI instead of .env files.
"""

import json
from datetime import datetime

from v_flask.extensions import db


class PluginConfig(db.Model):
    """Plugin-specific configuration storage.

    Each plugin can store multiple key-value pairs with type information.
    Supports automatic type conversion for common types.

    Usage:
        from v_flask.models import PluginConfig

        # Get a value with fallback
        api_key = PluginConfig.get_value('media', 'pexels_api_key')

        # Set a value
        PluginConfig.set_value(
            'media',
            'pexels_api_key',
            'abc123',
            value_type='string',
            is_secret=True,
            description='API Key for Pexels stock photos'
        )

        # Get all settings for a plugin
        settings = PluginConfig.get_plugin_settings('media')
    """

    __tablename__ = 'plugin_config'

    id = db.Column(db.Integer, primary_key=True)

    # Plugin identification
    plugin_name = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    # Key-value pair
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text)

    # Type information for automatic conversion
    value_type = db.Column(
        db.String(20),
        default='string',
        nullable=False
    )
    # Allowed types: 'string', 'int', 'float', 'bool', 'json'

    # Security flag for sensitive data (e.g., API keys)
    is_secret = db.Column(db.Boolean, default=False, nullable=False)

    # Documentation
    description = db.Column(db.String(200))

    # Audit fields
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    updated_by_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )

    # Unique constraint: one key per plugin
    __table_args__ = (
        db.UniqueConstraint(
            'plugin_name', 'key',
            name='uq_plugin_config_plugin_key'
        ),
    )

    # Relationship
    updated_by = db.relationship(
        'User',
        backref=db.backref('plugin_config_changes', lazy='dynamic'),
        foreign_keys=[updated_by_id]
    )

    def __repr__(self) -> str:
        return f'<PluginConfig {self.plugin_name}.{self.key}>'

    @staticmethod
    def _convert_value(value: str | None, value_type: str):
        """Convert string value to appropriate Python type.

        Args:
            value: The string value from database.
            value_type: The target type ('string', 'int', 'float', 'bool', 'json').

        Returns:
            The converted value, or None if value is None.
        """
        if value is None:
            return None

        if value_type == 'int':
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0

        if value_type == 'float':
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0

        if value_type == 'bool':
            return value.lower() in ('true', '1', 'yes', 'on')

        if value_type == 'json':
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return None

        # Default: string
        return value

    @staticmethod
    def _serialize_value(value, value_type: str) -> str | None:
        """Serialize Python value to string for database storage.

        Args:
            value: The Python value to serialize.
            value_type: The value type ('string', 'int', 'float', 'bool', 'json').

        Returns:
            The serialized string value.
        """
        if value is None:
            return None

        if value_type == 'bool':
            return 'true' if value else 'false'

        if value_type == 'json':
            return json.dumps(value)

        return str(value)

    @classmethod
    def get_value(cls, plugin_name: str, key: str, default=None):
        """Get a config value for a plugin.

        Args:
            plugin_name: The plugin identifier (e.g., 'media').
            key: The config key (e.g., 'pexels_api_key').
            default: Value to return if key doesn't exist.

        Returns:
            The config value (type-converted) or default.
        """
        config = db.session.query(cls).filter_by(
            plugin_name=plugin_name,
            key=key
        ).first()

        if not config:
            return default

        converted = cls._convert_value(config.value, config.value_type)
        return converted if converted is not None else default

    @classmethod
    def set_value(
        cls,
        plugin_name: str,
        key: str,
        value,
        value_type: str = 'string',
        is_secret: bool = False,
        description: str | None = None,
        user_id: int | None = None
    ) -> 'PluginConfig':
        """Set a config value for a plugin (upsert).

        Args:
            plugin_name: The plugin identifier.
            key: The config key.
            value: The value to set (will be serialized).
            value_type: Type for serialization ('string', 'int', 'float', 'bool', 'json').
            is_secret: Whether this is a sensitive value.
            description: Optional description of the setting.
            user_id: Optional user ID for audit trail.

        Returns:
            The created or updated PluginConfig instance.
        """
        serialized = cls._serialize_value(value, value_type)

        config = db.session.query(cls).filter_by(
            plugin_name=plugin_name,
            key=key
        ).first()

        if config:
            config.value = serialized
            config.value_type = value_type
            if description is not None:
                config.description = description
            if is_secret is not None:
                config.is_secret = is_secret
            if user_id is not None:
                config.updated_by_id = user_id
        else:
            config = cls(
                plugin_name=plugin_name,
                key=key,
                value=serialized,
                value_type=value_type,
                is_secret=is_secret,
                description=description,
                updated_by_id=user_id
            )
            db.session.add(config)

        db.session.commit()
        return config

    @classmethod
    def get_plugin_settings(cls, plugin_name: str) -> dict:
        """Get all settings for a plugin as a dictionary.

        Args:
            plugin_name: The plugin identifier.

        Returns:
            Dictionary of key -> converted value.
        """
        configs = db.session.query(cls).filter_by(
            plugin_name=plugin_name
        ).all()

        return {
            config.key: cls._convert_value(config.value, config.value_type)
            for config in configs
        }

    @classmethod
    def get_plugin_configs(cls, plugin_name: str) -> list['PluginConfig']:
        """Get all config entries for a plugin.

        Args:
            plugin_name: The plugin identifier.

        Returns:
            List of PluginConfig instances.
        """
        return db.session.query(cls).filter_by(
            plugin_name=plugin_name
        ).all()

    @classmethod
    def delete_value(cls, plugin_name: str, key: str) -> bool:
        """Delete a config value.

        Args:
            plugin_name: The plugin identifier.
            key: The config key.

        Returns:
            True if deleted, False if not found.
        """
        config = db.session.query(cls).filter_by(
            plugin_name=plugin_name,
            key=key
        ).first()

        if config:
            db.session.delete(config)
            db.session.commit()
            return True

        return False

    def to_dict(self, include_value: bool = True) -> dict:
        """Return dictionary representation.

        Args:
            include_value: Whether to include the value (False for secrets in listings).

        Returns:
            Dictionary representation of the config entry.
        """
        result = {
            'id': self.id,
            'plugin_name': self.plugin_name,
            'key': self.key,
            'value_type': self.value_type,
            'is_secret': self.is_secret,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_value and not self.is_secret:
            result['value'] = self._convert_value(self.value, self.value_type)
        elif self.is_secret:
            result['value'] = '••••••••' if self.value else None

        return result