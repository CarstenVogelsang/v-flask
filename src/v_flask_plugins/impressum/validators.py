"""Impressum validation for German legal requirements."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from v_flask.models import Betreiber


@dataclass
class ValidationResult:
    """Result of Impressum validation.

    Attributes:
        errors: List of missing required fields (Pflichtfelder).
        warnings: List of recommended but missing fields.
        is_valid: True if no errors (warnings are acceptable).
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if Impressum has all required fields."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


class ImpressumValidator:
    """Validates Impressum data for German legal compliance.

    Checks required fields according to § 5 TMG (Telemediengesetz)
    and provides warnings for recommended but optional information.

    Usage:
        from v_flask.models import Betreiber
        from v_flask_plugins.impressum.validators import ImpressumValidator

        betreiber = Betreiber.query.first()
        validator = ImpressumValidator(betreiber)

        result = validator.validate()
        if not result.is_valid:
            print("Errors:", result.errors)
        if result.has_warnings:
            print("Warnings:", result.warnings)
    """

    # Regex pattern for German USt-IdNr (DE + 9 digits)
    UST_IDNR_PATTERN = re.compile(r'^DE\d{9}$')

    def __init__(self, betreiber: Betreiber):
        """Initialize validator with Betreiber data.

        Args:
            betreiber: Betreiber instance to validate.
        """
        self.betreiber = betreiber

    def validate(self) -> ValidationResult:
        """Perform full validation of Impressum data.

        Returns:
            ValidationResult with errors and warnings.
        """
        result = ValidationResult()

        self._check_pflichtfelder(result)
        self._check_empfohlene_felder(result)
        self._check_format(result)

        return result

    def _check_pflichtfelder(self, result: ValidationResult) -> None:
        """Check mandatory fields required by § 5 TMG.

        Pflichtangaben nach § 5 TMG:
        - Name und Anschrift des Diensteanbieters
        - Vertretungsberechtigter bei juristischen Personen
        - Elektronische Kontaktaufnahme (E-Mail)
        - Handelsregister bei eingetragenen Unternehmen
        - USt-IdNr. wenn vorhanden
        """
        b = self.betreiber

        # 1. Firmenname
        if not b.name:
            result.errors.append('Firmenname fehlt (Pflichtangabe)')

        # 2. Vollständige Anschrift
        if not b.strasse:
            result.errors.append('Straße fehlt (Pflichtangabe)')
        if not b.plz:
            result.errors.append('Postleitzahl fehlt (Pflichtangabe)')
        if not b.ort:
            result.errors.append('Ort fehlt (Pflichtangabe)')

        # 3. E-Mail (elektronische Kontaktaufnahme ist Pflicht)
        if not b.email:
            result.errors.append('E-Mail-Adresse fehlt (Pflichtangabe)')

        # 4. Rechtsform und Vertretung für Kapitalgesellschaften
        if b.rechtsform:
            rechtsform_upper = b.rechtsform.upper()
            kapitalgesellschaften = ('GMBH', 'UG', 'AG', 'SE', 'GMBH & CO. KG')

            if any(rf in rechtsform_upper for rf in kapitalgesellschaften):
                if not b.geschaeftsfuehrer:
                    result.errors.append(
                        'Vertretungsberechtigter fehlt (Pflicht für Kapitalgesellschaften)'
                    )

        # 5. Handelsregister - Pflicht wenn eingetragen
        if b.handelsregister_nummer and not b.handelsregister_gericht:
            result.errors.append(
                'Registergericht fehlt (bei Angabe der Registernummer erforderlich)'
            )
        if b.handelsregister_gericht and not b.handelsregister_nummer:
            result.errors.append(
                'Registernummer fehlt (bei Angabe des Registergerichts erforderlich)'
            )

    def _check_empfohlene_felder(self, result: ValidationResult) -> None:
        """Check recommended fields that improve Impressum quality."""
        b = self.betreiber

        # Telefonnummer - empfohlen für Erreichbarkeit
        if not b.telefon:
            result.warnings.append(
                'Telefonnummer empfohlen (verbessert Erreichbarkeit)'
            )

        # USt-IdNr. - empfohlen wenn umsatzsteuerpflichtig
        if not b.ust_idnr:
            result.warnings.append(
                'USt-IdNr. empfohlen (falls umsatzsteuerpflichtig)'
            )

        # Handelsregister für Kapitalgesellschaften
        if b.rechtsform:
            rechtsform_upper = b.rechtsform.upper()
            if any(rf in rechtsform_upper for rf in ('GMBH', 'UG', 'AG')):
                if not b.handelsregister_nummer:
                    result.warnings.append(
                        'Handelsregistereintrag empfohlen (für Kapitalgesellschaften üblich)'
                    )

        # V.i.S.d.P. bei redaktionellen Inhalten
        show_visdp = b.get_impressum_option('show_visdp', False)
        if show_visdp and not b.inhaltlich_verantwortlich:
            result.warnings.append(
                'V.i.S.d.P. ist aktiviert, aber keine verantwortliche Person angegeben'
            )

    def _check_format(self, result: ValidationResult) -> None:
        """Validate format of specific fields."""
        b = self.betreiber

        # USt-IdNr. Format (DE + 9 Ziffern)
        if b.ust_idnr:
            # Allow spaces and normalize
            normalized = b.ust_idnr.replace(' ', '').upper()
            if not self.UST_IDNR_PATTERN.match(normalized):
                result.warnings.append(
                    'USt-IdNr. Format prüfen (erwartet: DE + 9 Ziffern, z.B. DE123456789)'
                )

        # PLZ Format für Deutschland (5 Ziffern)
        if b.plz and (b.land is None or b.land == 'Deutschland'):
            if not re.match(r'^\d{5}$', b.plz.strip()):
                result.warnings.append(
                    'PLZ Format prüfen (für Deutschland: 5 Ziffern)'
                )

        # E-Mail Format (basic check)
        if b.email and '@' not in b.email:
            result.errors.append('E-Mail-Adresse ungültig (kein @ enthalten)')

    def get_completeness_score(self) -> int:
        """Calculate Impressum completeness as percentage.

        Returns:
            Percentage (0-100) of filled relevant fields.
        """
        b = self.betreiber
        fields_to_check = [
            b.name,
            b.strasse,
            b.plz,
            b.ort,
            b.email,
            b.telefon,
            b.rechtsform,
            b.geschaeftsfuehrer,
            b.handelsregister_gericht,
            b.handelsregister_nummer,
            b.ust_idnr,
        ]

        filled = sum(1 for f in fields_to_check if f)
        total = len(fields_to_check)

        return int((filled / total) * 100)
