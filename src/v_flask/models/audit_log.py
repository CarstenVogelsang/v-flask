"""AuditLog model for tracking user actions."""

from datetime import datetime

from v_flask.extensions import db


class AuditLog(db.Model):
    """Audit log for tracking user actions.

    Logs are created via the logging_service:
        from v_flask.services import log_event

        log_event(
            modul='projekt',
            aktion='erstellt',
            details='Projekt "Website Relaunch" erstellt',
            wichtigkeit='mittel',
            entity_type='Projekt',
            entity_id=42
        )

    Importance levels:
        - niedrig: Routine actions (view, list)
        - mittel: Standard changes (create, update)
        - hoch: Important changes (delete, permission changes)
        - kritisch: Security-relevant actions (login failures, permission denied)
    """

    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    modul = db.Column(db.String(50), index=True)
    aktion = db.Column(db.String(100))
    details = db.Column(db.Text)
    wichtigkeit = db.Column(db.String(20), default='niedrig', index=True)
    entity_type = db.Column(db.String(50), index=True)
    entity_id = db.Column(db.Integer)

    # IP address for security auditing
    ip_address = db.Column(db.String(45))  # IPv6 max length

    # Relationship
    user = db.relationship('User', backref='audit_logs')

    def __repr__(self) -> str:
        return f'<AuditLog {self.modul}:{self.aktion}>'

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'modul': self.modul,
            'aktion': self.aktion,
            'details': self.details,
            'wichtigkeit': self.wichtigkeit,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
        }
