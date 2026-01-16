"""Validators for the Datenschutz plugin.

Validates DatenschutzConfig for completeness and DSGVO compliance.
"""

from dataclasses import dataclass, field

from v_flask_plugins.datenschutz.bausteine import get_all_bausteine, get_baustein_by_id
from v_flask_plugins.datenschutz.models import DatenschutzConfig


@dataclass
class ValidationResult:
    """Result of privacy policy validation.

    Attributes:
        errors: List of critical errors (missing mandatory fields)
        warnings: List of recommendations (optional but recommended fields)
        unconfigured_services: List of detected but not configured services
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unconfigured_services: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid (no critical errors)."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    @property
    def has_unconfigured(self) -> bool:
        """Check if there are unconfigured detected services."""
        return len(self.unconfigured_services) > 0


class DatenschutzValidator:
    """Validates DatenschutzConfig for DSGVO compliance.

    Checks:
    1. Mandatory fields (Verantwortlicher)
    2. Required Baustein fields
    3. Detected but not configured services
    4. Format validations
    """

    def __init__(self, config: DatenschutzConfig, detected_services: list[str] | None = None):
        """Initialize validator.

        Args:
            config: The configuration to validate
            detected_services: Optional list of detected service Baustein IDs
        """
        self.config = config
        self.detected_services = detected_services or []

    def validate(self) -> ValidationResult:
        """Run all validations and return result.

        Returns:
            ValidationResult with errors, warnings, and unconfigured services
        """
        result = ValidationResult()

        self._check_verantwortlicher(result)
        self._check_datenschutzbeauftragter(result)
        self._check_baustein_config(result)
        self._check_unconfigured_services(result)
        self._check_mandatory_bausteine(result)

        return result

    def _check_verantwortlicher(self, result: ValidationResult) -> None:
        """Check mandatory Verantwortlicher fields (DSGVO Art. 13 Abs. 1 lit. a)."""
        if not self.config.verantwortlicher_name:
            result.errors.append(
                'Name des Verantwortlichen fehlt (Pflichtangabe nach DSGVO Art. 13)'
            )

        if not self.config.verantwortlicher_strasse:
            result.errors.append('Straße des Verantwortlichen fehlt')

        if not self.config.verantwortlicher_plz:
            result.errors.append('PLZ des Verantwortlichen fehlt')

        if not self.config.verantwortlicher_ort:
            result.errors.append('Ort des Verantwortlichen fehlt')

        if not self.config.verantwortlicher_email:
            result.errors.append(
                'E-Mail des Verantwortlichen fehlt (Pflichtangabe nach DSGVO Art. 13)'
            )
        elif '@' not in self.config.verantwortlicher_email:
            result.errors.append('E-Mail-Adresse ist ungültig')

        # Warnings for optional but recommended fields
        if not self.config.verantwortlicher_telefon:
            result.warnings.append(
                'Telefonnummer des Verantwortlichen empfohlen für bessere Erreichbarkeit'
            )

    def _check_datenschutzbeauftragter(self, result: ValidationResult) -> None:
        """Check Datenschutzbeauftragter fields if enabled."""
        if not self.config.dsb_vorhanden:
            return

        if not self.config.dsb_name:
            result.errors.append(
                'Name des Datenschutzbeauftragten fehlt (wenn DSB vorhanden)'
            )

        if not self.config.dsb_email:
            result.errors.append(
                'E-Mail des Datenschutzbeauftragten fehlt'
            )

    def _check_baustein_config(self, result: ValidationResult) -> None:
        """Check that activated Bausteine have required configuration."""
        aktivierte = self.config.aktivierte_bausteine or []

        for baustein_id in aktivierte:
            baustein = get_baustein_by_id(baustein_id)
            if not baustein:
                continue

            # Check Pflichtfelder for this Baustein
            if baustein.pflichtfelder:
                baustein_config = self.config.get_baustein_config(baustein_id)
                for feld in baustein.pflichtfelder:
                    if not baustein_config.get(feld):
                        result.warnings.append(
                            f'{baustein.name}: Feld "{feld}" sollte ausgefüllt werden'
                        )

    def _check_unconfigured_services(self, result: ValidationResult) -> None:
        """Check for detected but not configured services."""
        aktivierte = set(self.config.aktivierte_bausteine or [])

        for service_id in self.detected_services:
            if service_id not in aktivierte:
                baustein = get_baustein_by_id(service_id)
                name = baustein.name if baustein else service_id
                result.unconfigured_services.append(name)

    def _check_mandatory_bausteine(self, result: ValidationResult) -> None:
        """Check that all mandatory Bausteine are activated."""
        aktivierte = set(self.config.aktivierte_bausteine or [])

        for baustein in get_all_bausteine():
            if not baustein.optional and baustein.id not in aktivierte:
                result.warnings.append(
                    f'Pflicht-Baustein "{baustein.name}" ist nicht aktiviert'
                )

    def get_completeness_score(self) -> int:
        """Calculate completeness score (0-100).

        Returns:
            Percentage of filled fields and configurations
        """
        total_points = 0
        earned_points = 0

        # Verantwortlicher (mandatory fields = 5 points each)
        verantwortlicher_fields = [
            self.config.verantwortlicher_name,
            self.config.verantwortlicher_strasse,
            self.config.verantwortlicher_plz,
            self.config.verantwortlicher_ort,
            self.config.verantwortlicher_email,
        ]
        for field_value in verantwortlicher_fields:
            total_points += 5
            if field_value:
                earned_points += 5

        # Optional Verantwortlicher fields (2 points each)
        optional_fields = [
            self.config.verantwortlicher_telefon,
            self.config.verantwortlicher_land,
        ]
        for field_value in optional_fields:
            total_points += 2
            if field_value:
                earned_points += 2

        # DSB if enabled (3 points for having it configured)
        if self.config.dsb_vorhanden:
            total_points += 6
            if self.config.dsb_name:
                earned_points += 3
            if self.config.dsb_email:
                earned_points += 3

        # Bausteine (2 points for each mandatory, 1 for optional)
        aktivierte = set(self.config.aktivierte_bausteine or [])
        for baustein in get_all_bausteine():
            if baustein.optional:
                total_points += 1
                if baustein.id in aktivierte:
                    earned_points += 1
            else:
                total_points += 2
                if baustein.id in aktivierte:
                    earned_points += 2

        # Avoid division by zero
        if total_points == 0:
            return 0

        return round((earned_points / total_points) * 100)
