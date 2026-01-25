"""Shop services facade.

Usage:
    from v_flask_plugins.shop.services import shop_service

    # Cart operations
    cart = shop_service.cart.get_or_create(customer_id)
    shop_service.cart.add_item(cart, product_id, quantity)

    # Order operations
    order = shop_service.orders.create_from_cart(cart, customer_id, shipping_address)
    shop_service.orders.change_status(order, 'confirmed', 'admin@example.com')

    # Catalog (PIM + Pricing wrapper)
    products = shop_service.catalog.get_products_by_category(category_id, customer_id)
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from v_flask_plugins.shop.services.cart_service import CartService
    from v_flask_plugins.shop.services.catalog_service import CatalogService
    from v_flask_plugins.shop.services.order_service import OrderService


class ShopService:
    """Facade for all Shop services with lazy loading."""

    def __init__(self):
        self._cart: Optional['CartService'] = None
        self._orders: Optional['OrderService'] = None
        self._catalog: Optional['CatalogService'] = None

    @property
    def cart(self) -> 'CartService':
        """Get cart service (lazy loaded)."""
        if self._cart is None:
            from v_flask_plugins.shop.services.cart_service import CartService
            self._cart = CartService()
        return self._cart

    @property
    def orders(self) -> 'OrderService':
        """Get order service (lazy loaded)."""
        if self._orders is None:
            from v_flask_plugins.shop.services.order_service import OrderService
            self._orders = OrderService()
        return self._orders

    @property
    def catalog(self) -> 'CatalogService':
        """Get catalog service (lazy loaded)."""
        if self._catalog is None:
            from v_flask_plugins.shop.services.catalog_service import CatalogService
            self._catalog = CatalogService()
        return self._catalog


# Singleton instance
shop_service = ShopService()

__all__ = ['shop_service', 'ShopService']
