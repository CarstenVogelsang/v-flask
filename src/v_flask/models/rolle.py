"""Rolle (Role) model for user access control."""

from datetime import datetime

from v_flask.extensions import db
from v_flask.models.permission import rolle_permission


class Rolle(db.Model):
    """Role model for user authorization with permission support.

    Standard roles:
        - admin: Full access to all features
        - mitarbeiter: Internal staff access
        - kunde: Customer/client access

    Permissions support wildcards:
        - projekt.* allows projekt.read, projekt.create, projekt.delete, etc.
        - admin.* grants full admin access

    Usage:
        from v_flask.models import Rolle, Permission

        admin_role = Rolle(name='admin', beschreibung='Administrator')
        perm = Permission(code='admin.*')
        admin_role.permissions.append(perm)
        db.session.add(admin_role)
        db.session.commit()

        # Check permission
        if admin_role.has_permission('user.delete'):
            print('Role can delete users')
    """

    __tablename__ = 'rolle'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False, index=True)
    beschreibung = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship('User', back_populates='rolle_obj', lazy='dynamic')
    permissions = db.relationship(
        'Permission',
        secondary=rolle_permission,
        backref='rollen',
        lazy='dynamic'
    )

    def __repr__(self) -> str:
        return f'<Rolle {self.name}>'

    def has_permission(self, code: str) -> bool:
        """Check if role has a specific permission.

        Supports wildcards: 'projekt.*' matches 'projekt.read', 'projekt.delete', etc.

        Args:
            code: Permission code to check (e.g., 'projekt.delete').

        Returns:
            True if role has the permission, False otherwise.
        """
        for perm in self.permissions:
            if perm.code == code:
                return True
            # Wildcard support: 'projekt.*' allows 'projekt.delete'
            if perm.code.endswith('.*'):
                prefix = perm.code[:-1]  # 'projekt.'
                if code.startswith(prefix):
                    return True
        return False

    def add_permission(self, permission) -> None:
        """Add a permission to this role.

        Args:
            permission: Permission instance to add.
        """
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission) -> None:
        """Remove a permission from this role.

        Args:
            permission: Permission instance to remove.
        """
        if permission in self.permissions:
            self.permissions.remove(permission)

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'beschreibung': self.beschreibung,
            'permissions': [p.code for p in self.permissions],
        }
