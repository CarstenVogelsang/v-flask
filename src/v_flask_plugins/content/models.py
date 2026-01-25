"""Database models for the Content Plugin."""
from datetime import datetime
from v_flask import db


class ContentBlock(db.Model):
    """A content block (Inhaltsbaustein).

    Content blocks are template-based content sections that can be
    assigned to pages via ContentAssignment.
    """

    __tablename__ = 'content_block'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Admin display name
    intention = db.Column(db.String(50), nullable=False)  # e.g. 'ueber_uns', 'leistungen'
    layout = db.Column(db.String(50), nullable=False)  # e.g. 'bild_links', 'banner_text'

    # Content data as JSON
    # Structure: {"titel": "...", "text": "...", "bilder": [...]}
    content_data = db.Column(db.JSON, default=dict)

    # Optional reference to a text snippet
    text_snippet_id = db.Column(
        db.Integer,
        db.ForeignKey('content_text_snippet.id'),
        nullable=True
    )

    # Status flags
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    text_snippet = db.relationship(
        'TextSnippet',
        backref=db.backref('content_blocks', lazy='dynamic')
    )
    assignments = db.relationship(
        'ContentAssignment',
        back_populates='content_block',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<ContentBlock {self.id}: {self.name}>'

    @property
    def titel(self) -> str | None:
        """Get title from content_data."""
        return self.content_data.get('titel') if self.content_data else None

    @property
    def text(self) -> str | None:
        """Get text from content_data."""
        return self.content_data.get('text') if self.content_data else None

    @property
    def bilder(self) -> list:
        """Get images from content_data."""
        return self.content_data.get('bilder', []) if self.content_data else []


class ContentAssignment(db.Model):
    """Assignment of a ContentBlock to a PageRoute.

    This creates the connection between content blocks and the pages
    they should appear on.
    """

    __tablename__ = 'content_assignment'

    id = db.Column(db.Integer, primary_key=True)
    content_block_id = db.Column(
        db.Integer,
        db.ForeignKey('content_block.id'),
        nullable=False
    )
    page_route_id = db.Column(
        db.Integer,
        db.ForeignKey('page_route.id'),
        nullable=False
    )

    # Slot positioning
    slot_position = db.Column(
        db.String(50),
        default='after_content',
        nullable=False
    )  # 'before_content', 'after_content', 'sidebar'

    # Ordering when multiple blocks on same slot
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    # Priority for slot rendering (higher = rendered first)
    priority = db.Column(db.Integer, default=50, nullable=False)

    # Status
    active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    content_block = db.relationship('ContentBlock', back_populates='assignments')
    page_route = db.relationship(
        'PageRoute',
        backref=db.backref('content_assignments', lazy='dynamic')
    )

    # Constraints
    __table_args__ = (
        db.Index(
            'ix_content_assignment_page_slot',
            'page_route_id',
            'slot_position',
            'sort_order'
        ),
    )

    def __repr__(self) -> str:
        return f'<ContentAssignment {self.id}: Block {self.content_block_id} -> Route {self.page_route_id}>'


class TextSnippet(db.Model):
    """Reusable text snippets (Textbausteine).

    Text snippets can be predefined (system) or user-created.
    They are organized by category and optionally by industry (branche).
    """

    __tablename__ = 'content_text_snippet'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Internal name
    kategorie = db.Column(db.String(50), nullable=False)  # e.g. 'startseite', 'ueber_uns'
    branche = db.Column(db.String(50), nullable=True)  # NULL = general, else specific industry

    # Content
    titel = db.Column(db.String(200))
    text = db.Column(db.Text)

    # Source tracking
    source = db.Column(
        db.String(20),
        default='user',
        nullable=False
    )  # 'system', 'user', 'ki'

    # Owner tracking (NULL = global template)
    betreiber_id = db.Column(db.Integer, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<TextSnippet {self.id}: {self.name}>'

    @property
    def is_global(self) -> bool:
        """Check if this is a global template (not betreiber-specific)."""
        return self.betreiber_id is None

    @property
    def is_system(self) -> bool:
        """Check if this is a system-provided snippet."""
        return self.source == 'system'
