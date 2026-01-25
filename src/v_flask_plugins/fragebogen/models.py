"""Fragebogen (Questionnaire) models.

Provides:
    - Fragebogen: Questionnaire definition with V2 schema (multi-page wizard)
    - FragebogenTeilnahme: Participant record with magic-link token
    - FragebogenAntwort: Individual question answers

Schema V2 (multi-page wizard):
{
    "version": 2,
    "seiten": [
        {
            "id": "s1",
            "titel": "Allgemeine Fragen",
            "hilfetext": "Optionaler Hilfetext",
            "fragen": [
                {
                    "id": "q1",
                    "typ": "text|dropdown|date|number|single_choice|...",
                    "frage": "Fragetext",
                    "pflicht": true,
                    "prefill": "teilnehmer.email",
                    "hilfetext": "Hilfe zur Frage",
                    "show_if": {"frage_id": "x", "equals": true}
                }
            ]
        }
    ]
}
"""

from __future__ import annotations

import secrets
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from v_flask.extensions import db

if TYPE_CHECKING:
    pass


class FragebogenStatus(Enum):
    """Status of a Fragebogen."""
    ENTWURF = 'entwurf'
    AKTIV = 'aktiv'
    GESCHLOSSEN = 'geschlossen'


class TeilnahmeStatus(Enum):
    """Status of a FragebogenTeilnahme."""
    EINGELADEN = 'eingeladen'
    GESTARTET = 'gestartet'
    ABGESCHLOSSEN = 'abgeschlossen'


class Fragebogen(db.Model):
    """Questionnaire definition.

    Stores the questionnaire structure using V2 schema (multi-page wizard).
    Supports versioning via vorgaenger_id chain.

    Attributes:
        titel: Display title of the questionnaire.
        beschreibung: Optional description text.
        definition_json: V2 schema with pages and questions.
        status: Current status (entwurf/aktiv/geschlossen).
        erlaubt_anonym: Whether anonymous participation is allowed.
        kontakt_felder_config: JSON config for additional contact fields.
    """
    __tablename__ = 'fragebogen'

    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(200), nullable=False)
    beschreibung = db.Column(db.Text)
    definition_json = db.Column(db.JSON, nullable=False, default=dict)
    status = db.Column(db.String(20), nullable=False, default=FragebogenStatus.ENTWURF.value)

    # Anonymous participation settings
    erlaubt_anonym = db.Column(db.Boolean, default=False, nullable=False)
    kontakt_felder_config = db.Column(db.JSON, nullable=True)

    # Creator reference
    erstellt_von_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

    # Status timestamps
    aktiviert_am = db.Column(db.DateTime)
    geschlossen_am = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Versioning: V1 -> V2 -> V3 chain
    vorgaenger_id = db.Column(db.Integer, db.ForeignKey('fragebogen.id'), nullable=True)
    version_nummer = db.Column(db.Integer, default=1, nullable=False)

    # Soft-delete via archiving
    archiviert = db.Column(db.Boolean, default=False, nullable=False)
    archiviert_am = db.Column(db.DateTime, nullable=True)

    # Relationships
    erstellt_von = db.relationship(
        'User',
        backref=db.backref('erstellte_frageboegen', lazy='dynamic')
    )
    teilnahmen = db.relationship(
        'FragebogenTeilnahme',
        back_populates='fragebogen',
        cascade='all, delete-orphan'
    )

    # Self-referential relationship for version chain
    vorgaenger = db.relationship(
        'Fragebogen',
        remote_side='Fragebogen.id',
        backref=db.backref('nachfolger', lazy='dynamic'),
        foreign_keys=[vorgaenger_id]
    )

    def __repr__(self) -> str:
        return f'<Fragebogen {self.titel}>'

    # =========================================================================
    # Schema Properties
    # =========================================================================

    @property
    def is_v2(self) -> bool:
        """Check if this fragebogen uses V2 schema (with pages)."""
        return self.definition_json and self.definition_json.get('version') == 2

    @property
    def seiten(self) -> list:
        """Get the list of pages (V2 only)."""
        if self.is_v2:
            return self.definition_json.get('seiten', [])
        return []

    @property
    def fragen(self) -> list:
        """Get all questions from all pages."""
        if not self.definition_json:
            return []

        if self.is_v2:
            alle_fragen = []
            for seite in self.definition_json.get('seiten', []):
                alle_fragen.extend(seite.get('fragen', []))
            return alle_fragen

        # Fallback for V1 (flat list)
        return self.definition_json.get('fragen', [])

    @property
    def fragen_mit_prefill(self) -> list:
        """Get all questions that have prefill configured."""
        return [f for f in self.fragen if f.get('prefill')]

    @property
    def anzahl_fragen(self) -> int:
        """Get number of questions."""
        return len(self.fragen)

    @property
    def anzahl_seiten(self) -> int:
        """Get number of pages."""
        if self.is_v2:
            return len(self.seiten)
        return 1 if self.fragen else 0

    # =========================================================================
    # Statistics
    # =========================================================================

    @property
    def anzahl_teilnehmer(self) -> int:
        """Get number of participants."""
        return len(self.teilnahmen)

    @property
    def anzahl_abgeschlossen(self) -> int:
        """Get number of completed participations."""
        return sum(
            1 for t in self.teilnahmen
            if t.status == TeilnahmeStatus.ABGESCHLOSSEN.value
        )

    @property
    def teilnehmer_ohne_einladung(self) -> int:
        """Count participants who haven't received invitation email."""
        return sum(
            1 for t in self.teilnahmen
            if t.einladung_gesendet_am is None
        )

    # =========================================================================
    # Status Properties
    # =========================================================================

    @property
    def is_entwurf(self) -> bool:
        return self.status == FragebogenStatus.ENTWURF.value

    @property
    def is_aktiv(self) -> bool:
        return self.status == FragebogenStatus.AKTIV.value

    @property
    def is_geschlossen(self) -> bool:
        return self.status == FragebogenStatus.GESCHLOSSEN.value

    @property
    def is_archiviert(self) -> bool:
        return self.archiviert

    # =========================================================================
    # Version Chain
    # =========================================================================

    @property
    def ist_neueste_version(self) -> bool:
        """Check if this is the newest version (has no successors)."""
        return self.nachfolger.count() == 0

    @property
    def version_kette(self) -> list:
        """Get the complete version chain, starting from V1."""
        # Navigate to V1 (root of the chain)
        root = self
        while root.vorgaenger:
            root = root.vorgaenger

        # Collect all versions forward
        chain = [root]
        current = root
        while current.nachfolger.first():
            current = current.nachfolger.first()
            chain.append(current)

        return chain

    # =========================================================================
    # Status Changes
    # =========================================================================

    def aktivieren(self) -> None:
        """Set status to AKTIV."""
        self.status = FragebogenStatus.AKTIV.value
        self.aktiviert_am = datetime.utcnow()

    def schliessen(self) -> None:
        """Set status to GESCHLOSSEN."""
        self.status = FragebogenStatus.GESCHLOSSEN.value
        self.geschlossen_am = datetime.utcnow()

    def reaktivieren(self) -> None:
        """Set status back to AKTIV from GESCHLOSSEN."""
        if self.status != FragebogenStatus.GESCHLOSSEN.value:
            raise ValueError('Nur geschlossene Fragebögen können reaktiviert werden')
        self.status = FragebogenStatus.AKTIV.value

    def archivieren(self) -> None:
        """Archive this Fragebogen (soft-delete)."""
        self.archiviert = True
        self.archiviert_am = datetime.utcnow()

    def dearchivieren(self) -> None:
        """Restore an archived Fragebogen."""
        self.archiviert = False
        self.archiviert_am = None

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'titel': self.titel,
            'beschreibung': self.beschreibung,
            'definition_json': self.definition_json,
            'status': self.status,
            'erlaubt_anonym': self.erlaubt_anonym,
            'kontakt_felder_config': self.kontakt_felder_config,
            'erstellt_von_id': self.erstellt_von_id,
            'erstellt_am': self.erstellt_am.isoformat() if self.erstellt_am else None,
            'aktiviert_am': self.aktiviert_am.isoformat() if self.aktiviert_am else None,
            'geschlossen_am': self.geschlossen_am.isoformat() if self.geschlossen_am else None,
            'anzahl_fragen': self.anzahl_fragen,
            'anzahl_seiten': self.anzahl_seiten,
            'anzahl_teilnehmer': self.anzahl_teilnehmer,
            'anzahl_abgeschlossen': self.anzahl_abgeschlossen,
            'version_nummer': self.version_nummer,
            'vorgaenger_id': self.vorgaenger_id,
            'ist_neueste_version': self.ist_neueste_version,
            'archiviert': self.archiviert,
            'archiviert_am': self.archiviert_am.isoformat() if self.archiviert_am else None,
        }


class FragebogenTeilnahme(db.Model):
    """Participation record for a questionnaire.

    Links a participant to a Fragebogen with a unique Magic-Link token.
    Supports both known participants (via teilnehmer_id) and anonymous
    participants (via kontakt_* fields).

    Attributes:
        fragebogen_id: Reference to the questionnaire.
        teilnehmer_id: Optional reference to participant entity.
        teilnehmer_typ: Type of participant (e.g., 'kunde', 'user', 'lead').
        token: Unique magic-link token for direct access.
        kontakt_email: Email for anonymous participants.
        kontakt_name: Name for anonymous participants.
        kontakt_zusatz: Additional contact fields (JSON).
    """
    __tablename__ = 'fragebogen_teilnahme'
    __table_args__ = (
        # Unique constraint for known participants per fragebogen
        db.UniqueConstraint(
            'fragebogen_id', 'teilnehmer_id', 'teilnehmer_typ',
            name='uq_fragebogen_teilnehmer'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    fragebogen_id = db.Column(
        db.Integer,
        db.ForeignKey('fragebogen.id'),
        nullable=False
    )

    # Flexible participant reference
    teilnehmer_id = db.Column(db.Integer, nullable=True)
    teilnehmer_typ = db.Column(db.String(50), nullable=True)

    # Magic-link token
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Status
    status = db.Column(
        db.String(20),
        nullable=False,
        default=TeilnahmeStatus.EINGELADEN.value
    )

    # Anonymous participant contact data
    kontakt_email = db.Column(db.String(255), nullable=True)
    kontakt_name = db.Column(db.String(255), nullable=True)
    kontakt_zusatz = db.Column(db.JSON, nullable=True)

    # Prefill snapshot for change detection
    prefill_snapshot_json = db.Column(db.JSON, nullable=True)

    # Timestamps
    eingeladen_am = db.Column(db.DateTime, default=datetime.utcnow)
    gestartet_am = db.Column(db.DateTime)
    abgeschlossen_am = db.Column(db.DateTime)
    einladung_gesendet_am = db.Column(db.DateTime)

    # Relationships
    fragebogen = db.relationship('Fragebogen', back_populates='teilnahmen')
    antworten = db.relationship(
        'FragebogenAntwort',
        back_populates='teilnahme',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<FragebogenTeilnahme fragebogen={self.fragebogen_id} token={self.token[:8]}...>'

    # =========================================================================
    # Factory Methods
    # =========================================================================

    @classmethod
    def create_for_teilnehmer(
        cls,
        fragebogen_id: int,
        teilnehmer_id: int,
        teilnehmer_typ: str
    ) -> 'FragebogenTeilnahme':
        """Create a new participation for a known participant.

        Args:
            fragebogen_id: The Fragebogen ID.
            teilnehmer_id: ID of the participant entity.
            teilnehmer_typ: Type of participant (e.g., 'kunde').

        Returns:
            FragebogenTeilnahme instance (not yet committed).
        """
        return cls(
            fragebogen_id=fragebogen_id,
            teilnehmer_id=teilnehmer_id,
            teilnehmer_typ=teilnehmer_typ,
            token=secrets.token_urlsafe(48)
        )

    @classmethod
    def create_anonymous(cls, fragebogen_id: int) -> 'FragebogenTeilnahme':
        """Create a new anonymous participation.

        Contact data will be collected during the wizard.

        Args:
            fragebogen_id: The Fragebogen ID.

        Returns:
            FragebogenTeilnahme instance (not yet committed).
        """
        return cls(
            fragebogen_id=fragebogen_id,
            teilnehmer_id=None,
            teilnehmer_typ=None,
            token=secrets.token_urlsafe(48)
        )

    @classmethod
    def get_by_token(cls, token: str) -> 'FragebogenTeilnahme | None':
        """Find participation by magic-link token.

        Args:
            token: The magic-link token.

        Returns:
            FragebogenTeilnahme if found, None otherwise.
        """
        return db.session.query(cls).filter_by(token=token).first()

    # =========================================================================
    # Status Properties
    # =========================================================================

    @property
    def is_eingeladen(self) -> bool:
        return self.status == TeilnahmeStatus.EINGELADEN.value

    @property
    def is_gestartet(self) -> bool:
        return self.status == TeilnahmeStatus.GESTARTET.value

    @property
    def is_abgeschlossen(self) -> bool:
        return self.status == TeilnahmeStatus.ABGESCHLOSSEN.value

    @property
    def is_anonym(self) -> bool:
        """Check if this is an anonymous participation."""
        return self.teilnehmer_id is None

    @property
    def display_name(self) -> str:
        """Get display name for the participant."""
        if self.kontakt_name:
            return self.kontakt_name
        if self.kontakt_email:
            return self.kontakt_email
        if self.teilnehmer_id:
            return f'{self.teilnehmer_typ}:{self.teilnehmer_id}'
        return 'Anonym'

    # =========================================================================
    # Status Changes
    # =========================================================================

    def starten(self) -> None:
        """Mark participation as started."""
        if self.is_eingeladen:
            self.status = TeilnahmeStatus.GESTARTET.value
            self.gestartet_am = datetime.utcnow()

    def abschliessen(self) -> None:
        """Mark participation as completed."""
        self.status = TeilnahmeStatus.ABGESCHLOSSEN.value
        self.abgeschlossen_am = datetime.utcnow()

    # =========================================================================
    # Answer Access
    # =========================================================================

    def get_antwort(self, frage_id: str) -> 'FragebogenAntwort | None':
        """Get answer for a specific question.

        Args:
            frage_id: The question ID from the schema.

        Returns:
            FragebogenAntwort if found, None otherwise.
        """
        for antwort in self.antworten:
            if antwort.frage_id == frage_id:
                return antwort
        return None

    def get_geaenderte_felder(self) -> list[dict]:
        """Compare prefill snapshot with answers, return changed fields.

        Returns:
            List of dicts with frage_id, prefill_key, original, neu.
        """
        if not self.prefill_snapshot_json:
            return []

        changes = []
        for frage in self.fragebogen.fragen_mit_prefill:
            prefill_key = frage.get('prefill')
            if not prefill_key:
                continue

            original = self.prefill_snapshot_json.get(prefill_key)
            antwort = self.get_antwort(frage['id'])

            if antwort:
                neue_value = antwort.value
                original_normalized = original if original else ''
                neue_normalized = neue_value if neue_value else ''

                if original_normalized != neue_normalized:
                    changes.append({
                        'frage_id': frage['id'],
                        'prefill_key': prefill_key,
                        'original': original,
                        'neu': neue_value
                    })

        return changes

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'fragebogen_id': self.fragebogen_id,
            'teilnehmer_id': self.teilnehmer_id,
            'teilnehmer_typ': self.teilnehmer_typ,
            'token': self.token,
            'status': self.status,
            'is_anonym': self.is_anonym,
            'display_name': self.display_name,
            'kontakt_email': self.kontakt_email,
            'kontakt_name': self.kontakt_name,
            'kontakt_zusatz': self.kontakt_zusatz,
            'eingeladen_am': self.eingeladen_am.isoformat() if self.eingeladen_am else None,
            'gestartet_am': self.gestartet_am.isoformat() if self.gestartet_am else None,
            'abgeschlossen_am': self.abgeschlossen_am.isoformat() if self.abgeschlossen_am else None,
            'einladung_gesendet_am': self.einladung_gesendet_am.isoformat() if self.einladung_gesendet_am else None,
        }


class FragebogenAntwort(db.Model):
    """Answer to a question in a Fragebogen.

    Stores the answer as JSON to support different question types:
    - single_choice: {"value": "Option A"}
    - multiple_choice: {"values": ["Option A", "Option C"]}
    - skala: {"value": 4}
    - text: {"value": "Free text answer"}
    - ja_nein: {"value": true}
    - date: {"value": "2024-01-15"}
    - number: {"value": 42}
    - dropdown: {"value": "Option B"} or {"value": "Sonstiges", "freitext": "Custom"}
    - url: {"value": "https://example.com"}

    Attributes:
        teilnahme_id: Reference to the participation record.
        frage_id: Question ID from the schema.
        antwort_json: The answer in type-specific JSON format.
    """
    __tablename__ = 'fragebogen_antwort'
    __table_args__ = (
        db.UniqueConstraint(
            'teilnahme_id', 'frage_id',
            name='uq_teilnahme_frage'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    teilnahme_id = db.Column(
        db.Integer,
        db.ForeignKey('fragebogen_teilnahme.id'),
        nullable=False
    )
    frage_id = db.Column(db.String(50), nullable=False)
    antwort_json = db.Column(db.JSON, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    teilnahme = db.relationship('FragebogenTeilnahme', back_populates='antworten')

    def __repr__(self) -> str:
        return f'<FragebogenAntwort teilnahme={self.teilnahme_id} frage={self.frage_id}>'

    @property
    def value(self):
        """Get the primary value from the answer.

        Returns:
            The value (for single-value types) or list of values (for multi-select).
        """
        if not self.antwort_json:
            return None
        return self.antwort_json.get('value') or self.antwort_json.get('values')

    @property
    def freitext(self) -> str | None:
        """Get the freitext value for dropdown questions with custom option."""
        if not self.antwort_json:
            return None
        return self.antwort_json.get('freitext')

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'teilnahme_id': self.teilnahme_id,
            'frage_id': self.frage_id,
            'antwort_json': self.antwort_json,
            'value': self.value,
            'freitext': self.freitext,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ParticipantSourceConfig(db.Model):
    """Configuration for participant data sources.

    Defines which model provides participant data for questionnaires,
    including field mappings for email, name, and optional fields like
    anrede (salutation) and titel (title).

    Field-Mapping Format:
    {
        "email": "email",                           # Simple field mapping
        "name": "firmierung",                       # Single field for name
        # OR composite name:
        "name": {"fields": ["vorname", "nachname"], "separator": " "},
        "anrede": "anrede",                         # Optional: Herr/Frau/Divers
        "titel": "titel"                            # Optional: Dr., Prof.
    }

    Greeting Template:
        Jinja2 template for personalized greetings.
        Example: "Sehr geehrte{{ 'r' if anrede == 'Herr' else '' }} {{ anrede }} {{ titel }} {{ name }}"

    Attributes:
        model_path: Full import path to the model (e.g., 'myapp.models.Kunde').
        display_name: Human-readable name for the source (e.g., 'Kunden').
        field_mapping: JSON mapping of standard fields to model attributes.
        greeting_template: Optional Jinja2 template for personalized greeting.
        query_filter: Optional JSON filter criteria for loading participants.
        is_default: Whether this is the default participant source.
        is_active: Whether this source is currently available.
    """
    __tablename__ = 'fragebogen_participant_source_config'

    id = db.Column(db.Integer, primary_key=True)

    # Model identification
    model_path = db.Column(db.String(255), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)

    # Field mapping (JSON)
    field_mapping = db.Column(db.JSON, nullable=False)

    # Optional: Greeting template with Jinja2 syntax
    greeting_template = db.Column(db.Text, nullable=True)

    # Optional: Query filter as JSON
    query_filter = db.Column(db.JSON, nullable=True)

    # Default source (only one can be default)
    is_default = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        server_default='0'  # SQLite compatibility
    )

    # Active flag
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        server_default='1'  # SQLite compatibility
    )

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<ParticipantSourceConfig {self.display_name} ({self.model_path})>'

    # =========================================================================
    # Query Methods
    # =========================================================================

    @classmethod
    def get_default(cls) -> 'ParticipantSourceConfig | None':
        """Get the default participant source."""
        return db.session.query(cls).filter_by(
            is_default=True,
            is_active=True
        ).first()

    @classmethod
    def get_for_type(cls, teilnehmer_typ: str) -> 'ParticipantSourceConfig | None':
        """Get config for a specific participant type.

        Args:
            teilnehmer_typ: The type identifier (derived from model name).

        Returns:
            Matching config or None.
        """
        # teilnehmer_typ is typically the model class name lowercase
        return db.session.query(cls).filter(
            cls.model_path.ilike(f'%{teilnehmer_typ}'),
            cls.is_active == True  # noqa: E712
        ).first()

    @classmethod
    def get_all_active(cls) -> list['ParticipantSourceConfig']:
        """Get all active participant sources."""
        return db.session.query(cls).filter_by(
            is_active=True
        ).order_by(cls.display_name).all()

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def get_type_identifier(self) -> str:
        """Extract type identifier from model path.

        Returns:
            Lowercase model class name (e.g., 'kunde' from 'myapp.models.Kunde').
        """
        return self.model_path.split('.')[-1].lower()

    def validate_field_mapping(self) -> list[str]:
        """Validate that field mapping contains required fields.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []
        if not self.field_mapping:
            errors.append('Field-Mapping ist erforderlich')
            return errors

        if 'email' not in self.field_mapping:
            errors.append('Field-Mapping muss "email" enthalten')
        if 'name' not in self.field_mapping:
            errors.append('Field-Mapping muss "name" enthalten')

        return errors

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'model_path': self.model_path,
            'display_name': self.display_name,
            'field_mapping': self.field_mapping,
            'greeting_template': self.greeting_template,
            'query_filter': self.query_filter,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'type_identifier': self.get_type_identifier(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
