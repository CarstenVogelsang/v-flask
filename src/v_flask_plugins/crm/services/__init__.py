"""CRM Plugin Services.

Provides business logic layer for customer management:
- CustomerGroupService: Customer group CRUD
- CustomerService: Customer CRUD and search
- ContactService: Contact person management
- AddressService: Address management
- CustomerAuthService: Shop authentication with bcrypt
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from flask import current_app
from sqlalchemy import or_

from v_flask.extensions import db
from werkzeug.security import check_password_hash, generate_password_hash


# ============================================================================
# Helper Functions
# ============================================================================

def parse_uuid(value: UUID | str) -> UUID | None:
    """Parse a UUID from string or pass through UUID.

    Args:
        value: UUID instance or string representation

    Returns:
        UUID instance or None if invalid
    """
    if isinstance(value, UUID):
        return value
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


# ============================================================================
# Data Transfer Objects
# ============================================================================

@dataclass
class CustomerGroupCreate:
    """Data for creating a new customer group."""
    name: str
    description: Optional[str] = None
    discount_percent: float = 0.0
    sort_order: int = 0
    is_default: bool = False


@dataclass
class CustomerGroupUpdate:
    """Data for updating a customer group."""
    name: Optional[str] = None
    description: Optional[str] = None
    discount_percent: Optional[float] = None
    sort_order: Optional[int] = None
    is_default: Optional[bool] = None


@dataclass
class CustomerCreate:
    """Data for creating a new customer."""
    company_name: str
    email: str
    legal_form: Optional[str] = None
    vat_id: Optional[str] = None
    tax_number: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    group_id: Optional[UUID | str] = None


@dataclass
class CustomerUpdate:
    """Data for updating a customer."""
    company_name: Optional[str] = None
    email: Optional[str] = None
    legal_form: Optional[str] = None
    vat_id: Optional[str] = None
    tax_number: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None
    group_id: Optional[UUID | str] = None


@dataclass
class ContactCreate:
    """Data for creating a new contact."""
    first_name: str
    last_name: str
    salutation: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone_direct: Optional[str] = None
    phone_mobile: Optional[str] = None
    notes: Optional[str] = None
    is_primary: bool = False


@dataclass
class ContactUpdate:
    """Data for updating a contact."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    salutation: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone_direct: Optional[str] = None
    phone_mobile: Optional[str] = None
    notes: Optional[str] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None


@dataclass
class AddressCreate:
    """Data for creating a new address."""
    street: str
    zip_code: str
    city: str
    address_type: str = 'both'
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    street2: Optional[str] = None
    country: str = 'DE'
    is_default_billing: bool = False
    is_default_shipping: bool = False


@dataclass
class AddressUpdate:
    """Data for updating an address."""
    street: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    address_type: Optional[str] = None
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    street2: Optional[str] = None
    country: Optional[str] = None
    is_default_billing: Optional[bool] = None
    is_default_shipping: Optional[bool] = None


@dataclass
class AuthResult:
    """Result of authentication attempt."""
    success: bool
    customer: Optional['Customer'] = None
    error: Optional[str] = None  # 'invalid_credentials', 'account_locked', 'access_disabled'


# ============================================================================
# Validators
# ============================================================================

class VatIdValidator:
    """Validates VAT identification numbers (USt-IdNr.).

    Supports DE, AT, CH formats.
    """

    PATTERNS = {
        'DE': re.compile(r'^DE[0-9]{9}$'),
        'AT': re.compile(r'^ATU[0-9]{8}$'),
        'CH': re.compile(r'^CHE[0-9]{3}\.[0-9]{3}\.[0-9]{3}$'),
    }

    def validate(self, vat_id: str) -> tuple[bool, str]:
        """Validate VAT-ID format.

        Args:
            vat_id: VAT identification number to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not vat_id:
            return True, ""  # Optional field

        vat_id = vat_id.strip().upper()

        # Detect country and validate
        if vat_id.startswith('DE'):
            vat_id = vat_id.replace(' ', '')
            if not self.PATTERNS['DE'].match(vat_id):
                return False, "USt-IdNr. muss Format DE123456789 haben"
        elif vat_id.startswith('ATU'):
            vat_id = vat_id.replace(' ', '')
            if not self.PATTERNS['AT'].match(vat_id):
                return False, "USt-IdNr. muss Format ATU12345678 haben"
        elif vat_id.startswith('CHE'):
            if not self.PATTERNS['CH'].match(vat_id):
                return False, "USt-IdNr. muss Format CHE123.456.789 haben"
        else:
            return False, "Unbekanntes USt-IdNr. Format (DE, AT, CH unterstützt)"

        return True, ""


class PasswordValidator:
    """Validates password strength based on settings."""

    def __init__(self, min_length: int = 8, require_special: bool = False):
        self.min_length = min_length
        self.require_special = require_special

    def validate(self, password: str) -> tuple[bool, str]:
        """Validate password strength.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < self.min_length:
            return False, f"Mindestens {self.min_length} Zeichen erforderlich"

        if self.require_special:
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return False, "Mindestens ein Sonderzeichen erforderlich"

        return True, ""


# ============================================================================
# CustomerGroupService
# ============================================================================

class CustomerGroupService:
    """Service for customer group management."""

    def get_by_id(self, group_id: UUID | str) -> Optional['CustomerGroup']:
        """Get customer group by ID.

        Args:
            group_id: Group UUID or string

        Returns:
            CustomerGroup instance or None
        """
        from v_flask_plugins.crm.models import CustomerGroup

        uuid_val = parse_uuid(group_id)
        if not uuid_val:
            return None
        return db.session.get(CustomerGroup, uuid_val)

    def get_all(self) -> list['CustomerGroup']:
        """Get all customer groups ordered by sort_order.

        Returns:
            List of CustomerGroup instances
        """
        from v_flask_plugins.crm.models import CustomerGroup
        return CustomerGroup.query.order_by(
            CustomerGroup.sort_order,
            CustomerGroup.name
        ).all()

    def get_default(self) -> Optional['CustomerGroup']:
        """Get the default customer group.

        Returns:
            Default CustomerGroup or None
        """
        from v_flask_plugins.crm.models import CustomerGroup
        return CustomerGroup.query.filter_by(is_default=True).first()

    def create(self, data: CustomerGroupCreate) -> 'CustomerGroup':
        """Create a new customer group.

        Args:
            data: CustomerGroupCreate DTO

        Returns:
            Created CustomerGroup instance

        Raises:
            ValueError: If name already exists
        """
        from v_flask_plugins.crm.models import CustomerGroup

        # Check for duplicate name
        existing = CustomerGroup.query.filter_by(name=data.name).first()
        if existing:
            raise ValueError(f"Kundengruppe '{data.name}' existiert bereits")

        # Clear other defaults if this is default
        if data.is_default:
            self._clear_default()

        group = CustomerGroup(
            name=data.name.strip(),
            description=data.description,
            discount_percent=data.discount_percent,
            sort_order=data.sort_order,
            is_default=data.is_default,
        )

        db.session.add(group)
        db.session.commit()

        return group

    def update(self, group_id: UUID | str, data: CustomerGroupUpdate) -> 'CustomerGroup':
        """Update a customer group.

        Args:
            group_id: Group UUID or string
            data: CustomerGroupUpdate DTO

        Returns:
            Updated CustomerGroup instance

        Raises:
            ValueError: If group not found or validation fails
        """
        from v_flask_plugins.crm.models import CustomerGroup

        group = self.get_by_id(group_id)
        if not group:
            raise ValueError("Kundengruppe nicht gefunden")

        # Check name uniqueness if changed
        if data.name is not None and data.name != group.name:
            existing = CustomerGroup.query.filter_by(name=data.name).first()
            if existing:
                raise ValueError(f"Kundengruppe '{data.name}' existiert bereits")

        # Handle default flag
        if data.is_default is True and not group.is_default:
            self._clear_default()

        # Update fields
        if data.name is not None:
            group.name = data.name.strip()
        if data.description is not None:
            group.description = data.description
        if data.discount_percent is not None:
            group.discount_percent = data.discount_percent
        if data.sort_order is not None:
            group.sort_order = data.sort_order
        if data.is_default is not None:
            group.is_default = data.is_default

        db.session.commit()
        return group

    def delete(self, group_id: UUID | str) -> bool:
        """Delete a customer group.

        Sets customers' group_id to NULL before deleting.

        Args:
            group_id: Group UUID or string

        Returns:
            True if deleted
        """
        from v_flask_plugins.crm.models import Customer

        group = self.get_by_id(group_id)
        if not group:
            return False

        # Clear group from all customers
        Customer.query.filter_by(group_id=group.id).update({'group_id': None})

        db.session.delete(group)
        db.session.commit()
        return True

    def _clear_default(self):
        """Clear is_default flag for all groups."""
        from v_flask_plugins.crm.models import CustomerGroup
        CustomerGroup.query.filter_by(is_default=True).update({'is_default': False})


# ============================================================================
# CustomerService
# ============================================================================

class CustomerService:
    """Service for customer management operations.

    Provides CRUD operations, search, and customer number generation.
    """

    def __init__(self):
        self.vat_validator = VatIdValidator()

    def get_by_id(self, customer_id: UUID | str) -> Optional['Customer']:
        """Get customer by ID.

        Args:
            customer_id: Customer UUID or string

        Returns:
            Customer instance or None
        """
        from v_flask_plugins.crm.models import Customer

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            return None
        return db.session.get(Customer, uuid_val)

    def get_by_number(self, customer_number: str) -> Optional['Customer']:
        """Get customer by customer number.

        Args:
            customer_number: Unique customer number

        Returns:
            Customer instance or None
        """
        from v_flask_plugins.crm.models import Customer
        return Customer.query.filter_by(customer_number=customer_number).first()

    def get_by_email(self, email: str) -> Optional['Customer']:
        """Get customer by email address.

        Args:
            email: Email address

        Returns:
            Customer instance or None
        """
        from v_flask_plugins.crm.models import Customer
        return Customer.query.filter_by(email=email.lower().strip()).first()

    def search(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        group_id: Optional[UUID | str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list['Customer'], int]:
        """Search customers with filtering and pagination.

        Args:
            query: Search text (company name, customer number, email)
            status: Filter by status (active, inactive, blocked)
            group_id: Filter by customer group UUID
            page: Page number (1-based)
            per_page: Results per page

        Returns:
            Tuple of (results list, total count)
        """
        from v_flask_plugins.crm.models import Customer, CustomerStatus

        q = Customer.query

        # Text search
        if query:
            search_term = f'%{query}%'
            q = q.filter(
                or_(
                    Customer.company_name.ilike(search_term),
                    Customer.customer_number.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.vat_id.ilike(search_term),
                )
            )

        # Status filter
        if status:
            q = q.filter(Customer.status == status)

        # Group filter
        if group_id:
            uuid_val = parse_uuid(group_id)
            if uuid_val:
                q = q.filter(Customer.group_id == uuid_val)

        # Get total count
        total = q.count()

        # Paginate
        customers = q.order_by(Customer.company_name).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        return customers, total

    def get_all(self, active_only: bool = True) -> list['Customer']:
        """Get all customers.

        Args:
            active_only: Only return active customers

        Returns:
            List of customers
        """
        from v_flask_plugins.crm.models import Customer, CustomerStatus

        q = Customer.query
        if active_only:
            q = q.filter(Customer.status == CustomerStatus.ACTIVE.value)
        return q.order_by(Customer.company_name).all()

    def create(self, data: CustomerCreate) -> 'Customer':
        """Create a new customer.

        Generates customer number automatically.
        Validates VAT-ID if provided.

        Args:
            data: CustomerCreate DTO

        Returns:
            Created Customer instance

        Raises:
            ValueError: If validation fails
        """
        from v_flask_plugins.crm.models import Customer, CustomerStatus

        # Validate VAT-ID
        if data.vat_id:
            is_valid, error = self.vat_validator.validate(data.vat_id)
            if not is_valid:
                raise ValueError(error)

        # Check for duplicate email
        existing = self.get_by_email(data.email)
        if existing:
            raise ValueError(f"E-Mail {data.email} wird bereits verwendet")

        # Parse group_id if provided
        group_uuid = parse_uuid(data.group_id) if data.group_id else None

        # Generate customer number
        customer_number = self.generate_customer_number()

        customer = Customer(
            customer_number=customer_number,
            company_name=data.company_name.strip(),
            email=data.email.lower().strip(),
            legal_form=data.legal_form,
            vat_id=data.vat_id.upper().replace(' ', '') if data.vat_id else None,
            tax_number=data.tax_number,
            phone=data.phone,
            website=data.website,
            notes=data.notes,
            status=CustomerStatus.ACTIVE.value,
            group_id=group_uuid,
        )

        if data.tags:
            customer.set_tags_list(data.tags)

        db.session.add(customer)
        db.session.commit()

        current_app.logger.info(f'Customer created: {customer_number}')
        return customer

    def update(self, customer_id: UUID | str, data: CustomerUpdate) -> 'Customer':
        """Update customer data.

        Args:
            customer_id: Customer UUID or string
            data: CustomerUpdate DTO

        Returns:
            Updated Customer instance

        Raises:
            ValueError: If customer not found or validation fails
        """
        customer = self.get_by_id(customer_id)
        if not customer:
            raise ValueError("Kunde nicht gefunden")

        # Validate VAT-ID if changed
        if data.vat_id is not None and data.vat_id != customer.vat_id:
            is_valid, error = self.vat_validator.validate(data.vat_id)
            if not is_valid:
                raise ValueError(error)

        # Check email uniqueness if changed
        if data.email is not None and data.email.lower() != customer.email:
            existing = self.get_by_email(data.email)
            if existing:
                raise ValueError(f"E-Mail {data.email} wird bereits verwendet")

        # Update fields
        if data.company_name is not None:
            customer.company_name = data.company_name.strip()
        if data.email is not None:
            customer.email = data.email.lower().strip()
        if data.legal_form is not None:
            customer.legal_form = data.legal_form
        if data.vat_id is not None:
            customer.vat_id = data.vat_id.upper().replace(' ', '') if data.vat_id else None
        if data.tax_number is not None:
            customer.tax_number = data.tax_number
        if data.phone is not None:
            customer.phone = data.phone
        if data.website is not None:
            customer.website = data.website
        if data.notes is not None:
            customer.notes = data.notes
        if data.tags is not None:
            customer.set_tags_list(data.tags)
        if data.status is not None:
            customer.status = data.status
        if data.group_id is not None:
            customer.group_id = parse_uuid(data.group_id)

        db.session.commit()
        return customer

    def delete(self, customer_id: UUID | str) -> bool:
        """Delete a customer.

        Args:
            customer_id: Customer UUID or string

        Returns:
            True if deleted
        """
        customer = self.get_by_id(customer_id)
        if not customer:
            return False

        # For POC: hard delete
        # MVP: Check for orders, then soft-delete
        db.session.delete(customer)
        db.session.commit()

        current_app.logger.info(f'Customer deleted: {customer.customer_number}')
        return True

    def generate_customer_number(self) -> str:
        """Generate unique customer number based on configured format.

        Format: K-{YYYY}-{NNNNN}

        Returns:
            Generated customer number
        """
        from v_flask_plugins.crm.models import Customer

        format_str = 'K-{YYYY}-{NNNNN}'
        year = datetime.utcnow().year

        # Find highest existing number for this year
        prefix = f'K-{year}-'
        latest = Customer.query.filter(
            Customer.customer_number.like(f'{prefix}%')
        ).order_by(Customer.customer_number.desc()).first()

        if latest:
            try:
                num_part = latest.customer_number.replace(prefix, '')
                next_num = int(num_part) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        result = format_str.replace('{YYYY}', str(year))
        result = result.replace('{YY}', str(year)[-2:])
        result = result.replace('{NNNNN}', f'{next_num:05d}')

        return result

    def get_customer_count(self, active_only: bool = True) -> int:
        """Get total customer count.

        Args:
            active_only: Only count active customers

        Returns:
            Customer count
        """
        from v_flask_plugins.crm.models import Customer, CustomerStatus

        q = Customer.query
        if active_only:
            q = q.filter(Customer.status == CustomerStatus.ACTIVE.value)
        return q.count()


# ============================================================================
# ContactService
# ============================================================================

class ContactService:
    """Service for contact person management."""

    def get_by_id(self, contact_id: UUID | str) -> Optional['Contact']:
        """Get contact by ID.

        Args:
            contact_id: Contact UUID or string

        Returns:
            Contact instance or None
        """
        from v_flask_plugins.crm.models import Contact

        uuid_val = parse_uuid(contact_id)
        if not uuid_val:
            return None
        return db.session.get(Contact, uuid_val)

    def get_by_customer(
        self,
        customer_id: UUID | str,
        active_only: bool = True
    ) -> list['Contact']:
        """Get all contacts for a customer.

        Args:
            customer_id: Customer UUID or string
            active_only: Only return active contacts

        Returns:
            List of contacts
        """
        from v_flask_plugins.crm.models import Contact

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            return []

        q = Contact.query.filter_by(customer_id=uuid_val)
        if active_only:
            q = q.filter_by(is_active=True)
        return q.order_by(Contact.is_primary.desc(), Contact.last_name).all()

    def get_primary(self, customer_id: UUID | str) -> Optional['Contact']:
        """Get primary contact for a customer.

        Args:
            customer_id: Customer UUID or string

        Returns:
            Primary Contact or None
        """
        from v_flask_plugins.crm.models import Contact

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            return None
        return Contact.query.filter_by(
            customer_id=uuid_val,
            is_primary=True,
            is_active=True
        ).first()

    def create(self, customer_id: UUID | str, data: ContactCreate) -> 'Contact':
        """Create a new contact for a customer.

        Args:
            customer_id: Customer UUID or string
            data: ContactCreate DTO

        Returns:
            Created Contact instance

        Raises:
            ValueError: If customer not found
        """
        from v_flask_plugins.crm.models import Contact, Customer

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            raise ValueError("Ungültige Kunden-ID")

        # Verify customer exists
        customer = db.session.get(Customer, uuid_val)
        if not customer:
            raise ValueError("Kunde nicht gefunden")

        # Clear other primary if this is primary
        if data.is_primary:
            self._clear_primary(uuid_val)

        contact = Contact(
            customer_id=uuid_val,
            salutation=data.salutation,
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            position=data.position,
            department=data.department,
            email=data.email.lower().strip() if data.email else None,
            phone_direct=data.phone_direct,
            phone_mobile=data.phone_mobile,
            notes=data.notes,
            is_primary=data.is_primary,
            is_active=True,
        )

        db.session.add(contact)
        db.session.commit()

        return contact

    def update(self, contact_id: UUID | str, data: ContactUpdate) -> 'Contact':
        """Update a contact.

        Args:
            contact_id: Contact UUID or string
            data: ContactUpdate DTO

        Returns:
            Updated Contact instance

        Raises:
            ValueError: If contact not found
        """
        contact = self.get_by_id(contact_id)
        if not contact:
            raise ValueError("Ansprechpartner nicht gefunden")

        # Handle primary flag
        if data.is_primary is True and not contact.is_primary:
            self._clear_primary(contact.customer_id)

        # Update fields
        if data.first_name is not None:
            contact.first_name = data.first_name.strip()
        if data.last_name is not None:
            contact.last_name = data.last_name.strip()
        if data.salutation is not None:
            contact.salutation = data.salutation
        if data.position is not None:
            contact.position = data.position
        if data.department is not None:
            contact.department = data.department
        if data.email is not None:
            contact.email = data.email.lower().strip() if data.email else None
        if data.phone_direct is not None:
            contact.phone_direct = data.phone_direct
        if data.phone_mobile is not None:
            contact.phone_mobile = data.phone_mobile
        if data.notes is not None:
            contact.notes = data.notes
        if data.is_primary is not None:
            contact.is_primary = data.is_primary
        if data.is_active is not None:
            contact.is_active = data.is_active

        db.session.commit()
        return contact

    def delete(self, contact_id: UUID | str) -> bool:
        """Delete a contact (soft-delete by setting is_active=False).

        Args:
            contact_id: Contact UUID or string

        Returns:
            True if deleted
        """
        contact = self.get_by_id(contact_id)
        if not contact:
            return False

        # Soft delete
        contact.is_active = False
        contact.is_primary = False
        db.session.commit()
        return True

    def set_primary(self, contact_id: UUID | str) -> Optional['Contact']:
        """Set contact as primary for their customer.

        Args:
            contact_id: Contact UUID or string

        Returns:
            Updated Contact or None if not found
        """
        contact = self.get_by_id(contact_id)
        if not contact:
            return None

        self._clear_primary(contact.customer_id)
        contact.is_primary = True
        db.session.commit()
        return contact

    def _clear_primary(self, customer_id: UUID):
        """Clear is_primary flag for all customer contacts."""
        from v_flask_plugins.crm.models import Contact
        Contact.query.filter_by(
            customer_id=customer_id,
            is_primary=True
        ).update({'is_primary': False})


# ============================================================================
# AddressService
# ============================================================================

class AddressService:
    """Service for address management operations."""

    def get_by_id(self, address_id: UUID | str) -> Optional['Address']:
        """Get address by ID.

        Args:
            address_id: Address UUID or string

        Returns:
            Address instance or None
        """
        from v_flask_plugins.crm.models import Address

        uuid_val = parse_uuid(address_id)
        if not uuid_val:
            return None
        return db.session.get(Address, uuid_val)

    def get_by_customer(self, customer_id: UUID | str) -> list['Address']:
        """Get all addresses for a customer.

        Args:
            customer_id: Customer UUID or string

        Returns:
            List of addresses
        """
        from v_flask_plugins.crm.models import Address

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            return []
        return Address.query.filter_by(customer_id=uuid_val).all()

    def get_default_billing(self, customer_id: UUID | str) -> Optional['Address']:
        """Get default billing address for a customer.

        Args:
            customer_id: Customer UUID or string

        Returns:
            Address instance or None
        """
        from v_flask_plugins.crm.models import Address

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            return None
        return Address.query.filter_by(
            customer_id=uuid_val,
            is_default_billing=True
        ).first()

    def get_default_shipping(self, customer_id: UUID | str) -> Optional['Address']:
        """Get default shipping address for a customer.

        Args:
            customer_id: Customer UUID or string

        Returns:
            Address instance or None
        """
        from v_flask_plugins.crm.models import Address

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            return None
        return Address.query.filter_by(
            customer_id=uuid_val,
            is_default_shipping=True
        ).first()

    def create(self, customer_id: UUID | str, data: AddressCreate) -> 'Address':
        """Create a new address for a customer.

        Args:
            customer_id: Customer UUID or string
            data: AddressCreate DTO

        Returns:
            Created Address instance

        Raises:
            ValueError: If customer not found
        """
        from v_flask_plugins.crm.models import Address, Customer

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            raise ValueError("Ungültige Kunden-ID")

        # Verify customer exists
        customer = db.session.get(Customer, uuid_val)
        if not customer:
            raise ValueError("Kunde nicht gefunden")

        # Handle default flags
        if data.is_default_billing:
            self._clear_default_billing(uuid_val)
        if data.is_default_shipping:
            self._clear_default_shipping(uuid_val)

        address = Address(
            customer_id=uuid_val,
            address_type=data.address_type,
            company_name=data.company_name,
            contact_name=data.contact_name,
            street=data.street.strip(),
            street2=data.street2,
            zip_code=data.zip_code.strip(),
            city=data.city.strip(),
            country=data.country.upper(),
            is_default_billing=data.is_default_billing,
            is_default_shipping=data.is_default_shipping,
        )

        db.session.add(address)
        db.session.commit()

        return address

    def update(self, address_id: UUID | str, data: AddressUpdate) -> 'Address':
        """Update an address.

        Args:
            address_id: Address UUID or string
            data: AddressUpdate DTO

        Returns:
            Updated Address instance

        Raises:
            ValueError: If address not found
        """
        address = self.get_by_id(address_id)
        if not address:
            raise ValueError("Adresse nicht gefunden")

        # Handle default flag changes
        if data.is_default_billing is True and not address.is_default_billing:
            self._clear_default_billing(address.customer_id)
        if data.is_default_shipping is True and not address.is_default_shipping:
            self._clear_default_shipping(address.customer_id)

        # Update fields
        if data.street is not None:
            address.street = data.street.strip()
        if data.zip_code is not None:
            address.zip_code = data.zip_code.strip()
        if data.city is not None:
            address.city = data.city.strip()
        if data.address_type is not None:
            address.address_type = data.address_type
        if data.company_name is not None:
            address.company_name = data.company_name
        if data.contact_name is not None:
            address.contact_name = data.contact_name
        if data.street2 is not None:
            address.street2 = data.street2
        if data.country is not None:
            address.country = data.country.upper()
        if data.is_default_billing is not None:
            address.is_default_billing = data.is_default_billing
        if data.is_default_shipping is not None:
            address.is_default_shipping = data.is_default_shipping

        db.session.commit()
        return address

    def delete(self, address_id: UUID | str) -> bool:
        """Delete an address.

        Args:
            address_id: Address UUID or string

        Returns:
            True if deleted
        """
        address = self.get_by_id(address_id)
        if not address:
            return False

        db.session.delete(address)
        db.session.commit()
        return True

    def set_default_billing(self, address_id: UUID | str) -> bool:
        """Set address as default billing address.

        Args:
            address_id: Address UUID or string

        Returns:
            True if successful
        """
        address = self.get_by_id(address_id)
        if not address:
            return False

        self._clear_default_billing(address.customer_id)
        address.is_default_billing = True
        db.session.commit()
        return True

    def set_default_shipping(self, address_id: UUID | str) -> bool:
        """Set address as default shipping address.

        Args:
            address_id: Address UUID or string

        Returns:
            True if successful
        """
        address = self.get_by_id(address_id)
        if not address:
            return False

        self._clear_default_shipping(address.customer_id)
        address.is_default_shipping = True
        db.session.commit()
        return True

    def _clear_default_billing(self, customer_id: UUID):
        """Clear default billing flag for all customer addresses."""
        from v_flask_plugins.crm.models import Address
        Address.query.filter_by(
            customer_id=customer_id,
            is_default_billing=True
        ).update({'is_default_billing': False})

    def _clear_default_shipping(self, customer_id: UUID):
        """Clear default shipping flag for all customer addresses."""
        from v_flask_plugins.crm.models import Address
        Address.query.filter_by(
            customer_id=customer_id,
            is_default_shipping=True
        ).update({'is_default_shipping': False})


# ============================================================================
# CustomerAuthService
# ============================================================================

class CustomerAuthService:
    """Service for customer shop authentication.

    Provides login, password management, and brute-force protection.
    """

    def __init__(
        self,
        min_password_length: int = 8,
        require_special: bool = False,
        max_attempts: int = 5,
        lockout_minutes: int = 15,
    ):
        self.password_validator = PasswordValidator(
            min_length=min_password_length,
            require_special=require_special
        )
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes

    def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate customer login.

        Args:
            email: Customer email
            password: Plain text password

        Returns:
            AuthResult with success status and customer/error
        """
        from v_flask_plugins.crm.models import CustomerAuth

        auth = CustomerAuth.query.filter_by(email=email.lower().strip()).first()

        if not auth:
            return AuthResult(success=False, error='invalid_credentials')

        # Check if locked
        if auth.is_locked():
            return AuthResult(success=False, error='account_locked')

        # Check if access disabled
        if not auth.is_active:
            return AuthResult(success=False, error='access_disabled')

        # Verify password
        if not auth.check_password(password):
            auth.record_failed_login(self.max_attempts, self.lockout_minutes)
            db.session.commit()
            return AuthResult(success=False, error='invalid_credentials')

        # Success - update login stats
        auth.record_successful_login()
        db.session.commit()

        return AuthResult(success=True, customer=auth.customer)

    def enable_shop_access(
        self,
        customer_id: UUID | str,
        password: str,
    ) -> 'CustomerAuth':
        """Enable shop access for a customer.

        Args:
            customer_id: Customer UUID or string
            password: Initial password

        Returns:
            CustomerAuth instance

        Raises:
            ValueError: If password invalid or customer not found
        """
        from v_flask_plugins.crm.models import CustomerAuth, Customer

        # Validate password
        is_valid, error = self.password_validator.validate(password)
        if not is_valid:
            raise ValueError(error)

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            raise ValueError("Ungültige Kunden-ID")

        customer = db.session.get(Customer, uuid_val)
        if not customer:
            raise ValueError("Kunde nicht gefunden")

        auth = customer.auth

        if auth:
            # Update existing
            auth.set_password(password)
            auth.is_active = True
            auth.reset_failed_logins()
        else:
            # Create new
            auth = CustomerAuth(
                customer_id=uuid_val,
                email=customer.email,
                password_hash='',  # Will be set by set_password
                is_active=True,
            )
            auth.set_password(password)
            db.session.add(auth)

        db.session.commit()
        current_app.logger.info(f'Shop access enabled for customer {customer.customer_number}')
        return auth

    def disable_shop_access(self, customer_id: UUID | str) -> bool:
        """Disable shop access for a customer.

        Args:
            customer_id: Customer UUID or string

        Returns:
            True if successful
        """
        from v_flask_plugins.crm.models import CustomerAuth

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            return False

        auth = CustomerAuth.query.filter_by(customer_id=uuid_val).first()
        if not auth:
            return False

        auth.is_active = False
        db.session.commit()
        return True

    def change_password(
        self,
        customer_id: UUID | str,
        old_password: str,
        new_password: str,
    ) -> bool:
        """Change customer password.

        Args:
            customer_id: Customer UUID or string
            old_password: Current password for verification
            new_password: New password

        Returns:
            True if successful

        Raises:
            ValueError: If validation fails
        """
        from v_flask_plugins.crm.models import CustomerAuth

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            raise ValueError("Ungültige Kunden-ID")

        auth = CustomerAuth.query.filter_by(customer_id=uuid_val).first()
        if not auth:
            raise ValueError("Kein Shop-Zugang vorhanden")

        # Verify old password
        if not auth.check_password(old_password):
            raise ValueError("Aktuelles Passwort ist falsch")

        # Validate new password
        is_valid, error = self.password_validator.validate(new_password)
        if not is_valid:
            raise ValueError(error)

        auth.set_password(new_password)
        db.session.commit()
        return True

    def set_password(self, customer_id: UUID | str, new_password: str) -> bool:
        """Set customer password (admin function, no old password check).

        Args:
            customer_id: Customer UUID or string
            new_password: New password

        Returns:
            True if successful

        Raises:
            ValueError: If validation fails
        """
        from v_flask_plugins.crm.models import CustomerAuth

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            raise ValueError("Ungültige Kunden-ID")

        auth = CustomerAuth.query.filter_by(customer_id=uuid_val).first()
        if not auth:
            raise ValueError("Kein Shop-Zugang vorhanden")

        # Validate new password
        is_valid, error = self.password_validator.validate(new_password)
        if not is_valid:
            raise ValueError(error)

        auth.set_password(new_password)
        auth.reset_failed_logins()
        db.session.commit()
        return True

    def unlock_account(self, customer_id: UUID | str) -> bool:
        """Unlock a locked customer account.

        Args:
            customer_id: Customer UUID or string

        Returns:
            True if successful
        """
        from v_flask_plugins.crm.models import CustomerAuth

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            return False

        auth = CustomerAuth.query.filter_by(customer_id=uuid_val).first()
        if not auth:
            return False

        auth.reset_failed_logins()
        db.session.commit()
        return True

    def get_by_customer(self, customer_id: UUID | str) -> Optional['CustomerAuth']:
        """Get auth record for a customer.

        Args:
            customer_id: Customer UUID or string

        Returns:
            CustomerAuth instance or None
        """
        from v_flask_plugins.crm.models import CustomerAuth

        uuid_val = parse_uuid(customer_id)
        if not uuid_val:
            return None
        return CustomerAuth.query.filter_by(customer_id=uuid_val).first()


# ============================================================================
# CRM Service Facade
# ============================================================================

class CRMService:
    """Facade providing access to all CRM services."""

    def __init__(self):
        self._group_service: Optional[CustomerGroupService] = None
        self._customer_service: Optional[CustomerService] = None
        self._contact_service: Optional[ContactService] = None
        self._address_service: Optional[AddressService] = None
        self._auth_service: Optional[CustomerAuthService] = None

    @property
    def groups(self) -> CustomerGroupService:
        """Get customer group service instance."""
        if self._group_service is None:
            self._group_service = CustomerGroupService()
        return self._group_service

    @property
    def customers(self) -> CustomerService:
        """Get customer service instance."""
        if self._customer_service is None:
            self._customer_service = CustomerService()
        return self._customer_service

    @property
    def contacts(self) -> ContactService:
        """Get contact service instance."""
        if self._contact_service is None:
            self._contact_service = ContactService()
        return self._contact_service

    @property
    def addresses(self) -> AddressService:
        """Get address service instance."""
        if self._address_service is None:
            self._address_service = AddressService()
        return self._address_service

    @property
    def auth(self) -> CustomerAuthService:
        """Get auth service instance."""
        if self._auth_service is None:
            self._auth_service = CustomerAuthService()
        return self._auth_service

    # Convenience methods
    def get_customer_count(self, active_only: bool = True) -> int:
        """Get total customer count."""
        return self.customers.get_customer_count(active_only)

    def get_all_groups(self) -> list:
        """Get all customer groups."""
        return self.groups.get_all()


# ============================================================================
# Singleton instance
# ============================================================================

crm_service = CRMService()

__all__ = [
    # Helpers
    'parse_uuid',
    # DTOs
    'CustomerGroupCreate',
    'CustomerGroupUpdate',
    'CustomerCreate',
    'CustomerUpdate',
    'ContactCreate',
    'ContactUpdate',
    'AddressCreate',
    'AddressUpdate',
    'AuthResult',
    # Validators
    'VatIdValidator',
    'PasswordValidator',
    # Services
    'CustomerGroupService',
    'CustomerService',
    'ContactService',
    'AddressService',
    'CustomerAuthService',
    'CRMService',
    'crm_service',
]
