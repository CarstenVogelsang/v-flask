"""Cart service for Shop plugin."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class CartTotal:
    """Cart totals with customer-specific prices."""

    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    item_count: int


@dataclass
class CartItemWithPrice:
    """Cart item enriched with product and price data."""

    item: 'CartItem'
    product: 'Product'
    unit_price: Decimal
    line_total: Decimal
    is_discounted: bool
    list_price: Decimal


class CartService:
    """Service for shopping cart operations."""

    def get_or_create(self, customer_id: str) -> 'Cart':
        """Get existing cart or create new one for customer.

        Args:
            customer_id: CRM customer UUID

        Returns:
            Cart instance
        """
        from v_flask.extensions import db
        from v_flask_plugins.shop.models import Cart

        cart = Cart.query.filter_by(customer_id=customer_id).first()
        if not cart:
            cart = Cart(customer_id=customer_id)
            db.session.add(cart)
            db.session.commit()
        return cart

    def add_item(
        self,
        cart: 'Cart',
        product_id: str,
        quantity: int = 1
    ) -> 'CartItem':
        """Add product to cart or increase quantity if exists.

        Args:
            cart: Cart instance
            product_id: PIM product UUID
            quantity: Amount to add (default 1)

        Returns:
            CartItem instance
        """
        from v_flask.extensions import db
        from v_flask_plugins.shop.models import CartItem

        # Check for existing item
        item = CartItem.query.filter_by(
            cart_id=cart.id,
            product_id=product_id
        ).first()

        if item:
            item.quantity += quantity
        else:
            item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(item)

        db.session.commit()
        return item

    def update_quantity(self, item_id: str, quantity: int) -> bool:
        """Update item quantity or remove if quantity is 0.

        Args:
            item_id: CartItem UUID
            quantity: New quantity (0 to remove)

        Returns:
            True if successful, False if item not found
        """
        from v_flask.extensions import db
        from v_flask_plugins.shop.models import CartItem

        item = CartItem.query.get(item_id)
        if not item:
            return False

        if quantity <= 0:
            db.session.delete(item)
        else:
            item.quantity = quantity

        db.session.commit()
        return True

    def remove_item(self, item_id: str) -> bool:
        """Remove item from cart.

        Args:
            item_id: CartItem UUID

        Returns:
            True if successful, False if item not found
        """
        return self.update_quantity(item_id, 0)

    def clear(self, cart: 'Cart') -> None:
        """Remove all items from cart.

        Args:
            cart: Cart instance
        """
        from v_flask.extensions import db
        from v_flask_plugins.shop.models import CartItem

        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()

    def get_items_with_prices(
        self,
        cart: 'Cart',
        customer_id: str
    ) -> list[CartItemWithPrice]:
        """Get cart items enriched with product and price data.

        Args:
            cart: Cart instance
            customer_id: CRM customer UUID for price lookup

        Returns:
            List of CartItemWithPrice objects
        """
        from v_flask_plugins.pim.services import pim_service
        from v_flask_plugins.pricing.services import pricing_service

        result = []
        for item in cart.items:
            product = pim_service.products.get_by_id(item.product_id)
            if not product:
                continue

            price_result = pricing_service.prices.get_price(
                item.product_id,
                customer_id
            )

            line_total = (price_result.final_price * item.quantity).quantize(
                Decimal('0.01')
            )

            result.append(CartItemWithPrice(
                item=item,
                product=product,
                unit_price=price_result.final_price,
                line_total=line_total,
                is_discounted=price_result.is_discounted,
                list_price=price_result.list_price,
            ))

        return result

    def get_totals(self, cart: 'Cart', customer_id: str) -> CartTotal:
        """Calculate cart totals with customer-specific prices.

        Args:
            cart: Cart instance
            customer_id: CRM customer UUID for price lookup

        Returns:
            CartTotal with subtotal, tax, and total
        """
        items_with_prices = self.get_items_with_prices(cart, customer_id)

        subtotal = Decimal('0.00')
        item_count = 0

        for item_data in items_with_prices:
            subtotal += item_data.line_total
            item_count += item_data.item.quantity

        # Default tax rate (could be made configurable)
        tax_rate = Decimal('19.00')
        tax_amount = (subtotal * tax_rate / 100).quantize(Decimal('0.01'))
        total = subtotal + tax_amount

        return CartTotal(
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total=total,
            item_count=item_count,
        )

    def get_by_customer(self, customer_id: str) -> Optional['Cart']:
        """Get cart for customer if exists.

        Args:
            customer_id: CRM customer UUID

        Returns:
            Cart instance or None
        """
        from v_flask_plugins.shop.models import Cart

        return Cart.query.filter_by(customer_id=customer_id).first()
