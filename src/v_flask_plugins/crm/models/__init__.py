"""CRM Plugin Models.

Provides models for customer relationship management:
- CustomerGroup: Groups for pricing tiers
- Customer: B2B business customers
- Contact: Contact persons at customers
- Address: Billing/shipping addresses
- CustomerAuth: Shop authentication data
"""

from v_flask_plugins.crm.models.customer_group import CustomerGroup
from v_flask_plugins.crm.models.customer import Customer, CustomerStatus
from v_flask_plugins.crm.models.contact import Contact, Salutation
from v_flask_plugins.crm.models.address import Address, AddressType, COUNTRY_NAMES
from v_flask_plugins.crm.models.customer_auth import CustomerAuth

__all__ = [
    # CustomerGroup (no FK dependencies)
    'CustomerGroup',
    # Customer (depends on CustomerGroup)
    'Customer',
    'CustomerStatus',
    # Contact (depends on Customer)
    'Contact',
    'Salutation',
    # Address (depends on Customer)
    'Address',
    'AddressType',
    'COUNTRY_NAMES',
    # CustomerAuth (depends on Customer)
    'CustomerAuth',
]
