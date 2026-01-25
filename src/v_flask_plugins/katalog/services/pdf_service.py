"""PDF service for handling file uploads, downloads, and viewing.

Manages PDF file storage, retrieval, and statistics tracking.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from werkzeug.utils import secure_filename

if TYPE_CHECKING:
    from flask import Flask

    from v_flask_plugins.katalog.models import KatalogPDF


class PDFService:
    """Service for managing PDF catalog files.

    Handles:
    - File uploads with validation
    - File path resolution
    - Download and view tracking
    - Cover image management
    """

    ALLOWED_EXTENSIONS = {'pdf'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    def __init__(self, app: Flask) -> None:
        """Initialize the PDF service.

        Args:
            app: Flask application instance.
        """
        self.app = app
        self._upload_path: str | None = None

    @property
    def upload_path(self) -> Path:
        """Get the upload directory path.

        Creates the directory if it doesn't exist.

        Returns:
            Path to the upload directory.
        """
        if self._upload_path is None:
            # Get from plugin settings or use default
            from v_flask.models import PluginConfig
            try:
                config_value = PluginConfig.get('katalog', 'upload_path')
                relative_path = config_value or 'katalog/pdfs'
            except Exception:
                relative_path = 'katalog/pdfs'

            self._upload_path = Path(self.app.instance_path) / relative_path

        # Ensure directory exists
        self._upload_path.mkdir(parents=True, exist_ok=True)
        return self._upload_path

    @property
    def max_file_size(self) -> int:
        """Get maximum file size in bytes."""
        from v_flask.models import PluginConfig
        try:
            mb = PluginConfig.get('katalog', 'max_file_size_mb') or 50
            return int(mb) * 1024 * 1024
        except Exception:
            return 50 * 1024 * 1024  # 50 MB default

    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed for PDFs.

        Args:
            filename: Name of the file to check.

        Returns:
            True if file extension is allowed.
        """
        return (
            '.' in filename and
            filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
        )

    def allowed_image(self, filename: str) -> bool:
        """Check if file extension is allowed for images.

        Args:
            filename: Name of the file to check.

        Returns:
            True if file extension is allowed.
        """
        return (
            '.' in filename and
            filename.rsplit('.', 1)[1].lower() in self.ALLOWED_IMAGE_EXTENSIONS
        )

    def save_pdf(
        self,
        file: BinaryIO,
        filename: str
    ) -> tuple[str, int]:
        """Save an uploaded PDF file.

        Args:
            file: File-like object to save.
            filename: Original filename.

        Returns:
            Tuple of (relative_path, file_size).

        Raises:
            ValueError: If file is not a valid PDF or too large.
        """
        if not self.allowed_file(filename):
            raise ValueError('Nur PDF-Dateien sind erlaubt.')

        # Generate unique filename
        safe_name = secure_filename(filename)
        unique_name = f'{uuid.uuid4().hex}_{safe_name}'
        file_path = self.upload_path / unique_name

        # Save file
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > self.max_file_size:
            max_mb = self.max_file_size // (1024 * 1024)
            raise ValueError(f'Datei ist zu groß. Maximum: {max_mb} MB')

        with open(file_path, 'wb') as f:
            f.write(file.read())

        # Return relative path (from instance folder)
        relative_path = str(file_path.relative_to(self.app.instance_path))
        return relative_path, file_size

    def save_cover_image(
        self,
        file: BinaryIO,
        filename: str
    ) -> str:
        """Save a cover image for a PDF.

        Args:
            file: File-like object to save.
            filename: Original filename.

        Returns:
            Relative path to saved image.

        Raises:
            ValueError: If file is not a valid image.
        """
        if not self.allowed_image(filename):
            raise ValueError('Nur PNG, JPG oder WebP Bilder sind erlaubt.')

        # Use covers subdirectory
        covers_path = self.upload_path / 'covers'
        covers_path.mkdir(exist_ok=True)

        safe_name = secure_filename(filename)
        unique_name = f'{uuid.uuid4().hex}_{safe_name}'
        file_path = covers_path / unique_name

        with open(file_path, 'wb') as f:
            f.write(file.read())

        return str(file_path.relative_to(self.app.instance_path))

    def get_file_path(self, relative_path: str) -> Path:
        """Get absolute path for a stored file.

        Args:
            relative_path: Path relative to instance folder.

        Returns:
            Absolute Path object.
        """
        return Path(self.app.instance_path) / relative_path

    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists.

        Args:
            relative_path: Path relative to instance folder.

        Returns:
            True if file exists.
        """
        return self.get_file_path(relative_path).exists()

    def delete_file(self, relative_path: str) -> bool:
        """Delete a stored file.

        Args:
            relative_path: Path relative to instance folder.

        Returns:
            True if file was deleted, False if not found.
        """
        file_path = self.get_file_path(relative_path)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_pdf_url(self, pdf: KatalogPDF) -> str:
        """Get the URL for viewing a PDF.

        Args:
            pdf: KatalogPDF instance.

        Returns:
            URL string for the PDF viewer.
        """
        from flask import url_for
        return url_for('katalog.view', pdf_id=str(pdf.id))

    def get_download_url(self, pdf: KatalogPDF) -> str:
        """Get the URL for downloading a PDF.

        Args:
            pdf: KatalogPDF instance.

        Returns:
            URL string for download.
        """
        from flask import url_for
        return url_for('katalog.download', pdf_id=str(pdf.id))

    def get_file_url(self, pdf: KatalogPDF) -> str:
        """Get the direct URL to the PDF file.

        Args:
            pdf: KatalogPDF instance.

        Returns:
            URL string for the PDF file.
        """
        from flask import url_for
        return url_for('katalog.serve_pdf', pdf_id=str(pdf.id))

    def get_cover_url(self, pdf: KatalogPDF) -> str | None:
        """Get the URL for a PDF's cover image.

        Args:
            pdf: KatalogPDF instance.

        Returns:
            URL string or None if no cover.
        """
        if not pdf.cover_image_path:
            return None
        from flask import url_for
        return url_for('katalog.serve_cover', pdf_id=str(pdf.id))

    def require_login(self) -> bool:
        """Check if login is required for downloads.

        Returns:
            True if downloads require authentication.
        """
        from v_flask.models import PluginConfig
        try:
            return bool(PluginConfig.get('katalog', 'require_login'))
        except Exception:
            return False


def get_pdf_service() -> PDFService:
    """Get the PDF service from the current app.

    Returns:
        PDFService instance.

    Raises:
        RuntimeError: If called outside app context.
    """
    from flask import current_app
    return current_app.extensions.get('katalog_pdf_service')
