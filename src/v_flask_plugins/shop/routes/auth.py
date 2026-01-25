"""Authentication routes for Shop plugin.

Provides customer login/logout using CRM CustomerAuth.
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

shop_auth_bp = Blueprint(
    'shop_auth',
    __name__,
    template_folder='../templates'
)


@shop_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Customer login page."""
    # Redirect if already logged in
    if 'shop_customer_id' in session:
        return redirect(url_for('shop_public.home'))

    if request.method == 'POST':
        from v_flask_plugins.crm.services import crm_service

        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Bitte E-Mail und Passwort eingeben.', 'error')
            return render_template('shop/public/login.html')

        # Authenticate via CRM
        result = crm_service.auth.authenticate(email, password)

        if result.success:
            # Store customer data in session
            session['shop_customer_id'] = str(result.customer.id)
            session['shop_customer_email'] = result.customer.email
            session['shop_customer_name'] = result.customer.company_name

            flash('Erfolgreich angemeldet.', 'success')

            # Redirect to next URL or home
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/shop'):
                return redirect(next_url)
            return redirect(url_for('shop_public.home'))
        else:
            # Handle specific error types
            if result.error == 'account_locked':
                flash('Konto temporär gesperrt. Bitte später erneut versuchen.', 'error')
            elif result.error == 'access_disabled':
                flash('Shop-Zugang deaktiviert. Bitte kontaktieren Sie uns.', 'error')
            else:
                flash('Ungültige Zugangsdaten.', 'error')

    return render_template('shop/public/login.html')


@shop_auth_bp.route('/logout')
def logout():
    """Customer logout."""
    session.pop('shop_customer_id', None)
    session.pop('shop_customer_email', None)
    session.pop('shop_customer_name', None)

    flash('Erfolgreich abgemeldet.', 'success')
    return redirect(url_for('shop_auth.login'))
