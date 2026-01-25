"""Admin routes for Shop plugin.

Provides order management for administrators.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from v_flask.auth import admin_required

shop_admin_bp = Blueprint(
    'shop_admin',
    __name__,
    template_folder='../templates'
)


@shop_admin_bp.route('/')
@admin_required
def dashboard():
    """Shop admin dashboard - redirects to orders list."""
    return redirect(url_for('shop_admin.orders_list'))


@shop_admin_bp.route('/bestellungen')
@admin_required
def orders_list():
    """Order list with optional status filter."""
    from v_flask_plugins.shop.models import OrderStatus
    from v_flask_plugins.shop.services import shop_service

    status_filter = request.args.get('status')
    orders = shop_service.orders.get_all(status=status_filter)

    return render_template(
        'shop/admin/orders_list.html',
        orders=orders,
        status_filter=status_filter,
        status_choices=OrderStatus.choices(),
    )


@shop_admin_bp.route('/bestellung/<order_id>')
@admin_required
def order_detail(order_id: str):
    """Order detail view."""
    from v_flask_plugins.crm.services import crm_service
    from v_flask_plugins.shop.models import OrderStatus
    from v_flask_plugins.shop.services import shop_service

    order = shop_service.orders.get_by_id(order_id)
    if not order:
        flash('Bestellung nicht gefunden.', 'error')
        return redirect(url_for('shop_admin.orders_list'))

    # Get customer info
    customer = None
    if order.customer_id:
        customer = crm_service.customers.get_by_id(order.customer_id)

    return render_template(
        'shop/admin/order_detail.html',
        order=order,
        customer=customer,
        status_choices=OrderStatus.choices(),
    )


@shop_admin_bp.route('/bestellung/<order_id>/status', methods=['POST'])
@admin_required
def order_change_status(order_id: str):
    """Change order status."""
    from v_flask_plugins.shop.services import shop_service

    order = shop_service.orders.get_by_id(order_id)
    if not order:
        flash('Bestellung nicht gefunden.', 'error')
        return redirect(url_for('shop_admin.orders_list'))

    new_status = request.form.get('status', '')
    comment = request.form.get('comment', '').strip()

    if not new_status:
        flash('Bitte einen Status auswählen.', 'error')
        return redirect(url_for('shop_admin.order_detail', order_id=order_id))

    # Get admin email for audit trail
    changed_by = current_user.email if hasattr(current_user, 'email') else 'admin'

    shop_service.orders.change_status(
        order=order,
        new_status=new_status,
        changed_by=changed_by,
        comment=comment if comment else None,
    )

    flash(f'Status auf "{order.status_label}" geändert.', 'success')
    return redirect(url_for('shop_admin.order_detail', order_id=order_id))
