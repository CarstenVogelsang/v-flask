"""Customer model for CRM plugin.

B2B customer master data with company information, VAT-ID, and contact details.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4
import json

from sqlalchemy.dialects.postgresql import UUID

from v_flask.extensions import db


class CustomerStatus(str, Enum):
    """Customer status enumeration."""

    ACTIVE = 'active'
    INACTIVE = 'inactive'
    BLOCKED = 'blocked'

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.ACTIVE: 'Aktiv',
            cls.INACTIVE: 'Inaktiv',
            cls.BLOCKED: 'Gesperrt',
        }
        return [(s.value, labels[s]) for s in cls]

    @property
    def display(self) -> str:
        """Get localized status display text."""
        labels = {
            CustomerStatus.ACTIVE: 'Aktiv',
            CustomerStatus.INACTIVE: 'Inaktiv',
            CustomerStatus.BLOCKED: 'Gesperrt',
        }
        return labels.get(self, self.value)

    @property
    def badge_class(self) -> str:
        """Get DaisyUI badge class for this status."""
        classes = {
            CustomerStatus.ACTIVE: 'badge-success',
            CustomerStatus.INACTIVE: 'badge-ghost',
            CustomerStatus.BLOCKED: 'badge-error',
        }
        return classes.get(self, 'badge-ghost')


class Customer(db.Model):
    """B2B Customer entity with company information.

    Stores business customer master data including company name,
    VAT-ID (USt-IdNr.), and contact information.

    Attributes:
        id: UUID primary key.
        customer_number: Unique auto-generated customer number (e.g., K-2025-00001).
        company_name: Legal company name.
        legal_form: Company legal form (GmbH, AG, etc.).
        vat_id: EU VAT-ID (USt-IdNr.), e.g., DE123456789.
        tax_number: Tax number (Steuernummer).
        email: Primary contact email.
        phone: Primary phone number.
        website: Company website URL.
        notes: Internal notes about the customer.
        tags: JSON array of tags for filtering/categorization.
        status: Customer status (active, inactive, blocked).
        group_id: Foreign key to CustomerGroup (optional).
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.

    Relationships:
        group: CustomerGroup for pricing tiers.
        contacts: List of contact persons (Ansprechpartner).
        addresses: List of customer addresses.
        auth: CustomerAuth for shop login (1:1).

    Example:
        >>> customer = Customer(
        ...     customer_number='K-2025-00001',
        ...     company_name='Musterfirma GmbH',
        ...     email='info@musterfirma.de'
        ... )
    """

    __tablename__ = 'crm_customer'

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    customer_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )
    company_name = db.Column(db.String(255), nullable=False)
    legal_form = db.Column(db.String(50), nullable=True)
    vat_id = db.Column(db.String(20), nullable=True, index=True)
    tax_number = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)  # JSON array stored as text
    status = db.Column(
        db.String(20),
        default=CustomerStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    group_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('crm_customer_group.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
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
    group = db.relationship('CustomerGroup', back_populates='customers')
    contacts = db.relationship(
        'Contact',
        back_populates='customer',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    addresses = db.relationship(
        'Address',
        back_populates='customer',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    auth = db.relationship(
        'CustomerAuth',
        back_populates='customer',
        uselist=False,
        cascade='all, delete-orphan'
    )

    # Additional indexes
    __table_args__ = (
        db.Index('idx_crm_customer_group', 'group_id'),
    )

    def __repr__(self) -> str:
        return f'<Customer {self.customer_number}: {self.company_name}>'

    @property
    def is_active(self) -> bool:
        """Check if customer is active."""
        return self.status == CustomerStatus.ACTIVE.value

    @property
    def is_blocked(self) -> bool:
        """Check if customer is blocked."""
        return self.status == CustomerStatus.BLOCKED.value

    @property
    def status_display(self) -> str:
        """Get localized status display text."""
        try:
            return CustomerStatus(self.status).display
        except ValueError:
            return self.status

    @property
    def status_badge_class(self) -> str:
        """Get DaisyUI badge class for status."""
        try:
            return CustomerStatus(self.status).badge_class
        except ValueError:
            return 'badge-ghost'

    @property
    def has_shop_access(self) -> bool:
        """Check if customer has active shop access."""
        return self.auth is not None and self.auth.is_active

    @property
    def primary_contact(self):
        """Get primary contact person.

        Returns:
            Contact or None if no primary contact.
        """
        return self.contacts.filter_by(is_primary=True, is_active=True).first()

    @property
    def default_billing_address(self):
        """Get default billing address.

        Returns:
            Address or None if not set.
        """
        return self.addresses.filter_by(is_default_billing=True).first()

    @property
    def default_shipping_address(self):
        """Get default shipping address.

        Returns:
            Address or None if not set.
        """
        return self.addresses.filter_by(is_default_shipping=True).first()

    def get_tags_list(self) -> list[str]:
        """Get tags as Python list.

        Returns:
            List of tag strings or empty list.
        """
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_tags_list(self, tags: list[str]) -> None:
        """Set tags from Python list.

        Args:
            tags: List of tag strings.
        """
        self.tags = json.dumps(tags) if tags else None

    def add_tag(self, tag: str) -> None:
        """Add a tag to the customer.

        Args:
            tag: Tag string to add.
        """
        tags = self.get_tags_list()
        if tag not in tags:
            tags.append(tag)
            self.set_tags_list(tags)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the customer.

        Args:
            tag: Tag string to remove.
        """
        tags = self.get_tags_list()
        if tag in tags:
            tags.remove(tag)
            self.set_tags_list(tags)

    def to_dict(self, include_addresses: bool = False, include_contacts: bool = False) -> dict:
        """Return dictionary representation.

        Args:
            include_addresses: Include address list in output.
            include_contacts: Include contact list in output.

        Returns:
            Dictionary with customer data.
        """
        result = {
            'id': str(self.id),
            'customer_number': self.customer_number,
            'company_name': self.company_name,
            'legal_form': self.legal_form,
            'vat_id': self.vat_id,
            'tax_number': self.tax_number,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'notes': self.notes,
            'tags': self.get_tags_list(),
            'status': self.status,
            'status_display': self.status_display,
            'group_id': str(self.group_id) if self.group_id else None,
            'group_name': self.group.name if self.group else None,
            'has_shop_access': self.has_shop_access,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_addresses:
            result['addresses'] = [addr.to_dict() for addr in self.addresses.all()]

        if include_contacts:
            result['contacts'] = [contact.to_dict() for contact in self.contacts.all()]

        return result
