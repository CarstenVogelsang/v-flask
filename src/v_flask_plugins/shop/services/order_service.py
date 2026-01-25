"""Order service for Shop plugin."""

from datetime import datetime
from decimal import Decimal
from typing import Optional


class OrderService:
    """Service for order operations."""

    def create_from_cart(
        self,
        cart: 'Cart',
        customer_id: str,
        shipping_address: dict,
        billing_address: Optional[dict] = None,
        notes: Optional[str] = None,
    ) -> 'Order':
        """Create order from shopping cart.

        Creates order with all items, calculates totals using customer prices,
        creates initial status history entry, and clears the cart.

        Args:
            cart: Cart instance with items
            customer_id: CRM customer UUID
            shipping_address: Address dict for shipping
            billing_address: Optional address dict for billing
            notes: Optional customer notes

        Returns:
            Created Order instance
        """
        from v_flask.extensions import db
        from v_flask_plugins.pim.services import pim_service
        from v_flask_plugins.pricing.services import pricing_service
        from v_flask_plugins.shop.models import (
            Order,
            OrderItem,
            OrderStatus,
            OrderStatusHistory,
        )
        from v_flask_plugins.shop.services import shop_service

        # Calculate totals
        totals = shop_service.cart.get_totals(cart, customer_id)

        # Create order
        order = Order(
            order_number=self.generate_order_number(),
            customer_id=customer_id,
            status=OrderStatus.NEW.value,
            shipping_address=shipping_address,
            billing_address=billing_address,
            subtotal=totals.subtotal,
            tax_rate=totals.tax_rate,
            tax_amount=totals.tax_amount,
            total=totals.total,
            notes=notes,
        )
        db.session.add(order)
        db.session.flush()  # Get order ID

        # Create order items with product snapshots
        for cart_item in cart.items:
            product = pim_service.products.get_by_id(cart_item.product_id)
            if not product:
                continue

            price_result = pricing_service.prices.get_price(
                cart_item.product_id,
                customer_id
            )

            line_total = (
                price_result.final_price * cart_item.quantity
            ).quantize(Decimal('0.01'))

            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                sku=product.sku,
                name=product.name,
                quantity=cart_item.quantity,
                unit_price=price_result.final_price,
                total=line_total,
            )
            db.session.add(order_item)

        # Create initial status history
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=None,
            new_status=OrderStatus.NEW.value,
            changed_by='system',
            comment='Bestellung aufgegeben',
        )
        db.session.add(history)

        # Clear cart
        shop_service.cart.clear(cart)

        db.session.commit()
        return order

    def generate_order_number(self) -> str:
        """Generate unique order number (ORD-YYYY-NNNNN).

        Returns:
            Unique order number string
        """
        from v_flask_plugins.shop.models import Order

        year = datetime.utcnow().year
        prefix = f'ORD-{year}-'

        # Find latest order number for this year
        latest = Order.query.filter(
            Order.order_number.like(f'{prefix}%')
        ).order_by(Order.order_number.desc()).first()

        if latest:
            try:
                num_part = latest.order_number.replace(prefix, '')
                next_num = int(num_part) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f'{prefix}{next_num:05d}'

    def get_by_id(self, order_id: str) -> Optional['Order']:
        """Get order by ID.

        Args:
            order_id: Order UUID

        Returns:
            Order instance or None
        """
        from v_flask_plugins.shop.models import Order

        return Order.query.get(order_id)

    def get_by_number(self, order_number: str) -> Optional['Order']:
        """Get order by order number.

        Args:
            order_number: Order number (e.g., ORD-2026-00001)

        Returns:
            Order instance or None
        """
        from v_flask_plugins.shop.models import Order

        return Order.query.filter_by(order_number=order_number).first()

    def get_by_customer(
        self,
        customer_id: str,
        limit: int = 20
    ) -> list['Order']:
        """Get orders for a customer.

        Args:
            customer_id: CRM customer UUID
            limit: Maximum number of orders to return

        Returns:
            List of Order instances, newest first
        """
        from v_flask_plugins.shop.models import Order

        return Order.query.filter_by(
            customer_id=customer_id
        ).order_by(
            Order.created_at.desc()
        ).limit(limit).all()

    def get_all(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list['Order']:
        """Get all orders with optional status filter.

        Args:
            status: Optional status filter
            limit: Maximum number of orders
            offset: Pagination offset

        Returns:
            List of Order instances, newest first
        """
        from v_flask_plugins.shop.models import Order

        query = Order.query
        if status:
            query = query.filter_by(status=status)

        return query.order_by(
            Order.created_at.desc()
        ).offset(offset).limit(limit).all()

    def get_count(self, status: Optional[str] = None) -> int:
        """Get total order count with optional status filter.

        Args:
            status: Optional status filter

        Returns:
            Number of orders
        """
        from v_flask_plugins.shop.models import Order

        query = Order.query
        if status:
            query = query.filter_by(status=status)

        return query.count()

    def change_status(
        self,
        order: 'Order',
        new_status: str,
        changed_by: str,
        comment: Optional[str] = None,
    ) -> 'Order':
        """Change order status with history entry.

        Args:
            order: Order instance
            new_status: New status value
            changed_by: Email or identifier of person making change
            comment: Optional comment for history

        Returns:
            Updated Order instance
        """
        from v_flask.extensions import db
        from v_flask_plugins.shop.models import OrderStatusHistory

        old_status = order.status
        order.status = new_status

        history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            comment=comment,
        )
        db.session.add(history)
        db.session.commit()

        return order
