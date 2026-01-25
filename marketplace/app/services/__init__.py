"""Marketplace services."""
from app.services.plugin_scanner import scan_plugins
from app.services.plugin_packager import package_plugin
from app.services.trial import (
    start_plugin_trial,
    convert_trial_to_paid,
    expire_trial,
    get_expiring_trials,
    expire_all_overdue_trials,
)
from app.services.pricing import (
    calculate_checkout_price,
    get_plugin_price_matrix,
    get_all_prices_for_plugin,
    format_price_for_display,
)

__all__ = [
    # Plugin packaging
    'scan_plugins',
    'package_plugin',
    # Trial management
    'start_plugin_trial',
    'convert_trial_to_paid',
    'expire_trial',
    'get_expiring_trials',
    'expire_all_overdue_trials',
    # Pricing
    'calculate_checkout_price',
    'get_plugin_price_matrix',
    'get_all_prices_for_plugin',
    'format_price_for_display',
]
