"""Admin routes for user management.

Core v-flask admin functionality for:
- User CRUD (list, create, edit, delete)
- Password management
- Role assignment
- 2FA reset

Routes are available under /admin/users/ and require user.* permissions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from v_flask.auth import admin_required, permission_required
from v_flask.extensions import db
from v_flask.models import User, Rolle
from v_flask.services import log_event

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

# Blueprint for user admin routes
users_admin_bp = Blueprint(
    'users_admin',
    __name__,
    url_prefix='/admin/users',
    template_folder='../templates',
)


# =============================================================================
# User List
# =============================================================================

@users_admin_bp.route('/')
@permission_required('user.read')
def list_users():
    """Display list of all users with filtering."""
    # Get filter parameters
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', 'all')
    search = request.args.get('q', '').strip()

    # Base query
    query = User.query

    # Apply filters
    if role_filter:
        query = query.filter(User.rolle_id == int(role_filter))

    if status_filter == 'active':
        query = query.filter(User.aktiv == True)
    elif status_filter == 'inactive':
        query = query.filter(User.aktiv == False)

    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                User.email.ilike(search_pattern),
                User.vorname.ilike(search_pattern),
                User.nachname.ilike(search_pattern),
            )
        )

    # Order by name
    users = query.order_by(User.nachname, User.vorname).all()

    # Get all roles for filter dropdown
    roles = Rolle.query.order_by(Rolle.name).all()

    # HTMX partial response
    if request.headers.get('HX-Request'):
        return render_template(
            'v_flask/admin/users/_user_list.html',
            users=users,
            current_filters={
                'role': role_filter,
                'status': status_filter,
                'q': search,
            },
        )

    return render_template(
        'v_flask/admin/users/list.html',
        users=users,
        roles=roles,
        current_filters={
            'role': role_filter,
            'status': status_filter,
            'q': search,
        },
    )


# =============================================================================
# User Create
# =============================================================================

@users_admin_bp.route('/new', methods=['GET', 'POST'])
@permission_required('user.create')
def create_user():
    """Create a new user."""
    roles = Rolle.query.order_by(Rolle.name).all()

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        vorname = request.form.get('vorname', '').strip()
        nachname = request.form.get('nachname', '').strip()
        rolle_id = request.form.get('rolle_id', type=int)
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        aktiv = request.form.get('aktiv') == 'on'

        # Validation
        errors = []

        if not email:
            errors.append('E-Mail ist erforderlich.')
        elif User.query.filter_by(email=email).first():
            errors.append('Diese E-Mail-Adresse ist bereits vergeben.')

        if not vorname:
            errors.append('Vorname ist erforderlich.')

        if not nachname:
            errors.append('Nachname ist erforderlich.')

        if not rolle_id:
            errors.append('Rolle ist erforderlich.')

        if not password:
            errors.append('Passwort ist erforderlich.')
        elif len(password) < 8:
            errors.append('Passwort muss mindestens 8 Zeichen lang sein.')
        elif password != password_confirm:
            errors.append('Passwörter stimmen nicht überein.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'v_flask/admin/users/form.html',
                user=None,
                roles=roles,
                form_data=request.form,
            )

        # Create user
        user = User(
            email=email,
            vorname=vorname,
            nachname=nachname,
            rolle_id=rolle_id,
            aktiv=aktiv,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Log event
        log_event(
            modul='user_admin',
            aktion='user_created',
            details=f'Benutzer {user.email} erstellt',
            wichtigkeit='mittel',
            entity_type='User',
            entity_id=user.id,
        )

        flash(f'Benutzer "{user.full_name}" wurde erstellt.', 'success')
        return redirect(url_for('users_admin.list_users'))

    return render_template(
        'v_flask/admin/users/form.html',
        user=None,
        roles=roles,
        form_data={},
    )


# =============================================================================
# User Edit
# =============================================================================

@users_admin_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@permission_required('user.update')
def edit_user(user_id: int):
    """Edit an existing user."""
    user = User.query.get_or_404(user_id)
    roles = Rolle.query.order_by(Rolle.name).all()

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        vorname = request.form.get('vorname', '').strip()
        nachname = request.form.get('nachname', '').strip()
        rolle_id = request.form.get('rolle_id', type=int)
        aktiv = request.form.get('aktiv') == 'on'

        # Validation
        errors = []

        if not email:
            errors.append('E-Mail ist erforderlich.')
        else:
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user.id:
                errors.append('Diese E-Mail-Adresse ist bereits vergeben.')

        if not vorname:
            errors.append('Vorname ist erforderlich.')

        if not nachname:
            errors.append('Nachname ist erforderlich.')

        if not rolle_id:
            errors.append('Rolle ist erforderlich.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'v_flask/admin/users/form.html',
                user=user,
                roles=roles,
                form_data=request.form,
            )

        # Update user
        user.email = email
        user.vorname = vorname
        user.nachname = nachname
        user.rolle_id = rolle_id
        user.aktiv = aktiv

        db.session.commit()

        # Log event
        log_event(
            modul='user_admin',
            aktion='user_updated',
            details=f'Benutzer {user.email} bearbeitet',
            wichtigkeit='niedrig',
            entity_type='User',
            entity_id=user.id,
        )

        flash(f'Benutzer "{user.full_name}" wurde aktualisiert.', 'success')
        return redirect(url_for('users_admin.list_users'))

    return render_template(
        'v_flask/admin/users/form.html',
        user=user,
        roles=roles,
        form_data={},
    )


# =============================================================================
# User Detail
# =============================================================================

@users_admin_bp.route('/<int:user_id>')
@permission_required('user.read')
def user_detail(user_id: int):
    """Display user details including activity log."""
    user = User.query.get_or_404(user_id)

    # Get recent audit logs for this user
    from v_flask.models import AuditLog
    recent_logs = AuditLog.query.filter_by(
        entity_type='User',
        entity_id=user_id
    ).order_by(AuditLog.created_at.desc()).limit(20).all()

    return render_template(
        'v_flask/admin/users/detail.html',
        user=user,
        recent_logs=recent_logs,
    )


# =============================================================================
# User Delete
# =============================================================================

@users_admin_bp.route('/<int:user_id>/delete', methods=['POST'])
@permission_required('user.delete')
def delete_user(user_id: int):
    """Delete a user (with confirmation)."""
    user = User.query.get_or_404(user_id)

    # Prevent self-deletion
    if user.id == current_user.id:
        flash('Du kannst deinen eigenen Account nicht löschen.', 'error')
        return redirect(url_for('users_admin.list_users'))

    email = user.email
    full_name = user.full_name

    db.session.delete(user)
    db.session.commit()

    # Log event
    log_event(
        modul='user_admin',
        aktion='user_deleted',
        details=f'Benutzer {email} ({full_name}) gelöscht',
        wichtigkeit='kritisch',
        entity_type='User',
        entity_id=user_id,
    )

    flash(f'Benutzer "{full_name}" wurde gelöscht.', 'success')
    return redirect(url_for('users_admin.list_users'))


# =============================================================================
# Password Management
# =============================================================================

@users_admin_bp.route('/<int:user_id>/password', methods=['POST'])
@permission_required('user.update')
def set_password(user_id: int):
    """Set a new password for a user (admin action)."""
    user = User.query.get_or_404(user_id)

    password = request.form.get('password', '')
    password_confirm = request.form.get('password_confirm', '')

    # Validation
    if not password:
        flash('Passwort ist erforderlich.', 'error')
        return redirect(url_for('users_admin.edit_user', user_id=user_id))

    if len(password) < 8:
        flash('Passwort muss mindestens 8 Zeichen lang sein.', 'error')
        return redirect(url_for('users_admin.edit_user', user_id=user_id))

    if password != password_confirm:
        flash('Passwörter stimmen nicht überein.', 'error')
        return redirect(url_for('users_admin.edit_user', user_id=user_id))

    # Set new password
    user.set_password(password)
    user.record_password_change()
    db.session.commit()

    # Log event
    log_event(
        modul='user_admin',
        aktion='password_reset',
        details=f'Passwort für {user.email} durch Admin zurückgesetzt',
        wichtigkeit='kritisch',
        entity_type='User',
        entity_id=user.id,
    )

    flash(f'Passwort für "{user.full_name}" wurde geändert.', 'success')
    return redirect(url_for('users_admin.edit_user', user_id=user_id))


# =============================================================================
# 2FA Management
# =============================================================================

@users_admin_bp.route('/<int:user_id>/reset-2fa', methods=['POST'])
@permission_required('user.update')
def reset_2fa(user_id: int):
    """Reset 2FA for a user (admin action)."""
    user = User.query.get_or_404(user_id)

    if not user.totp_enabled:
        flash(f'2FA ist für "{user.full_name}" nicht aktiviert.', 'info')
        return redirect(url_for('users_admin.edit_user', user_id=user_id))

    # Disable 2FA
    user.disable_2fa()
    db.session.commit()

    # Log event
    log_event(
        modul='user_admin',
        aktion='2fa_reset',
        details=f'2FA für {user.email} durch Admin zurückgesetzt',
        wichtigkeit='kritisch',
        entity_type='User',
        entity_id=user.id,
    )

    flash(f'2FA für "{user.full_name}" wurde zurückgesetzt.', 'success')
    return redirect(url_for('users_admin.edit_user', user_id=user_id))


# =============================================================================
# Toggle Active Status
# =============================================================================

@users_admin_bp.route('/<int:user_id>/toggle-active', methods=['POST'])
@permission_required('user.update')
def toggle_active(user_id: int):
    """Toggle user's active status."""
    user = User.query.get_or_404(user_id)

    # Prevent self-deactivation
    if user.id == current_user.id and user.aktiv:
        flash('Du kannst deinen eigenen Account nicht deaktivieren.', 'error')
        return redirect(url_for('users_admin.list_users'))

    user.aktiv = not user.aktiv
    db.session.commit()

    status = 'aktiviert' if user.aktiv else 'deaktiviert'

    # Log event
    log_event(
        modul='user_admin',
        aktion=f'user_{status}',
        details=f'Benutzer {user.email} {status}',
        wichtigkeit='mittel',
        entity_type='User',
        entity_id=user.id,
    )

    flash(f'Benutzer "{user.full_name}" wurde {status}.', 'success')

    # HTMX response
    if request.headers.get('HX-Request'):
        return render_template(
            'v_flask/admin/users/_user_row.html',
            user=user,
        )

    return redirect(url_for('users_admin.list_users'))


# =============================================================================
# Bulk Actions
# =============================================================================

@users_admin_bp.route('/bulk-action', methods=['POST'])
@permission_required('user.update')
def bulk_action():
    """Perform bulk action on selected users."""
    action = request.form.get('action')
    user_ids = request.form.getlist('user_ids', type=int)

    if not user_ids:
        flash('Keine Benutzer ausgewählt.', 'warning')
        return redirect(url_for('users_admin.list_users'))

    # Remove current user from selection if deactivating
    if action in ('deactivate', 'delete'):
        user_ids = [uid for uid in user_ids if uid != current_user.id]

    if not user_ids:
        flash('Keine gültigen Benutzer für diese Aktion.', 'warning')
        return redirect(url_for('users_admin.list_users'))

    users = User.query.filter(User.id.in_(user_ids)).all()

    if action == 'activate':
        for user in users:
            user.aktiv = True
        db.session.commit()
        flash(f'{len(users)} Benutzer aktiviert.', 'success')

    elif action == 'deactivate':
        for user in users:
            user.aktiv = False
        db.session.commit()
        flash(f'{len(users)} Benutzer deaktiviert.', 'success')

    elif action == 'delete':
        for user in users:
            db.session.delete(user)
        db.session.commit()
        flash(f'{len(users)} Benutzer gelöscht.', 'success')

    else:
        flash('Unbekannte Aktion.', 'error')

    return redirect(url_for('users_admin.list_users'))


# =============================================================================
# Registration Function
# =============================================================================

def register_user_admin_routes(app: Flask) -> None:
    """Register user admin routes with the Flask app.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(users_admin_bp)
    logger.info("Registered user admin routes at /admin/users/")