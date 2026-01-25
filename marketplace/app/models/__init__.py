"""Marketplace database models."""
from app.models.project import Project
from app.models.project_type import ProjectType
from app.models.plugin_category import PluginCategory
from app.models.plugin_meta import PluginMeta
from app.models.plugin_price import PluginPrice
from app.models.plugin_version import PluginVersion
from app.models.license import License
from app.models.license_history import LicenseHistory
from app.models.order import Order

# License status constants for convenience
from app.models.license import (
    LICENSE_STATUS_ACTIVE,
    LICENSE_STATUS_TRIAL,
    LICENSE_STATUS_SUSPENDED,
    LICENSE_STATUS_EXPIRED,
    LICENSE_STATUS_REVOKED,
    BILLING_CYCLE_ONCE,
    BILLING_CYCLE_MONTHLY,
    BILLING_CYCLE_YEARLY,
)

__all__ = [
    # Core models
    'Project',
    'ProjectType',
    'PluginCategory',
    'PluginMeta',
    'PluginPrice',
    'PluginVersion',
    'License',
    'LicenseHistory',
    'Order',
    # License status constants
    'LICENSE_STATUS_ACTIVE',
    'LICENSE_STATUS_TRIAL',
    'LICENSE_STATUS_SUSPENDED',
    'LICENSE_STATUS_EXPIRED',
    'LICENSE_STATUS_REVOKED',
    'BILLING_CYCLE_ONCE',
    'BILLING_CYCLE_MONTHLY',
    'BILLING_CYCLE_YEARLY',
]
