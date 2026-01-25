"""Address model for CRM plugin.

Customer billing and shipping addresses.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID

from v_flask.extensions import db


class AddressType(str, Enum):
    """Address type enumeration."""

    BILLING = 'billing'
    SHIPPING = 'shipping'
    BOTH = 'both'

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.BILLING: 'Rechnungsadresse',
            cls.SHIPPING: 'Lieferadresse',
            cls.BOTH: 'Rechnungs- & Lieferadresse',
        }
        return [(a.value, labels[a]) for a in cls]

    @property
    def display(self) -> str:
        """Get localized type display text."""
        labels = {
            AddressType.BILLING: 'Rechnungsadresse',
            AddressType.SHIPPING: 'Lieferadresse',
            AddressType.BOTH: 'Rechnungs-/Lieferadresse',
        }
        return labels.get(self, self.value)


# Country code to name mapping for DACH region
COUNTRY_NAMES = {
    'DE': 'Deutschland',
    'AT': 'Österreich',
    'CH': 'Schweiz',
    'NL': 'Niederlande',
    'BE': 'Belgien',
    'FR': 'Frankreich',
    'PL': 'Polen',
    'CZ': 'Tschechien',
    'LU': 'Luxemburg',
    'IT': 'Italien',
}


class Address(db.Model):
    """Customer address entity.

    Stores billing and shipping addresses for customers.
    Each customer can have multiple addresses with one default
    for billing and one for shipping.

    Attributes:
        id: UUID primary key.
        customer_id: Foreign key to customer.
        address_type: Type of address (billing, shipping, both).
        company_name: Optional different company name (e.g., branch).
        contact_name: Contact person for delivery.
        street: Street and house number.
        street2: Additional address line.
        zip_code: Postal code.
        city: City name.
        country: ISO country code (default: DE).
        is_default_billing: Whether this is the default billing address.
        is_default_shipping: Whether this is the default shipping address.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.

    Relationships:
        customer: Parent customer entity.

    Example:
        >>> address = Address(
        ...     customer_id=customer.id,
        ...     address_type=AddressType.BOTH.value,
        ...     street='Musterstraße 123',
        ...     zip_code='12345',
        ...     city='Berlin'
        ... )
    """

    __tablename__ = 'crm_address'

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
    address_type = db.Column(
        db.String(20),
        default=AddressType.BOTH.value,
        nullable=False
    )
    company_name = db.Column(db.String(255), nullable=True)
    contact_name = db.Column(db.String(200), nullable=True)
    street = db.Column(db.String(255), nullable=False)
    street2 = db.Column(db.String(255), nullable=True)
    zip_code = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(2), default='DE', nullable=False)
    is_default_billing = db.Column(db.Boolean, default=False, nullable=False)
    is_default_shipping = db.Column(db.Boolean, default=False, nullable=False)
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

    # Index for finding defaults
    __table_args__ = (
        db.Index(
            'idx_crm_address_defaults',
            'customer_id', 'is_default_billing', 'is_default_shipping'
        ),
    )

    # Relationship
    customer = db.relationship('Customer', back_populates='addresses')

    def __repr__(self) -> str:
        return f'<Address {self.id}: {self.street}, {self.city}>'

    @property
    def full_address(self) -> str:
        """Return formatted full address as single line."""
        parts = [self.street]
        if self.street2:
            parts.append(self.street2)
        parts.append(f'{self.zip_code} {self.city}')
        parts.append(self.country)
        return ', '.join(parts)

    @property
    def formatted(self) -> str:
        """Get formatted address string with line breaks.

        Returns:
            Multi-line formatted address suitable for labels.
        """
        lines = []
        if self.company_name:
            lines.append(self.company_name)
        if self.contact_name:
            lines.append(self.contact_name)
        lines.append(self.street)
        if self.street2:
            lines.append(self.street2)
        lines.append(f'{self.zip_code} {self.city}')
        if self.country != 'DE':
            lines.append(self.country_name)
        return '\n'.join(lines)

    @property
    def country_name(self) -> str:
        """Get country name from ISO code."""
        return COUNTRY_NAMES.get(self.country, self.country)

    @property
    def type_display(self) -> str:
        """Get localized address type."""
        try:
            return AddressType(self.address_type).display
        except ValueError:
            return self.address_type

    @property
    def display_name(self) -> str:
        """Return display name for address selection."""
        type_labels = {
            AddressType.BILLING.value: 'Rechnung',
            AddressType.SHIPPING.value: 'Lieferung',
            AddressType.BOTH.value: 'Rechnung/Lieferung',
        }
        label = type_labels.get(self.address_type, self.address_type)
        return f'{label}: {self.street}, {self.zip_code} {self.city}'

    @property
    def short_display(self) -> str:
        """Short display format for lists."""
        return f'{self.street}, {self.zip_code} {self.city}'

    @classmethod
    def country_choices(cls) -> list[tuple[str, str]]:
        """Return list of (code, name) tuples for country select.

        Returns:
            List of country code/name tuples sorted alphabetically.
        """
        return sorted(COUNTRY_NAMES.items(), key=lambda x: x[1])

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'address_type': self.address_type,
            'type_display': self.type_display,
            'company_name': self.company_name,
            'contact_name': self.contact_name,
            'street': self.street,
            'street2': self.street2,
            'zip_code': self.zip_code,
            'city': self.city,
            'country': self.country,
            'country_name': self.country_name,
            'is_default_billing': self.is_default_billing,
            'is_default_shipping': self.is_default_shipping,
            'full_address': self.full_address,
            'formatted': self.formatted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
