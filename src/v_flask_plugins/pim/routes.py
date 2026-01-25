"""Admin routes for the PIM plugin.

Provides CRUD endpoints for:
- Products
- Categories
- Tax Rates
- Manufacturers
- Brands
- Series
- Product Groups
- Price Tags
"""

from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from slugify import slugify

from v_flask.auth import permission_required

# Admin Blueprint
pim_admin_bp = Blueprint(
    'pim_admin',
    __name__,
    template_folder='templates',
)


# =============================================================================
# Products
# =============================================================================


@pim_admin_bp.route('/')
@pim_admin_bp.route('/products')
@permission_required('admin.*')
def list_products():
    """List all products with search and filtering."""
    from v_flask_plugins.pim.services import pim_service
    from v_flask_plugins.pim.models import Category

    # Get filter parameters
    search = request.args.get('search', '')
    category_id = request.args.get('category', '')
    show_inactive = request.args.get('show_inactive', '0') == '1'

    # Fetch products
    if search:
        products = pim_service.products.search(search, limit=100, active_only=not show_inactive)
    elif category_id:
        products = pim_service.products.get_by_category(category_id, active_only=not show_inactive)
    else:
        products = pim_service.products.get_all(active_only=not show_inactive, limit=100)

    # Fetch categories for filter dropdown
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()

    return render_template(
        'pim/admin/products/list.html',
        products=products,
        categories=categories,
        search=search,
        selected_category=category_id,
        show_inactive=show_inactive,
    )


@pim_admin_bp.route('/products/new', methods=['GET', 'POST'])
@permission_required('admin.*')
def new_product():
    """Create a new product."""
    from v_flask_plugins.pim.services import pim_service
    from v_flask_plugins.pim.models import Category, TaxRate, Manufacturer, ProductGroup, PriceTag

    if request.method == 'POST':
        try:
            # Parse decimal values
            price_net = Decimal(request.form.get('price_net', '0').replace(',', '.'))
            price_gross = Decimal(request.form.get('price_gross', '0').replace(',', '.'))
            cost_price = request.form.get('cost_price', '').replace(',', '.')
            cost_price = Decimal(cost_price) if cost_price else None
            stock_quantity = Decimal(request.form.get('stock_quantity', '0').replace(',', '.'))
            min_stock = Decimal(request.form.get('min_stock', '0').replace(',', '.'))

            product = pim_service.products.create(
                name=request.form['name'],
                sku=request.form['sku'],
                price_net=price_net,
                price_gross=price_gross,
                cost_price=cost_price,
                barcode=request.form.get('barcode') or None,
                description_short=request.form.get('description_short') or None,
                description_long=request.form.get('description_long') or None,
                category_id=request.form.get('category_id') or None,
                tax_rate_id=request.form.get('tax_rate_id') or None,
                manufacturer_id=request.form.get('manufacturer_id') or None,
                brand_id=request.form.get('brand_id') or None,
                series_id=request.form.get('series_id') or None,
                product_group_id=request.form.get('product_group_id') or None,
                stock_quantity=stock_quantity,
                stock_unit=request.form.get('stock_unit', 'Stück'),
                min_stock=min_stock,
                is_active=request.form.get('is_active') == 'on',
                is_featured=request.form.get('is_featured') == 'on',
            )

            flash(f'Produkt "{product.name}" wurde erfolgreich erstellt.', 'success')
            return redirect(url_for('pim_admin.list_products'))

        except InvalidOperation:
            flash('Ungültiger Zahlenwert. Bitte prüfe die Preisangaben.', 'error')
        except Exception as e:
            flash(f'Fehler beim Erstellen: {e}', 'error')

    # Load form data
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    tax_rates = TaxRate.query.filter_by(is_active=True).order_by(TaxRate.rate).all()
    manufacturers = Manufacturer.query.filter_by(is_active=True).order_by(Manufacturer.name).all()
    product_groups = ProductGroup.query.filter_by(is_active=True).order_by(ProductGroup.name).all()
    price_tags = PriceTag.query.filter_by(is_active=True).order_by(PriceTag.name).all()

    return render_template(
        'pim/admin/products/form.html',
        product=None,
        categories=categories,
        tax_rates=tax_rates,
        manufacturers=manufacturers,
        product_groups=product_groups,
        price_tags=price_tags,
    )


@pim_admin_bp.route('/products/<product_id>/edit', methods=['GET', 'POST'])
@permission_required('admin.*')
def edit_product(product_id):
    """Edit an existing product."""
    from v_flask_plugins.pim.services import pim_service
    from v_flask_plugins.pim.models import Category, TaxRate, Manufacturer, ProductGroup, PriceTag

    product = pim_service.products.get_by_id(product_id)
    if not product:
        flash('Produkt nicht gefunden.', 'error')
        return redirect(url_for('pim_admin.list_products'))

    if request.method == 'POST':
        try:
            # Parse decimal values
            price_net = Decimal(request.form.get('price_net', '0').replace(',', '.'))
            price_gross = Decimal(request.form.get('price_gross', '0').replace(',', '.'))
            cost_price = request.form.get('cost_price', '').replace(',', '.')
            cost_price = Decimal(cost_price) if cost_price else None
            stock_quantity = Decimal(request.form.get('stock_quantity', '0').replace(',', '.'))
            min_stock = Decimal(request.form.get('min_stock', '0').replace(',', '.'))

            pim_service.products.update(
                product_id,
                name=request.form['name'],
                sku=request.form['sku'],
                price_net=price_net,
                price_gross=price_gross,
                cost_price=cost_price,
                barcode=request.form.get('barcode') or None,
                description_short=request.form.get('description_short') or None,
                description_long=request.form.get('description_long') or None,
                category_id=request.form.get('category_id') or None,
                tax_rate_id=request.form.get('tax_rate_id') or None,
                manufacturer_id=request.form.get('manufacturer_id') or None,
                brand_id=request.form.get('brand_id') or None,
                series_id=request.form.get('series_id') or None,
                product_group_id=request.form.get('product_group_id') or None,
                stock_quantity=stock_quantity,
                stock_unit=request.form.get('stock_unit', 'Stück'),
                min_stock=min_stock,
                is_active=request.form.get('is_active') == 'on',
                is_featured=request.form.get('is_featured') == 'on',
            )

            flash(f'Produkt "{product.name}" wurde erfolgreich aktualisiert.', 'success')
            return redirect(url_for('pim_admin.list_products'))

        except InvalidOperation:
            flash('Ungültiger Zahlenwert. Bitte prüfe die Preisangaben.', 'error')
        except Exception as e:
            flash(f'Fehler beim Speichern: {e}', 'error')

    # Load form data
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    tax_rates = TaxRate.query.filter_by(is_active=True).order_by(TaxRate.rate).all()
    manufacturers = Manufacturer.query.filter_by(is_active=True).order_by(Manufacturer.name).all()
    product_groups = ProductGroup.query.filter_by(is_active=True).order_by(ProductGroup.name).all()
    price_tags = PriceTag.query.filter_by(is_active=True).order_by(PriceTag.name).all()

    return render_template(
        'pim/admin/products/form.html',
        product=product,
        categories=categories,
        tax_rates=tax_rates,
        manufacturers=manufacturers,
        product_groups=product_groups,
        price_tags=price_tags,
    )


@pim_admin_bp.route('/products/<product_id>/delete', methods=['POST'])
@permission_required('admin.*')
def delete_product(product_id):
    """Delete a product (soft delete)."""
    from v_flask_plugins.pim.services import pim_service

    product = pim_service.products.get_by_id(product_id)
    if product:
        pim_service.products.delete(product_id)
        flash(f'Produkt "{product.name}" wurde deaktiviert.', 'success')
    else:
        flash('Produkt nicht gefunden.', 'error')

    return redirect(url_for('pim_admin.list_products'))


# =============================================================================
# Categories
# =============================================================================


@pim_admin_bp.route('/categories')
@permission_required('admin.*')
def list_categories():
    """List all categories in tree view."""
    from v_flask_plugins.pim.services import pim_service

    show_inactive = request.args.get('show_inactive', '0') == '1'
    category_tree = pim_service.categories.get_tree(active_only=not show_inactive)

    return render_template(
        'pim/admin/categories/list.html',
        category_tree=category_tree,
        show_inactive=show_inactive,
    )


@pim_admin_bp.route('/categories/new', methods=['GET', 'POST'])
@permission_required('admin.*')
def new_category():
    """Create a new category."""
    from v_flask_plugins.pim.services import pim_service
    from v_flask_plugins.pim.models import Category

    if request.method == 'POST':
        try:
            category = pim_service.categories.create(
                name=request.form['name'],
                slug=request.form.get('slug') or None,
                parent_id=request.form.get('parent_id') or None,
                description=request.form.get('description') or None,
                is_active=request.form.get('is_active') == 'on',
            )
            flash(f'Kategorie "{category.name}" wurde erstellt.', 'success')
            return redirect(url_for('pim_admin.list_categories'))
        except Exception as e:
            flash(f'Fehler beim Erstellen: {e}', 'error')

    # Load parent categories for dropdown
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()

    return render_template(
        'pim/admin/categories/form.html',
        category=None,
        categories=categories,
    )


@pim_admin_bp.route('/categories/<category_id>/edit', methods=['GET', 'POST'])
@permission_required('admin.*')
def edit_category(category_id):
    """Edit an existing category."""
    from v_flask_plugins.pim.services import pim_service
    from v_flask_plugins.pim.models import Category

    category = pim_service.categories.get_by_id(category_id)
    if not category:
        flash('Kategorie nicht gefunden.', 'error')
        return redirect(url_for('pim_admin.list_categories'))

    if request.method == 'POST':
        try:
            pim_service.categories.update(
                category_id,
                name=request.form['name'],
                slug=request.form.get('slug') or slugify(request.form['name']),
                parent_id=request.form.get('parent_id') or None,
                description=request.form.get('description') or None,
                is_active=request.form.get('is_active') == 'on',
            )
            flash(f'Kategorie "{category.name}" wurde aktualisiert.', 'success')
            return redirect(url_for('pim_admin.list_categories'))
        except Exception as e:
            flash(f'Fehler beim Speichern: {e}', 'error')

    # Load parent categories for dropdown (exclude self and descendants)
    categories = Category.query.filter(
        Category.is_active == True,  # noqa: E712
        Category.id != category_id,
    ).order_by(Category.name).all()

    return render_template(
        'pim/admin/categories/form.html',
        category=category,
        categories=categories,
    )


@pim_admin_bp.route('/categories/<category_id>/delete', methods=['POST'])
@permission_required('admin.*')
def delete_category(category_id):
    """Delete a category (soft delete)."""
    from v_flask_plugins.pim.services import pim_service

    category = pim_service.categories.get_by_id(category_id)
    if category:
        pim_service.categories.delete(category_id)
        flash(f'Kategorie "{category.name}" wurde deaktiviert.', 'success')
    else:
        flash('Kategorie nicht gefunden.', 'error')

    return redirect(url_for('pim_admin.list_categories'))


# =============================================================================
# Tax Rates
# =============================================================================


@pim_admin_bp.route('/tax-rates')
@permission_required('admin.*')
def list_tax_rates():
    """List all tax rates."""
    from v_flask_plugins.pim.services import pim_service

    show_inactive = request.args.get('show_inactive', '0') == '1'
    tax_rates = pim_service.tax_rates.get_all(active_only=not show_inactive)

    return render_template(
        'pim/admin/tax_rates/list.html',
        tax_rates=tax_rates,
        show_inactive=show_inactive,
    )


@pim_admin_bp.route('/tax-rates/new', methods=['GET', 'POST'])
@permission_required('admin.*')
def new_tax_rate():
    """Create a new tax rate."""
    from v_flask_plugins.pim.services import pim_service

    if request.method == 'POST':
        try:
            rate = Decimal(request.form.get('rate', '0').replace(',', '.'))
            tax_rate = pim_service.tax_rates.create(
                name=request.form['name'],
                rate=rate,
                is_default=request.form.get('is_default') == 'on',
            )
            flash(f'Steuersatz "{tax_rate.name}" wurde erstellt.', 'success')
            return redirect(url_for('pim_admin.list_tax_rates'))
        except Exception as e:
            flash(f'Fehler beim Erstellen: {e}', 'error')

    return render_template(
        'pim/admin/tax_rates/form.html',
        tax_rate=None,
    )


@pim_admin_bp.route('/tax-rates/<tax_rate_id>/edit', methods=['GET', 'POST'])
@permission_required('admin.*')
def edit_tax_rate(tax_rate_id):
    """Edit an existing tax rate."""
    from v_flask_plugins.pim.services import pim_service

    tax_rate = pim_service.tax_rates.get_by_id(tax_rate_id)
    if not tax_rate:
        flash('Steuersatz nicht gefunden.', 'error')
        return redirect(url_for('pim_admin.list_tax_rates'))

    if request.method == 'POST':
        try:
            rate = Decimal(request.form.get('rate', '0').replace(',', '.'))
            pim_service.tax_rates.update(
                tax_rate_id,
                name=request.form['name'],
                rate=rate,
                is_default=request.form.get('is_default') == 'on',
                is_active=request.form.get('is_active') == 'on',
            )
            flash(f'Steuersatz "{tax_rate.name}" wurde aktualisiert.', 'success')
            return redirect(url_for('pim_admin.list_tax_rates'))
        except Exception as e:
            flash(f'Fehler beim Speichern: {e}', 'error')

    return render_template(
        'pim/admin/tax_rates/form.html',
        tax_rate=tax_rate,
    )


@pim_admin_bp.route('/tax-rates/<tax_rate_id>/delete', methods=['POST'])
@permission_required('admin.*')
def delete_tax_rate(tax_rate_id):
    """Delete a tax rate (soft delete)."""
    from v_flask_plugins.pim.services import pim_service

    tax_rate = pim_service.tax_rates.get_by_id(tax_rate_id)
    if tax_rate:
        pim_service.tax_rates.delete(tax_rate_id)
        flash(f'Steuersatz "{tax_rate.name}" wurde deaktiviert.', 'success')
    else:
        flash('Steuersatz nicht gefunden.', 'error')

    return redirect(url_for('pim_admin.list_tax_rates'))


# =============================================================================
# Manufacturers
# =============================================================================


@pim_admin_bp.route('/manufacturers')
@permission_required('admin.*')
def list_manufacturers():
    """List all manufacturers with their brands."""
    from v_flask_plugins.pim.services import pim_service

    show_inactive = request.args.get('show_inactive', '0') == '1'
    manufacturers = pim_service.manufacturers.get_all_manufacturers(active_only=not show_inactive)

    return render_template(
        'pim/admin/manufacturers/list.html',
        manufacturers=manufacturers,
        show_inactive=show_inactive,
    )


@pim_admin_bp.route('/manufacturers/new', methods=['GET', 'POST'])
@permission_required('admin.*')
def new_manufacturer():
    """Create a new manufacturer."""
    from v_flask_plugins.pim.services import pim_service

    if request.method == 'POST':
        try:
            manufacturer = pim_service.manufacturers.create_manufacturer(
                name=request.form['name'],
                slug=request.form.get('slug') or None,
                description=request.form.get('description') or None,
                website=request.form.get('website') or None,
                is_active=request.form.get('is_active') == 'on',
            )
            flash(f'Hersteller "{manufacturer.name}" wurde erstellt.', 'success')
            return redirect(url_for('pim_admin.list_manufacturers'))
        except Exception as e:
            flash(f'Fehler beim Erstellen: {e}', 'error')

    return render_template(
        'pim/admin/manufacturers/form.html',
        manufacturer=None,
    )


@pim_admin_bp.route('/manufacturers/<manufacturer_id>/edit', methods=['GET', 'POST'])
@permission_required('admin.*')
def edit_manufacturer(manufacturer_id):
    """Edit an existing manufacturer."""
    from v_flask_plugins.pim.services import pim_service

    manufacturer = pim_service.manufacturers.get_manufacturer_by_id(manufacturer_id)
    if not manufacturer:
        flash('Hersteller nicht gefunden.', 'error')
        return redirect(url_for('pim_admin.list_manufacturers'))

    if request.method == 'POST':
        try:
            pim_service.manufacturers.update_manufacturer(
                manufacturer_id,
                name=request.form['name'],
                slug=request.form.get('slug') or slugify(request.form['name']),
                description=request.form.get('description') or None,
                website=request.form.get('website') or None,
                is_active=request.form.get('is_active') == 'on',
            )
            flash(f'Hersteller "{manufacturer.name}" wurde aktualisiert.', 'success')
            return redirect(url_for('pim_admin.list_manufacturers'))
        except Exception as e:
            flash(f'Fehler beim Speichern: {e}', 'error')

    return render_template(
        'pim/admin/manufacturers/form.html',
        manufacturer=manufacturer,
    )


@pim_admin_bp.route('/manufacturers/<manufacturer_id>/delete', methods=['POST'])
@permission_required('admin.*')
def delete_manufacturer(manufacturer_id):
    """Delete a manufacturer (soft delete)."""
    from v_flask_plugins.pim.services import pim_service

    manufacturer = pim_service.manufacturers.get_manufacturer_by_id(manufacturer_id)
    if manufacturer:
        pim_service.manufacturers.delete_manufacturer(manufacturer_id)
        flash(f'Hersteller "{manufacturer.name}" wurde deaktiviert.', 'success')
    else:
        flash('Hersteller nicht gefunden.', 'error')

    return redirect(url_for('pim_admin.list_manufacturers'))


# =============================================================================
# API Endpoints (for HTMX cascading dropdowns)
# =============================================================================


@pim_admin_bp.route('/api/brands/<manufacturer_id>')
@permission_required('admin.*')
def api_get_brands(manufacturer_id):
    """Get brands for a manufacturer (for cascading dropdown)."""
    from v_flask_plugins.pim.services import pim_service

    brands = pim_service.manufacturers.get_brands_by_manufacturer(manufacturer_id)
    return jsonify([
        {'id': b.id, 'name': b.name}
        for b in brands
    ])


@pim_admin_bp.route('/api/series/<brand_id>')
@permission_required('admin.*')
def api_get_series(brand_id):
    """Get series for a brand (for cascading dropdown)."""
    from v_flask_plugins.pim.services import pim_service

    series = pim_service.manufacturers.get_series_by_brand(brand_id)
    return jsonify([
        {'id': s.id, 'name': s.name}
        for s in series
    ])


@pim_admin_bp.route('/api/validate-barcode')
@permission_required('admin.*')
def api_validate_barcode():
    """Validate a barcode and return type/status."""
    from v_flask_plugins.pim.services import pim_service

    barcode = request.args.get('barcode', '')
    result = pim_service.validate_barcode(barcode)

    return jsonify({
        'original': result.original,
        'normalized': result.normalized,
        'type': result.type,
        'is_valid': result.is_valid,
        'error': result.error,
    })
