"""Admin routes for CRM plugin.

Provides customer management interface at /admin/crm/.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
)

from v_flask.extensions import db
from v_flask.auth import admin_required

from v_flask_plugins.crm.models import CustomerStatus, AddressType
from v_flask_plugins.crm.services import (
    crm_service,
    CustomerCreate,
    CustomerUpdate,
    AddressCreate,
)
from v_flask_plugins.crm.validators import VatIdValidator

# Admin Blueprint
crm_admin_bp = Blueprint(
    'crm_admin',
    __name__,
    template_folder='../templates'
)

vat_validator = VatIdValidator()


# =============================================================================
# Customer Routes
# =============================================================================

@crm_admin_bp.route('/customers')
@admin_required
def list_customers():
    """List all customers with search and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    query = request.args.get('q', '').strip()
    status = request.args.get('status', '')

    customers, total = crm_service.customers.search(
        query=query if query else None,
        status=status if status else None,
        page=page,
        per_page=per_page,
    )

    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'crm/admin/customers/list.html',
        customers=customers,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        query=query,
        status=status,
        statuses=CustomerStatus.choices(),
    )


@crm_admin_bp.route('/customers/new', methods=['GET', 'POST'])
@admin_required
def new_customer():
    """Create a new customer."""
    if request.method == 'POST':
        try:
            data = CustomerCreate(
                company_name=request.form.get('company_name', '').strip(),
                email=request.form.get('email', '').strip(),
                legal_form=request.form.get('legal_form', '').strip() or None,
                vat_id=request.form.get('vat_id', '').strip() or None,
                tax_number=request.form.get('tax_number', '').strip() or None,
                phone=request.form.get('phone', '').strip() or None,
                website=request.form.get('website', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None,
            )

            customer = crm_service.customers.create(data)

            # Create address if provided
            if request.form.get('street'):
                address_data = AddressCreate(
                    street=request.form.get('street', '').strip(),
                    zip_code=request.form.get('zip_code', '').strip(),
                    city=request.form.get('city', '').strip(),
                    country=request.form.get('country', 'DE').strip(),
                    address_type='both',
                    is_default_billing=True,
                    is_default_shipping=True,
                )
                crm_service.addresses.create(customer.id, address_data)

            flash(f'Kunde {customer.customer_number} wurde angelegt.', 'success')
            return redirect(url_for('crm_admin.show_customer', customer_id=customer.id))

        except ValueError as e:
            flash(str(e), 'error')

    return render_template(
        'crm/admin/customers/form.html',
        customer=None,
        address=None,
        statuses=CustomerStatus.choices(),
        address_types=AddressType.choices(),
    )


@crm_admin_bp.route('/customers/<customer_id>')
@admin_required
def show_customer(customer_id: str):
    """Show customer details."""
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    addresses = customer.addresses.all()
    contacts = customer.contacts.filter_by(is_active=True).all()

    return render_template(
        'crm/admin/customers/detail.html',
        customer=customer,
        addresses=addresses,
        contacts=contacts,
        statuses=CustomerStatus.choices(),
    )


@crm_admin_bp.route('/customers/<customer_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_customer(customer_id: str):
    """Edit customer data."""
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    # Get first address (POC: single address per customer)
    address = customer.addresses.first()

    if request.method == 'POST':
        try:
            data = CustomerUpdate(
                company_name=request.form.get('company_name', '').strip() or None,
                email=request.form.get('email', '').strip() or None,
                legal_form=request.form.get('legal_form', '').strip() or None,
                vat_id=request.form.get('vat_id', '').strip() or None,
                tax_number=request.form.get('tax_number', '').strip() or None,
                phone=request.form.get('phone', '').strip() or None,
                website=request.form.get('website', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None,
                status=request.form.get('status') or None,
            )

            crm_service.customers.update(customer_id, data)

            # Update or create address
            if request.form.get('street'):
                if address:
                    # Update existing
                    address.street = request.form.get('street', '').strip()
                    address.zip_code = request.form.get('zip_code', '').strip()
                    address.city = request.form.get('city', '').strip()
                    address.country = request.form.get('country', 'DE').strip()
                    db.session.commit()
                else:
                    # Create new
                    address_data = AddressCreate(
                        street=request.form.get('street', '').strip(),
                        zip_code=request.form.get('zip_code', '').strip(),
                        city=request.form.get('city', '').strip(),
                        country=request.form.get('country', 'DE').strip(),
                        address_type='both',
                        is_default_billing=True,
                        is_default_shipping=True,
                    )
                    crm_service.addresses.create(customer.id, address_data)

            flash('Kundendaten wurden aktualisiert.', 'success')
            return redirect(url_for('crm_admin.show_customer', customer_id=customer_id))

        except ValueError as e:
            flash(str(e), 'error')

    # Get all addresses for the sidebar
    addresses = customer.addresses.all()

    return render_template(
        'crm/admin/customers/form.html',
        customer=customer,
        address=address,
        addresses=addresses,
        statuses=CustomerStatus.choices(),
        address_types=AddressType.choices(),
    )


@crm_admin_bp.route('/customers/<customer_id>/delete', methods=['POST'])
@admin_required
def delete_customer(customer_id: str):
    """Delete a customer."""
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    customer_number = customer.customer_number
    success = crm_service.customers.delete(customer_id)

    if success:
        flash(f'Kunde {customer_number} wurde gelöscht.', 'success')
    else:
        flash('Kunde konnte nicht gelöscht werden.', 'error')

    return redirect(url_for('crm_admin.list_customers'))


# =============================================================================
# Shop Access Routes
# =============================================================================

@crm_admin_bp.route('/customers/<customer_id>/enable-access', methods=['GET', 'POST'])
@admin_required
def enable_shop_access(customer_id: str):
    """Enable shop access for a customer."""
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()

        if not password:
            flash('Bitte ein Passwort eingeben.', 'error')
        elif password != password_confirm:
            flash('Passwörter stimmen nicht überein.', 'error')
        else:
            try:
                crm_service.auth.enable_shop_access(customer_id, password)
                flash('Shop-Zugang wurde aktiviert.', 'success')
                return redirect(url_for('crm_admin.show_customer', customer_id=customer_id))
            except ValueError as e:
                flash(str(e), 'error')

    return render_template(
        'crm/admin/customers/enable_access.html',
        customer=customer,
    )


@crm_admin_bp.route('/customers/<customer_id>/disable-access', methods=['POST'])
@admin_required
def disable_shop_access(customer_id: str):
    """Disable shop access for a customer."""
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    success = crm_service.auth.disable_shop_access(customer_id)

    if success:
        flash('Shop-Zugang wurde deaktiviert.', 'success')
    else:
        flash('Shop-Zugang konnte nicht deaktiviert werden.', 'error')

    return redirect(url_for('crm_admin.show_customer', customer_id=customer_id))


@crm_admin_bp.route('/customers/<customer_id>/reset-password', methods=['GET', 'POST'])
@admin_required
def reset_password(customer_id: str):
    """Reset customer shop password."""
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    if not customer.auth:
        flash('Kunde hat keinen Shop-Zugang.', 'error')
        return redirect(url_for('crm_admin.show_customer', customer_id=customer_id))

    if request.method == 'POST':
        # Form uses 'new_password' field name
        password = request.form.get('new_password', '').strip()

        if not password:
            flash('Bitte ein neues Passwort eingeben.', 'error')
        else:
            try:
                crm_service.auth.set_password(customer_id, password)
                flash('Passwort wurde zurückgesetzt.', 'success')
                return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))
            except ValueError as e:
                flash(str(e), 'error')

    return render_template(
        'crm/admin/customers/reset_password.html',
        customer=customer,
    )


@crm_admin_bp.route('/customers/<customer_id>/unlock', methods=['POST'])
@admin_required
def unlock_account(customer_id: str):
    """Unlock a locked customer account."""
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    success = crm_service.auth.unlock_account(customer_id)

    if success:
        flash('Account wurde entsperrt.', 'success')
    else:
        flash('Account konnte nicht entsperrt werden.', 'error')

    return redirect(url_for('crm_admin.show_customer', customer_id=customer_id))


# =============================================================================
# Address Routes
# =============================================================================

@crm_admin_bp.route('/customers/<customer_id>/addresses', methods=['POST'])
@admin_required
def add_address(customer_id: str):
    """Add a new address for a customer."""
    customer = crm_service.customers.get_by_id(customer_id)
    if not customer:
        flash('Kunde nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    try:
        address_data = AddressCreate(
            street=request.form.get('street', '').strip(),
            street2=request.form.get('street2', '').strip() or None,
            zip_code=request.form.get('zip_code', '').strip(),
            city=request.form.get('city', '').strip(),
            country=request.form.get('country', 'DE').strip(),
            address_type='both',
            is_default_billing='is_default_billing' in request.form,
            is_default_shipping='is_default_shipping' in request.form,
        )
        crm_service.addresses.create(customer_id, address_data)
        flash('Adresse wurde hinzugefügt.', 'success')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))


@crm_admin_bp.route('/addresses/<address_id>/delete', methods=['POST'])
@admin_required
def delete_address(address_id: str):
    """Delete an address."""
    address = crm_service.addresses.get_by_id(address_id)
    if not address:
        flash('Adresse nicht gefunden.', 'error')
        return redirect(url_for('crm_admin.list_customers'))

    customer_id = str(address.customer_id)  # UUID to string for url_for
    success = crm_service.addresses.delete(address_id)

    if success:
        flash('Adresse wurde gelöscht.', 'success')
    else:
        flash('Adresse konnte nicht gelöscht werden.', 'error')

    return redirect(url_for('crm_admin.edit_customer', customer_id=customer_id))
