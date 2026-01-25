"""
v-flask Auth

Decorators for access control and 2FA routes.

Usage:
    from v_flask.auth import permission_required, admin_required

    @app.route('/projekt/<int:id>/delete', methods=['POST'])
    @permission_required('projekt.delete')
    def delete_projekt(id):
        ...

    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        ...

2FA Integration:
    from v_flask.auth import register_2fa_routes, check_2fa_required

    # In app factory
    register_2fa_routes(app)

    # In login route (after password check)
    if user.check_password(password):
        redirect_url = check_2fa_required(user, remember, next_page)
        if redirect_url:
            return redirect(redirect_url)
        login_user(user)
"""

from v_flask.auth.decorators import (
    admin_required,
    login_required_with_message,
    mitarbeiter_required,
    permission_required,
)
from v_flask.auth.routes import (
    check_2fa_required,
    register_2fa_routes,
    two_fa_bp,
)

__all__ = [
    # Decorators
    'permission_required',
    'admin_required',
    'mitarbeiter_required',
    'login_required_with_message',
    # 2FA
    'register_2fa_routes',
    'check_2fa_required',
    'two_fa_bp',
]
