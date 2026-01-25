"""Hero Section models for the Hero plugin.

Provides HeroSection, HeroTemplate and HeroAssignment models
for managing hero sections with multiple layout variants, text templates,
and route-based page assignments.

PageRoute is imported from v_flask.content_slots (core module).
"""

from datetime import datetime

from v_flask.extensions import db
from v_flask.content_slots.models import PageRoute  # Import from Core

# Re-export PageRoute for backwards compatibility
__all__ = ['PageRoute', 'HeroAssignment', 'HeroTemplate', 'HeroSection']


# =============================================================================
# HeroAssignment - Link Hero Sections to Pages
# =============================================================================

class HeroAssignment(db.Model):
    """Assignment of a Hero section to a page/route in a specific slot.

    Enables:
    - One Hero section displayed on multiple pages
    - Multiple Hero sections on one page (different slots)
    - Priority ordering for overlapping assignments

    Attributes:
        id: Primary key.
        hero_section_id: FK to HeroSection.
        page_route_id: FK to PageRoute.
        slot_position: Template slot ('hero_top', 'above_content', 'below_content').
        priority: Higher = preferred on conflicts.
        active: Whether this assignment is active.
        created_at: Creation timestamp.
    """

    __tablename__ = 'hero_assignment'

    id = db.Column(db.Integer, primary_key=True)

    # The Hero section to display
    hero_section_id = db.Column(
        db.Integer,
        db.ForeignKey('hero_section.id'),
        nullable=False
    )

    # The page to display on
    page_route_id = db.Column(
        db.Integer,
        db.ForeignKey('page_route.id'),
        nullable=False
    )

    # Slot position in template
    slot_position = db.Column(
        db.String(50),
        default='hero_top',
        nullable=False
    )

    # Priority (higher = preferred on conflicts)
    priority = db.Column(db.Integer, default=100, nullable=False)

    # Active status
    active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    hero_section = db.relationship(
        'HeroSection',
        back_populates='assignments'
    )
    # Use backref since PageRoute is defined in Core without hero_assignments
    page_route = db.relationship(
        'PageRoute',
        backref=db.backref('hero_assignments', cascade='all, delete-orphan')
    )

    # Unique constraint: One hero per page per slot
    __table_args__ = (
        db.UniqueConstraint(
            'page_route_id', 'slot_position',
            name='uq_hero_assignment_page_slot'
        ),
    )

    def __repr__(self) -> str:
        return f'<HeroAssignment hero={self.hero_section_id} route={self.page_route_id} slot={self.slot_position}>'


# =============================================================================
# HeroTemplate - Predefined Text Templates
# =============================================================================


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
    background image, text content, and CTA button. Can be assigned
    to multiple pages via HeroAssignment.

    Attributes:
        id: Primary key.
        name: Admin display name (e.g., 'Homepage Hero', 'Winter Action').
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

    # Admin display name for identification
    name = db.Column(db.String(100))

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
    assignments = db.relationship(
        'HeroAssignment',
        back_populates='hero_section',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        status = 'active' if self.active else 'inactive'
        name = self.name or f'#{self.id}'
        return f'<HeroSection {name} ({self.variant}, {status})>'

    @property
    def display_name(self) -> str:
        """Return name or fallback to variant + ID."""
        if self.name:
            return self.name
        return f'{self.variant.title()} Hero #{self.id}'

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
            'name': self.name,
            'display_name': self.display_name,
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
