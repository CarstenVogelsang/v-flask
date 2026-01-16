"""HelpText model for editable UI help texts.

Provides context-sensitive help content for UI elements like editors,
forms, and admin pages. Content is stored as Markdown and rendered to HTML.

Usage:
    # In templates (via context processor):
    {% set help = get_help_text('impressum.editor') %}
    {% if help %}
        {{ help.inhalt_markdown|markdown }}
    {% endif %}

    # Via help_icon macro:
    {{ help_icon('impressum.editor', 'Hilfe zum Impressum') }}
"""

from datetime import datetime, UTC

from v_flask.extensions import db


class HelpText(db.Model):
    """Editable help texts for UI components (Cards, Forms, Editors, etc.).

    Attributes:
        schluessel: Unique identifier for the help text location.
                   Format: "module.page.section" e.g. "impressum.editor"
        titel: Display title shown in modal header.
        inhalt_markdown: Help content in Markdown format.
        aktiv: Whether this help text is active/visible.
        plugin: Optional plugin name that owns this help text.
        created_at: Timestamp when created.
        updated_at: Timestamp when last updated.
        updated_by_id: User who last updated this help text.
    """

    __tablename__ = 'help_text'

    id = db.Column(db.Integer, primary_key=True)

    # Unique key for identifying the help text location
    # Format: "module.page.section" e.g. "impressum.editor"
    schluessel = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # Display title shown in modal header
    titel = db.Column(db.String(200), nullable=False)

    # Markdown content that will be rendered as HTML
    inhalt_markdown = db.Column(db.Text, nullable=False)

    # Active flag to enable/disable help texts
    aktiv = db.Column(db.Boolean, default=True)

    # Optional: Plugin that owns this help text (for tracking origin)
    plugin = db.Column(db.String(50), nullable=True)

    # Audit fields
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relationship to User who last updated
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])

    def __repr__(self) -> str:
        status = 'aktiv' if self.aktiv else 'inaktiv'
        return f'<HelpText {self.schluessel} ({status})>'

    def to_dict(self) -> dict:
        """Return dictionary representation for API responses."""
        return {
            'id': self.id,
            'schluessel': self.schluessel,
            'titel': self.titel,
            'inhalt_markdown': self.inhalt_markdown,
            'aktiv': self.aktiv,
            'plugin': self.plugin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by.vorname if self.updated_by else None,
        }

    @classmethod
    def get_or_create(
        cls,
        schluessel: str,
        titel: str,
        inhalt_markdown: str,
        plugin: str | None = None,
    ) -> 'HelpText':
        """Get existing help text or create new one.

        Used during plugin initialization to seed default help texts.
        Does not update existing entries to preserve user customizations.

        Args:
            schluessel: Unique key for the help text.
            titel: Display title.
            inhalt_markdown: Help content in Markdown.
            plugin: Optional plugin name.

        Returns:
            Existing or newly created HelpText instance.
        """
        help_text = cls.query.filter_by(schluessel=schluessel).first()
        if help_text is None:
            help_text = cls(
                schluessel=schluessel,
                titel=titel,
                inhalt_markdown=inhalt_markdown,
                plugin=plugin,
            )
            db.session.add(help_text)
        return help_text
