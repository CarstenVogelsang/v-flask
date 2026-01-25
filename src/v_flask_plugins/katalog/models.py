"""Models for the Katalog plugin.

Provides KatalogKategorie and KatalogPDF models for organizing
and managing PDF catalogs.
"""

from datetime import datetime
from uuid import uuid4

from slugify import slugify
from sqlalchemy.dialects.postgresql import UUID

from v_flask.extensions import db


class KatalogKategorie(db.Model):
    """Catalog category for organizing PDFs.

    Examples: Hauptkatalog, Neuheiten, Sonderangebote, Archiv

    Attributes:
        id: UUID primary key.
        name: Category display name.
        slug: URL-friendly identifier.
        description: Optional description text.
        icon: Tabler icon class (e.g., 'ti ti-book').
        sort_order: Display order (lower = first).
        is_active: Whether category is visible.
        created_at: Creation timestamp.
    """

    __tablename__ = 'katalog_kategorie'

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='ti ti-book')
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    pdfs = db.relationship(
        'KatalogPDF',
        back_populates='kategorie',
        lazy='dynamic',
        order_by='KatalogPDF.sort_order'
    )

    def __repr__(self) -> str:
        return f'<KatalogKategorie {self.name}>'

    @property
    def pdf_count(self) -> int:
        """Get number of active PDFs in this category."""
        return self.pdfs.filter_by(is_active=True).count()

    @classmethod
    def get_active(cls) -> list['KatalogKategorie']:
        """Get all active categories ordered by sort_order."""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'pdf_count': self.pdf_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class KatalogPDF(db.Model):
    """PDF catalog document.

    Stores metadata for PDF catalogs that can be viewed in-browser
    or downloaded.

    Attributes:
        id: UUID primary key.
        kategorie_id: Foreign key to KatalogKategorie.
        title: Display title.
        description: Optional description text.
        file_path: Path to PDF file (relative to upload folder).
        file_size: File size in bytes.
        cover_image_path: Path to cover image for preview.
        year: Publication year (optional).
        is_active: Whether PDF is visible.
        download_count: Number of downloads.
        view_count: Number of views in browser.
        sort_order: Display order within category.
        created_at: Upload timestamp.
        updated_at: Last modification timestamp.
    """

    __tablename__ = 'katalog_pdf'

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    kategorie_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('katalog_kategorie.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # Bytes
    cover_image_path = db.Column(db.String(500), nullable=True)
    year = db.Column(db.Integer, nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    download_count = db.Column(db.Integer, default=0, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
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

    # Relationships
    kategorie = db.relationship('KatalogKategorie', back_populates='pdfs')

    def __repr__(self) -> str:
        return f'<KatalogPDF {self.title}>'

    @property
    def file_size_display(self) -> str:
        """Get human-readable file size."""
        if not self.file_size:
            return 'Unbekannt'
        if self.file_size < 1024:
            return f'{self.file_size} B'
        elif self.file_size < 1024 * 1024:
            return f'{self.file_size / 1024:.1f} KB'
        else:
            return f'{self.file_size / (1024 * 1024):.1f} MB'

    @property
    def has_cover(self) -> bool:
        """Check if PDF has a cover image."""
        return bool(self.cover_image_path)

    def increment_view_count(self) -> None:
        """Increment the view counter."""
        self.view_count += 1
        db.session.commit()

    def increment_download_count(self) -> None:
        """Increment the download counter."""
        self.download_count += 1
        db.session.commit()

    @classmethod
    def get_active(cls, kategorie_id: str | None = None) -> list['KatalogPDF']:
        """Get active PDFs, optionally filtered by category."""
        query = cls.query.filter_by(is_active=True)
        if kategorie_id:
            query = query.filter_by(kategorie_id=kategorie_id)
        return query.order_by(cls.sort_order, cls.year.desc()).all()

    @classmethod
    def get_by_year(cls, year: int) -> list['KatalogPDF']:
        """Get all active PDFs from a specific year."""
        return cls.query.filter_by(is_active=True, year=year).order_by(cls.sort_order).all()

    def to_dict(self, include_stats: bool = False) -> dict:
        """Return dictionary representation.

        Args:
            include_stats: Include view_count and download_count.
        """
        result = {
            'id': str(self.id),
            'kategorie_id': str(self.kategorie_id) if self.kategorie_id else None,
            'kategorie_name': self.kategorie.name if self.kategorie else None,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_display': self.file_size_display,
            'cover_image_path': self.cover_image_path,
            'year': self.year,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_stats:
            result['view_count'] = self.view_count
            result['download_count'] = self.download_count
        return result


def generate_unique_slug(name: str, model_class=KatalogKategorie) -> str:
    """Generate a unique slug for a category.

    Args:
        name: Category name to slugify.
        model_class: Model class to check for uniqueness.

    Returns:
        Unique slug string.
    """
    base_slug = slugify(name, lowercase=True)
    slug = base_slug
    counter = 1

    while model_class.query.filter_by(slug=slug).first() is not None:
        slug = f'{base_slug}-{counter}'
        counter += 1

    return slug
