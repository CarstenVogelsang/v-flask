"""Admin routes for role management.

Core v-flask admin functionality for:
- Role CRUD (list, create, edit, delete)
- Permission assignment to roles

Routes are available under /admin/roles/ and require role.* permissions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from flask import Blueprint, flash, redirect, render_template, request, url_for

from v_flask.auth import permission_required
from v_flask.extensions import db
from v_flask.models import Rolle, Permission, User
from v_flask.services import log_event

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

# Blueprint for role admin routes
roles_admin_bp = Blueprint(
    'roles_admin',
    __name__,
    url_prefix='/admin/roles',
    template_folder='../templates',
)


# =============================================================================
# Role List
# =============================================================================

@roles_admin_bp.route('/')
@permission_required('user.read')
def list_roles():
    """Display list of all roles with user count."""
    roles = Rolle.query.order_by(Rolle.name).all()

    # Get user counts per role
    role_user_counts = {}
    for rolle in roles:
        role_user_counts[rolle.id] = User.query.filter_by(rolle_id=rolle.id).count()

    return render_template(
        'v_flask/admin/roles/list.html',
        roles=roles,
        role_user_counts=role_user_counts,
    )


# =============================================================================
# Role Create
# =============================================================================

@roles_admin_bp.route('/new', methods=['GET', 'POST'])
@permission_required('user.create')
def create_role():
    """Create a new role."""
    # Get all available permissions grouped by module
    permissions = Permission.query.order_by(Permission.modul, Permission.code).all()
    permissions_by_module = _group_permissions_by_module(permissions)

    if request.method == 'POST':
        name = request.form.get('name', '').strip().lower()
        beschreibung = request.form.get('beschreibung', '').strip()
        selected_perms = request.form.getlist('permissions')

        # Validation
        errors = []

        if not name:
            errors.append('Name ist erforderlich.')
        elif Rolle.query.filter_by(name=name).first():
            errors.append('Eine Rolle mit diesem Namen existiert bereits.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'v_flask/admin/roles/form.html',
                role=None,
                permissions_by_module=permissions_by_module,
                form_data=request.form,
                selected_permissions=selected_perms,
            )

        # Create role
        rolle = Rolle(
            name=name,
            beschreibung=beschreibung,
        )
        db.session.add(rolle)
        db.session.flush()  # Get the ID

        # Add permissions
        for perm_id in selected_perms:
            perm = Permission.query.get(int(perm_id))
            if perm:
                rolle.permissions.append(perm)

        db.session.commit()

        # Log event
        log_event(
            modul='user_admin',
            aktion='role_created',
            details=f'Rolle "{rolle.name}" erstellt mit {len(selected_perms)} Berechtigungen',
            wichtigkeit='mittel',
            entity_type='Rolle',
            entity_id=rolle.id,
        )

        flash(f'Rolle "{rolle.name}" wurde erstellt.', 'success')
        return redirect(url_for('roles_admin.list_roles'))

    return render_template(
        'v_flask/admin/roles/form.html',
        role=None,
        permissions_by_module=permissions_by_module,
        form_data={},
        selected_permissions=[],
    )


# =============================================================================
# Role Edit
# =============================================================================

@roles_admin_bp.route('/<int:role_id>/edit', methods=['GET', 'POST'])
@permission_required('user.update')
def edit_role(role_id: int):
    """Edit an existing role."""
    rolle = Rolle.query.get_or_404(role_id)

    # Get all available permissions grouped by module
    permissions = Permission.query.order_by(Permission.modul, Permission.code).all()
    permissions_by_module = _group_permissions_by_module(permissions)

    # Get currently assigned permission IDs
    current_perm_ids = [p.id for p in rolle.permissions.all()]

    if request.method == 'POST':
        name = request.form.get('name', '').strip().lower()
        beschreibung = request.form.get('beschreibung', '').strip()
        selected_perms = request.form.getlist('permissions')

        # Validation
        errors = []

        if not name:
            errors.append('Name ist erforderlich.')
        else:
            existing = Rolle.query.filter_by(name=name).first()
            if existing and existing.id != rolle.id:
                errors.append('Eine Rolle mit diesem Namen existiert bereits.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'v_flask/admin/roles/form.html',
                role=rolle,
                permissions_by_module=permissions_by_module,
                form_data=request.form,
                selected_permissions=selected_perms,
            )

        # Update role
        rolle.name = name
        rolle.beschreibung = beschreibung

        # Update permissions
        rolle.permissions = []  # Clear existing
        for perm_id in selected_perms:
            perm = Permission.query.get(int(perm_id))
            if perm:
                rolle.permissions.append(perm)

        db.session.commit()

        # Log event
        log_event(
            modul='user_admin',
            aktion='role_updated',
            details=f'Rolle "{rolle.name}" bearbeitet',
            wichtigkeit='niedrig',
            entity_type='Rolle',
            entity_id=rolle.id,
        )

        flash(f'Rolle "{rolle.name}" wurde aktualisiert.', 'success')
        return redirect(url_for('roles_admin.list_roles'))

    return render_template(
        'v_flask/admin/roles/form.html',
        role=rolle,
        permissions_by_module=permissions_by_module,
        form_data={},
        selected_permissions=[str(p) for p in current_perm_ids],
    )


# =============================================================================
# Role Delete
# =============================================================================

@roles_admin_bp.route('/<int:role_id>/delete', methods=['POST'])
@permission_required('user.delete')
def delete_role(role_id: int):
    """Delete a role (if no users assigned)."""
    rolle = Rolle.query.get_or_404(role_id)

    # Check if any users have this role
    user_count = User.query.filter_by(rolle_id=rolle.id).count()
    if user_count > 0:
        flash(
            f'Rolle "{rolle.name}" kann nicht gelöscht werden, '
            f'da noch {user_count} Benutzer zugewiesen sind.',
            'error'
        )
        return redirect(url_for('roles_admin.list_roles'))

    # Prevent deletion of system roles
    system_roles = ['admin', 'betreiber', 'mitarbeiter', 'kunde']
    if rolle.name in system_roles:
        flash(f'System-Rolle "{rolle.name}" kann nicht gelöscht werden.', 'error')
        return redirect(url_for('roles_admin.list_roles'))

    name = rolle.name

    db.session.delete(rolle)
    db.session.commit()

    # Log event
    log_event(
        modul='user_admin',
        aktion='role_deleted',
        details=f'Rolle "{name}" gelöscht',
        wichtigkeit='kritisch',
        entity_type='Rolle',
        entity_id=role_id,
    )

    flash(f'Rolle "{name}" wurde gelöscht.', 'success')
    return redirect(url_for('roles_admin.list_roles'))


# =============================================================================
# Helper Functions
# =============================================================================

def _group_permissions_by_module(permissions: list[Permission]) -> dict[str, list[Permission]]:
    """Group permissions by their module.

    Args:
        permissions: List of Permission objects.

    Returns:
        Dict mapping module names to lists of permissions.
    """
    grouped: dict[str, list[Permission]] = {}

    for perm in permissions:
        module = perm.modul or 'other'
        if module not in grouped:
            grouped[module] = []
        grouped[module].append(perm)

    return grouped


# =============================================================================
# Registration Function
# =============================================================================

def register_role_admin_routes(app: Flask) -> None:
    """Register role admin routes with the Flask app.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(roles_admin_bp)
    logger.info("Registered role admin routes at /admin/roles/")
