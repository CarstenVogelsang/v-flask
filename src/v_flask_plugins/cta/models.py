"""CTA Section models for the CTA plugin.

Provides CtaTemplate, CtaSection, and CtaAssignment models
for managing Call-to-Action sections with multiple design variants,
text templates, and route-based page assignments.

PageRoute is imported from v_flask.content_slots (core module).
"""

from datetime import datetime

from v_flask.extensions import db
from v_flask.content_slots.models import PageRoute  # Import from Core

# Re-export PageRoute for convenience
__all__ = ['PageRoute', 'CtaTemplate', 'CtaSection', 'CtaAssignment']


# =============================================================================
# CtaTemplate - Predefined Text Templates
# =============================================================================

class CtaTemplate(db.Model):
    """Predefined CTA text templates with Jinja2 placeholders.

    Allows management of reusable CTA texts (title + description) with
    placeholders like {{ plattform.name }} that get rendered dynamically.

    Attributes:
        id: Primary key.
        slug: Unique identifier for template selection.
        name: Display name in admin UI.
        titel: Title text with optional Jinja2 placeholders.
        beschreibung: Description text with optional Jinja2 placeholders.
        active: Whether this template is available for selection.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = 'plugin_cta_template'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)

    # Text with Jinja2 placeholders
    titel = db.Column(db.String(200), nullable=False)
    beschreibung = db.Column(db.Text, nullable=False)

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

    def __repr__(self) -> str:
        return f'<CtaTemplate {self.slug}: {self.name}>'


# =============================================================================
# CtaSection - CTA Configuration
# =============================================================================

class CtaSection(db.Model):
    """CTA section configuration.

    Stores the CTA settings including design variant, text content,
    and CTA button. Can be assigned to multiple pages via CtaAssignment.

    Attributes:
        id: Primary key.
        name: Admin display name (e.g., 'Homepage CTA', 'Signup Alert').
        variant: Design variant ('card', 'alert', 'floating').
        template_id: FK to CtaTemplate for predefined texts.
        custom_title: Custom title (overrides template).
        custom_description: Custom description (overrides template).
        cta_text: Call-to-action button text.
        cta_link: Call-to-action button link.
        active: Whether this CTA section is active.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = 'plugin_cta_section'

    id = db.Column(db.Integer, primary_key=True)

    # Admin display name for identification
    name = db.Column(db.String(100), nullable=False)

    # Design variant
    variant = db.Column(
        db.String(20),
        default='card',
        nullable=False,
        index=True
    )
    # Allowed values: 'card', 'alert', 'floating'

    # Text content - either via template or custom
    template_id = db.Column(
        db.Integer,
        db.ForeignKey('plugin_cta_template.id'),
        nullable=True
    )
    custom_title = db.Column(db.String(200))
    custom_description = db.Column(db.Text)

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
        'CtaTemplate',
        backref=db.backref('cta_sections', lazy='dynamic')
    )
    assignments = db.relationship(
        'CtaAssignment',
        back_populates='cta_section',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        status = 'active' if self.active else 'inactive'
        return f'<CtaSection {self.name} ({self.variant}, {status})>'

    @property
    def display_name(self) -> str:
        """Return name or fallback to variant + ID."""
        if self.name:
            return self.name
        return f'{self.variant.title()} CTA #{self.id}'

    @property
    def title(self) -> str:
        """Return the effective title (custom or from template)."""
        if self.custom_title:
            return self.custom_title
        if self.template:
            return self.template.titel
        return ''

    @property
    def description(self) -> str:
        """Return the effective description (custom or from template)."""
        if self.custom_description:
            return self.custom_description
        if self.template:
            return self.template.beschreibung
        return ''

    def to_dict(self) -> dict:
        """Return dictionary representation for API/JSON responses."""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'variant': self.variant,
            'title': self.title,
            'description': self.description,
            'cta_text': self.cta_text,
            'cta_link': self.cta_link,
            'active': self.active,
        }


# =============================================================================
# CtaAssignment - Link CTA Sections to Pages
# =============================================================================

class CtaAssignment(db.Model):
    """Assignment of a CTA section to a page/route in a specific slot.

    Enables:
    - One CTA section displayed on multiple pages
    - Multiple CTA sections on one page (different slots)
    - Priority ordering for overlapping assignments

    Attributes:
        id: Primary key.
        cta_section_id: FK to CtaSection.
        page_route_id: FK to PageRoute.
        slot_position: Template slot ('after_content', 'floating', etc.).
        priority: Higher = preferred on conflicts.
        active: Whether this assignment is active.
        created_at: Creation timestamp.
    """

    __tablename__ = 'plugin_cta_assignment'

    id = db.Column(db.Integer, primary_key=True)

    # The CTA section to display
    cta_section_id = db.Column(
        db.Integer,
        db.ForeignKey('plugin_cta_section.id'),
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
        default='after_content',
        nullable=False,
        index=True
    )

    # Priority (higher = preferred on conflicts)
    priority = db.Column(db.Integer, default=50, nullable=False)

    # Active status
    active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    cta_section = db.relationship(
        'CtaSection',
        back_populates='assignments'
    )
    # Use backref since PageRoute is defined in Core
    page_route = db.relationship(
        'PageRoute',
        backref=db.backref('cta_assignments', cascade='all, delete-orphan')
    )

    # Unique constraint: One CTA per page per slot
    __table_args__ = (
        db.UniqueConstraint(
            'page_route_id', 'slot_position',
            name='uq_cta_assignment_page_slot'
        ),
    )

    def __repr__(self) -> str:
        return f'<CtaAssignment cta={self.cta_section_id} route={self.page_route_id} slot={self.slot_position}>'
