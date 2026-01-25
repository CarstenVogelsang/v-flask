"""Two-Factor Authentication (2FA) service using TOTP.

Provides functionality for:
- TOTP secret generation
- QR code generation for authenticator apps
- Code verification
- Backup code generation and management

Usage:
    from v_flask.services import TwoFAService

    # Generate secret and QR code for setup
    secret = TwoFAService.generate_secret()
    qr_uri = TwoFAService.get_provisioning_uri(
        secret=secret,
        email='user@example.com',
        issuer='MyApp'
    )
    qr_image = TwoFAService.generate_qr_code(qr_uri)

    # Verify code from authenticator app
    if TwoFAService.verify_code(secret, user_code):
        print('Valid code!')

    # Generate backup codes
    codes = TwoFAService.generate_backup_codes()
    hashed = TwoFAService.hash_backup_codes(codes)
"""

from __future__ import annotations

import io
import json
import secrets
from typing import TYPE_CHECKING

from werkzeug.security import generate_password_hash

if TYPE_CHECKING:
    pass


class TwoFAService:
    """Service for TOTP-based Two-Factor Authentication.

    Uses pyotp for TOTP generation and verification.
    Uses qrcode for QR code image generation.

    All methods are static for easy usage without instantiation.
    """

    # TOTP settings
    TOTP_INTERVAL = 30  # seconds per code
    TOTP_DIGITS = 6  # code length

    # Backup code settings
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8  # characters (hex)

    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret.

        Returns:
            Base32 encoded secret string (32 characters).
        """
        import pyotp
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(
        secret: str,
        email: str,
        issuer: str = 'v-flask'
    ) -> str:
        """Generate the otpauth:// URI for QR code.

        This URI can be encoded in a QR code and scanned by
        authenticator apps like Google Authenticator, Authy, etc.

        Args:
            secret: The TOTP secret (Base32 encoded).
            email: User's email address (account identifier).
            issuer: Application name shown in authenticator app.

        Returns:
            otpauth:// URI string.
        """
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=issuer
        )

    @staticmethod
    def generate_qr_code(uri: str, size: int = 200) -> bytes:
        """Generate a QR code image for the provisioning URI.

        Args:
            uri: The otpauth:// URI to encode.
            size: Size of the QR code image in pixels.

        Returns:
            PNG image data as bytes.
        """
        import qrcode
        from qrcode.constants import ERROR_CORRECT_L

        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color='black', back_color='white')

        # Resize if needed
        img = img.resize((size, size))

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_qr_code_base64(uri: str, size: int = 200) -> str:
        """Generate a QR code as base64-encoded data URI.

        Useful for embedding directly in HTML img src.

        Args:
            uri: The otpauth:// URI to encode.
            size: Size of the QR code image in pixels.

        Returns:
            Base64 data URI string (data:image/png;base64,...).
        """
        import base64
        png_data = TwoFAService.generate_qr_code(uri, size)
        b64 = base64.b64encode(png_data).decode('utf-8')
        return f'data:image/png;base64,{b64}'

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """Verify a TOTP code from an authenticator app.

        Allows ±1 time window (±30 seconds) to account for clock drift.

        Args:
            secret: The TOTP secret (Base32 encoded).
            code: The 6-digit code from the authenticator app.

        Returns:
            True if the code is valid, False otherwise.
        """
        if not secret or not code:
            return False

        # Clean up the code (remove spaces, ensure string)
        code = str(code).strip().replace(' ', '')

        # Validate format (should be 6 digits)
        if not code.isdigit() or len(code) != 6:
            return False

        try:
            import pyotp
            totp = pyotp.TOTP(secret)
            # valid_window=1 allows codes from ±1 interval (±30 seconds)
            return totp.verify(code, valid_window=1)
        except Exception:
            return False

    @staticmethod
    def generate_backup_codes(count: int | None = None) -> list[str]:
        """Generate a set of backup codes.

        Backup codes are one-time use codes that can be used
        when the authenticator app is unavailable.

        Args:
            count: Number of codes to generate. Defaults to BACKUP_CODE_COUNT.

        Returns:
            List of backup code strings (lowercase hex).
        """
        if count is None:
            count = TwoFAService.BACKUP_CODE_COUNT

        codes = []
        for _ in range(count):
            # Generate random hex string (e.g., "a1b2c3d4")
            code = secrets.token_hex(TwoFAService.BACKUP_CODE_LENGTH // 2)
            codes.append(code)

        return codes

    @staticmethod
    def format_backup_code(code: str) -> str:
        """Format a backup code for display (with hyphen).

        Example: "a1b2c3d4" -> "a1b2-c3d4"

        Args:
            code: The raw backup code.

        Returns:
            Formatted code with hyphen in middle.
        """
        if len(code) >= 4:
            mid = len(code) // 2
            return f'{code[:mid]}-{code[mid:]}'
        return code

    @staticmethod
    def normalize_backup_code(code: str) -> str:
        """Normalize a backup code for verification.

        Removes hyphens, spaces, and converts to lowercase.

        Args:
            code: The backup code as entered by user.

        Returns:
            Normalized code string.
        """
        return code.lower().replace('-', '').replace(' ', '').strip()

    @staticmethod
    def hash_backup_codes(codes: list[str]) -> str:
        """Hash backup codes for secure database storage.

        Each code is hashed individually using werkzeug's
        generate_password_hash for secure storage.

        Args:
            codes: List of plaintext backup codes.

        Returns:
            JSON string of hashed codes (for DB storage).
        """
        hashed_codes = []
        for code in codes:
            # Normalize before hashing
            normalized = TwoFAService.normalize_backup_code(code)
            hashed = generate_password_hash(normalized, method='pbkdf2:sha256')
            hashed_codes.append(hashed)

        return json.dumps(hashed_codes)

    @staticmethod
    def get_current_code(secret: str) -> str:
        """Get the current TOTP code for a secret.

        Useful for testing and debugging. NOT for production use
        (users should use their authenticator app).

        Args:
            secret: The TOTP secret (Base32 encoded).

        Returns:
            Current 6-digit code as string.
        """
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.now()


# Convenience function for logging 2FA events
def log_2fa_event(
    user_id: int,
    action: str,
    details: str | None = None,
    success: bool = True
) -> None:
    """Log a 2FA-related event to the audit log.

    Args:
        user_id: The user ID.
        action: Action type (e.g., 'setup', 'verify', 'disable').
        details: Additional details.
        success: Whether the action was successful.
    """
    from v_flask.services import log_event

    importance = 'mittel' if success else 'kritisch'

    log_event(
        modul='auth',
        aktion=f'2fa_{action}',
        details=details,
        wichtigkeit=importance,
        entity_type='User',
        entity_id=user_id
    )