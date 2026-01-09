"""Auth decorators for granular permission-based access control."""

from functools import wraps
from typing import Callable

from flask import flash, redirect, url_for
from flask_login import current_user


def permission_required(permission_code: str) -> Callable:
    """Decorator for granular permission checking.

    Checks if the current user has the specified permission via their role.
    Admin users (is_admin=True) automatically bypass all permission checks.
    Supports wildcards in role permissions (e.g., 'projekt.*' allows 'projekt.delete').

    Args:
        permission_code: Permission code to check (e.g., 'projekt.delete').

    Usage:
        @blueprint.route('/projekt/<int:id>/delete', methods=['POST'])
        @permission_required('projekt.delete')
        def delete_projekt(id):
            projekt = Projekt.query.get_or_404(id)
            db.session.delete(projekt)
            db.session.commit()
            flash('Projekt gelöscht.', 'success')
            return redirect(url_for('.list_projekte'))
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bitte melde dich an.', 'warning')
                return redirect(url_for('auth.login'))
            # Admin users bypass all permission checks
            if current_user.is_admin:
                return f(*args, **kwargs)
            if not current_user.has_permission(permission_code):
                flash('Keine Berechtigung für diese Aktion.', 'danger')
                # Try common index routes
                for endpoint in ['public.index', 'main.index']:
                    try:
                        return redirect(url_for(endpoint))
                    except Exception:
                        continue
                return redirect('/')
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f: Callable) -> Callable:
    """Decorator shortcut for admin permission.

    Equivalent to @permission_required('admin.*').

    Usage:
        @app.route('/admin')
        @admin_required
        def admin_dashboard():
            return render_template('admin/dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bitte melde dich an.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Zugriff verweigert. Admin-Rechte erforderlich.', 'danger')
            # Try common index routes
            for endpoint in ['public.index', 'main.index']:
                try:
                    return redirect(url_for(endpoint))
                except Exception:
                    continue
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


def mitarbeiter_required(f: Callable) -> Callable:
    """Decorator for internal staff access (admin or mitarbeiter).

    Usage:
        @app.route('/intern')
        @mitarbeiter_required
        def internal_dashboard():
            return render_template('intern/dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bitte melde dich an.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_mitarbeiter:
            flash('Zugriff verweigert. Mitarbeiter-Rechte erforderlich.', 'danger')
            # Try common index routes
            for endpoint in ['public.index', 'main.index']:
                try:
                    return redirect(url_for(endpoint))
                except Exception:
                    continue
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


def login_required_with_message(f: Callable) -> Callable:
    """Login required decorator with German flash message.

    Usage:
        @app.route('/profile')
        @login_required_with_message
        def profile():
            return render_template('profile.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bitte melde dich an.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
