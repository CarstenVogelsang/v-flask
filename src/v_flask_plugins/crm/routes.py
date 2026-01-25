"""CRM Plugin Admin Routes.

Provides admin interface for customer management:
- Customer CRUD with search and filtering
- Address management
- Shop access management

POC Phase: Basic customer CRUD with one address
MVP Phase: + Contacts, groups, import/export
"""

from uuid import UUID

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import validate_csrf

from v_flask.auth import permission_required

from v_flask_plugins.crm.services import (
    crm_service,
    CustomerCreate,
    CustomerUpdate,
    AddressCreate,
    AddressUpdate,
)

# Create Blueprint
crm_admin_bp = Blueprint(
    'crm_admin',
    __name__,
    template_folder='templates',
)


# ============================================================================
# Customer Routes
# ============================================================================

@crm_admin_bp.route('/customers')
@permission_required('admin.*')
def list_customers():
    """Display customer list with search and filtering."""
    # Get search/filter parameters
    search = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Search customers
    customers, total = crm_service.customers.search(
        query=search if search else None,
        status=status if status else None,
        page=page,
        per_page=per_page,
    )

    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'crm/admin/customers/list.html',
        customers=customers,
        search=search,
        status=status,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
    )


@crm_admin_bp.route('/customers/new')
@permission_required('admin.*')
def new_customer():
    """Display form for creating a new customer."""
    return render_template('crm/admin/customers/form.html', customer=None)


@crm_admin_bp.route('/customers', methods=['POST'])
@permission_required('admin.*')
def create_customer():
    """Create a new customer."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token. Bitte erneut versuchen.', 'error')
        return redirect(url_for('crm_admin.new_customer'))

    try:
        data = CustomerCreate(
            company_name=request.form.get('company_name', ''),
            email=request.form.get('email', ''),
            legal_form=request.form.get('legal_form') or None,
            vat_id=request.form.get('vat_id') or None,
            tax_number=request.form.get('tax_number') or None,
            phone=request.form.get('phone') or None,
            website=request.form.get('website') or None,
            notes=request.form.get('notes') or None,
        )

        customer = crm_service.customers.create(data)

        # Create initial address if provided
        street = request.form.get('street', '').strip()
        if street:
            address_data = AddressCreate(
                street=street,
                zip_code=request.form.get('zip_code', '').strip(),
                city=request.form.get('city', '').strip(),
                country=request.form.get('country', 'DE'),
                is_default_billing=True,
                is_default_shipping=True,
            )
            crm_service.addresses.create(customer.id, address_data)

        flash(f'Kunde "{customer.company_name}" erfolgreich angelegt.', 'success')
        return redirect(url_for('crm_admin.edit_customer', customer_id=customer.id))

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('crm_admin.new_customer'))


@crm_admin_bp.route('/customers/<uuid:customer_id>')
@permission_required('admin.*')
def edit_customer(customer_id: UUID):
    """Display form for editing a customer."""
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    # Get addresses
    addresses = crm_service.addresses.get_by_customer(customer_id)

    return render_template(
        'crm/admin/customers/form.html',
        customer=customer,
        addresses=addresses,
    )


@crm_admin_bp.route('/customers/<uuid:customer_id>', methods=['POST'])
@permission_required('admin.*')
def update_customer(customer_id: UUID):
    """Update a customer."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token. Bitte erneut versuchen.', 'error')
        return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))

    try:
        data = CustomerUpdate(
            company_name=request.form.get('company_name'),
            email=request.form.get('email'),
            legal_form=request.form.get('legal_form') or None,
            vat_id=request.form.get('vat_id') or None,
            tax_number=request.form.get('tax_number') or None,
            phone=request.form.get('phone') or None,
            website=request.form.get('website') or None,
            notes=request.form.get('notes') or None,
            status=request.form.get('status') or None,
        )

        customer = crm_service.customers.update(customer_id, data)
        flash(f'Kunde "{customer.company_name}" erfolgreich aktualisiert.', 'success')

    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))


@crm_admin_bp.route('/customers/<uuid:customer_id>/delete', methods=['POST'])
@permission_required('admin.*')
def delete_customer(customer_id: UUID):
    """Delete a customer."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    customer = crm_service.customers.get_by_id(customer_id)
    if customer:
        company_name = customer.company_name
        if crm_service.customers.delete(customer_id):
            flash(f'Kunde "{company_name}" wurde gelöscht.', 'success')
        else:
            flash('Fehler beim Löschen des Kunden.', 'error')
    else:
        flash('Kunde nicht gefunden.', 'error')

    return redirect(url_for('crm_admin.list_customers'))


# ============================================================================
# Address Routes
# ============================================================================

@crm_admin_bp.route('/customers/<uuid:customer_id>/addresses', methods=['POST'])
@permission_required('admin.*')
def add_address(customer_id: UUID):
    """Add a new address to a customer."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token.', 'error')
        return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))

    try:
        data = AddressCreate(
            street=request.form.get('street', '').strip(),
            zip_code=request.form.get('zip_code', '').strip(),
            city=request.form.get('city', '').strip(),
            country=request.form.get('country', 'DE'),
            address_type=request.form.get('address_type', 'both'),
            company_name=request.form.get('address_company_name') or None,
            contact_name=request.form.get('contact_name') or None,
            street2=request.form.get('street2') or None,
            is_default_billing=request.form.get('is_default_billing') == 'on',
            is_default_shipping=request.form.get('is_default_shipping') == 'on',
        )

        crm_service.addresses.create(customer_id, data)
        flash('Adresse erfolgreich hinzugefügt.', 'success')

    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))


@crm_admin_bp.route('/addresses/<uuid:address_id>', methods=['POST'])
@permission_required('admin.*')
def update_address(address_id: UUID):
    """Update an address."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    address = crm_service.addresses.get_by_id(address_id)
    if not address:
        flash('Adresse nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    customer_id = address.customer_id

    try:
        data = AddressUpdate(
            street=request.form.get('street', '').strip(),
            zip_code=request.form.get('zip_code', '').strip(),
            city=request.form.get('city', '').strip(),
            country=request.form.get('country', 'DE'),
            address_type=request.form.get('address_type'),
            company_name=request.form.get('address_company_name') or None,
            contact_name=request.form.get('contact_name') or None,
            street2=request.form.get('street2') or None,
            is_default_billing=request.form.get('is_default_billing') == 'on',
            is_default_shipping=request.form.get('is_default_shipping') == 'on',
        )

        crm_service.addresses.update(address_id, data)
        flash('Adresse erfolgreich aktualisiert.', 'success')

    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))


@crm_admin_bp.route('/addresses/<uuid:address_id>/delete', methods=['POST'])
@permission_required('admin.*')
def delete_address(address_id: UUID):
    """Delete an address."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    address = crm_service.addresses.get_by_id(address_id)
    if not address:
        flash('Adresse nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    customer_id = address.customer_id

    if crm_service.addresses.delete(address_id):
        flash('Adresse wurde gelöscht.', 'success')
    else:
        flash('Fehler beim Löschen der Adresse.', 'error')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))


# ============================================================================
# Shop Access Routes
# ============================================================================

@crm_admin_bp.route('/customers/<uuid:customer_id>/enable-access', methods=['POST'])
@permission_required('admin.*')
def enable_shop_access(customer_id: UUID):
    """Enable shop access for a customer."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token.', 'error')
        return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))

    password = request.form.get('password', '')
    if not password:
        flash('Passwort ist erforderlich.', 'error')
        return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))

    try:
        crm_service.auth.enable_shop_access(customer_id, password)
        flash('Shop-Zugang wurde aktiviert.', 'success')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))


@crm_admin_bp.route('/customers/<uuid:customer_id>/disable-access', methods=['POST'])
@permission_required('admin.*')
def disable_shop_access(customer_id: UUID):
    """Disable shop access for a customer."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token.', 'error')
        return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))

    if crm_service.auth.disable_shop_access(customer_id):
        flash('Shop-Zugang wurde deaktiviert.', 'success')
    else:
        flash('Kunde hat keinen Shop-Zugang.', 'warning')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))


@crm_admin_bp.route('/customers/<uuid:customer_id>/reset-password', methods=['POST'])
@permission_required('admin.*')
def reset_customer_password(customer_id: UUID):
    """Reset customer password (admin function)."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token.', 'error')
        return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))

    password = request.form.get('new_password', '')
    if not password:
        flash('Neues Passwort ist erforderlich.', 'error')
        return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))

    try:
        crm_service.auth.set_password(customer_id, password)
        flash('Passwort wurde zurückgesetzt.', 'success')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))


@crm_admin_bp.route('/customers/<uuid:customer_id>/unlock', methods=['POST'])
@permission_required('admin.*')
def unlock_customer(customer_id: UUID):
    """Unlock a locked customer account."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Ungültiges CSRF-Token.', 'error')
        return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))

    if crm_service.auth.unlock_account(customer_id):
        flash('Account wurde entsperrt.', 'success')
    else:
        flash('Account konnte nicht entsperrt werden.', 'error')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))


# ============================================================================
# Customer Groups (MVP - Placeholder)
# ============================================================================

@crm_admin_bp.route('/groups')
@permission_required('admin.*')
def list_groups():
    """Display customer groups list (MVP feature)."""
    flash('Kundengruppen werden in der MVP-Version verfügbar sein.', 'info')
    return redirect(url_for('crm_admin.list_customers'))


# ============================================================================
# Exports
# ============================================================================

__all__ = ['crm_admin_bp']
