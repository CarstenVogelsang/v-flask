"""GeoLand Model.

Country level of the geographic hierarchy from unternehmensdaten.org.
"""

from v_flask.extensions import db


class GeoLand(db.Model):
    """Country (e.g., Germany, Austria, Switzerland).

    Top level of the geographic hierarchy:
    GeoLand -> GeoBundesland -> GeoKreis -> GeoOrt -> DirectoryEntry
    """

    __tablename__ = 'business_directory_geo_land'

    # UUID from unternehmensdaten.org API
    id = db.Column(db.String(36), primary_key=True)

    # ISO-2 country code (e.g., "DE", "AT", "CH")
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

    # Relationships
    bundeslaender = db.relationship(
        'GeoBundesland',
        back_populates='land',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<GeoLand {self.code}: {self.name}>'

    @classmethod
    def get_by_code(cls, code: str) -> 'GeoLand | None':
        """Get country by ISO code."""
        return cls.query.filter_by(code=code).first()

    @classmethod
    def get_by_slug(cls, slug: str) -> 'GeoLand | None':
        """Get country by slug."""
        return cls.query.filter_by(slug=slug).first()
