"""
v-flask Auth

Decorators for access control.

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
"""

from v_flask.auth.decorators import (
    admin_required,
    login_required_with_message,
    mitarbeiter_required,
    permission_required,
)

__all__ = [
    'permission_required',
    'admin_required',
    'mitarbeiter_required',
    'login_required_with_message',
]
