"""DirectoryEntry Model.

Generic business entry for any directory type.
Replaces the hardcoded Location model from vz_fruehstueckenclick.
"""

from datetime import datetime, timezone

from v_flask.extensions import db


class DirectoryEntry(db.Model):
    """Generischer Verzeichnis-Eintrag.

    Enthält feste Basis-Felder (Name, Adresse, Kontakt) und
    ein flexibles `data` JSON-Feld für branchenspezifische Daten.

    Attributes:
        directory_type_id: Referenz auf DirectoryType (z.B. "Händler")
        name: Name des Eintrags
        slug: URL-Slug (eindeutig pro GeoOrt)
        geo_ort_id: Geografische Zuordnung
        strasse, telefon, email, website: Basis-Kontaktdaten
        data: JSON mit branchenspezifischen Daten (Öffnungszeiten, Marken, etc.)
        active, verified, self_managed: Status-Flags
        owner_id: Besitzer (für Self-Management)
    """

    __tablename__ = 'business_directory_entry'

    id = db.Column(db.Integer, primary_key=True)

    # Directory Type (z.B. "Spielwarenhändler", "Spielwarenhersteller")
    directory_type_id = db.Column(
        db.Integer,
        db.ForeignKey('business_directory_type.id'),
        nullable=False,
        index=True
    )

    # === FESTE Basis-Felder (immer vorhanden) ===

    # Identification
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    kurzbeschreibung = db.Column(db.String(500))

    # Address
    strasse = db.Column(db.String(200))
    # PLZ/Ort: Fallback for self-registration before geo_ort_id is assigned
    plz = db.Column(db.String(10))
    ort = db.Column(db.String(100))

    # GeoOrt reference (from Geo-Hierarchy)
    geo_ort_id = db.Column(
        db.String(36),
        db.ForeignKey('business_directory_geo_ort.id'),
        nullable=True,
        index=True
    )

    # Coordinates (for future map view)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # External Place IDs (for deduplication)
    geoapify_place_id = db.Column(db.String(100))
    google_places_id = db.Column(db.String(100))

    # === FESTE Kontakt-Felder ===

    telefon = db.Column(db.String(50))
    email = db.Column(db.String(200))
    website = db.Column(db.String(500))

    # Social Media
    instagram_handle = db.Column(db.String(100))
    facebook_url = db.Column(db.String(300))

    # === FLEXIBLE branchenspezifische Daten ===

    # JSON storage for type-specific fields
    # Examples:
    # - Händler: {"oeffnungszeiten": {...}, "marken": ["LEGO", "Playmobil"]}
    # - Hersteller: {"marken": ["Fisher-Price"], "gruendungsjahr": 1930}
    # - Frühstück: {"preise": {"klein": 9.0}, "reservierung": true}
    data = db.Column(db.JSON, default=dict)

    # === Status Flags ===

    active = db.Column(db.Boolean, default=False, nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    self_managed = db.Column(db.Boolean, default=False, nullable=False)

    # === Timestamps ===

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # === Owner (for self-managed entries) ===

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )

    # === Relationships ===

    directory_type = db.relationship(
        'DirectoryType',
        back_populates='entries'
    )

    geo_ort = db.relationship(
        'GeoOrt',
        back_populates='entries'
    )

    claim_requests = db.relationship(
        'ClaimRequest',
        back_populates='entry',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # === Constraints ===

    __table_args__ = (
        db.UniqueConstraint(
            'directory_type_id', 'geo_ort_id', 'slug',
            name='uq_directory_entry_type_ort_slug'
        ),
    )

    def __repr__(self) -> str:
        return f'<DirectoryEntry {self.name}>'

    # === Properties ===

    @property
    def full_address(self) -> str:
        """Return formatted full address."""
        parts = []
        if self.strasse:
            parts.append(self.strasse)
        if self.plz and self.ort:
            parts.append(f'{self.plz} {self.ort}')
        elif self.ort:
            parts.append(self.ort)
        elif self.geo_ort:
            parts.append(self.geo_ort.full_name)
        return ', '.join(parts)

    @property
    def public_url(self) -> str | None:
        """Return public URL for this entry.

        Builds URL from: /directory_type/bundesland/kreis/ort/entry/
        Returns None if geo_ort is not assigned.
        """
        if not self.geo_ort or not self.directory_type:
            return None

        geo_ort = self.geo_ort
        geo_kreis = geo_ort.kreis
        geo_bundesland = geo_kreis.bundesland

        return (
            f"/{self.directory_type.slug}/"
            f"{geo_bundesland.slug}/{geo_kreis.slug}/"
            f"{geo_ort.url_slug}/{self.slug}/"
        )

    # === Data Access Helpers ===

    def get_data_field(self, field_name: str, default=None):
        """Get a field from the data JSON."""
        if not self.data:
            return default
        return self.data.get(field_name, default)

    def set_data_field(self, field_name: str, value) -> None:
        """Set a field in the data JSON."""
        if self.data is None:
            self.data = {}
        self.data[field_name] = value

    def get_display_value(self, field_name: str) -> str:
        """Get display-formatted value for a field.

        Handles both fixed fields and data fields.
        """
        # Check fixed fields first
        if hasattr(self, field_name):
            return getattr(self, field_name) or ''

        # Then check data fields
        value = self.get_data_field(field_name)
        if value is None:
            return ''

        # Format based on type
        if isinstance(value, bool):
            return 'Ja' if value else 'Nein'
        if isinstance(value, list):
            return ', '.join(str(v) for v in value)
        if isinstance(value, dict):
            # Could be opening hours or similar
            return str(value)

        return str(value)

    # === Class Methods ===

    @classmethod
    def get_by_type_and_slug(
        cls,
        directory_type_id: int,
        geo_ort_id: str,
        slug: str
    ) -> 'DirectoryEntry | None':
        """Get entry by type, location, and slug."""
        return cls.query.filter_by(
            directory_type_id=directory_type_id,
            geo_ort_id=geo_ort_id,
            slug=slug,
            active=True
        ).first()

    @classmethod
    def search(
        cls,
        directory_type_id: int | None = None,
        query: str | None = None,
        geo_kreis_id: str | None = None,
        limit: int = 20
    ) -> list['DirectoryEntry']:
        """Search entries with optional filters."""
        q = cls.query.filter_by(active=True)

        if directory_type_id:
            q = q.filter_by(directory_type_id=directory_type_id)

        if query:
            q = q.filter(cls.name.ilike(f'%{query}%'))

        if geo_kreis_id:
            from .geo_ort import GeoOrt
            q = q.join(GeoOrt).filter(GeoOrt.kreis_id == geo_kreis_id)

        return q.order_by(cls.name).limit(limit).all()
