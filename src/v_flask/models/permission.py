"""Permission model for granular access control."""

from v_flask.extensions import db


# Association table for Rolle <-> Permission (many-to-many)
rolle_permission = db.Table(
    'rolle_permission',
    db.Column('rolle_id', db.Integer, db.ForeignKey('rolle.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)


class Permission(db.Model):
    """Permission model for granular access control.

    Permissions use a code format: <module>.<action>
    Examples:
        - projekt.read
        - projekt.create
        - projekt.update
        - projekt.delete
        - task.comment

    Wildcards are supported:
        - projekt.* - All project actions
        - admin.* - All admin actions

    Usage:
        from v_flask.models import Permission

        perm = Permission(
            code='projekt.delete',
            beschreibung='Projekte löschen',
            modul='projektverwaltung'
        )
        db.session.add(perm)
        db.session.commit()
    """

    __tablename__ = 'permission'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    beschreibung = db.Column(db.String(200))
    modul = db.Column(db.String(50), index=True)  # e.g. 'projektverwaltung'

    def __repr__(self) -> str:
        return f'<Permission {self.code}>'

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'code': self.code,
            'beschreibung': self.beschreibung,
            'modul': self.modul,
        }
