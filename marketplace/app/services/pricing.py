"""Pricing calculation for plugin checkout.

Handles differentiated pricing per project type and billing calculations.
"""
from v_flask import db
from app.models import Project, PluginMeta, PluginPrice


def calculate_checkout_price(
    plugin_id: int,
    project_id: int,
    billing_cycle: str = 'once'
) -> dict | None:
    """Calculate the full checkout price for a plugin.

    Uses differentiated pricing if configured, otherwise base price.
    Includes setup fee if applicable.

    Args:
        plugin_id: ID of the plugin
        project_id: ID of the project (for project type)
        billing_cycle: Billing cycle (once, monthly, yearly)

    Returns:
        Dict with price details, or None if plugin/project not found.
        {
            'plugin_id': int,
            'plugin_name': str,
            'project_type_code': str | None,
            'billing_cycle': str,
            'price_cents': int,
            'setup_fee_cents': int,
            'total_cents': int,
            'currency': str,
            'is_free': bool,
        }
    """
    plugin = db.session.get(PluginMeta, plugin_id)
    if not plugin:
        return None

    project = db.session.get(Project, project_id)
    if not project:
        return None

    # Try to get differentiated price
    price_cents = plugin.price_cents  # Base price fallback
    setup_fee_cents = 0
    currency = 'EUR'
    project_type_code = None

    if project.project_type_id:
        project_type_code = project.project_type.code if project.project_type else None

        # Look for specific price
        plugin_price = PluginPrice.get_for_plugin_and_type(
            plugin_id=plugin_id,
            project_type_id=project.project_type_id,
            billing_cycle=billing_cycle
        )

        if plugin_price and plugin_price.is_valid:
            price_cents = plugin_price.price_cents
            setup_fee_cents = plugin_price.setup_fee_cents
            currency = plugin_price.currency

    return {
        'plugin_id': plugin_id,
        'plugin_name': plugin.name,
        'project_type_code': project_type_code,
        'billing_cycle': billing_cycle,
        'price_cents': price_cents,
        'setup_fee_cents': setup_fee_cents,
        'total_cents': price_cents + setup_fee_cents,
        'currency': currency,
        'is_free': price_cents == 0,
    }


def get_plugin_price_matrix(plugin_id: int) -> dict:
    """Get all prices for a plugin grouped by project type.

    Convenience wrapper around PluginPrice.get_price_matrix().

    Args:
        plugin_id: ID of the plugin

    Returns:
        Dict mapping project_type_code to list of price dicts.
        Example:
        {
            'einzelkunde': [
                {'billing_cycle': 'once', 'price_cents': 5000, ...},
                {'billing_cycle': 'monthly', 'price_cents': 500, ...},
            ],
            'business_directory': [...]
        }
    """
    return PluginPrice.get_price_matrix(plugin_id)


def get_all_prices_for_plugin(plugin_id: int) -> list[dict]:
    """Get all prices for a plugin as flat list.

    Useful for admin views.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of price dicts with project type info.
    """
    prices = db.session.query(PluginPrice).filter_by(
        plugin_id=plugin_id,
        is_active=True
    ).all()

    return [
        {
            'id': p.id,
            'project_type_id': p.project_type_id,
            'project_type_code': p.project_type.code if p.project_type else None,
            'project_type_name': p.project_type.name if p.project_type else None,
            'billing_cycle': p.billing_cycle,
            'price_cents': p.price_cents,
            'price_display': p.price_display,
            'setup_fee_cents': p.setup_fee_cents,
            'currency': p.currency,
            'is_valid': p.is_valid,
        }
        for p in prices
    ]


def format_price_for_display(cents: int, currency: str = 'EUR') -> str:
    """Format price in cents to display string.

    Args:
        cents: Price in cents
        currency: Currency code

    Returns:
        Formatted string like "50,00 €"
    """
    if cents == 0:
        return 'Kostenlos'

    if currency == 'EUR':
        euros = cents / 100
        return f'{euros:.2f} €'.replace('.', ',')

    # Other currencies
    amount = cents / 100
    return f'{amount:.2f} {currency}'
