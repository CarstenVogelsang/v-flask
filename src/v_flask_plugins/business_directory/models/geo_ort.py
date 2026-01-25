"""GeoOrt Model.

City/town level of the geographic hierarchy from unternehmensdaten.org.
"""

from v_flask.extensions import db


class GeoOrt(db.Model):
    """City or town with postal code (one entry per PLZ).

    Fourth level of the geographic hierarchy:
    GeoLand -> GeoBundesland -> GeoKreis -> GeoOrt -> DirectoryEntry

    Note: Cities with multiple PLZ codes (e.g., "Essen" with 50+ PLZ) have
    multiple entries. Only the first entry (ist_hauptort=True) gets a slug
    for URL routing.
    """

    __tablename__ = 'business_directory_geo_ort'

    # UUID from unternehmensdaten.org API
    id = db.Column(db.String(36), primary_key=True)

    # Unique code from API
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # Postal code (PLZ)
    plz = db.Column(db.String(10))

    # Geographic coordinates
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    # Hauptort marking - first entry per name in a Kreis
    # Only ist_hauptort=True entries get a slug for URL routing
    ist_hauptort = db.Column(db.Boolean, default=False)

    # Slug only set when ist_hauptort=True
    slug = db.Column(db.String(100))

    # Foreign key to GeoKreis
    kreis_id = db.Column(
        db.String(36),
        db.ForeignKey('business_directory_geo_kreis.id'),
        nullable=False
    )

    # Relationships
    kreis = db.relationship('GeoKreis', back_populates='orte')

    entries = db.relationship(
        'DirectoryEntry',
        back_populates='geo_ort',
        lazy='dynamic'
    )

    # Unique constraint: slug unique per kreis (only for hauptort entries)
    __table_args__ = (
        db.UniqueConstraint(
            'kreis_id', 'slug',
            name='uq_business_directory_geo_ort_slug'
        ),
    )

    def __repr__(self) -> str:
        hauptort_str = " [H]" if self.ist_hauptort else ""
        return f'<GeoOrt {self.name} {self.plz}{hauptort_str}>'

    @property
    def full_name(self) -> str:
        """Return name with PLZ."""
        if self.plz:
            return f"{self.plz} {self.name}"
        return self.name

    @property
    def hauptort(self) -> 'GeoOrt':
        """Get the hauptort entry for this ort's name.

        For Orte with multiple PLZ, returns the entry with ist_hauptort=True.
        This is used for URL generation, as only hauptort entries have slugs.
        """
        if self.ist_hauptort:
            return self

        # Find the hauptort with the same name in this kreis
        return GeoOrt.query.filter_by(
            kreis_id=self.kreis_id,
            name=self.name,
            ist_hauptort=True
        ).first() or self  # Fallback to self if no hauptort found

    @property
    def url_slug(self) -> str:
        """Get the slug for URL generation.

        Returns the hauptort's slug for URL routing.
        """
        return self.hauptort.slug or ''

    def active_entry_count(self, directory_type_id: int | None = None) -> int:
        """Count active entries in this Ort.

        Args:
            directory_type_id: Optional filter by directory type.

        Returns:
            Count of active DirectoryEntry instances.
        """
        from .directory_entry import DirectoryEntry

        query = DirectoryEntry.query.filter_by(
            geo_ort_id=self.id,
            active=True
        )

        if directory_type_id:
            query = query.filter_by(directory_type_id=directory_type_id)

        return query.count()

    @classmethod
    def get_by_slug(
        cls,
        slug: str,
        kreis_id: str | None = None
    ) -> 'GeoOrt | None':
        """Get Ort by slug.

        Args:
            slug: The URL slug.
            kreis_id: Optional Kreis filter.

        Returns:
            GeoOrt instance or None.
        """
        query = cls.query.filter_by(slug=slug, ist_hauptort=True)
        if kreis_id:
            query = query.filter_by(kreis_id=kreis_id)
        return query.first()

    @classmethod
    def get_by_plz(cls, plz: str) -> list['GeoOrt']:
        """Get all Orte with the given PLZ."""
        return cls.query.filter_by(plz=plz).all()
