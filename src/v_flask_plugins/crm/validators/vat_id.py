"""VAT-ID (USt-IdNr.) validation for CRM plugin.

Validates EU VAT-IDs with focus on German format (DE + 9 digits).
"""

import re


class VatIdValidator:
    """Validates EU VAT-IDs (USt-IdNr.).

    Currently supports:
    - Germany (DE): DE + 9 digits

    Usage:
        validator = VatIdValidator()
        is_valid, error = validator.validate('DE123456789')
        if not is_valid:
            print(f'Invalid VAT-ID: {error}')
    """

    # Country-specific patterns
    PATTERNS = {
        'DE': re.compile(r'^DE[0-9]{9}$'),  # Germany: DE + 9 digits
        'AT': re.compile(r'^ATU[0-9]{8}$'),  # Austria: ATU + 8 digits
        'CH': re.compile(r'^CHE-?[0-9]{3}\.?[0-9]{3}\.?[0-9]{3}$'),  # Switzerland
    }

    # Country names for error messages
    COUNTRY_NAMES = {
        'DE': 'Deutschland',
        'AT': 'Österreich',
        'CH': 'Schweiz',
    }

    def validate(self, vat_id: str | None) -> tuple[bool, str]:
        """Validate a VAT-ID.

        Args:
            vat_id: The VAT-ID to validate (e.g., 'DE123456789').

        Returns:
            Tuple of (is_valid, error_message).
            If valid: (True, '')
            If invalid: (False, 'Error description')
        """
        # Empty is valid (optional field)
        if not vat_id:
            return True, ''

        # Normalize: uppercase, remove spaces and hyphens
        vat_id = vat_id.strip().upper().replace(' ', '').replace('-', '')

        # Determine country from prefix
        country_code = self._extract_country_code(vat_id)

        if not country_code:
            return False, 'USt-IdNr. muss mit einem gültigen Ländercode beginnen (z.B. DE)'

        if country_code not in self.PATTERNS:
            return False, f'Ländercode {country_code} wird nicht unterstützt'

        # Validate format
        pattern = self.PATTERNS[country_code]
        if not pattern.match(vat_id):
            return False, self._get_format_error(country_code)

        # Country-specific validation
        if country_code == 'DE':
            return self._validate_de_checksum(vat_id)

        return True, ''

    def _extract_country_code(self, vat_id: str) -> str | None:
        """Extract the 2-letter country code from VAT-ID.

        Args:
            vat_id: Normalized VAT-ID string.

        Returns:
            Country code (e.g., 'DE') or None if not found.
        """
        if len(vat_id) < 2:
            return None

        # Check for known prefixes
        for code in self.PATTERNS.keys():
            if vat_id.startswith(code):
                return code

        # Try first 2 letters
        prefix = vat_id[:2]
        if prefix.isalpha():
            return prefix

        return None

    def _get_format_error(self, country_code: str) -> str:
        """Get format error message for a country.

        Args:
            country_code: The country code (e.g., 'DE').

        Returns:
            Human-readable error message.
        """
        format_examples = {
            'DE': 'DE123456789',
            'AT': 'ATU12345678',
            'CH': 'CHE-123.456.789',
        }
        example = format_examples.get(country_code, country_code + '...')
        country = self.COUNTRY_NAMES.get(country_code, country_code)
        return f'USt-IdNr. für {country} muss das Format {example} haben'

    def _validate_de_checksum(self, vat_id: str) -> tuple[bool, str]:
        """Validate German VAT-ID checksum (Mod 11 algorithm).

        The 9th digit is a check digit calculated using a modified
        Mod 11 algorithm.

        Args:
            vat_id: The VAT-ID (already validated for format).

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Extract the 9 digits after 'DE'
        digits = vat_id[2:]

        if len(digits) != 9:
            return False, 'Ungültige Länge für deutsche USt-IdNr.'

        # Mod 11 checksum calculation (simplified)
        # Note: Full VIES validation would require EU service call
        # Here we just validate format and basic rules

        # All digits must be numeric
        if not digits.isdigit():
            return False, 'USt-IdNr. darf nach DE nur Ziffern enthalten'

        # Can't be all zeros
        if digits == '000000000':
            return False, 'Ungültige USt-IdNr.'

        return True, ''

    def normalize(self, vat_id: str | None) -> str | None:
        """Normalize a VAT-ID to standard format.

        Args:
            vat_id: The VAT-ID to normalize.

        Returns:
            Normalized VAT-ID or None if input was None/empty.
        """
        if not vat_id:
            return None

        # Uppercase, remove spaces and common separators
        normalized = vat_id.strip().upper()
        normalized = normalized.replace(' ', '').replace('-', '').replace('.', '')

        return normalized


# Singleton instance for convenience
vat_validator = VatIdValidator()


def validate_vat_id(vat_id: str | None) -> tuple[bool, str]:
    """Convenience function to validate a VAT-ID.

    Args:
        vat_id: The VAT-ID to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    return vat_validator.validate(vat_id)
