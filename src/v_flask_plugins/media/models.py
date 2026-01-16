"""Media model for uploaded files.

Provides the Media model for storing uploaded files with metadata,
including support for stock photo imports (Pexels, Unsplash) and
automatic image resizing.
"""

from datetime import datetime
from enum import Enum

from v_flask.extensions import db


class MediaType(str, Enum):
    """Supported media types."""
    IMAGE = 'image'
    DOCUMENT = 'document'
    OTHER = 'other'


class MediaSource(str, Enum):
    """Media source tracking."""
    UPLOAD = 'upload'
    PEXELS = 'pexels'
    UNSPLASH = 'unsplash'


class Media(db.Model):
    """Uploaded media file (images, documents).

    Storage path follows pattern: YYYY/MM/uuid_filename.ext
    This structure is S3-compatible for future cloud storage.

    Attributes:
        id: Primary key.
        filename: Stored filename (with uuid prefix).
        original_filename: Original upload filename.
        storage_path: Relative path (e.g., "2026/01/abc123_photo.jpg").
        mime_type: MIME type (e.g., "image/jpeg").
        media_type: Type category (image, document, other).
        file_size: Size in bytes.

        width: Original image width.
        height: Original image height.

        path_thumbnail: 150x150 version path.
        path_small: 400x400 version path.
        path_medium: 800x800 version path.
        path_large: 1200x1200 version path.

        alt_text: Image alt text for SEO.
        title: Display title.
        caption: Optional caption/description.
        kategorien: JSON array of category values.

        source: Origin (upload, pexels, unsplash).
        source_id: External ID for stock photos.
        source_url: Original URL for attribution.
        photographer: Photographer name (stock photos).

        uploaded_by_id: User who uploaded.
        uploaded_at: Upload timestamp.
    """

    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)

    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False, unique=True)
    mime_type = db.Column(db.String(100), nullable=False)
    media_type = db.Column(db.String(20), default=MediaType.OTHER.value)
    file_size = db.Column(db.Integer)  # in bytes

    # Image dimensions
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    # Resized variants (stored as relative paths)
    path_thumbnail = db.Column(db.String(500))  # 150x150
    path_small = db.Column(db.String(500))      # 400x400
    path_medium = db.Column(db.String(500))     # 800x800
    path_large = db.Column(db.String(500))      # 1200x1200

    # SEO metadata
    alt_text = db.Column(db.String(200))
    title = db.Column(db.String(200))
    caption = db.Column(db.Text)

    # Categorization
    kategorien = db.Column(db.JSON, default=list)

    # Source tracking (for stock photo imports)
    source = db.Column(db.String(50), default=MediaSource.UPLOAD.value)
    source_id = db.Column(db.String(100))      # External ID (e.g., Pexels photo ID)
    source_url = db.Column(db.String(500))     # Original URL for attribution
    photographer = db.Column(db.String(200))   # Photographer name

    # Tracking
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    uploaded_by = db.relationship('User', backref='uploaded_media')

    def __repr__(self) -> str:
        return f'<Media {self.id}: {self.filename}>'

    @property
    def is_image(self) -> bool:
        """Check if media is an image."""
        return self.media_type == MediaType.IMAGE.value or \
               (self.mime_type and self.mime_type.startswith('image/'))

    @property
    def url(self) -> str:
        """Get public URL for original file."""
        return f'/media/{self.storage_path}'

    def get_url(self, size: str = 'medium') -> str:
        """Get URL for specific size variant.

        Args:
            size: One of 'thumbnail', 'small', 'medium', 'large', 'original'

        Returns:
            URL string for the requested size, falls back to original.
        """
        if size == 'original' or not self.is_image:
            return self.url

        path_attr = f'path_{size}'
        path = getattr(self, path_attr, None)

        if path:
            return f'/media/{path}'
        return self.url  # Fallback to original

    @property
    def attribution_html(self) -> str:
        """Get attribution HTML for stock photos.

        Returns:
            HTML string with photographer and source links, or empty string.
        """
        if self.source == MediaSource.PEXELS.value and self.photographer:
            photo_url = self.source_url or 'https://www.pexels.com'
            return (
                f'Foto von <a href="{photo_url}" target="_blank" rel="noopener">'
                f'{self.photographer}</a> auf '
                f'<a href="https://www.pexels.com" target="_blank" rel="noopener">Pexels</a>'
            )
        elif self.source == MediaSource.UNSPLASH.value and self.photographer:
            photo_url = self.source_url or 'https://unsplash.com'
            return (
                f'Foto von <a href="{photo_url}" target="_blank" rel="noopener">'
                f'{self.photographer}</a> auf '
                f'<a href="https://unsplash.com" target="_blank" rel="noopener">Unsplash</a>'
            )
        return ''

    @property
    def requires_attribution(self) -> bool:
        """Check if this media requires attribution."""
        return self.source in (MediaSource.PEXELS.value, MediaSource.UNSPLASH.value)

    def to_dict(self) -> dict:
        """Return dictionary representation for API/JSON responses."""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'url': self.url,
            'url_thumbnail': self.get_url('thumbnail'),
            'url_small': self.get_url('small'),
            'url_medium': self.get_url('medium'),
            'url_large': self.get_url('large'),
            'mime_type': self.mime_type,
            'media_type': self.media_type,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'alt_text': self.alt_text,
            'title': self.title,
            'caption': self.caption,
            'kategorien': self.kategorien or [],
            'source': self.source,
            'photographer': self.photographer,
            'attribution_html': self.attribution_html,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
