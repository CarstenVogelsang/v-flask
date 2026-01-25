"""GeoKreis Model.

District level of the geographic hierarchy from unternehmensdaten.org.
"""

from datetime import datetime, timezone

from v_flask.extensions import db


class GeoKreis(db.Model):
    """District or independent city (Kreis or kreisfreie Stadt).

    Third level of the geographic hierarchy:
    GeoLand -> GeoBundesland -> GeoKreis -> GeoOrt -> DirectoryEntry
    """

    __tablename__ = 'business_directory_geo_kreis'

    # UUID from unternehmensdaten.org API
    id = db.Column(db.String(36), primary_key=True)

    # Kreis code (e.g., "DE-NW-05154")
    code = db.Column(db.String(20), unique=True, nullable=False)

    # Vehicle registration code (Autokennzeichen, e.g., "KLE", "DU")
    kuerzel = db.Column(db.String(10))

    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, index=True)

    # Type flags
    ist_landkreis = db.Column(db.Boolean, default=False)
    ist_kreisfreie_stadt = db.Column(db.Boolean, default=False)

    # Population (rounded to 1000)
    einwohner = db.Column(db.Integer)

    # Foreign key to GeoBundesland
    bundesland_id = db.Column(
        db.String(36),
        db.ForeignKey('business_directory_geo_bundesland.id'),
        nullable=False
    )

    # Import tracking
    orte_importiert = db.Column(db.Boolean, default=False)
    import_datum = db.Column(db.DateTime)

    # Relationships
    bundesland = db.relationship('GeoBundesland', back_populates='kreise')

    orte = db.relationship(
        'GeoOrt',
        back_populates='kreis',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Unique constraint: slug unique per bundesland
    __table_args__ = (
        db.UniqueConstraint(
            'bundesland_id', 'slug',
            name='uq_business_directory_geo_kreis_slug'
        ),
    )

    def __repr__(self) -> str:
        type_str = (
            "Kreis" if self.ist_landkreis
            else "Stadt" if self.ist_kreisfreie_stadt
            else "?"
        )
        return f'<GeoKreis {self.kuerzel or self.code}: {self.name} ({type_str})>'

    def mark_imported(self) -> None:
        """Mark this Kreis as having its Orte imported."""
        self.orte_importiert = True
        self.import_datum = datetime.now(timezone.utc)

    def active_entry_count(self, directory_type_id: int | None = None) -> int:
        """Count active entries in this Kreis."""
        from .directory_entry import DirectoryEntry
        from .geo_ort import GeoOrt

        query = db.session.query(DirectoryEntry).join(
            GeoOrt, DirectoryEntry.geo_ort_id == GeoOrt.id
        ).filter(
            GeoOrt.kreis_id == self.id,
            DirectoryEntry.active == True  # noqa: E712
        )

        if directory_type_id:
            query = query.filter(
                DirectoryEntry.directory_type_id == directory_type_id
            )

        return query.count()

    @classmethod
    def get_by_slug(
        cls,
        slug: str,
        bundesland_id: str | None = None
    ) -> 'GeoKreis | None':
        """Get Kreis by slug."""
        query = cls.query.filter_by(slug=slug)
        if bundesland_id:
            query = query.filter_by(bundesland_id=bundesland_id)
        return query.first()

    @classmethod
    def get_imported(cls, bundesland_id: str | None = None) -> list['GeoKreis']:
        """Get all Kreise with imported Orte."""
        query = cls.query.filter_by(orte_importiert=True)
        if bundesland_id:
            query = query.filter_by(bundesland_id=bundesland_id)
        return query.order_by(cls.name).all()
