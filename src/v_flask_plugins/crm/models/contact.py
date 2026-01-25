"""Contact model for CRM plugin.

Contact persons (Ansprechpartner) at customer companies.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID

from v_flask.extensions import db


class Salutation(str, Enum):
    """Contact salutation options."""

    MR = 'mr'
    MRS = 'mrs'
    DIVERSE = 'diverse'
    NONE = 'none'

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.MR: 'Herr',
            cls.MRS: 'Frau',
            cls.DIVERSE: 'Divers',
            cls.NONE: '(keine Anrede)',
        }
        return [(s.value, labels[s]) for s in cls]

    @property
    def display(self) -> str:
        """Get localized salutation display text."""
        mapping = {
            Salutation.MR: 'Herr',
            Salutation.MRS: 'Frau',
            Salutation.DIVERSE: 'Divers',
            Salutation.NONE: '',
        }
        return mapping.get(self, '')


class Contact(db.Model):
    """Contact person at a customer company.

    Represents an individual contact (Ansprechpartner) at a B2B customer.
    Each customer can have multiple contacts with one designated as primary.

    Attributes:
        id: UUID primary key.
        customer_id: Foreign key to parent customer.
        salutation: Salutation (Herr, Frau, Divers, none).
        first_name: First name (required).
        last_name: Last name (required).
        position: Job title or position.
        department: Department name.
        email: Direct email address.
        phone_direct: Direct phone number.
        phone_mobile: Mobile phone number.
        notes: Internal notes about the contact.
        is_primary: Whether this is the primary contact for the customer.
        is_active: Whether the contact is active.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.

    Relationships:
        customer: Parent customer entity.

    Example:
        >>> contact = Contact(
        ...     customer_id=customer.id,
        ...     salutation=Salutation.MR,
        ...     first_name='Max',
        ...     last_name='Mustermann',
        ...     position='Einkaufsleiter',
        ...     email='m.mustermann@example.com'
        ... )
    """

    __tablename__ = 'crm_contact'

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    customer_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('crm_customer.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    salutation = db.Column(
        db.String(20),
        default=Salutation.NONE.value,
        nullable=True
    )
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), nullable=True, index=True)
    phone_direct = db.Column(db.String(50), nullable=True)
    phone_mobile = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
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

    # Composite index for finding primary contact
    __table_args__ = (
        db.Index('idx_crm_contact_primary', 'customer_id', 'is_primary'),
        db.Index('idx_crm_contact_active', 'customer_id', 'is_active'),
    )

    # Relationship
    customer = db.relationship('Customer', back_populates='contacts')

    def __repr__(self) -> str:
        return f'<Contact {self.full_name}>'

    @property
    def full_name(self) -> str:
        """Get full name (first + last)."""
        return f'{self.first_name} {self.last_name}'

    @property
    def formal_name(self) -> str:
        """Get formal name with salutation."""
        salutation_text = Salutation(self.salutation).display if self.salutation else ''
        if salutation_text:
            return f'{salutation_text} {self.first_name} {self.last_name}'
        return self.full_name

    @property
    def salutation_display(self) -> str:
        """Get localized salutation."""
        if not self.salutation:
            return ''
        try:
            return Salutation(self.salutation).display
        except ValueError:
            return ''

    @property
    def display_info(self) -> str:
        """Get display info for lists (name + position/department)."""
        parts = [self.full_name]
        if self.position:
            parts.append(self.position)
        elif self.department:
            parts.append(self.department)
        return ' - '.join(parts)

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'salutation': self.salutation,
            'salutation_display': self.salutation_display,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'formal_name': self.formal_name,
            'position': self.position,
            'department': self.department,
            'email': self.email,
            'phone_direct': self.phone_direct,
            'phone_mobile': self.phone_mobile,
            'notes': self.notes,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
