"""RegistrationDraft Model.

Wizard state persistence for self-registration process.
"""

from datetime import datetime, timezone, timedelta

from v_flask.extensions import db


class RegistrationDraft(db.Model):
    """Temporary storage for incomplete wizard registrations.

    Stores wizard progress including account data and entry details.
    Drafts are automatically deleted after 30 days of inactivity.

    Multi-Directory Support:
        Each draft is associated with a DirectoryType, allowing
        different registration flows for different directory types.

    Usage:
        # Create new draft for a specific directory type
        draft = RegistrationDraft(
            session_id=session.get('draft_id'),
            directory_type_id=directory_type.id,
            current_step=1,
            email='user@example.com'
        )
        db.session.add(draft)

        # Update draft with entry data
        draft.entry_data = {
            'name': 'Spielwaren Schmidt',
            'strasse': 'Hauptstr. 1',
            ...
        }
        draft.current_step = 3
        db.session.commit()

        # Resume draft after login
        draft = RegistrationDraft.query.filter_by(user_id=current_user.id).first()
    """

    __tablename__ = 'business_directory_registration_draft'

    id = db.Column(db.Integer, primary_key=True)

    # Directory type for multi-directory support
    directory_type_id = db.Column(
        db.Integer,
        db.ForeignKey('business_directory_type.id'),
        nullable=False,
        index=True
    )

    # Session/User identification
    # Before login: identified by session_id
    # After login: identified by user_id
    session_id = db.Column(db.String(100), nullable=True, index=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True,
        index=True
    )

    # Wizard state (dynamic based on DirectoryType.registration_steps)
    current_step = db.Column(db.Integer, default=1)

    # Account data (Step 1 typically)
    email = db.Column(db.String(200))
    password_hash = db.Column(db.String(256))
    vorname = db.Column(db.String(50))
    nachname = db.Column(db.String(50))
    telefon_betreiber = db.Column(db.String(50))
    agb_akzeptiert = db.Column(db.Boolean, default=False)

    # Entry data (remaining steps) stored as JSON
    # Structure depends on DirectoryType.field_schema
    # Example for Spielwarenhändler:
    # {
    #   "name": "Spielwaren Schmidt",
    #   "strasse": "Hauptstr. 1",
    #   "plz": "47533",
    #   "ort": "Kleve",
    #   "telefon": "02821-12345",
    #   "website": "https://spielwaren-schmidt.de",
    #   "oeffnungszeiten": {...},
    #   "marken": ["LEGO", "Playmobil"]
    # }
    entry_data = db.Column(db.JSON, default=dict)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    expires_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=30)
    )

    # Relationships
    directory_type = db.relationship(
        'DirectoryType',
        backref=db.backref('registration_drafts', lazy='dynamic')
    )
    user = db.relationship(
        'User',
        backref=db.backref('directory_registration_drafts', lazy='dynamic')
    )

    def __repr__(self) -> str:
        return f'<RegistrationDraft {self.id} type={self.directory_type_id} step={self.current_step}>'

    @property
    def is_expired(self) -> bool:
        """Check if draft has expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def refresh_expiry(self) -> None:
        """Extend expiry by 30 days from now."""
        self.expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    def get_entry_field(self, field: str, default=None):
        """Get a field from entry_data with default fallback.

        Args:
            field: Field name to retrieve.
            default: Default value if field not found.

        Returns:
            Field value or default.
        """
        if not self.entry_data:
            return default
        return self.entry_data.get(field, default)

    def set_entry_field(self, field: str, value) -> None:
        """Set a field in entry_data.

        Args:
            field: Field name to set.
            value: Value to store.
        """
        if self.entry_data is None:
            self.entry_data = {}
        self.entry_data[field] = value

    def get_total_steps(self) -> int:
        """Get total number of registration steps from DirectoryType.

        Returns:
            Number of steps, defaults to 6 if not configured.
        """
        if self.directory_type and self.directory_type.registration_steps:
            return len(self.directory_type.registration_steps)
        return 6  # Default wizard steps

    @classmethod
    def cleanup_expired(cls) -> int:
        """Delete all expired drafts.

        Returns:
            Count of deleted drafts.
        """
        now = datetime.now(timezone.utc)
        result = cls.query.filter(cls.expires_at < now).delete()
        db.session.commit()
        return result

    @classmethod
    def get_by_session(
        cls,
        session_id: str,
        directory_type_id: int | None = None
    ) -> 'RegistrationDraft | None':
        """Get draft by session ID.

        Args:
            session_id: The session identifier.
            directory_type_id: Optional filter by directory type.

        Returns:
            RegistrationDraft instance or None.
        """
        query = cls.query.filter_by(session_id=session_id)
        if directory_type_id:
            query = query.filter_by(directory_type_id=directory_type_id)
        return query.first()

    @classmethod
    def get_by_user(
        cls,
        user_id: int,
        directory_type_id: int | None = None
    ) -> 'RegistrationDraft | None':
        """Get draft by user ID.

        Args:
            user_id: The user identifier.
            directory_type_id: Optional filter by directory type.

        Returns:
            RegistrationDraft instance or None.
        """
        query = cls.query.filter_by(user_id=user_id)
        if directory_type_id:
            query = query.filter_by(directory_type_id=directory_type_id)
        return query.first()
