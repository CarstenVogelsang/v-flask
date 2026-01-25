"""Fragebogen Service for questionnaire management.

Handles:
- Fragebogen CRUD operations
- JSON definition validation (V2 schema)
- Teilnehmer (participant) management
- Einladungs-E-Mail sending
- Antwort (answer) storage
- Auswertung (statistics)
"""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from v_flask.extensions import db
from v_flask_plugins.fragebogen.models import (
    Fragebogen,
    FragebogenAntwort,
    FragebogenStatus,
    FragebogenTeilnahme,
)

if TYPE_CHECKING:
    pass


# Valid question types (V2 schema)
VALID_FRAGE_TYPEN = [
    'single_choice',
    'multiple_choice',
    'dropdown',
    'skala',
    'text',
    'ja_nein',
    'date',
    'number',
    'url',
    'group',
    'table',
]

# Valid show_if operators
VALID_SHOW_IF_OPERATORS = ['equals', 'not_equals', 'is_set', 'is_not_set']


@dataclass
class ValidationResult:
    """Result of JSON definition validation."""
    valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class EinladungResult:
    """Result of sending invitations."""
    success: bool
    sent_count: int = 0
    failed_count: int = 0
    errors: list[str] = field(default_factory=list)


class TeilnehmerResolver(ABC):
    """Abstract interface for resolving participant data.

    Host applications can implement this to provide participant data
    for prefill and email sending.

    Example:
        class KundeResolver(TeilnehmerResolver):
            def get_email(self, teilnehmer_id, teilnehmer_typ):
                kunde = Kunde.query.get(teilnehmer_id)
                return kunde.email if kunde else None

            def get_name(self, teilnehmer_id, teilnehmer_typ):
                kunde = Kunde.query.get(teilnehmer_id)
                return kunde.firmierung if kunde else None

            def get_prefill_value(self, teilnehmer_id, teilnehmer_typ, prefill_key):
                kunde = Kunde.query.get(teilnehmer_id)
                if prefill_key == 'kunde.firmierung':
                    return kunde.firmierung
                ...
    """

    @abstractmethod
    def get_email(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get email address for a participant."""
        ...

    @abstractmethod
    def get_name(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get display name for a participant."""
        ...

    def get_prefill_value(
        self,
        teilnehmer_id: int,
        teilnehmer_typ: str,
        prefill_key: str
    ) -> Any | None:
        """Get prefill value for a field.

        Override to provide prefill values for known participants.
        """
        return None


class NullTeilnehmerResolver(TeilnehmerResolver):
    """Null implementation that returns None for all lookups."""

    def get_email(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        return None

    def get_name(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        return None


class DynamicTeilnehmerResolverAdapter(TeilnehmerResolver):
    """Adapter that wraps DynamicParticipantResolver to TeilnehmerResolver interface.

    This adapter allows the DynamicParticipantResolver (which uses
    ParticipantSourceConfig) to be used anywhere a TeilnehmerResolver is expected.

    The adapter provides lazy initialization to avoid circular imports and
    database access during module load.
    """

    def __init__(self):
        """Initialize the adapter with lazy resolver loading."""
        self._resolver = None

    def _get_resolver(self):
        """Lazily load the dynamic resolver."""
        if self._resolver is None:
            from v_flask_plugins.fragebogen.services.participant_source import (
                get_dynamic_participant_resolver
            )
            self._resolver = get_dynamic_participant_resolver()
        return self._resolver

    def get_email(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get email via dynamic resolver."""
        return self._get_resolver().get_email(teilnehmer_id, teilnehmer_typ)

    def get_name(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get name via dynamic resolver."""
        return self._get_resolver().get_name(teilnehmer_id, teilnehmer_typ)

    def get_prefill_value(
        self,
        teilnehmer_id: int,
        teilnehmer_typ: str,
        prefill_key: str
    ) -> Any | None:
        """Get prefill value via dynamic resolver."""
        return self._get_resolver().get_prefill_value(
            teilnehmer_id, teilnehmer_typ, prefill_key
        )

    def get_greeting(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        """Get personalized greeting via dynamic resolver.

        Note: This method is an extension beyond the base TeilnehmerResolver interface.
        """
        return self._get_resolver().get_greeting(teilnehmer_id, teilnehmer_typ)


class FragebogenService:
    """Service for managing Fragebögen (questionnaires).

    Provides CRUD operations, validation, participant management,
    and statistics for questionnaires.
    """

    def __init__(self, teilnehmer_resolver: TeilnehmerResolver | None = None):
        """Initialize the service.

        Args:
            teilnehmer_resolver: Optional resolver for participant data.
                                 Defaults to NullTeilnehmerResolver.
        """
        self._teilnehmer_resolver = teilnehmer_resolver or NullTeilnehmerResolver()

    def set_teilnehmer_resolver(self, resolver: TeilnehmerResolver) -> None:
        """Set the participant resolver.

        Args:
            resolver: TeilnehmerResolver implementation.
        """
        self._teilnehmer_resolver = resolver

    # =========================================================================
    # Validation
    # =========================================================================

    def validate_definition(self, definition: dict[str, Any]) -> ValidationResult:
        """Validate a Fragebogen JSON definition (V2 schema).

        V2 Schema:
        {
            "version": 2,
            "seiten": [
                {
                    "id": "s1",
                    "titel": "Abschnitt 1",
                    "hilfetext": "Optional",
                    "fragen": [
                        {"id": "q1", "typ": "dropdown", "frage": "...", ...}
                    ]
                }
            ]
        }

        Args:
            definition: The JSON definition dict.

        Returns:
            ValidationResult with valid flag and errors.
        """
        if not isinstance(definition, dict):
            return ValidationResult(valid=False, errors=['Definition muss ein Objekt sein'])

        version = definition.get('version', 2)
        if version != 2:
            return ValidationResult(
                valid=False,
                errors=['Nur V2 Schema wird unterstützt. Bitte "version": 2 setzen.']
            )

        return self._validate_definition_v2(definition)

    def _validate_definition_v2(self, definition: dict[str, Any]) -> ValidationResult:
        """Validate V2 schema (page-based)."""
        errors = []

        if 'seiten' not in definition:
            return ValidationResult(valid=False, errors=['Feld "seiten" fehlt'])

        seiten = definition['seiten']
        if not isinstance(seiten, list):
            return ValidationResult(valid=False, errors=['"seiten" muss eine Liste sein'])

        if len(seiten) == 0:
            return ValidationResult(valid=False, errors=['Mindestens eine Seite erforderlich'])

        seen_ids: set[str] = set()
        seen_seiten_ids: set[str] = set()
        total_fragen = 0

        for si, seite in enumerate(seiten):
            seite_prefix = f'Seite {si + 1}'

            if not isinstance(seite, dict):
                errors.append(f'{seite_prefix}: Muss ein Objekt sein')
                continue

            # Validate seite fields
            if 'id' not in seite:
                errors.append(f'{seite_prefix}: Feld "id" fehlt')
            elif seite['id'] in seen_seiten_ids:
                errors.append(f'{seite_prefix}: ID "{seite["id"]}" ist doppelt')
            else:
                seen_seiten_ids.add(seite['id'])

            if 'titel' not in seite:
                errors.append(f'{seite_prefix}: Feld "titel" fehlt')

            # Validate fragen within seite
            fragen = seite.get('fragen', [])
            if not isinstance(fragen, list):
                errors.append(f'{seite_prefix}: "fragen" muss eine Liste sein')
                continue

            for fi, frage in enumerate(fragen):
                frage_prefix = f'{seite_prefix}, Frage {fi + 1}'
                frage_errors = self._validate_frage(frage, frage_prefix, seen_ids)
                errors.extend(frage_errors)
                total_fragen += 1

        if total_fragen == 0:
            errors.append('Mindestens eine Frage erforderlich')

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def _validate_frage(
        self,
        frage: dict[str, Any],
        prefix: str,
        seen_ids: set[str]
    ) -> list[str]:
        """Validate a single question."""
        errors = []

        if not isinstance(frage, dict):
            return [f'{prefix}: Muss ein Objekt sein']

        # Required fields
        if 'id' not in frage:
            errors.append(f'{prefix}: Feld "id" fehlt')
        elif frage['id'] in seen_ids:
            errors.append(f'{prefix}: ID "{frage["id"]}" ist doppelt')
        else:
            seen_ids.add(frage['id'])

        if 'typ' not in frage:
            errors.append(f'{prefix}: Feld "typ" fehlt')
        elif frage['typ'] not in VALID_FRAGE_TYPEN:
            errors.append(f'{prefix}: Ungültiger Typ "{frage["typ"]}"')

        typ = frage.get('typ')

        # "frage" field is optional for group type
        if typ != 'group' and 'frage' not in frage:
            errors.append(f'{prefix}: Feld "frage" (Fragetext) fehlt')

        # Type-specific validation
        errors.extend(self._validate_frage_type_specific(frage, prefix, typ))

        # show_if validation
        if 'show_if' in frage:
            errors.extend(self._validate_show_if(frage['show_if'], prefix))

        return errors

    def _validate_frage_type_specific(
        self,
        frage: dict[str, Any],
        prefix: str,
        typ: str | None
    ) -> list[str]:
        """Validate type-specific fields."""
        errors = []

        if typ in ['single_choice', 'multiple_choice', 'dropdown']:
            if 'optionen' not in frage:
                errors.append(f'{prefix}: Feld "optionen" fehlt für {typ}')
            elif not isinstance(frage['optionen'], list) or len(frage['optionen']) < 2:
                errors.append(f'{prefix}: Mindestens 2 Optionen erforderlich')

        elif typ == 'skala':
            if 'min' not in frage or 'max' not in frage:
                errors.append(f'{prefix}: Felder "min" und "max" erforderlich')
            elif not isinstance(frage.get('min'), int) or not isinstance(frage.get('max'), int):
                errors.append(f'{prefix}: "min" und "max" müssen Zahlen sein')
            elif frage['min'] >= frage['max']:
                errors.append(f'{prefix}: "min" muss kleiner als "max" sein')

        elif typ == 'number':
            if 'min' in frage and not isinstance(frage['min'], (int, float)):
                errors.append(f'{prefix}: "min" muss eine Zahl sein')
            if 'max' in frage and not isinstance(frage['max'], (int, float)):
                errors.append(f'{prefix}: "max" muss eine Zahl sein')

        elif typ == 'group':
            if 'fields' not in frage:
                errors.append(f'{prefix}: Feld "fields" fehlt für group')
            elif not isinstance(frage['fields'], list) or len(frage['fields']) == 0:
                errors.append(f'{prefix}: Mindestens ein Feld in "fields" erforderlich')

        elif typ == 'table':
            if 'columns' not in frage:
                errors.append(f'{prefix}: Feld "columns" fehlt für table')
            elif not isinstance(frage['columns'], list) or len(frage['columns']) == 0:
                errors.append(f'{prefix}: Mindestens eine Spalte erforderlich')

        return errors

    def _validate_show_if(self, show_if: Any, prefix: str) -> list[str]:
        """Validate show_if condition."""
        errors = []

        if not isinstance(show_if, dict):
            return [f'{prefix}: "show_if" muss ein Objekt sein']

        if 'frage_id' not in show_if:
            errors.append(f'{prefix}: "show_if.frage_id" fehlt')

        # Check for valid operator
        has_operator = any(op in show_if for op in VALID_SHOW_IF_OPERATORS)
        if not has_operator:
            errors.append(
                f'{prefix}: "show_if" braucht einen Operator '
                f'(equals, not_equals, is_set, is_not_set)'
            )

        return errors

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_fragebogen(
        self,
        titel: str,
        beschreibung: str | None,
        definition: dict[str, Any],
        erstellt_von_id: int,
        erlaubt_anonym: bool = False,
        kontakt_felder_config: dict[str, Any] | None = None
    ) -> Fragebogen:
        """Create a new Fragebogen.

        Args:
            titel: Title of the questionnaire.
            beschreibung: Optional description.
            definition: V2 JSON definition with questions.
            erstellt_von_id: Creator user ID.
            erlaubt_anonym: Whether anonymous participation is allowed.
            kontakt_felder_config: Configuration for additional contact fields.

        Returns:
            Created Fragebogen instance.
        """
        fragebogen = Fragebogen(
            titel=titel,
            beschreibung=beschreibung,
            definition_json=definition,
            status=FragebogenStatus.ENTWURF.value,
            erstellt_von_id=erstellt_von_id,
            erlaubt_anonym=erlaubt_anonym,
            kontakt_felder_config=kontakt_felder_config,
        )
        db.session.add(fragebogen)
        db.session.commit()
        return fragebogen

    def update_fragebogen(
        self,
        fragebogen: Fragebogen,
        titel: str | None = None,
        beschreibung: str | None = None,
        definition: dict[str, Any] | None = None,
        erlaubt_anonym: bool | None = None,
        kontakt_felder_config: dict[str, Any] | None = None
    ) -> Fragebogen:
        """Update a Fragebogen (only in ENTWURF status).

        Args:
            fragebogen: The Fragebogen to update.
            titel: New title (optional).
            beschreibung: New description (optional).
            definition: New JSON definition (optional).
            erlaubt_anonym: New anonymous setting (optional).
            kontakt_felder_config: New contact fields config (optional).

        Returns:
            Updated Fragebogen.

        Raises:
            ValueError: If Fragebogen is not in ENTWURF status.
        """
        if not fragebogen.is_entwurf:
            raise ValueError('Fragebogen kann nur im Entwurf-Status bearbeitet werden')

        if titel is not None:
            fragebogen.titel = titel
        if beschreibung is not None:
            fragebogen.beschreibung = beschreibung
        if definition is not None:
            fragebogen.definition_json = definition
        if erlaubt_anonym is not None:
            fragebogen.erlaubt_anonym = erlaubt_anonym
        if kontakt_felder_config is not None:
            fragebogen.kontakt_felder_config = kontakt_felder_config

        db.session.commit()
        return fragebogen

    def duplicate_fragebogen(
        self,
        fragebogen: Fragebogen,
        user_id: int,
        new_titel: str | None = None
    ) -> Fragebogen:
        """Create a new version of a Fragebogen in ENTWURF status.

        Creates a version chain: V1 → V2 → V3, etc.
        Only the newest version can be duplicated.

        Args:
            fragebogen: Source fragebogen (must be newest version).
            user_id: ID of user creating the copy.
            new_titel: Optional custom title.

        Returns:
            New Fragebogen in ENTWURF status.

        Raises:
            ValueError: If trying to duplicate a non-newest version.
        """
        if not fragebogen.ist_neueste_version:
            newest = fragebogen.nachfolger.first()
            raise ValueError(
                f"Nur die neueste Version kann dupliziert werden. "
                f"Bitte Version {newest.version_nummer} verwenden."
            )

        titel = new_titel or fragebogen.titel
        definition_copy = copy.deepcopy(fragebogen.definition_json)

        new_fragebogen = Fragebogen(
            titel=titel,
            beschreibung=fragebogen.beschreibung,
            definition_json=definition_copy,
            status=FragebogenStatus.ENTWURF.value,
            erstellt_von_id=user_id,
            erlaubt_anonym=fragebogen.erlaubt_anonym,
            kontakt_felder_config=fragebogen.kontakt_felder_config,
            vorgaenger_id=fragebogen.id,
            version_nummer=fragebogen.version_nummer + 1
        )
        db.session.add(new_fragebogen)
        db.session.commit()

        return new_fragebogen

    # =========================================================================
    # Participant Management
    # =========================================================================

    def add_teilnehmer(
        self,
        fragebogen: Fragebogen,
        teilnehmer_id: int,
        teilnehmer_typ: str
    ) -> FragebogenTeilnahme:
        """Add a participant to a Fragebogen.

        Args:
            fragebogen: The Fragebogen.
            teilnehmer_id: ID of the participant entity.
            teilnehmer_typ: Type of participant (e.g., 'kunde', 'user').

        Returns:
            Created FragebogenTeilnahme.

        Raises:
            ValueError: If participant has no email or is already added.
        """
        # Check if email is available
        email = self._teilnehmer_resolver.get_email(teilnehmer_id, teilnehmer_typ)
        if not email:
            raise ValueError(
                f'{teilnehmer_typ}:{teilnehmer_id}: Keine E-Mail-Adresse hinterlegt'
            )

        # Check if already exists
        existing = db.session.query(FragebogenTeilnahme).filter_by(
            fragebogen_id=fragebogen.id,
            teilnehmer_id=teilnehmer_id,
            teilnehmer_typ=teilnehmer_typ
        ).first()

        if existing:
            raise ValueError(f'{teilnehmer_typ}:{teilnehmer_id} ist bereits Teilnehmer')

        teilnahme = FragebogenTeilnahme.create_for_teilnehmer(
            fragebogen_id=fragebogen.id,
            teilnehmer_id=teilnehmer_id,
            teilnehmer_typ=teilnehmer_typ
        )
        db.session.add(teilnahme)
        db.session.commit()
        return teilnahme

    def create_anonymous_teilnahme(self, fragebogen: Fragebogen) -> FragebogenTeilnahme:
        """Create an anonymous participation for a Fragebogen.

        Contact data will be collected during the wizard.

        Args:
            fragebogen: The Fragebogen.

        Returns:
            Created FragebogenTeilnahme with generated token.

        Raises:
            ValueError: If anonymous participation is not allowed.
        """
        if not fragebogen.erlaubt_anonym:
            raise ValueError('Anonyme Teilnahme ist für diesen Fragebogen nicht erlaubt')

        teilnahme = FragebogenTeilnahme.create_anonymous(fragebogen.id)
        db.session.add(teilnahme)
        db.session.commit()
        return teilnahme

    def remove_teilnehmer(self, teilnahme: FragebogenTeilnahme) -> None:
        """Remove a participant (only if EINGELADEN and no email sent).

        Args:
            teilnahme: The participation to remove.

        Raises:
            ValueError: If participation cannot be removed.
        """
        if teilnahme.einladung_gesendet_am:
            raise ValueError('Teilnehmer hat bereits eine Einladung erhalten')
        if not teilnahme.is_eingeladen:
            raise ValueError('Teilnehmer hat bereits begonnen')

        db.session.delete(teilnahme)
        db.session.commit()

    def get_teilnahme_by_token(self, token: str) -> FragebogenTeilnahme | None:
        """Get a participation by its magic-link token.

        Args:
            token: The magic-link token.

        Returns:
            FragebogenTeilnahme or None.
        """
        return FragebogenTeilnahme.get_by_token(token)

    # =========================================================================
    # Email Sending
    # =========================================================================

    def send_einladungen(
        self,
        fragebogen: Fragebogen,
        teilnahmen: list[FragebogenTeilnahme] | None = None,
        is_resend: bool = False
    ) -> EinladungResult:
        """Send invitation emails to participants.

        Args:
            fragebogen: The Fragebogen.
            teilnahmen: Specific participations (default: all unsent).
            is_resend: If True, allows resending.

        Returns:
            EinladungResult with counts.
        """
        from flask import current_app, url_for

        from v_flask.services import get_email_service

        if not fragebogen.is_aktiv:
            return EinladungResult(
                success=False,
                errors=['Fragebogen muss aktiv sein um Einladungen zu senden']
            )

        email_service = get_email_service()
        if not email_service.is_configured:
            return EinladungResult(
                success=False,
                errors=['E-Mail-Service ist nicht konfiguriert']
            )

        # Get participants to invite
        if teilnahmen is None:
            teilnahmen = [
                t for t in fragebogen.teilnahmen
                if t.einladung_gesendet_am is None and not t.is_anonym
            ]

        if not teilnahmen:
            return EinladungResult(
                success=True,
                sent_count=0,
                errors=['Keine Teilnehmer zum Einladen gefunden']
            )

        sent_count = 0
        failed_count = 0
        errors = []

        for teilnahme in teilnahmen:
            # Get participant info via resolver
            to_email = self._teilnehmer_resolver.get_email(
                teilnahme.teilnehmer_id,
                teilnahme.teilnehmer_typ
            )
            to_name = self._teilnehmer_resolver.get_name(
                teilnahme.teilnehmer_id,
                teilnahme.teilnehmer_typ
            ) or to_email

            if not to_email:
                errors.append(
                    f'{teilnahme.teilnehmer_typ}:{teilnahme.teilnehmer_id}: '
                    f'Keine E-Mail-Adresse'
                )
                failed_count += 1
                continue

            # Generate magic URL
            try:
                magic_url = url_for(
                    'fragebogen_public.wizard',
                    token=teilnahme.token,
                    _external=True
                )
            except RuntimeError:
                # Outside request context - use config
                base_url = current_app.config.get('SERVER_NAME', 'localhost:5000')
                magic_url = f"https://{base_url}/fragebogen/t/{teilnahme.token}"

            result = email_service.send_fragebogen_einladung(
                to_email=to_email,
                to_name=to_name,
                fragebogen_titel=fragebogen.titel,
                magic_url=magic_url
            )

            if result.success:
                teilnahme.einladung_gesendet_am = datetime.utcnow()
                sent_count += 1
            else:
                errors.append(
                    f'{teilnahme.teilnehmer_typ}:{teilnahme.teilnehmer_id}: {result.error}'
                )
                failed_count += 1

        db.session.commit()

        return EinladungResult(
            success=failed_count == 0,
            sent_count=sent_count,
            failed_count=failed_count,
            errors=errors if errors else []
        )

    # =========================================================================
    # Answer Management
    # =========================================================================

    def save_antwort(
        self,
        teilnahme: FragebogenTeilnahme,
        frage_id: str,
        antwort_json: dict[str, Any]
    ) -> FragebogenAntwort:
        """Save or update an answer for a question.

        Args:
            teilnahme: The participation.
            frage_id: The question ID.
            antwort_json: The answer data.

        Returns:
            The created/updated FragebogenAntwort.

        Raises:
            ValueError: If Fragebogen is not active or already completed.
        """
        if not teilnahme.fragebogen.is_aktiv:
            raise ValueError('Fragebogen ist nicht mehr aktiv')

        if teilnahme.is_abgeschlossen:
            raise ValueError('Teilnahme ist bereits abgeschlossen')

        # Start participation if not yet started
        if teilnahme.is_eingeladen:
            teilnahme.starten()
            # Create prefill snapshot for change detection
            if teilnahme.fragebogen.is_v2 and not teilnahme.prefill_snapshot_json:
                self._create_prefill_snapshot(teilnahme)

        # Check if answer exists
        antwort = db.session.query(FragebogenAntwort).filter_by(
            teilnahme_id=teilnahme.id,
            frage_id=frage_id
        ).first()

        if antwort:
            antwort.antwort_json = antwort_json
        else:
            antwort = FragebogenAntwort(
                teilnahme_id=teilnahme.id,
                frage_id=frage_id,
                antwort_json=antwort_json
            )
            db.session.add(antwort)

        db.session.commit()
        return antwort

    def save_kontakt_daten(
        self,
        teilnahme: FragebogenTeilnahme,
        email: str,
        name: str,
        zusatz: dict[str, Any] | None = None
    ) -> None:
        """Save contact data for anonymous participation.

        Args:
            teilnahme: The anonymous participation.
            email: Contact email (required).
            name: Contact name (required).
            zusatz: Additional contact fields.

        Raises:
            ValueError: If participation is not anonymous.
        """
        if not teilnahme.is_anonym:
            raise ValueError('Kontaktdaten nur für anonyme Teilnahmen')

        teilnahme.kontakt_email = email
        teilnahme.kontakt_name = name
        teilnahme.kontakt_zusatz = zusatz
        db.session.commit()

    def complete_teilnahme(self, teilnahme: FragebogenTeilnahme) -> bool:
        """Mark a participation as completed.

        Validates that all required questions are answered.

        Args:
            teilnahme: The participation to complete.

        Returns:
            True if completed successfully.

        Raises:
            ValueError: If required questions are not answered.
        """
        fragebogen = teilnahme.fragebogen

        # Validate anonymous participation has contact data
        if teilnahme.is_anonym:
            if not teilnahme.kontakt_email or not teilnahme.kontakt_name:
                raise ValueError('Kontaktdaten sind erforderlich')

        # Build answer lookup for show_if evaluation
        antworten = {a.frage_id: a.value for a in teilnahme.antworten}

        # Check required questions
        missing = []
        for frage in fragebogen.fragen:
            if not frage.get('pflicht', False):
                continue

            # Check if question is visible (show_if condition met)
            if not self._is_frage_visible(frage, antworten):
                continue

            antwort = teilnahme.get_antwort(frage['id'])
            if not antwort or not antwort.value:
                missing.append(frage.get('frage', frage['id']))

        if missing:
            raise ValueError(
                f'Pflichtfragen nicht beantwortet: {", ".join(missing[:3])}...'
            )

        teilnahme.abschliessen()
        db.session.commit()
        return True

    def _is_frage_visible(
        self,
        frage: dict[str, Any],
        antworten: dict[str, Any]
    ) -> bool:
        """Check if a question should be visible based on show_if condition."""
        show_if = frage.get('show_if')
        if not show_if:
            return True

        ref_frage_id = show_if.get('frage_id')
        if not ref_frage_id:
            return True

        ref_value = antworten.get(ref_frage_id)

        if 'equals' in show_if:
            return ref_value == show_if['equals']

        if 'not_equals' in show_if:
            return ref_value != show_if['not_equals']

        if 'is_set' in show_if:
            return ref_value is not None and ref_value != ''

        if 'is_not_set' in show_if:
            return ref_value is None or ref_value == ''

        return True

    # =========================================================================
    # Prefill
    # =========================================================================

    def get_prefill_values(
        self,
        fragebogen: Fragebogen,
        teilnahme: FragebogenTeilnahme
    ) -> dict[str, Any]:
        """Get prefill values for a participation.

        For known participants, uses TeilnehmerResolver.
        For anonymous participants, returns empty dict.

        Args:
            fragebogen: The Fragebogen.
            teilnahme: The participation.

        Returns:
            Dict mapping prefill keys to their values.
        """
        if teilnahme.is_anonym:
            return {}

        prefill_values = {}
        for frage in fragebogen.fragen_mit_prefill:
            prefill_key = frage.get('prefill')
            if not prefill_key:
                continue

            value = self._teilnehmer_resolver.get_prefill_value(
                teilnahme.teilnehmer_id,
                teilnahme.teilnehmer_typ,
                prefill_key
            )
            prefill_values[prefill_key] = value

        return prefill_values

    def _create_prefill_snapshot(self, teilnahme: FragebogenTeilnahme) -> dict[str, Any]:
        """Create and save a snapshot of prefill values for change detection."""
        fragebogen = teilnahme.fragebogen

        if not fragebogen.is_v2 or not fragebogen.fragen_mit_prefill:
            return {}

        snapshot = self.get_prefill_values(fragebogen, teilnahme)
        teilnahme.prefill_snapshot_json = snapshot
        db.session.commit()

        return snapshot

    def get_initial_antworten(
        self,
        fragebogen: Fragebogen,
        teilnahme: FragebogenTeilnahme
    ) -> dict[str, dict[str, Any]]:
        """Get initial answer values for form pre-population.

        Args:
            fragebogen: The Fragebogen.
            teilnahme: The participation.

        Returns:
            Dict mapping frage_id to answer dict.
        """
        if not fragebogen.is_v2 or teilnahme.is_anonym:
            return {}

        initial = {}
        for frage in fragebogen.fragen_mit_prefill:
            frage_id = frage.get('id')
            prefill_key = frage.get('prefill')

            if prefill_key:
                value = self._teilnehmer_resolver.get_prefill_value(
                    teilnahme.teilnehmer_id,
                    teilnahme.teilnehmer_typ,
                    prefill_key
                )
                if value is not None:
                    initial[frage_id] = {'value': value}

        return initial

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_auswertung(self, fragebogen: Fragebogen) -> dict[str, Any]:
        """Get statistics and summary for a Fragebogen.

        Args:
            fragebogen: The Fragebogen.

        Returns:
            Dict with statistics per question.
        """
        auswertung = {
            'fragebogen_id': fragebogen.id,
            'titel': fragebogen.titel,
            'status': fragebogen.status,
            'teilnehmer_gesamt': fragebogen.anzahl_teilnehmer,
            'teilnehmer_abgeschlossen': fragebogen.anzahl_abgeschlossen,
            'fragen': []
        }

        # Get all completed answers
        abgeschlossene = [t for t in fragebogen.teilnahmen if t.is_abgeschlossen]

        for frage in fragebogen.fragen:
            frage_stats = {
                'id': frage['id'],
                'typ': frage['typ'],
                'frage': frage.get('frage', frage['id']),
                'antworten_count': 0,
                'statistik': {}
            }

            # Collect answers for this question
            answers = []
            for teilnahme in abgeschlossene:
                antwort = teilnahme.get_antwort(frage['id'])
                if antwort and antwort.value is not None:
                    answers.append(antwort.value)
                    frage_stats['antworten_count'] += 1

            # Calculate statistics based on type
            frage_stats['statistik'] = self._calculate_frage_statistik(
                frage['typ'], answers
            )

            auswertung['fragen'].append(frage_stats)

        return auswertung

    def _calculate_frage_statistik(
        self,
        typ: str,
        answers: list[Any]
    ) -> dict[str, Any]:
        """Calculate statistics for a question based on its type."""
        if typ in ['single_choice', 'ja_nein', 'dropdown']:
            counts = {}
            for a in answers:
                key = str(a)
                counts[key] = counts.get(key, 0) + 1
            return {'typ': 'verteilung', 'werte': counts}

        elif typ == 'multiple_choice':
            counts = {}
            for a in answers:
                if isinstance(a, list):
                    for item in a:
                        counts[item] = counts.get(item, 0) + 1
            return {'typ': 'verteilung_mehrfach', 'werte': counts}

        elif typ == 'skala':
            if answers:
                numeric = [
                    int(a) for a in answers
                    if isinstance(a, (int, float, str)) and str(a).isdigit()
                ]
                if numeric:
                    return {
                        'typ': 'skala',
                        'durchschnitt': sum(numeric) / len(numeric),
                        'min': min(numeric),
                        'max': max(numeric),
                        'verteilung': {str(v): numeric.count(v) for v in set(numeric)}
                    }
            return {}

        elif typ == 'text':
            return {'typ': 'text', 'antworten': answers}

        return {}


# =============================================================================
# Singleton
# =============================================================================

_fragebogen_service: FragebogenService | None = None


def get_fragebogen_service() -> FragebogenService:
    """Get the fragebogen service singleton.

    Automatically configures DynamicTeilnehmerResolverAdapter if
    ParticipantSourceConfig entries exist in the database.
    """
    global _fragebogen_service
    if _fragebogen_service is None:
        _fragebogen_service = FragebogenService()

        # Try to use dynamic resolver if configs exist
        try:
            from v_flask_plugins.fragebogen.models import ParticipantSourceConfig
            if ParticipantSourceConfig.get_all_active():
                _fragebogen_service.set_teilnehmer_resolver(
                    DynamicTeilnehmerResolverAdapter()
                )
        except Exception:
            # Fallback to NullTeilnehmerResolver (default)
            pass

    return _fragebogen_service
