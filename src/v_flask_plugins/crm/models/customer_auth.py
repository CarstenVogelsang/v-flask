"""CustomerAuth model for CRM plugin.

Shop authentication for customers with brute-force protection.
"""

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from v_flask.extensions import db


# Constants for brute-force protection (can be overridden via plugin settings)
DEFAULT_MAX_FAILED_ATTEMPTS = 5
DEFAULT_LOCKOUT_MINUTES = 15


class CustomerAuth(db.Model):
    """Customer authentication entity for shop login.

    Provides shop authentication with password hashing (werkzeug.security)
    and brute-force protection.

    Attributes:
        id: UUID primary key.
        customer_id: Foreign key to customer (1:1 relationship).
        email: Login email (usually same as customer email).
        password_hash: Hashed password (pbkdf2:sha256).
        is_active: Whether shop access is enabled.
        last_login: Last successful login timestamp.
        login_count: Total successful login count.
        failed_attempts: Current failed login attempt count.
        locked_until: Account lockout expiry timestamp.
        password_reset_token: Token for password reset flow.
        password_reset_expires: Reset token expiry timestamp.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.

    Relationships:
        customer: Parent customer entity.

    Example:
        >>> auth = CustomerAuth(
        ...     customer_id=customer.id,
        ...     email='shop@example.com'
        ... )
        >>> auth.set_password('secure123')
        >>> auth.is_active = True
    """

    __tablename__ = 'crm_customer_auth'

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    customer_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('crm_customer.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0, nullable=False)
    failed_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_reset_token = db.Column(db.String(100), nullable=True, index=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Additional index for reset token lookup
    __table_args__ = (
        db.Index('idx_crm_auth_reset_token', 'password_reset_token'),
    )

    # Relationship
    customer = db.relationship('Customer', back_populates='auth')

    def __repr__(self) -> str:
        status = 'active' if self.is_active else 'inactive'
        return f'<CustomerAuth {self.email} ({status})>'

    def set_password(self, password: str) -> None:
        """Hash and set the password.

        Uses werkzeug.security with pbkdf2:sha256 algorithm.

        Args:
            password: Plain text password to hash.
        """
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256'
        )

    def check_password(self, password: str) -> bool:
        """Check if password matches hash.

        Args:
            password: Plain text password to verify.

        Returns:
            True if password is correct, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    def is_locked(self) -> bool:
        """Check if account is currently locked due to failed login attempts.

        Returns:
            True if account is locked, False otherwise.
        """
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    @property
    def can_login(self) -> bool:
        """Check if customer can log in.

        Returns:
            True if account is active and not locked.
        """
        return self.is_active and not self.is_locked()

    def record_failed_login(
        self,
        max_attempts: int = DEFAULT_MAX_FAILED_ATTEMPTS,
        lockout_minutes: int = DEFAULT_LOCKOUT_MINUTES
    ) -> None:
        """Record a failed login attempt and lock account if threshold reached.

        Args:
            max_attempts: Maximum failed attempts before lockout.
            lockout_minutes: Lockout duration in minutes.
        """
        self.failed_attempts += 1

        if self.failed_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(
                minutes=lockout_minutes
            )

    def reset_failed_logins(self) -> None:
        """Reset failed login counter after successful login."""
        self.failed_attempts = 0
        self.locked_until = None

    def record_successful_login(self) -> None:
        """Record a successful login (reset failed attempts, update stats)."""
        self.reset_failed_logins()
        self.last_login = datetime.utcnow()
        self.login_count += 1

    @property
    def lockout_remaining_minutes(self) -> int | None:
        """Get remaining lockout time in minutes.

        Returns:
            Minutes remaining in lockout, or None if not locked.
        """
        if not self.is_locked():
            return None
        remaining = self.locked_until - datetime.utcnow()
        return max(0, int(remaining.total_seconds() / 60))

    def generate_reset_token(self, expires_hours: int = 24) -> str:
        """Generate a password reset token.

        Args:
            expires_hours: Token validity in hours.

        Returns:
            The generated reset token string.
        """
        import secrets
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=expires_hours)
        return self.password_reset_token

    def verify_reset_token(self, token: str) -> bool:
        """Verify a password reset token.

        Args:
            token: The token to verify.

        Returns:
            True if token is valid and not expired.
        """
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        if self.password_reset_token != token:
            return False
        if datetime.utcnow() > self.password_reset_expires:
            return False
        return True

    def clear_reset_token(self) -> None:
        """Clear the password reset token after use."""
        self.password_reset_token = None
        self.password_reset_expires = None

    def to_dict(self) -> dict:
        """Return dictionary representation (excluding password hash)."""
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'email': self.email,
            'is_active': self.is_active,
            'is_locked': self.is_locked(),
            'can_login': self.can_login,
            'lockout_remaining_minutes': self.lockout_remaining_minutes,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'failed_attempts': self.failed_attempts,
            'has_reset_token': bool(self.password_reset_token),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
