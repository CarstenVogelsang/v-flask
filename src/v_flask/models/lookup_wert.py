"""LookupWert model for dynamic types, icons, and colors."""

from datetime import datetime

from v_flask.extensions import db


class LookupWert(db.Model):
    """Dynamic lookup values for categories like status, priority, etc.

    Supports hybrid multi-tenancy:
        - Global values: betreiber_id = NULL (shared across all tenants)
        - Tenant-specific: betreiber_id = X (only for that tenant)

    Tenants can only ADD values, not override global ones.

    Usage:
        from v_flask.models import LookupWert

        # Create global value
        status_open = LookupWert(
            kategorie='status',
            code='open',
            name='Offen',
            farbe='#3b82f6',
            icon='circle',
            sort_order=1
        )

        # Create tenant-specific value
        status_custom = LookupWert(
            kategorie='status',
            code='in_review',
            name='In Prüfung',
            farbe='#f59e0b',
            betreiber_id=1,
            sort_order=5
        )

        # Get all values for a category (global + tenant)
        statuses = LookupWert.get_for_kategorie('status', betreiber_id=1)
    """

    __tablename__ = 'lookup_wert'

    id = db.Column(db.Integer, primary_key=True)
    kategorie = db.Column(db.String(50), nullable=False, index=True)
    code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    farbe = db.Column(db.String(7))  # HEX color, e.g. '#3b82f6'
    icon = db.Column(db.String(50))  # Tabler icon name, e.g. 'circle-check'
    sort_order = db.Column(db.Integer, default=0)
    aktiv = db.Column(db.Boolean, default=True, nullable=False)

    # Multi-tenancy: NULL = global, otherwise tenant-specific
    betreiber_id = db.Column(
        db.Integer,
        db.ForeignKey('betreiber.id'),
        nullable=True,
        index=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Unique constraint: same code can exist once globally and once per tenant
    __table_args__ = (
        db.UniqueConstraint('kategorie', 'code', 'betreiber_id', name='uq_lookup_kategorie_code_betreiber'),
    )

    # Relationship
    betreiber = db.relationship('Betreiber', backref='lookup_werte')

    def __repr__(self) -> str:
        return f'<LookupWert {self.kategorie}:{self.code}>'

    @classmethod
    def get_for_kategorie(
        cls,
        kategorie: str,
        betreiber_id: int | None = None,
        include_inactive: bool = False
    ) -> list['LookupWert']:
        """Get all lookup values for a category.

        Returns global values plus tenant-specific values (if betreiber_id provided).

        Args:
            kategorie: Category name (e.g., 'status', 'priority').
            betreiber_id: Tenant ID. If None, only returns global values.
            include_inactive: If True, also returns inactive values.

        Returns:
            List of LookupWert instances, ordered by sort_order.
        """
        query = db.session.query(cls).filter_by(kategorie=kategorie)

        if not include_inactive:
            query = query.filter_by(aktiv=True)

        if betreiber_id:
            # Global + tenant-specific
            query = query.filter(
                db.or_(cls.betreiber_id.is_(None), cls.betreiber_id == betreiber_id)
            )
        else:
            # Only global
            query = query.filter(cls.betreiber_id.is_(None))

        return query.order_by(cls.sort_order, cls.name).all()

    @classmethod
    def get_by_code(
        cls,
        kategorie: str,
        code: str,
        betreiber_id: int | None = None
    ) -> 'LookupWert | None':
        """Get a specific lookup value by category and code.

        Prefers tenant-specific value over global if both exist.

        Args:
            kategorie: Category name.
            code: Value code.
            betreiber_id: Tenant ID for tenant-specific lookup.

        Returns:
            LookupWert instance or None.
        """
        query = db.session.query(cls).filter_by(kategorie=kategorie, code=code)

        if betreiber_id:
            # Try tenant-specific first
            tenant_value = query.filter_by(betreiber_id=betreiber_id).first()
            if tenant_value:
                return tenant_value

        # Fallback to global
        return query.filter(cls.betreiber_id.is_(None)).first()

    @classmethod
    def get_kategorien(cls, betreiber_id: int | None = None) -> list[str]:
        """Get all unique category names.

        Args:
            betreiber_id: If provided, includes tenant-specific categories.

        Returns:
            List of category names.
        """
        query = db.session.query(cls.kategorie).distinct()

        if betreiber_id:
            query = query.filter(
                db.or_(cls.betreiber_id.is_(None), cls.betreiber_id == betreiber_id)
            )
        else:
            query = query.filter(cls.betreiber_id.is_(None))

        return [row[0] for row in query.order_by(cls.kategorie).all()]

    def is_global(self) -> bool:
        """Check if this is a global (non-tenant-specific) value."""
        return self.betreiber_id is None

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'kategorie': self.kategorie,
            'code': self.code,
            'name': self.name,
            'farbe': self.farbe,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'aktiv': self.aktiv,
            'is_global': self.is_global(),
            'betreiber_id': self.betreiber_id,
        }
