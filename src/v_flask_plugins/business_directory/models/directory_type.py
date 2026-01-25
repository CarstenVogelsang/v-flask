"""DirectoryType Model.

Defines a type of directory (e.g., "Spielwarenhändler", "Spielwarenhersteller").
Each DirectoryType has its own field schema, registration steps, and display config.
"""

from datetime import datetime, timezone

from v_flask.extensions import db


class DirectoryType(db.Model):
    """Definition eines Verzeichnistyps (Admin-konfigurierbar).

    Beispiele:
    - Spielwarenhändler (mit Öffnungszeiten, geführte Marken)
    - Spielwarenhersteller (mit eigenen Marken, Gründungsjahr)
    - Frühstückslokale (mit Preisen, Reservierung)

    Attributes:
        slug: URL-Slug für das Verzeichnis (z.B. 'haendler')
        name: Anzeigename (z.B. 'Spielwarenhändler')
        name_singular: Singular-Form (z.B. 'Händler')
        name_plural: Plural-Form (z.B. 'Händler')
        icon: Tabler-Icon Klasse (z.B. 'ti-building-store')
        field_schema: JSON-Definition der verfügbaren Felder
        registration_steps: JSON-Definition der Wizard-Steps
        display_config: JSON-Definition der Detailseiten-Darstellung
    """

    __tablename__ = 'business_directory_type'

    id = db.Column(db.Integer, primary_key=True)

    # Identification
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    name_singular = db.Column(db.String(100))
    name_plural = db.Column(db.String(100))

    # Visual
    icon = db.Column(db.String(50), default='ti-building-store')
    color = db.Column(db.String(7))  # HEX color

    # Description
    description = db.Column(db.Text)

    # Schema-Definition: Welche Felder gibt es?
    # Format: {
    #   "oeffnungszeiten": {
    #     "type": "opening_hours",
    #     "label": "Öffnungszeiten",
    #     "required": true,
    #     "show_in_detail": true,
    #     "show_in_card": true
    #   },
    #   "marken": {
    #     "type": "multi_select",
    #     "label": "Geführte Marken",
    #     "options_source": "directory:hersteller",
    #     "required": false
    #   }
    # }
    field_schema = db.Column(db.JSON, default=dict)

    # Registrierungs-Wizard Konfiguration
    # Format: {
    #   "steps": [
    #     {"name": "account", "fields": ["email", "vorname", "nachname"]},
    #     {"name": "grunddaten", "fields": ["name", "kurzbeschreibung"]},
    #     {"name": "adresse", "fields": ["strasse", "plz", "ort"]},
    #     {"name": "kontakt", "fields": ["telefon", "email", "website"]},
    #     {"name": "details", "fields": ["oeffnungszeiten", "marken"]}
    #   ]
    # }
    registration_steps = db.Column(db.JSON, default=dict)

    # Detail-Anzeige Konfiguration
    # Format: {
    #   "sections": [
    #     {"name": "kontakt", "fields": ["telefon", "email", "website"]},
    #     {"name": "details", "fields": ["oeffnungszeiten", "marken"]}
    #   ],
    #   "card_fields": ["name", "kurzbeschreibung", "oeffnungszeiten"]
    # }
    display_config = db.Column(db.JSON, default=dict)

    # Status
    active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    entries = db.relationship(
        'DirectoryEntry',
        back_populates='directory_type',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<DirectoryType {self.slug}: {self.name}>'

    @property
    def entry_count(self) -> int:
        """Count active entries of this type."""
        return self.entries.filter_by(active=True).count()

    @property
    def pending_count(self) -> int:
        """Count pending (unverified) entries."""
        return self.entries.filter_by(active=False, verified=False).count()

    def get_field_definition(self, field_name: str) -> dict | None:
        """Get field definition from schema."""
        if not self.field_schema:
            return None
        return self.field_schema.get(field_name)

    def get_required_fields(self) -> list[str]:
        """Get list of required field names."""
        if not self.field_schema:
            return []
        return [
            name for name, config in self.field_schema.items()
            if config.get('required', False)
        ]

    def get_card_fields(self) -> list[str]:
        """Get fields to show in card view."""
        if not self.display_config:
            return ['name', 'kurzbeschreibung']
        return self.display_config.get('card_fields', ['name', 'kurzbeschreibung'])

    @classmethod
    def get_by_slug(cls, slug: str) -> 'DirectoryType | None':
        """Get active DirectoryType by slug."""
        return cls.query.filter_by(slug=slug, active=True).first()

    @classmethod
    def get_all_active(cls) -> list['DirectoryType']:
        """Get all active DirectoryTypes."""
        return cls.query.filter_by(active=True).order_by(cls.name).all()
