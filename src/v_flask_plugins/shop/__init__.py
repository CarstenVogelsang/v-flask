"""Shop Plugin for v-flask.

B2B Shop with catalog, cart and order management.
Uses PIM for products, CRM for customers, and Pricing for customer-specific prices.
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class ShopPlugin(PluginManifest):
    """B2B Shop Plugin for v-flask."""

    name = 'shop'
    version = '0.1.0'
    description = 'B2B-Shop mit Katalog, Warenkorb und Bestellungen'
    author = 'v-flask'

    dependencies = ['pim', 'crm', 'pricing']

    long_description = '''
B2B-Shop für Geschäftskunden mit:
- Kunden-Login (via CRM CustomerAuth)
- Katalog mit kundenspezifischen Preisen (via PIM + Pricing)
- Warenkorb und Checkout
- Bestellverwaltung im Admin
'''
    license = 'MIT'
    categories = ['shop', 'b2b', 'ecommerce']
    tags = ['shop', 'cart', 'orders', 'b2b', 'catalog', 'checkout']
    min_v_flask_version = '0.2.0'

    admin_category = 'commerce'

    ui_slots = {
        'admin_menu': [
            {
                'label': 'Shop-Bestellungen',
                'url': 'shop_admin.orders_list',
                'icon': 'ti ti-shopping-cart',
                'permission': 'admin.*',
                'order': 30,
            }
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Shop',
                'description': 'Bestellungen verwalten',
                'url': 'shop_admin.orders_list',
                'icon': 'ti-shopping-cart',
                'color_hex': '#f59e0b',
            }
        ],
    }

    def get_models(self):
        """Return all Shop plugin models (Lazy Import!)."""
        from v_flask_plugins.shop.models import (
            Cart,
            CartItem,
            Order,
            OrderItem,
            OrderStatusHistory,
        )
        return [Cart, CartItem, Order, OrderItem, OrderStatusHistory]

    def get_blueprints(self):
        """Return all blueprints (Lazy Import!)."""
        from v_flask_plugins.shop.routes import (
            shop_admin_bp,
            shop_auth_bp,
            shop_public_bp,
        )
        return [
            (shop_auth_bp, '/shop'),
            (shop_public_bp, '/shop'),
            (shop_admin_bp, '/admin/shop'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def on_init(self, app):
        """Initialize Shop plugin."""
        app.logger.info(f'Shop Plugin v{self.version} initialized (POC)')


__all__ = ['ShopPlugin']
