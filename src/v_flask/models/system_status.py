"""System status model for storing system-wide flags and settings."""

from datetime import datetime, UTC

from v_flask.extensions import db


class SystemStatus(db.Model):
    """Key-value store for system-wide status flags.

    This model stores system status information like:
    - 'restart_required': Whether a server restart is needed
    - 'restart_scheduled': ISO datetime when restart is scheduled
    - 'migrations_pending': Comma-separated list of plugins needing migration

    Attributes:
        id: Primary key.
        key: Unique status key.
        value: Status value (stored as text).
        updated_at: When the status was last updated.

    Usage:
        # Set a status
        SystemStatus.set('restart_required', 'true')

        # Get a status
        value = SystemStatus.get('restart_required')

        # Delete a status
        SystemStatus.delete('restart_scheduled')
    """

    __tablename__ = 'v_flask_system_status'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    # Common status keys
    KEY_RESTART_REQUIRED = 'restart_required'
    KEY_RESTART_SCHEDULED = 'restart_scheduled'
    KEY_MIGRATIONS_PENDING = 'migrations_pending'

    def __repr__(self) -> str:
        return f'<SystemStatus {self.key}={self.value}>'

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get(cls, key: str, default: str | None = None) -> str | None:
        """Get a status value by key.

        Args:
            key: The status key.
            default: Default value if key doesn't exist.

        Returns:
            The status value or default.
        """
        status = db.session.query(cls).filter_by(key=key).first()
        return status.value if status else default

    @classmethod
    def set(cls, key: str, value: str) -> 'SystemStatus':
        """Set a status value.

        Creates or updates the status entry.

        Args:
            key: The status key.
            value: The value to set.

        Returns:
            The SystemStatus instance.
        """
        status = db.session.query(cls).filter_by(key=key).first()

        if status:
            status.value = value
            status.updated_at = datetime.now(UTC)
        else:
            status = cls(key=key, value=value, updated_at=datetime.now(UTC))
            db.session.add(status)

        db.session.commit()
        return status

    @classmethod
    def delete(cls, key: str) -> bool:
        """Delete a status entry.

        Args:
            key: The status key to delete.

        Returns:
            True if deleted, False if not found.
        """
        status = db.session.query(cls).filter_by(key=key).first()
        if status:
            db.session.delete(status)
            db.session.commit()
            return True
        return False

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        """Get a status value as boolean.

        Args:
            key: The status key.
            default: Default value if key doesn't exist.

        Returns:
            Boolean interpretation of the value.
        """
        value = cls.get(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes')

    @classmethod
    def set_bool(cls, key: str, value: bool) -> 'SystemStatus':
        """Set a boolean status value.

        Args:
            key: The status key.
            value: Boolean value to set.

        Returns:
            The SystemStatus instance.
        """
        return cls.set(key, 'true' if value else 'false')

    @classmethod
    def get_list(cls, key: str) -> list[str]:
        """Get a status value as list (comma-separated).

        Args:
            key: The status key.

        Returns:
            List of values (empty list if not found).
        """
        value = cls.get(key)
        if not value:
            return []
        return [v.strip() for v in value.split(',') if v.strip()]

    @classmethod
    def add_to_list(cls, key: str, item: str) -> 'SystemStatus':
        """Add an item to a comma-separated list status.

        Args:
            key: The status key.
            item: Item to add.

        Returns:
            The SystemStatus instance.
        """
        current = cls.get_list(key)
        if item not in current:
            current.append(item)
        return cls.set(key, ','.join(current))

    @classmethod
    def remove_from_list(cls, key: str, item: str) -> 'SystemStatus | None':
        """Remove an item from a comma-separated list status.

        Args:
            key: The status key.
            item: Item to remove.

        Returns:
            The SystemStatus instance or None if list is now empty.
        """
        current = cls.get_list(key)
        if item in current:
            current.remove(item)
        if current:
            return cls.set(key, ','.join(current))
        else:
            cls.delete(key)
            return None

    @classmethod
    def get_datetime(cls, key: str) -> datetime | None:
        """Get a status value as datetime (ISO format).

        Args:
            key: The status key.

        Returns:
            Datetime object or None.
        """
        value = cls.get(key)
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @classmethod
    def set_datetime(cls, key: str, value: datetime) -> 'SystemStatus':
        """Set a datetime status value (stored as ISO format).

        Args:
            key: The status key.
            value: Datetime value to set.

        Returns:
            The SystemStatus instance.
        """
        return cls.set(key, value.isoformat())
