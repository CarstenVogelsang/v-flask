"""User model for authentication and authorization."""

from datetime import datetime
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from v_flask.extensions import db


class UserTyp(str, Enum):
    """User type for distinguishing humans from AI agents.

    Useful for task assignment attribution in project management.
    """

    MENSCH = 'mensch'
    KI_CLAUDE = 'ki_claude'
    KI_CODEX = 'ki_codex'
    KI_ANDERE = 'ki_andere'

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.MENSCH: 'Mensch',
            cls.KI_CLAUDE: 'KI: Claude',
            cls.KI_CODEX: 'KI: Codex',
            cls.KI_ANDERE: 'KI: Andere',
        }
        return [(t.value, labels[t]) for t in cls]

    @classmethod
    def ki_typen(cls) -> list[str]:
        """Return list of AI user type values."""
        return [cls.KI_CLAUDE.value, cls.KI_CODEX.value, cls.KI_ANDERE.value]


class User(UserMixin, db.Model):
    """User entity for authentication and authorization.

    Integrates with Flask-Login via UserMixin.
    Supports granular permissions via has_permission().

    Usage:
        from v_flask.models import User

        user = User(
            email='user@example.com',
            vorname='Max',
            nachname='Mustermann',
            rolle_id=1
        )
        user.set_password('secret')
        db.session.add(user)
        db.session.commit()

        # Check password
        if user.check_password('secret'):
            print('Password correct!')

        # Permission check (new system)
        if user.has_permission('projekt.delete'):
            print('User can delete projects')

        # Role checks (convenience, backward-compatible)
        if user.is_admin:
            print('User is admin')
    """

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    vorname = db.Column(db.String(50), nullable=False)
    nachname = db.Column(db.String(50), nullable=False)
    rolle_id = db.Column(db.Integer, db.ForeignKey('rolle.id'), nullable=False)
    aktiv = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # User type for human/AI distinction
    user_typ = db.Column(db.String(20), default=UserTyp.MENSCH.value, nullable=False)

    # Relationship to Rolle
    rolle_obj = db.relationship('Rolle', back_populates='users')

    def __repr__(self) -> str:
        return f'<User {self.email}>'

    def set_password(self, password: str) -> None:
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password: str) -> bool:
        """Check if password matches hash."""
        return check_password_hash(self.password_hash, password)

    def has_permission(self, code: str) -> bool:
        """Check if user has a specific permission via their role.

        Args:
            code: Permission code to check (e.g., 'projekt.delete').

        Returns:
            True if user's role has the permission, False otherwise.
        """
        if not self.rolle_obj:
            return False
        return self.rolle_obj.has_permission(code)

    def get_extension(self, name: str):
        """Get a registered model extension (1:1 relationship).

        Args:
            name: Name of the extension attribute (e.g., 'profile').

        Returns:
            The extension object or None if not found.
        """
        return getattr(self, name, None)

    # Convenience properties (backward-compatible)

    @property
    def rolle(self) -> str | None:
        """Return role name (backward-compatible property)."""
        return self.rolle_obj.name if self.rolle_obj else None

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.rolle_obj is not None and self.rolle_obj.name == 'admin'

    @property
    def is_mitarbeiter(self) -> bool:
        """Check if user has mitarbeiter or admin role."""
        return self.rolle_obj is not None and self.rolle_obj.name in ('admin', 'mitarbeiter')

    @property
    def is_kunde(self) -> bool:
        """Check if user has kunde role."""
        return self.rolle_obj is not None and self.rolle_obj.name == 'kunde'

    @property
    def is_internal(self) -> bool:
        """Check if user is internal (admin or mitarbeiter)."""
        return self.is_admin or self.is_mitarbeiter

    @property
    def is_ki(self) -> bool:
        """Check if user is an AI agent."""
        return self.user_typ in UserTyp.ki_typen()

    @property
    def full_name(self) -> str:
        """Return full name."""
        return f'{self.vorname} {self.nachname}'

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'email': self.email,
            'vorname': self.vorname,
            'nachname': self.nachname,
            'rolle': self.rolle,
            'rolle_id': self.rolle_id,
            'user_typ': self.user_typ,
            'is_ki': self.is_ki,
            'aktiv': self.aktiv,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
