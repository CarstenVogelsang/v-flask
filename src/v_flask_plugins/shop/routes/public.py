"""Public routes for Shop plugin.

Customer-facing routes for catalog, cart, and checkout.
All routes require customer authentication via @customer_required.
"""

from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

shop_public_bp = Blueprint(
    'shop_public',
    __name__,
    template_folder='../templates'
)


# --- Authentication Decorator ---

def customer_required(f):
    """Decorator to require customer login for route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'shop_customer_id' not in session:
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('shop_auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated


def get_current_customer_id() -> str:
    """Get current customer ID from session."""
    return session['shop_customer_id']


# --- Home / Category Tree ---

@shop_public_bp.route('/')
@customer_required
def home():
    """Shop homepage with category overview."""
    from v_flask_plugins.shop.services import shop_service

    categories = shop_service.catalog.get_all_categories()

    return render_template(
        'shop/public/home.html',
        categories=categories
    )


# --- Category View ---

@shop_public_bp.route('/kategorie/<slug>')
@customer_required
def category(slug: str):
    """Category page with products."""
    from v_flask_plugins.shop.services import shop_service

    customer_id = get_current_customer_id()
    cat = shop_service.catalog.get_category_by_slug(slug)

    if not cat:
        flash('Kategorie nicht gefunden.', 'error')
        return redirect(url_for('shop_public.home'))

    products = shop_service.catalog.get_products_by_category(
        str(cat.id),
        customer_id
    )

    return render_template(
        'shop/public/category.html',
        category=cat,
        products=products
    )


# --- Product Detail ---

@shop_public_bp.route('/produkt/<product_id>')
@customer_required
def product(product_id: str):
    """Product detail page with customer price."""
    from v_flask_plugins.shop.services import shop_service

    customer_id = get_current_customer_id()
    product_data = shop_service.catalog.get_product_by_id(product_id, customer_id)

    if not product_data:
        flash('Produkt nicht gefunden.', 'error')
        return redirect(url_for('shop_public.home'))

    return render_template(
        'shop/public/product.html',
        product=product_data
    )


# --- Cart ---

@shop_public_bp.route('/warenkorb')
@customer_required
def cart():
    """Shopping cart page."""
    from v_flask_plugins.shop.services import shop_service

    customer_id = get_current_customer_id()
    cart_obj = shop_service.cart.get_or_create(customer_id)
    items = shop_service.cart.get_items_with_prices(cart_obj, customer_id)
    totals = shop_service.cart.get_totals(cart_obj, customer_id)

    return render_template(
        'shop/public/cart.html',
        cart=cart_obj,
        items=items,
        totals=totals
    )


@shop_public_bp.route('/warenkorb/add', methods=['POST'])
@customer_required
def cart_add():
    """Add product to cart."""
    from v_flask_plugins.shop.services import shop_service

    customer_id = get_current_customer_id()
    product_id = request.form.get('product_id', '')
    quantity = int(request.form.get('quantity', 1))

    if not product_id:
        flash('Ungültiges Produkt.', 'error')
        return redirect(request.referrer or url_for('shop_public.home'))

    cart_obj = shop_service.cart.get_or_create(customer_id)
    shop_service.cart.add_item(cart_obj, product_id, quantity)

    flash('Produkt zum Warenkorb hinzugefügt.', 'success')
    return redirect(request.referrer or url_for('shop_public.cart'))


@shop_public_bp.route('/warenkorb/update', methods=['POST'])
@customer_required
def cart_update():
    """Update cart item quantity."""
    from v_flask_plugins.shop.services import shop_service

    item_id = request.form.get('item_id', '')
    quantity = int(request.form.get('quantity', 0))

    if not item_id:
        flash('Ungültige Position.', 'error')
        return redirect(url_for('shop_public.cart'))

    success = shop_service.cart.update_quantity(item_id, quantity)

    if success:
        if quantity <= 0:
            flash('Position entfernt.', 'success')
        else:
            flash('Menge aktualisiert.', 'success')
    else:
        flash('Position nicht gefunden.', 'error')

    return redirect(url_for('shop_public.cart'))


@shop_public_bp.route('/warenkorb/remove', methods=['POST'])
@customer_required
def cart_remove():
    """Remove item from cart."""
    from v_flask_plugins.shop.services import shop_service

    item_id = request.form.get('item_id', '')

    if not item_id:
        flash('Ungültige Position.', 'error')
        return redirect(url_for('shop_public.cart'))

    success = shop_service.cart.remove_item(item_id)

    if success:
        flash('Position entfernt.', 'success')
    else:
        flash('Position nicht gefunden.', 'error')

    return redirect(url_for('shop_public.cart'))


# --- Checkout ---

@shop_public_bp.route('/checkout', methods=['GET', 'POST'])
@customer_required
def checkout():
    """Checkout page for placing orders."""
    from v_flask_plugins.crm.services import crm_service
    from v_flask_plugins.shop.services import shop_service

    customer_id = get_current_customer_id()
    cart_obj = shop_service.cart.get_or_create(customer_id)

    # Check for empty cart
    if cart_obj.is_empty:
        flash('Ihr Warenkorb ist leer.', 'warning')
        return redirect(url_for('shop_public.cart'))

    # Get customer and address data
    customer = crm_service.customers.get_by_id(customer_id)
    shipping_address = crm_service.addresses.get_default_shipping(customer_id)

    if request.method == 'POST':
        # Validate shipping address
        if not shipping_address:
            flash('Bitte hinterlegen Sie eine Lieferadresse.', 'error')
            return redirect(url_for('shop_public.checkout'))

        # Create address snapshot
        address_snapshot = {
            'company_name': getattr(shipping_address, 'company_name', None) or customer.company_name,
            'street': shipping_address.street,
            'street2': getattr(shipping_address, 'street2', None),
            'zip_code': shipping_address.zip_code,
            'city': shipping_address.city,
            'country': shipping_address.country,
        }

        notes = request.form.get('notes', '').strip()

        # Create order
        order = shop_service.orders.create_from_cart(
            cart=cart_obj,
            customer_id=customer_id,
            shipping_address=address_snapshot,
            notes=notes if notes else None,
        )

        flash(f'Bestellung {order.order_number} erfolgreich aufgegeben!', 'success')

        return render_template(
            'shop/public/checkout.html',
            order=order,
            success=True
        )

    # GET: Show checkout form
    items = shop_service.cart.get_items_with_prices(cart_obj, customer_id)
    totals = shop_service.cart.get_totals(cart_obj, customer_id)

    return render_template(
        'shop/public/checkout.html',
        cart=cart_obj,
        items=items,
        totals=totals,
        customer=customer,
        shipping_address=shipping_address,
        success=False
    )
