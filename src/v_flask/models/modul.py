"""Modul model for dashboard registry and navigation."""

from datetime import datetime

from v_flask.extensions import db


class Modul(db.Model):
    """Module registry for dashboard tiles and navigation.

    Each module represents a functional area (e.g., Projektverwaltung, Benutzerverwaltung).
    Visibility is controlled by the min_permission field:
        - User must have this permission to see the module tile in dashboard
        - Actual access control uses the full permission system

    Usage:
        from v_flask.models import Modul

        # Register a module
        projekt_modul = Modul(
            code='projektverwaltung',
            name='Projektverwaltung',
            beschreibung='Projekte und Tasks verwalten',
            icon='folder',
            endpoint='admin.projekte',
            min_permission='projekt.read',
            sort_order=1
        )
        db.session.add(projekt_modul)
        db.session.commit()

        # Get modules for current user
        visible_modules = Modul.get_for_user(current_user)

        # In template
        {% for modul in get_modules() %}
            <a href="{{ url_for(modul.endpoint) }}">
                <i class="ti ti-{{ modul.icon }}"></i>
                {{ modul.name }}
            </a>
        {% endfor %}
    """

    __tablename__ = 'modul'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    beschreibung = db.Column(db.String(200))
    icon = db.Column(db.String(50))  # Tabler icon name, e.g. 'folder'
    endpoint = db.Column(db.String(100))  # Flask endpoint name, e.g. 'admin.projekte'
    min_permission = db.Column(db.String(100), nullable=False)  # Required for visibility
    sort_order = db.Column(db.Integer, default=0)
    aktiv = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<Modul {self.code}>'

    @classmethod
    def get_for_user(cls, user) -> list['Modul']:
        """Get all modules visible to a user based on permissions.

        Args:
            user: User instance (must have has_permission() method).
                  Can be an anonymous user (is_authenticated = False).

        Returns:
            List of Modul instances the user can see, ordered by sort_order.
        """
        # Anonymous users see no modules
        if not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            return []

        modules = db.session.query(cls).filter_by(aktiv=True).order_by(cls.sort_order).all()
        return [m for m in modules if user.has_permission(m.min_permission)]

    @classmethod
    def get_all_active(cls) -> list['Modul']:
        """Get all active modules, ordered by sort_order.

        Returns:
            List of all active Modul instances.
        """
        return db.session.query(cls).filter_by(aktiv=True).order_by(cls.sort_order).all()

    @classmethod
    def get_by_code(cls, code: str) -> 'Modul | None':
        """Get a module by its code.

        Args:
            code: Module code (e.g., 'projektverwaltung').

        Returns:
            Modul instance or None.
        """
        return db.session.query(cls).filter_by(code=code).first()

    def user_can_access(self, user) -> bool:
        """Check if a user can access this module.

        Args:
            user: User instance.

        Returns:
            True if user has the required permission.
        """
        if not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            return False
        return user.has_permission(self.min_permission)

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'beschreibung': self.beschreibung,
            'icon': self.icon,
            'endpoint': self.endpoint,
            'min_permission': self.min_permission,
            'sort_order': self.sort_order,
            'aktiv': self.aktiv,
        }
