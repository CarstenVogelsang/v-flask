"""GeoBundesland Model.

Federal state level of the geographic hierarchy from unternehmensdaten.org.
"""

from v_flask.extensions import db


class GeoBundesland(db.Model):
    """Federal state (e.g., Bayern, Nordrhein-Westfalen).

    Second level of the geographic hierarchy:
    GeoLand -> GeoBundesland -> GeoKreis -> GeoOrt -> DirectoryEntry
    """

    __tablename__ = 'business_directory_geo_bundesland'

    # UUID from unternehmensdaten.org API
    id = db.Column(db.String(36), primary_key=True)

    # Bundesland code (e.g., "DE-BY", "DE-NW")
    code = db.Column(db.String(10), unique=True, nullable=False)

    # Short code (e.g., "BY", "NW")
    kuerzel = db.Column(db.String(5))

    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, index=True)

    # Visual customization
    farbe = db.Column(db.String(7))  # HEX color
    icon = db.Column(db.String(30), default='ti-map-pin')

    # Foreign key to GeoLand
    land_id = db.Column(
        db.String(36),
        db.ForeignKey('business_directory_geo_land.id'),
        nullable=False
    )

    # Relationships
    land = db.relationship('GeoLand', back_populates='bundeslaender')

    kreise = db.relationship(
        'GeoKreis',
        back_populates='bundesland',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Unique constraint: slug unique per land
    __table_args__ = (
        db.UniqueConstraint(
            'land_id', 'slug',
            name='uq_business_directory_geo_bundesland_slug'
        ),
    )

    def __repr__(self) -> str:
        return f'<GeoBundesland {self.code}: {self.name}>'

    def active_entry_count(self, directory_type_id: int | None = None) -> int:
        """Count active entries in this Bundesland.

        Args:
            directory_type_id: Optional filter by directory type
        """
        from .directory_entry import DirectoryEntry
        from .geo_ort import GeoOrt
        from .geo_kreis import GeoKreis

        query = db.session.query(DirectoryEntry).join(
            GeoOrt, DirectoryEntry.geo_ort_id == GeoOrt.id
        ).join(
            GeoKreis, GeoOrt.kreis_id == GeoKreis.id
        ).filter(
            GeoKreis.bundesland_id == self.id,
            DirectoryEntry.active == True  # noqa: E712
        )

        if directory_type_id:
            query = query.filter(
                DirectoryEntry.directory_type_id == directory_type_id
            )

        return query.count()

    @classmethod
    def get_by_slug(cls, slug: str, land_id: str | None = None) -> 'GeoBundesland | None':
        """Get Bundesland by slug."""
        query = cls.query.filter_by(slug=slug)
        if land_id:
            query = query.filter_by(land_id=land_id)
        return query.first()

    @classmethod
    def get_with_kreise(cls, land_id: str | None = None) -> list['GeoBundesland']:
        """Get all Bundesländer that have imported Kreise."""
        from .geo_kreis import GeoKreis

        query = cls.query.join(GeoKreis).filter(
            GeoKreis.orte_importiert == True  # noqa: E712
        ).distinct()

        if land_id:
            query = query.filter(cls.land_id == land_id)

        return query.order_by(cls.name).all()
