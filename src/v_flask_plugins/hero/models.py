"""Hero Section models for the Hero plugin.

Provides HeroSection and HeroTemplate models for managing
hero sections with multiple layout variants and text templates.
"""

from datetime import datetime

from v_flask.extensions import db


class HeroTemplate(db.Model):
    """Predefined hero text templates with Jinja2 placeholders.

    Allows management of reusable hero texts (title + subtitle) with
    placeholders like {{ plattform.name }} that get rendered dynamically.

    Attributes:
        id: Primary key.
        slug: Unique identifier for template selection.
        name: Display name in admin UI.
        titel: Title text with optional Jinja2 placeholders.
        untertitel: Subtitle text with optional Jinja2 placeholders.
        is_default: Whether this is the default template.
        active: Whether this template is available for selection.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = 'hero_template'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # Text with Jinja2 placeholders
    titel = db.Column(db.String(200), nullable=False)
    untertitel = db.Column(db.Text, nullable=False)

    # Status
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f'<HeroTemplate {self.slug}: {self.name}>'


class HeroSection(db.Model):
    """Hero section configuration for a portal.

    Stores the hero section settings including layout variant,
    background image, text content, and CTA button.

    Attributes:
        id: Primary key.
        variant: Layout variant ('centered', 'split', 'overlay').
        image_path: Path to background/hero image.
        template_id: FK to HeroTemplate for predefined texts.
        custom_title: Custom title (overrides template).
        custom_subtitle: Custom subtitle (overrides template).
        cta_text: Call-to-action button text.
        cta_link: Call-to-action button link.
        active: Whether this hero section is active.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = 'hero_section'

    id = db.Column(db.Integer, primary_key=True)

    # Layout variant
    variant = db.Column(
        db.String(20),
        default='centered',
        nullable=False
    )
    # Allowed values: 'centered', 'split', 'overlay'

    # Background/Hero image (via Media plugin)
    media_id = db.Column(
        db.Integer,
        db.ForeignKey('media.id'),
        nullable=True
    )

    # Legacy: Keep for backwards compatibility during migration
    _image_path = db.Column('image_path', db.String(500))

    # Text content - either via template or custom
    template_id = db.Column(
        db.Integer,
        db.ForeignKey('hero_template.id'),
        nullable=True
    )
    custom_title = db.Column(db.String(200))
    custom_subtitle = db.Column(db.Text)

    # Call-to-action button
    cta_text = db.Column(db.String(100))
    cta_link = db.Column(db.String(500))

    # Status
    active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        onupdate=datetime.utcnow
    )

    # Relationships
    template = db.relationship(
        'HeroTemplate',
        backref=db.backref('hero_sections', lazy='dynamic')
    )
    media = db.relationship(
        'Media',
        backref=db.backref('hero_sections', lazy='dynamic')
    )

    def __repr__(self) -> str:
        status = 'active' if self.active else 'inactive'
        return f'<HeroSection {self.id} ({self.variant}, {status})>'

    @property
    def image_path(self) -> str | None:
        """Return the image URL (from media or legacy path).

        Provides backwards compatibility - prefers media URL over legacy path.
        """
        if self.media:
            return self.media.get_url('large')
        return self._image_path

    @image_path.setter
    def image_path(self, value: str | None) -> None:
        """Set the legacy image path (for backwards compatibility)."""
        self._image_path = value

    @property
    def title(self) -> str:
        """Return the effective title (custom or from template)."""
        if self.custom_title:
            return self.custom_title
        if self.template:
            return self.template.titel
        return ''

    @property
    def subtitle(self) -> str:
        """Return the effective subtitle (custom or from template)."""
        if self.custom_subtitle:
            return self.custom_subtitle
        if self.template:
            return self.template.untertitel
        return ''

    def to_dict(self) -> dict:
        """Return dictionary representation for API/JSON responses."""
        result = {
            'id': self.id,
            'variant': self.variant,
            'image_path': self.image_path,
            'media_id': self.media_id,
            'title': self.title,
            'subtitle': self.subtitle,
            'cta_text': self.cta_text,
            'cta_link': self.cta_link,
            'active': self.active,
        }
        if self.media:
            result['media'] = self.media.to_dict()
        return result
