"""Models for Projektverwaltung plugin.

This module defines all database models for the project management plugin:
- Projekt: Top-level container for components
- Komponente: PRD/module/entity within a project
- Task: Work item with Kanban status
- TaskKommentar: Comments on tasks (review workflow)
- ChangelogEintrag: Auto-generated changelog entries
"""
from datetime import datetime, timezone
from enum import Enum

from v_flask.extensions import db


# =============================================================================
# Enums
# =============================================================================

class ProjektTyp(str, Enum):
    """Project types for categorization."""
    INTERN = 'intern'
    KUNDE = 'kunde'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.INTERN: 'Intern',
            cls.KUNDE: 'Kundenprojekt',
        }
        return [(t.value, labels[t]) for t in cls]


class KomponenteTyp(str, Enum):
    """Component types for categorization."""
    MODUL = 'modul'
    BASISFUNKTION = 'basisfunktion'
    ENTITY = 'entity'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.MODUL: 'Modul',
            cls.BASISFUNKTION: 'Basisfunktion',
            cls.ENTITY: 'Entity/Stammdaten',
        }
        return [(t.value, labels[t]) for t in cls]


class KomponentePhase(str, Enum):
    """Development phases for components."""
    POC = 'poc'
    MVP = 'mvp'
    V1 = 'v1'
    V2 = 'v2'
    V3 = 'v3'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.POC: 'POC (Proof of Concept)',
            cls.MVP: 'MVP (Minimum Viable Product)',
            cls.V1: 'V1',
            cls.V2: 'V2',
            cls.V3: 'V3',
        }
        return [(t.value, labels[t]) for t in cls]


class KomponenteStatus(str, Enum):
    """Status of a component."""
    AKTIV = 'aktiv'
    ARCHIVIERT = 'archiviert'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.AKTIV: 'Aktiv',
            cls.ARCHIVIERT: 'Archiviert',
        }
        return [(t.value, labels[t]) for t in cls]


class TaskStatus(str, Enum):
    """Task status representing Kanban columns."""
    BACKLOG = 'backlog'
    GEPLANT = 'geplant'
    IN_ARBEIT = 'in_arbeit'
    REVIEW = 'review'
    ERLEDIGT = 'erledigt'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.BACKLOG: 'Backlog',
            cls.GEPLANT: 'Geplant',
            cls.IN_ARBEIT: 'In Arbeit',
            cls.REVIEW: 'Review',
            cls.ERLEDIGT: 'Erledigt',
        }
        return [(t.value, labels[t]) for t in cls]

    @classmethod
    def kanban_order(cls):
        """Return status values in Kanban board order."""
        return [cls.BACKLOG, cls.GEPLANT, cls.IN_ARBEIT, cls.REVIEW, cls.ERLEDIGT]


class TaskPrioritaet(str, Enum):
    """Task priority levels."""
    NIEDRIG = 'niedrig'
    MITTEL = 'mittel'
    HOCH = 'hoch'
    KRITISCH = 'kritisch'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.NIEDRIG: 'Niedrig',
            cls.MITTEL: 'Mittel',
            cls.HOCH: 'Hoch',
            cls.KRITISCH: 'Kritisch',
        }
        return [(t.value, labels[t]) for t in cls]

    @classmethod
    def color_map(cls):
        """Return DaisyUI color classes for each priority."""
        return {
            cls.NIEDRIG.value: 'ghost',
            cls.MITTEL.value: 'info',
            cls.HOCH.value: 'warning',
            cls.KRITISCH.value: 'error',
        }


class TaskPhase(str, Enum):
    """Development phase for tasks."""
    POC = 'poc'
    MVP = 'mvp'
    V1 = 'v1'
    V2 = 'v2'
    V3 = 'v3'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.POC: 'POC',
            cls.MVP: 'MVP',
            cls.V1: 'V1',
            cls.V2: 'V2',
            cls.V3: 'V3',
        }
        return [(t.value, labels[t]) for t in cls]


class KommentarTyp(str, Enum):
    """Types of task comments."""
    REVIEW = 'review'
    FRAGE = 'frage'
    HINWEIS = 'hinweis'
    KOMMENTAR = 'kommentar'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.REVIEW: 'Review',
            cls.FRAGE: 'Frage',
            cls.HINWEIS: 'Hinweis',
            cls.KOMMENTAR: 'Kommentar',
        }
        return [(t.value, labels[t]) for t in cls]


class ChangelogKategorie(str, Enum):
    """Changelog categories following Keep a Changelog convention."""
    ADDED = 'added'
    CHANGED = 'changed'
    FIXED = 'fixed'
    REMOVED = 'removed'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.ADDED: 'Added (Neu)',
            cls.CHANGED: 'Changed (Geändert)',
            cls.FIXED: 'Fixed (Behoben)',
            cls.REMOVED: 'Removed (Entfernt)',
        }
        return [(t.value, labels[t]) for t in cls]

    @classmethod
    def color_map(cls):
        """Return DaisyUI color classes for each category."""
        return {
            cls.ADDED.value: 'success',
            cls.CHANGED.value: 'info',
            cls.FIXED.value: 'warning',
            cls.REMOVED.value: 'error',
        }


class ChangelogSichtbarkeit(str, Enum):
    """Visibility of changelog entries."""
    INTERN = 'intern'
    OEFFENTLICH = 'oeffentlich'

    @classmethod
    def choices(cls):
        """Return list of (value, label) tuples for form selects."""
        labels = {
            cls.INTERN: 'Intern (nur Mitarbeiter)',
            cls.OEFFENTLICH: 'Öffentlich (auch Kunden)',
        }
        return [(t.value, labels[t]) for t in cls]


# =============================================================================
# Models
# =============================================================================

class Projekt(db.Model):
    """Represents a project in the project management system.

    A project contains multiple components (PRDs/modules) and can be
    either internal or customer-specific.
    """
    __tablename__ = 'pv_projekt'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    beschreibung = db.Column(db.Text, nullable=True)
    typ = db.Column(db.String(20), default=ProjektTyp.INTERN.value, nullable=False)

    # Generic customer reference (no FK constraint - host app defines customer model)
    kunde_id = db.Column(db.Integer, nullable=True, index=True)

    aktiv = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    komponenten = db.relationship(
        'Komponente',
        backref='projekt',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Komponente.sortierung'
    )

    def __repr__(self):
        return f'<Projekt {self.name}>'

    @property
    def ist_kundenprojekt(self):
        """Check if this is a customer project."""
        return self.typ == ProjektTyp.KUNDE.value

    @property
    def anzahl_komponenten(self):
        """Return number of components in this project."""
        return self.komponenten.count()

    @property
    def aktive_komponenten(self):
        """Return active components."""
        return self.komponenten.filter_by(status='aktiv').all()

    def to_dict(self, include_komponenten=False):
        """Return dictionary representation."""
        result = {
            'id': self.id,
            'name': self.name,
            'beschreibung': self.beschreibung,
            'typ': self.typ,
            'kunde_id': self.kunde_id,
            'aktiv': self.aktiv,
            'anzahl_komponenten': self.anzahl_komponenten,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_komponenten:
            result['komponenten'] = [k.to_dict() for k in self.aktive_komponenten]
        return result


class Komponente(db.Model):
    """Represents a component (PRD/module/entity) within a project."""
    __tablename__ = 'pv_komponente'

    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('pv_projekt.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    prd_nummer = db.Column(db.String(10), nullable=True)

    typ = db.Column(db.String(20), default=KomponenteTyp.MODUL.value, nullable=False)

    # Optional link to V-Flask Modul for dashboard/permission integration
    modul_id = db.Column(db.Integer, db.ForeignKey('modul.id'), nullable=True)

    prd_inhalt = db.Column(db.Text, nullable=True)

    aktuelle_phase = db.Column(db.String(10), default=KomponentePhase.POC.value)
    status = db.Column(db.String(20), default=KomponenteStatus.AKTIV.value)

    icon = db.Column(db.String(50), default='ti-package')
    sortierung = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    tasks = db.relationship(
        'Task',
        backref='komponente',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Task.sortierung'
    )
    changelog_eintraege = db.relationship(
        'ChangelogEintrag',
        backref='komponente',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='ChangelogEintrag.erstellt_am.desc()'
    )

    def __repr__(self):
        return f'<Komponente PRD-{self.prd_nummer} {self.name}>'

    @property
    def prd_bezeichnung(self):
        """Return formatted PRD designation."""
        if self.prd_nummer:
            return f'PRD-{self.prd_nummer}'
        return None

    @property
    def ist_modul(self):
        """Check if this is a module component."""
        return self.typ == KomponenteTyp.MODUL.value

    @property
    def typ_icon(self):
        """Return Tabler icon for component type."""
        icons = {
            'modul': 'ti-layout-grid',
            'basisfunktion': 'ti-settings',
            'entity': 'ti-database',
        }
        return icons.get(self.typ, 'ti-package')

    @property
    def typ_label(self):
        """Return display label for component type."""
        for value, label in KomponenteTyp.choices():
            if value == self.typ:
                return label
        return self.typ

    @property
    def anzahl_tasks(self):
        """Return number of tasks for this component."""
        return self.tasks.count()

    @property
    def offene_tasks(self):
        """Return tasks that are not completed."""
        return self.tasks.filter(Task.status != 'erledigt').all()

    def to_dict(self, include_prd=False, include_tasks=False):
        """Return dictionary representation."""
        result = {
            'id': self.id,
            'projekt_id': self.projekt_id,
            'name': self.name,
            'prd_nummer': self.prd_nummer,
            'prd_bezeichnung': self.prd_bezeichnung,
            'typ': self.typ,
            'typ_icon': self.typ_icon,
            'typ_label': self.typ_label,
            'modul_id': self.modul_id,
            'aktuelle_phase': self.aktuelle_phase,
            'status': self.status,
            'icon': self.icon,
            'sortierung': self.sortierung,
            'anzahl_tasks': self.anzahl_tasks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_prd:
            result['prd_inhalt'] = self.prd_inhalt
        if include_tasks:
            result['tasks'] = [t.to_dict() for t in self.offene_tasks]
        return result


class Task(db.Model):
    """Represents a task/work item within a component."""
    __tablename__ = 'pv_task'

    id = db.Column(db.Integer, primary_key=True)
    komponente_id = db.Column(db.Integer, db.ForeignKey('pv_komponente.id'), nullable=False)

    titel = db.Column(db.String(200), nullable=False)
    beschreibung = db.Column(db.Text, nullable=True)

    phase = db.Column(db.String(10), default=TaskPhase.POC.value, nullable=False)
    status = db.Column(db.String(20), default=TaskStatus.BACKLOG.value, nullable=False)
    prioritaet = db.Column(db.String(20), default=TaskPrioritaet.MITTEL.value, nullable=False)
    typ = db.Column(db.String(30), default='funktion', nullable=False)

    # User assignment via V-Flask User model
    zugewiesen_an = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    sortierung = db.Column(db.Integer, default=0)
    create_changelog_on_complete = db.Column(db.Boolean, default=True)

    ist_archiviert = db.Column(db.Boolean, default=False, nullable=False)

    # Task-Splitting: self-referential
    entstanden_aus_id = db.Column(db.Integer, db.ForeignKey('pv_task.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    erledigt_am = db.Column(db.DateTime, nullable=True)

    # Relationships
    zugewiesen_user = db.relationship(
        'User',
        backref=db.backref('pv_zugewiesene_tasks', lazy='dynamic'),
        foreign_keys=[zugewiesen_an]
    )
    changelog_eintraege = db.relationship(
        'ChangelogEintrag',
        backref='task',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    kommentare = db.relationship(
        'TaskKommentar',
        backref='task',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='TaskKommentar.created_at.desc()'
    )
    entstanden_aus = db.relationship(
        'Task',
        remote_side=[id],
        backref=db.backref('abgeleitete_tasks', lazy='dynamic'),
        foreign_keys=[entstanden_aus_id]
    )

    def __repr__(self):
        return f'<Task {self.id}: {self.titel[:30]}>'

    @property
    def ist_erledigt(self):
        """Check if task is completed."""
        return self.status == TaskStatus.ERLEDIGT.value

    @property
    def prioritaet_color(self):
        """Return DaisyUI color class for priority."""
        return TaskPrioritaet.color_map().get(self.prioritaet, 'ghost')

    @property
    def prioritaet_badge(self):
        """Return full DaisyUI badge class for priority."""
        return f'badge-{self.prioritaet_color}'

    @property
    def zugewiesen(self):
        """Return assigned user (alias for zugewiesen_user)."""
        return self.zugewiesen_user

    @property
    def zugewiesen_name(self):
        """Return name of assigned user or None."""
        if self.zugewiesen_user:
            return getattr(self.zugewiesen_user, 'full_name', str(self.zugewiesen_user))
        return None

    @property
    def typ_icon(self):
        """Return Tabler icon for task type."""
        try:
            from v_flask.models import LookupWert
            wert = LookupWert.query.filter_by(kategorie='task_typ', code=self.typ).first()
            if wert and wert.icon:
                return wert.icon
        except Exception:
            pass
        # Fallback icons
        icons = {
            'funktion': 'ti-code',
            'verbesserung': 'ti-trending-up',
            'fehlerbehebung': 'ti-bug',
            'technisch': 'ti-tool',
            'sicherheit': 'ti-shield',
            'recherche': 'ti-search',
            'dokumentation': 'ti-file-text',
            'test': 'ti-flask',
        }
        return icons.get(self.typ, 'ti-help')

    @property
    def typ_farbe(self):
        """Return DaisyUI color for task type."""
        try:
            from v_flask.models import LookupWert
            wert = LookupWert.query.filter_by(kategorie='task_typ', code=self.typ).first()
            if wert and wert.farbe:
                return wert.farbe
        except Exception:
            pass
        return 'ghost'

    @property
    def typ_label(self):
        """Return display label for task type."""
        try:
            from v_flask.models import LookupWert
            wert = LookupWert.query.filter_by(kategorie='task_typ', code=self.typ).first()
            if wert:
                return wert.name
        except Exception:
            pass
        return self.typ.title()

    @property
    def typ_beschreibung(self):
        """Return description for task type (used for AI prompts)."""
        beschreibungen = {
            'funktion': 'Neuentwicklung einer fachlichen oder technischen Funktion',
            'verbesserung': 'Optimierung bestehender Funktionen (UX, Performance)',
            'fehlerbehebung': 'Behebung eines reproduzierbaren Fehlers',
            'technisch': 'Refactoring, Architektur, Infrastruktur',
            'sicherheit': 'Zugriffskontrolle, Datenschutz, Sicherheitslücken',
            'recherche': 'Analyse- oder Evaluierungsaufgabe',
            'dokumentation': 'Benutzer- oder Entwickler-Dokumentation',
            'test': 'Tests, Testkonzepte, manuelle Prüfungen',
        }
        return beschreibungen.get(self.typ, '')

    @property
    def task_nummer(self):
        """Return readable task ID in format PRD{prd_nummer}-T{id:03d}."""
        if self.komponente and self.komponente.prd_nummer:
            return f"PRD{self.komponente.prd_nummer}-T{self.id:03d}"
        return f"T{self.id:03d}"

    @property
    def entstanden_aus_nummer(self):
        """Return task_nummer of parent task if exists."""
        if self.entstanden_aus:
            return self.entstanden_aus.task_nummer
        return None

    @property
    def anzahl_abgeleitete(self):
        """Return count of derived tasks."""
        return self.abgeleitete_tasks.count()

    @property
    def review_kommentare(self):
        """Return only non-completed review comments for prompt generation."""
        return self.kommentare.filter_by(typ='review', erledigt=False).all()

    @property
    def offene_review_kommentare(self):
        """Return count of open review comments."""
        return self.kommentare.filter_by(typ='review', erledigt=False).count()

    @property
    def anzahl_kommentare(self):
        """Return total comment count."""
        return self.kommentare.count()

    def erledigen(self, user_id=None):
        """Mark task as completed and set completion timestamp."""
        if self.ist_erledigt:
            return False
        self.status = TaskStatus.ERLEDIGT.value
        self.erledigt_am = datetime.now(timezone.utc)
        return True

    def to_dict(self, include_beschreibung=False):
        """Return dictionary representation."""
        result = {
            'id': self.id,
            'task_nummer': self.task_nummer,
            'komponente_id': self.komponente_id,
            'titel': self.titel,
            'phase': self.phase,
            'status': self.status,
            'prioritaet': self.prioritaet,
            'prioritaet_color': self.prioritaet_color,
            'prioritaet_badge': self.prioritaet_badge,
            'typ': self.typ,
            'typ_icon': self.typ_icon,
            'typ_farbe': self.typ_farbe,
            'typ_label': self.typ_label,
            'zugewiesen_an': self.zugewiesen_an,
            'zugewiesen_name': self.zugewiesen_name,
            'sortierung': self.sortierung,
            'ist_erledigt': self.ist_erledigt,
            'ist_archiviert': self.ist_archiviert,
            'entstanden_aus_id': self.entstanden_aus_id,
            'entstanden_aus_nummer': self.entstanden_aus_nummer,
            'anzahl_abgeleitete': self.anzahl_abgeleitete,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'erledigt_am': self.erledigt_am.isoformat() if self.erledigt_am else None,
        }
        if include_beschreibung:
            result['beschreibung'] = self.beschreibung
        return result


class TaskKommentar(db.Model):
    """A comment on a task for review workflow."""
    __tablename__ = 'pv_task_kommentar'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('pv_task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    typ = db.Column(db.String(20), default=KommentarTyp.KOMMENTAR.value, nullable=False)
    inhalt = db.Column(db.Text, nullable=False)

    erledigt = db.Column(db.Boolean, default=False, nullable=False)
    erledigt_am = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', backref='pv_task_kommentare')

    def __repr__(self):
        return f'<TaskKommentar {self.id} ({self.typ})>'

    @property
    def typ_icon(self):
        """Return Tabler icon for comment type."""
        icons = {
            'review': 'ti-eye-check',
            'frage': 'ti-help-circle',
            'hinweis': 'ti-bulb',
            'kommentar': 'ti-message',
        }
        return icons.get(self.typ, 'ti-message')

    @property
    def typ_farbe(self):
        """Return DaisyUI color for comment type."""
        colors = {
            'review': 'warning',
            'frage': 'info',
            'hinweis': 'ghost',
            'kommentar': 'ghost',
        }
        return colors.get(self.typ, 'ghost')

    @property
    def typ_label(self):
        """Return display label for comment type."""
        for value, label in KommentarTyp.choices():
            if value == self.typ:
                return label
        return self.typ

    def toggle_erledigt(self):
        """Toggle the completion status."""
        self.erledigt = not self.erledigt
        self.erledigt_am = datetime.now(timezone.utc) if self.erledigt else None

    def to_dict(self):
        """Return dictionary representation."""
        user_name = 'System'
        if self.user:
            user_name = getattr(self.user, 'vorname', None) or str(self.user)
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user_name': user_name,
            'typ': self.typ,
            'typ_icon': self.typ_icon,
            'typ_farbe': self.typ_farbe,
            'typ_label': self.typ_label,
            'inhalt': self.inhalt,
            'erledigt': self.erledigt,
            'erledigt_am': self.erledigt_am.isoformat() if self.erledigt_am else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ChangelogEintrag(db.Model):
    """Represents a changelog entry for a component."""
    __tablename__ = 'pv_changelog_eintrag'

    id = db.Column(db.Integer, primary_key=True)
    komponente_id = db.Column(db.Integer, db.ForeignKey('pv_komponente.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('pv_task.id'), nullable=True)

    version = db.Column(db.String(20), nullable=False)
    kategorie = db.Column(db.String(20), default=ChangelogKategorie.ADDED.value, nullable=False)
    beschreibung = db.Column(db.Text, nullable=False)

    sichtbarkeit = db.Column(
        db.String(20),
        default=ChangelogSichtbarkeit.INTERN.value,
        nullable=False
    )

    erstellt_am = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    erstellt_von = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relationships
    erstellt_user = db.relationship(
        'User',
        backref=db.backref('pv_changelog_eintraege', lazy='dynamic')
    )

    def __repr__(self):
        return f'<ChangelogEintrag {self.version}: {self.beschreibung[:30]}>'

    @property
    def kategorie_color(self):
        """Return DaisyUI color class for category."""
        return ChangelogKategorie.color_map().get(self.kategorie, 'ghost')

    @property
    def ist_oeffentlich(self):
        """Check if entry should be publicly visible."""
        return self.sichtbarkeit == ChangelogSichtbarkeit.OEFFENTLICH.value

    @property
    def erstellt_von_name(self):
        """Return name of creator or None."""
        if self.erstellt_user:
            return getattr(self.erstellt_user, 'full_name', str(self.erstellt_user))
        return None

    @classmethod
    def create_from_task(cls, task, kategorie=None, beschreibung=None, user_id=None):
        """Create a changelog entry from a completed task."""
        return cls(
            komponente_id=task.komponente_id,
            task_id=task.id,
            version=task.phase.upper(),
            kategorie=kategorie or ChangelogKategorie.ADDED.value,
            beschreibung=beschreibung or task.titel,
            sichtbarkeit=ChangelogSichtbarkeit.INTERN.value,
            erstellt_von=user_id,
        )

    def to_dict(self):
        """Return dictionary representation."""
        return {
            'id': self.id,
            'komponente_id': self.komponente_id,
            'task_id': self.task_id,
            'version': self.version,
            'kategorie': self.kategorie,
            'kategorie_color': self.kategorie_color,
            'beschreibung': self.beschreibung,
            'sichtbarkeit': self.sichtbarkeit,
            'ist_oeffentlich': self.ist_oeffentlich,
            'erstellt_am': self.erstellt_am.isoformat() if self.erstellt_am else None,
            'erstellt_von': self.erstellt_von,
            'erstellt_von_name': self.erstellt_von_name,
        }

    def to_markdown(self):
        """Return entry as Markdown list item."""
        kategorie_prefix = {
            ChangelogKategorie.ADDED.value: '✨',
            ChangelogKategorie.CHANGED.value: '🔄',
            ChangelogKategorie.FIXED.value: '🐛',
            ChangelogKategorie.REMOVED.value: '🗑️',
        }
        prefix = kategorie_prefix.get(self.kategorie, '•')
        return f'- {prefix} {self.beschreibung}'
