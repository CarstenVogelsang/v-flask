"""Admin routes for Pricing plugin.

Provides rule management at /admin/pricing/.
"""

from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, flash, redirect, url_for

from v_flask.auth import admin_required

from v_flask_plugins.pricing.services import pricing_service
from v_flask_plugins.pricing.models import PriceType


pricing_admin_bp = Blueprint(
    'pricing_admin',
    __name__,
    template_folder='../templates'
)


@pricing_admin_bp.route('/customer/<customer_id>/rules')
@admin_required
def list_rules(customer_id: str):
    """List all pricing rules for a customer."""
    from v_flask_plugins.crm.services import crm_service
    from v_flask_plugins.pim.services import pim_service

    # Get customer
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    # Get rules with product details
    rules = pricing_service.rules.get_rules_for_customer(customer_id)

    # Enrich rules with product info
    rules_with_products = []
    for rule in rules:
        product = pim_service.products.get_by_id(rule.product_id)
        rules_with_products.append({
            'rule': rule,
            'product': product,
        })

    return render_template(
        'pricing/admin/rules_list.html',
        customer=customer,
        rules=rules_with_products,
    )


@pricing_admin_bp.route('/customer/<customer_id>/rules/new', methods=['GET', 'POST'])
@admin_required
def new_rule(customer_id: str):
    """Create a new pricing rule."""
    from v_flask_plugins.crm.services import crm_service
    from v_flask_plugins.pim.services import pim_service

    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id', '').strip()
            name = request.form.get('name', '').strip()
            price_type = request.form.get('price_type', PriceType.FIXED.value)
            price_value_str = request.form.get('price_value', '0').strip().replace(',', '.')
            note = request.form.get('note', '').strip() or None

            # Validation
            if not product_id:
                raise ValueError("Bitte ein Produkt auswählen")
            if not name:
                raise ValueError("Bitte einen Namen eingeben")

            try:
                price_value = Decimal(price_value_str)
            except InvalidOperation:
                raise ValueError("Ungültiger Preis/Rabatt-Wert")

            if price_value < 0:
                raise ValueError("Preis/Rabatt darf nicht negativ sein")

            # Verify product exists
            product = pim_service.products.get_by_id(product_id)
            if not product:
                raise ValueError("Produkt nicht gefunden")

            rule = pricing_service.rules.create(
                customer_id=customer_id,
                product_id=product_id,
                name=name,
                price_type=price_type,
                price_value=price_value,
                note=note,
            )

            flash(f'Preisregel "{rule.name}" wurde erstellt.', 'success')
            return redirect(url_for('pricing_admin.list_rules', customer_id=customer_id))

        except ValueError as e:
            flash(str(e), 'error')

    # Get products for dropdown
    products = pim_service.products.get_all(active_only=True)

    return render_template(
        'pricing/admin/rule_form.html',
        customer=customer,
        rule=None,
        products=products,
        product=None,
        price_types=[
            (PriceType.FIXED.value, 'Festpreis (EUR)'),
            (PriceType.DISCOUNT_PERCENT.value, 'Rabatt (%)'),
        ],
    )


@pricing_admin_bp.route('/rules/<rule_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_rule(rule_id: str):
    """Edit an existing pricing rule."""
    from v_flask_plugins.crm.services import crm_service
    from v_flask_plugins.pim.services import pim_service

    rule = pricing_service.rules.get_by_id(rule_id)
    if not rule:
        flash('Preisregel nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    customer = crm_service.customers.get_by_id(rule.customer_id)
    product = pim_service.products.get_by_id(rule.product_id)

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            price_type = request.form.get('price_type', PriceType.FIXED.value)
            price_value_str = request.form.get('price_value', '0').strip().replace(',', '.')
            note = request.form.get('note', '').strip() or None
            is_active = 'is_active' in request.form

            if not name:
                raise ValueError("Bitte einen Namen eingeben")

            try:
                price_value = Decimal(price_value_str)
            except InvalidOperation:
                raise ValueError("Ungültiger Preis/Rabatt-Wert")

            if price_value < 0:
                raise ValueError("Preis/Rabatt darf nicht negativ sein")

            pricing_service.rules.update(
                rule_id=rule_id,
                name=name,
                price_type=price_type,
                price_value=price_value,
                note=note,
                is_active=is_active,
            )

            flash('Preisregel wurde aktualisiert.', 'success')
            return redirect(url_for('pricing_admin.list_rules', customer_id=rule.customer_id))

        except ValueError as e:
            flash(str(e), 'error')

    return render_template(
        'pricing/admin/rule_form.html',
        customer=customer,
        rule=rule,
        product=product,
        products=None,  # Don't allow changing product
        price_types=[
            (PriceType.FIXED.value, 'Festpreis (EUR)'),
            (PriceType.DISCOUNT_PERCENT.value, 'Rabatt (%)'),
        ],
    )


@pricing_admin_bp.route('/rules/<rule_id>/delete', methods=['POST'])
@admin_required
def delete_rule(rule_id: str):
    """Delete a pricing rule."""
    rule = pricing_service.rules.get_by_id(rule_id)
    if not rule:
        flash('Preisregel nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    customer_id = rule.customer_id
    rule_name = rule.name

    success = pricing_service.rules.delete(rule_id)

    if success:
        flash(f'Preisregel "{rule_name}" wurde gelöscht.', 'success')
    else:
        flash('Preisregel konnte nicht gelöscht werden.', 'error')

    return redirect(url_for('pricing_admin.list_rules', customer_id=customer_id))
