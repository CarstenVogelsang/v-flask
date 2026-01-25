"""Two-Factor Authentication routes for v-flask.

Provides routes for 2FA setup, verification, and management.
These routes are designed to be registered by consuming apps.

Usage in consuming app:
    from v_flask.auth.routes import register_2fa_routes

    def create_app():
        app = Flask(__name__)
        register_2fa_routes(app)
        return app

Or register the blueprint directly:
    from v_flask.auth.routes import two_fa_bp
    app.register_blueprint(two_fa_bp)
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps
from typing import TYPE_CHECKING, Callable

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from v_flask import db
from v_flask.models import User
from v_flask.services import log_event
from v_flask.services.two_fa_service import TwoFAService

if TYPE_CHECKING:
    from flask import Flask


two_fa_bp = Blueprint(
    'two_fa',
    __name__,
    url_prefix='/auth/2fa',
    template_folder='../templates/v_flask/auth',
)


def _get_issuer_name() -> str:
    """Get the issuer name for TOTP from app config."""
    return current_app.config.get('TOTP_ISSUER', 'v-flask')


def _require_password_confirmation(f: Callable) -> Callable:
    """Decorator that requires password confirmation for sensitive 2FA operations.

    Checks if session has recent password confirmation (within 5 minutes).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        confirmed_at = session.get('password_confirmed_at')
        if confirmed_at:
            # Check if confirmation is less than 5 minutes old
            try:
                confirmed_time = datetime.fromisoformat(confirmed_at)
                age = (datetime.now(timezone.utc) - confirmed_time).total_seconds()
                if age < 300:  # 5 minutes
                    return f(*args, **kwargs)
            except (ValueError, TypeError):
                pass

        # Redirect to password confirmation
        flash('Bitte bestätige dein Passwort, um fortzufahren.', 'warning')
        session['2fa_next'] = request.url
        return redirect(url_for('two_fa.confirm_password'))

    return decorated_function


@two_fa_bp.route('/confirm-password', methods=['GET', 'POST'])
@login_required
def confirm_password():
    """Confirm password before sensitive 2FA operations."""
    if request.method == 'POST':
        password = request.form.get('password', '')

        if current_user.check_password(password):
            session['password_confirmed_at'] = datetime.now(timezone.utc).isoformat()
            next_url = session.pop('2fa_next', None)
            if next_url:
                return redirect(next_url)
            return redirect(url_for('two_fa.setup'))

        flash('Falsches Passwort.', 'error')

    return render_template('2fa_confirm_password.html')


@two_fa_bp.route('/setup', methods=['GET', 'POST'])
@login_required
@_require_password_confirmation
def setup():
    """Setup 2FA for the current user.

    GET: Display QR code and setup instructions
    POST: Verify the initial code and enable 2FA
    """
    # If already enabled, redirect to status page
    if current_user.totp_enabled:
        flash('Zwei-Faktor-Authentifizierung ist bereits aktiviert.', 'info')
        return redirect(url_for('two_fa.status'))

    # Generate or retrieve temporary secret from session
    temp_secret = session.get('2fa_temp_secret')
    if not temp_secret:
        temp_secret = TwoFAService.generate_secret()
        session['2fa_temp_secret'] = temp_secret

    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        if not code:
            flash('Bitte gib den Code aus deiner Authenticator-App ein.', 'error')
        elif TwoFAService.verify_code(temp_secret, code):
            # Generate backup codes
            backup_codes = TwoFAService.generate_backup_codes()
            hashed_codes = TwoFAService.hash_backup_codes(backup_codes)

            # Enable 2FA for user
            current_user.totp_secret = temp_secret
            current_user.totp_enabled = True
            current_user.totp_backup_codes = hashed_codes
            current_user.totp_enabled_at = datetime.now(timezone.utc)
            db.session.commit()

            # Clear session
            session.pop('2fa_temp_secret', None)
            session.pop('password_confirmed_at', None)

            # Log the event
            log_event(
                modul='auth',
                aktion='2fa_enabled',
                details='2FA wurde aktiviert',
                wichtigkeit='hoch',
                entity_type='User',
                entity_id=current_user.id,
            )

            flash('Zwei-Faktor-Authentifizierung wurde aktiviert!', 'success')

            # Show backup codes (store in session for display)
            session['2fa_backup_codes_display'] = backup_codes
            return redirect(url_for('two_fa.backup_codes'))
        else:
            flash('Ungültiger Code. Bitte versuche es erneut.', 'error')

    # Generate QR code
    issuer = _get_issuer_name()
    uri = TwoFAService.get_provisioning_uri(
        secret=temp_secret,
        email=current_user.email,
        issuer=issuer,
    )
    qr_data = TwoFAService.generate_qr_code_base64(uri, size=250)

    return render_template(
        '2fa_setup.html',
        qr_data=qr_data,
        secret=temp_secret,
        issuer=issuer,
    )


@two_fa_bp.route('/backup-codes')
@login_required
def backup_codes():
    """Display backup codes after 2FA setup.

    Only accessible immediately after enabling 2FA.
    """
    codes = session.pop('2fa_backup_codes_display', None)

    if not codes:
        # If no codes in session, user must regenerate
        if current_user.totp_enabled:
            flash('Die Backup-Codes wurden bereits angezeigt. '
                  'Du kannst neue Codes generieren.', 'info')
            return redirect(url_for('two_fa.status'))
        return redirect(url_for('two_fa.setup'))

    # Format codes for display
    formatted_codes = [TwoFAService.format_backup_code(c) for c in codes]

    return render_template(
        '2fa_backup_codes.html',
        backup_codes=formatted_codes,
    )


@two_fa_bp.route('/status')
@login_required
def status():
    """Show 2FA status and management options."""
    return render_template(
        '2fa_status.html',
        is_enabled=current_user.totp_enabled,
        enabled_at=current_user.totp_enabled_at,
    )


@two_fa_bp.route('/disable', methods=['GET', 'POST'])
@login_required
@_require_password_confirmation
def disable():
    """Disable 2FA for the current user."""
    if not current_user.totp_enabled:
        flash('Zwei-Faktor-Authentifizierung ist nicht aktiviert.', 'info')
        return redirect(url_for('two_fa.status'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        # Verify with TOTP code
        if TwoFAService.verify_code(current_user.totp_secret, code):
            # Disable 2FA
            current_user.totp_secret = None
            current_user.totp_enabled = False
            current_user.totp_backup_codes = None
            current_user.totp_enabled_at = None
            db.session.commit()

            # Clear session
            session.pop('password_confirmed_at', None)

            # Log the event
            log_event(
                modul='auth',
                aktion='2fa_disabled',
                details='2FA wurde deaktiviert',
                wichtigkeit='hoch',
                entity_type='User',
                entity_id=current_user.id,
            )

            flash('Zwei-Faktor-Authentifizierung wurde deaktiviert.', 'success')
            return redirect(url_for('two_fa.status'))

        flash('Ungültiger Code. Bitte versuche es erneut.', 'error')

    return render_template('2fa_disable.html')


@two_fa_bp.route('/regenerate-codes', methods=['GET', 'POST'])
@login_required
@_require_password_confirmation
def regenerate_codes():
    """Regenerate backup codes."""
    if not current_user.totp_enabled:
        flash('Zwei-Faktor-Authentifizierung ist nicht aktiviert.', 'info')
        return redirect(url_for('two_fa.status'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        # Verify with TOTP code
        if TwoFAService.verify_code(current_user.totp_secret, code):
            # Generate new backup codes
            backup_codes = TwoFAService.generate_backup_codes()
            hashed_codes = TwoFAService.hash_backup_codes(backup_codes)

            current_user.totp_backup_codes = hashed_codes
            db.session.commit()

            # Clear session
            session.pop('password_confirmed_at', None)

            # Log the event
            log_event(
                modul='auth',
                aktion='2fa_backup_regenerated',
                details='Backup-Codes wurden neu generiert',
                wichtigkeit='mittel',
                entity_type='User',
                entity_id=current_user.id,
            )

            # Show new backup codes
            session['2fa_backup_codes_display'] = backup_codes
            return redirect(url_for('two_fa.backup_codes'))

        flash('Ungültiger Code. Bitte versuche es erneut.', 'error')

    return render_template('2fa_regenerate_codes.html')


# =============================================================================
# Login-Flow 2FA Verification Routes
# =============================================================================

@two_fa_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify 2FA code during login flow.

    This route is called after successful password verification
    when the user has 2FA enabled.
    """
    user_id = session.get('2fa_pending_user_id')

    if not user_id:
        flash('Keine ausstehende 2FA-Verifizierung.', 'error')
        return redirect(url_for('auth.login'))

    user = db.session.get(User, user_id)
    if not user or not user.totp_enabled:
        session.pop('2fa_pending_user_id', None)
        session.pop('2fa_remember_me', None)
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        use_backup = request.form.get('use_backup') == '1'

        verified = False

        if use_backup:
            # Verify backup code
            verified = user.verify_backup_code(code)
            if verified:
                db.session.commit()  # Save updated backup codes
        else:
            # Verify TOTP code
            verified = TwoFAService.verify_code(user.totp_secret, code)

        if verified:
            # Clear 2FA session data
            session.pop('2fa_pending_user_id', None)
            remember = session.pop('2fa_remember_me', False)

            # Reset failed login attempts
            user.reset_failed_logins()
            db.session.commit()

            # Actually log the user in
            login_user(user, remember=remember)

            # Log successful 2FA login
            log_event(
                modul='auth',
                aktion='2fa_login_success',
                details='2FA-Login erfolgreich' + (' (Backup-Code)' if use_backup else ''),
                wichtigkeit='niedrig',
                entity_type='User',
                entity_id=user.id,
            )

            flash('Erfolgreich angemeldet!', 'success')

            next_page = session.pop('2fa_next_page', None)
            if next_page and next_page.startswith('/'):
                return redirect(next_page)

            # Try to find the default dashboard
            if user.is_admin:
                try:
                    return redirect(url_for('admin.dashboard'))
                except Exception:
                    pass

            return redirect(url_for('public.index'))

        # Failed verification
        user.record_failed_login()
        db.session.commit()

        if user.is_locked():
            session.pop('2fa_pending_user_id', None)
            session.pop('2fa_remember_me', None)
            flash('Zu viele fehlgeschlagene Versuche. '
                  'Dein Konto ist vorübergehend gesperrt.', 'error')
            return redirect(url_for('auth.login'))

        flash('Ungültiger Code. Bitte versuche es erneut.', 'error')

    return render_template('2fa_verify.html')


@two_fa_bp.route('/cancel')
def cancel_verify():
    """Cancel 2FA verification and return to login."""
    session.pop('2fa_pending_user_id', None)
    session.pop('2fa_remember_me', None)
    session.pop('2fa_next_page', None)
    flash('Anmeldung abgebrochen.', 'info')
    return redirect(url_for('auth.login'))


# =============================================================================
# Registration Helper
# =============================================================================

def register_2fa_routes(app: Flask) -> None:
    """Register 2FA routes with the Flask application.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(two_fa_bp)

    app.logger.info('Registered 2FA routes at /auth/2fa/')


# =============================================================================
# Login Helper (to be used in consuming app's login route)
# =============================================================================

def check_2fa_required(user: User, remember: bool = False, next_page: str | None = None) -> str | None:
    """Check if 2FA verification is required and setup session.

    Call this after successful password verification in your login route.

    Args:
        user: The user attempting to login.
        remember: Whether to remember the user after 2FA.
        next_page: URL to redirect to after successful 2FA.

    Returns:
        URL to redirect to for 2FA verification, or None if 2FA not required.

    Usage in login route:
        if user.check_password(password):
            redirect_url = check_2fa_required(user, remember, next_page)
            if redirect_url:
                return redirect(redirect_url)
            # No 2FA required, log in directly
            login_user(user, remember=remember)
    """
    if not user.totp_enabled:
        return None

    # Store user ID in session for 2FA verification
    session['2fa_pending_user_id'] = user.id
    session['2fa_remember_me'] = remember
    if next_page:
        session['2fa_next_page'] = next_page

    return url_for('two_fa.verify')
