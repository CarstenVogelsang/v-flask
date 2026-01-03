"""Config model for key-value application settings."""

from v_flask.extensions import db


class Config(db.Model):
    """Key-value store for application configuration.

    Usage:
        from v_flask.models import Config

        # Set a value
        Config.set_value('app_name', 'My App', 'Name der Anwendung')

        # Get a value
        name = Config.get_value('app_name', default='Default App')
    """

    __tablename__ = 'config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    beschreibung = db.Column(db.String(200))

    def __repr__(self) -> str:
        return f'<Config {self.key}>'

    @classmethod
    def get_value(cls, key: str, default: str = '') -> str:
        """Get a config value by key.

        Args:
            key: The config key to look up.
            default: Value to return if key doesn't exist.

        Returns:
            The config value or default.
        """
        config = db.session.query(cls).filter_by(key=key).first()
        return config.value if config else default

    @classmethod
    def set_value(cls, key: str, value: str, beschreibung: str | None = None) -> None:
        """Set a config value.

        Args:
            key: The config key.
            value: The value to set.
            beschreibung: Optional description of the config.
        """
        config = db.session.query(cls).filter_by(key=key).first()
        if config:
            config.value = value
            if beschreibung is not None:
                config.beschreibung = beschreibung
        else:
            config = cls(key=key, value=value, beschreibung=beschreibung)
            db.session.add(config)
        db.session.commit()

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'beschreibung': self.beschreibung,
        }
