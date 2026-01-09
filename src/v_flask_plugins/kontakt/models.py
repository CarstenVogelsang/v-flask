"""Contact form models for the Kontakt plugin."""

from datetime import datetime

from v_flask.extensions import db


class KontaktAnfrage(db.Model):
    """Contact form submission model.

    Stores contact form submissions with read status tracking.

    Attributes:
        id: Primary key.
        name: Sender's name.
        email: Sender's email address.
        nachricht: Message content.
        gelesen: Whether the message has been read.
        created_at: Submission timestamp.
    """

    __tablename__ = 'kontakt_anfrage'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    nachricht = db.Column(db.Text, nullable=False)
    gelesen = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        status = 'gelesen' if self.gelesen else 'neu'
        return f'<KontaktAnfrage {self.id} ({status})>'

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'nachricht': self.nachricht,
            'gelesen': self.gelesen,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def mark_as_read(self) -> None:
        """Mark this submission as read."""
        self.gelesen = True
