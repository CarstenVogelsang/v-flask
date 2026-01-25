"""PIM (Product Information Management) Plugin for v-flask.

A comprehensive product management plugin providing:
- Products with images, barcodes (GTIN/EAN/UPC), and inventory
- Hierarchical categories
- Manufacturers, brands, and product series
- Product groups and price tags
- Tax rates management
- CSV import/export

This is a core plugin that provides product data for other plugins
like Shop, POS, and Warehouse Management.

Usage:
    from v_flask import VFlask
    from v_flask_plugins.pim import PIMPlugin

    v_flask = VFlask()
    v_flask.register_plugin(PIMPlugin())
    v_flask.init_app(app)

Dependencies:
    - media: Required for product image management
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class PIMPlugin(PluginManifest):
    """Product Information Management plugin for v-flask applications.

    Provides:
        - Product CRUD with images and barcodes
        - Hierarchical category management
        - Manufacturer/Brand/Series hierarchy
        - Product groups for pricing rules
        - Price tags for flexible product labeling
        - Tax rate management
        - CSV import/export
    """

    name = 'pim'
    version = '0.1.0'
    description = 'Produktverwaltung (PIM) mit Kategorien, Herstellern und Steuersätzen'
    author = 'v-flask'

    # Requires media plugin for image management
    dependencies = ['media']

    # Marketplace metadata
    long_description = '''
Ein umfassendes Produktverwaltungs-Plugin für v-flask Anwendungen.

**Features:**
- Produkte mit Bildern, Barcodes (GTIN/EAN/UPC) und Lagerbestand
- Hierarchische Kategorien
- Hersteller-Marken-Serien Hierarchie
- Warengruppen für Preisregeln
- Preis-Tags für flexible Produktkennzeichnung
- Steuersatzverwaltung
- CSV-Import/Export

**Konsumenten:**
Dieses Plugin stellt Produktdaten für Shop-, POS- und WaWi-Plugins bereit.
'''
    license = 'MIT'
    categories = ['products', 'admin', 'core']
    tags = ['pim', 'products', 'catalog', 'inventory', 'categories', 'manufacturers']
    min_v_flask_version = '0.2.0'

    # Admin navigation: appears under "Verwaltung" category
    admin_category = 'management'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'admin_menu': [
            {
                'label': 'Produkte',
                'url': 'pim_admin.list_products',
                'icon': 'ti ti-package',
                'permission': 'admin.*',
                'order': 10,
            },
            {
                'label': 'Kategorien',
                'url': 'pim_admin.list_categories',
                'icon': 'ti ti-category',
                'permission': 'admin.*',
                'order': 11,
            },
            {
                'label': 'Hersteller',
                'url': 'pim_admin.list_manufacturers',
                'icon': 'ti ti-building-factory',
                'permission': 'admin.*',
                'order': 12,
            },
            {
                'label': 'Steuersätze',
                'url': 'pim_admin.list_tax_rates',
                'icon': 'ti ti-receipt-tax',
                'permission': 'admin.*',
                'order': 13,
            },
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Produktverwaltung',
                'description': 'Produkte und Katalog verwalten',
                'url': 'pim_admin.list_products',
                'icon': 'ti-package',
                'color_hex': '#6366f1',
            }
        ],
    }

    def get_models(self):
        """Return all PIM plugin models (Lazy Import!)."""
        from v_flask_plugins.pim.models import (
            Category,
            TaxRate,
            Product,
            ProductImage,
            Manufacturer,
            Brand,
            Series,
            ProductGroup,
            PriceTag,
        )
        return [
            Category,
            TaxRate,
            Product,
            ProductImage,
            Manufacturer,
            Brand,
            Series,
            ProductGroup,
            PriceTag,
        ]

    def get_blueprints(self):
        """Return admin blueprint for PIM management (Lazy Import!)."""
        from v_flask_plugins.pim.routes import pim_admin_bp
        return [
            (pim_admin_bp, '/admin/pim'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_settings_schema(self) -> list[dict]:
        """Define available settings for the PIM plugin.

        Returns:
            List of setting definitions for PIM configuration.
        """
        return [
            {
                'key': 'default_tax_rate_id',
                'label': 'Standard-Steuersatz',
                'type': 'string',
                'description': 'UUID des Standard-Steuersatzes für neue Produkte',
                'default': '',
            },
            {
                'key': 'barcode_validation',
                'label': 'Barcode-Validierung',
                'type': 'bool',
                'description': 'GTIN/EAN/UPC Prüfsummen validieren',
                'default': True,
            },
            {
                'key': 'max_image_size_mb',
                'label': 'Max. Bildgröße (MB)',
                'type': 'int',
                'description': 'Maximale Dateigröße für Produktbilder',
                'default': 5,
                'min': 1,
                'max': 20,
            },
            {
                'key': 'auto_generate_sku',
                'label': 'SKU automatisch generieren',
                'type': 'bool',
                'description': 'Artikelnummer automatisch generieren wenn leer',
                'default': True,
            },
            {
                'key': 'sku_prefix',
                'label': 'SKU-Präfix',
                'type': 'string',
                'description': 'Präfix für automatisch generierte Artikelnummern',
                'default': 'ART-',
            },
            {
                'key': 'stock_unit_default',
                'label': 'Standard-Mengeneinheit',
                'type': 'select',
                'description': 'Standard-Einheit für Lagerbestand',
                'options': [
                    {'value': 'Stück', 'label': 'Stück'},
                    {'value': 'kg', 'label': 'Kilogramm'},
                    {'value': 'l', 'label': 'Liter'},
                    {'value': 'm', 'label': 'Meter'},
                ],
                'default': 'Stück',
            },
        ]

    def on_init(self, app):
        """Initialize PIM plugin services and context processors."""
        from v_flask_plugins.pim.services import pim_service

        @app.context_processor
        def pim_context():
            """Provide PIM helper functions to templates."""

            def get_product_count():
                """Get total active product count for dashboard."""
                return pim_service.get_product_count(active_only=True)

            def get_category_tree():
                """Get hierarchical category tree."""
                return pim_service.get_category_tree(active_only=True)

            return {
                'get_product_count': get_product_count,
                'get_category_tree': get_category_tree,
            }

        app.logger.info(f'PIM Plugin v{self.version} initialized')


# Export the plugin class
__all__ = ['PIMPlugin']
