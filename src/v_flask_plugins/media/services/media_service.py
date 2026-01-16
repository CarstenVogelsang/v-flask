"""Media management service for file uploads and storage.

Provides functions for:
- File upload with validation
- Automatic image resizing (thumbnail, small, medium, large)
- CRUD operations on Media records
- Media picker component rendering
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image
from flask import current_app, render_template_string
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from v_flask.extensions import db
from v_flask_plugins.media.models import Media, MediaType, MediaSource


# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

# Maximum file sizes (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20MB

# Image resize presets
IMAGE_SIZES = {
    'thumbnail': (150, 150),
    'small': (400, 400),
    'medium': (800, 800),
    'large': (1200, 1200),
}


class MediaService:
    """Service class for media operations.

    Handles file uploads, resizing, and CRUD operations.

    Usage:
        from v_flask_plugins.media.services.media_service import media_service

        # Upload a file
        media = media_service.save_uploaded_file(
            file=request.files['image'],
            uploaded_by_id=current_user.id,
            alt_text='Description'
        )

        # Get URL for specific size
        url = media_service.get_url(media.id, 'thumbnail')
    """

    def get_upload_folder(self) -> Path:
        """Get the media upload folder path.

        Returns:
            Path to upload folder.
        """
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/media')
        path = Path(upload_folder)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def validate_file(self, file: FileStorage) -> list[str]:
        """Validate uploaded file.

        Args:
            file: Uploaded file from request.files.

        Returns:
            List of error messages (empty if valid).
        """
        errors = []

        if not file or not file.filename:
            errors.append('Keine Datei ausgewählt.')
            return errors

        # Check extension
        extension = self.get_file_extension(file.filename)
        if extension not in ALLOWED_EXTENSIONS:
            allowed = ', '.join(sorted(ALLOWED_EXTENSIONS))
            errors.append(f'Dateityp nicht erlaubt. Erlaubt: {allowed}')
            return errors

        # Check file size (if content length available)
        if file.content_length:
            is_image = extension in ALLOWED_IMAGE_EXTENSIONS
            max_size = MAX_IMAGE_SIZE if is_image else MAX_DOCUMENT_SIZE
            if file.content_length > max_size:
                max_mb = max_size // (1024 * 1024)
                errors.append(f'Datei zu groß. Maximum: {max_mb}MB')

        return errors

    def get_file_extension(self, filename: str) -> str:
        """Get lowercase file extension.

        Args:
            filename: Original filename.

        Returns:
            Lowercase extension without dot.
        """
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    def get_media_type(self, filename: str) -> str:
        """Determine media type from filename.

        Args:
            filename: Original filename.

        Returns:
            MediaType value string.
        """
        extension = self.get_file_extension(filename)
        if extension in ALLOWED_IMAGE_EXTENSIONS:
            return MediaType.IMAGE.value
        elif extension in ALLOWED_DOCUMENT_EXTENSIONS:
            return MediaType.DOCUMENT.value
        return MediaType.OTHER.value

    def generate_storage_path(self, original_filename: str) -> str:
        """Generate unique storage path following YYYY/MM/uuid_filename pattern.

        Args:
            original_filename: Original uploaded filename.

        Returns:
            Storage path string (e.g., "2026/01/abc123_image.jpg").
        """
        now = datetime.utcnow()
        safe_filename = secure_filename(original_filename)
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{unique_id}_{safe_filename}"
        return f"{now.year}/{now.month:02d}/{filename}"

    def save_uploaded_file(
        self,
        file: FileStorage,
        uploaded_by_id: int,
        alt_text: Optional[str] = None,
        title: Optional[str] = None,
        kategorien: Optional[list[str]] = None,
        source: str = MediaSource.UPLOAD.value,
        source_id: Optional[str] = None,
        source_url: Optional[str] = None,
        photographer: Optional[str] = None,
    ) -> Media:
        """Save uploaded file and create Media record with resized variants.

        Args:
            file: Uploaded file from request.files.
            uploaded_by_id: ID of the uploading user.
            alt_text: Image alt text for SEO.
            title: Media title.
            kategorien: List of category values.
            source: Source of the file (upload, pexels, unsplash).
            source_id: External ID for imported files.
            source_url: Original URL for attribution.
            photographer: Photographer name for stock photos.

        Returns:
            Created Media instance.
        """
        original_filename = secure_filename(file.filename)
        storage_path = self.generate_storage_path(original_filename)

        # Create directory structure
        upload_folder = self.get_upload_folder()
        full_path = upload_folder / storage_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Save file
        file.save(str(full_path))

        # Get file info
        file_size = full_path.stat().st_size
        media_type = self.get_media_type(original_filename)

        # Get image dimensions
        width = None
        height = None
        if media_type == MediaType.IMAGE.value:
            try:
                with Image.open(full_path) as img:
                    width, height = img.size
            except Exception:
                pass

        # Create Media record
        media = Media(
            filename=full_path.name,
            original_filename=original_filename,
            storage_path=storage_path,
            mime_type=file.content_type or 'application/octet-stream',
            media_type=media_type,
            file_size=file_size,
            width=width,
            height=height,
            alt_text=alt_text,
            title=title or original_filename,
            uploaded_by_id=uploaded_by_id,
            kategorien=kategorien or [],
            source=source,
            source_id=source_id,
            source_url=source_url,
            photographer=photographer,
        )

        db.session.add(media)
        db.session.commit()

        # Generate resized variants for images
        if media_type == MediaType.IMAGE.value:
            self.generate_resized_variants(media)

        return media

    def generate_resized_variants(self, media: Media) -> dict[str, str]:
        """Generate all resized variants for an image.

        Args:
            media: Media instance (must be an image).

        Returns:
            Dict mapping size name to path.
        """
        if media.media_type != MediaType.IMAGE.value:
            return {}

        variants = {}
        for size_name in IMAGE_SIZES:
            path = self.resize_image(media, size_name)
            if path:
                variants[size_name] = path

        # Save paths to database
        media.path_thumbnail = variants.get('thumbnail')
        media.path_small = variants.get('small')
        media.path_medium = variants.get('medium')
        media.path_large = variants.get('large')
        db.session.commit()

        return variants

    def resize_image(self, media: Media, size_name: str) -> Optional[str]:
        """Create resized version of image.

        Args:
            media: Media instance (must be an image).
            size_name: Size preset name (thumbnail, small, medium, large).

        Returns:
            Relative path to resized image or None if failed.
        """
        if media.media_type != MediaType.IMAGE.value:
            return None

        if size_name not in IMAGE_SIZES:
            return None

        target_size = IMAGE_SIZES[size_name]
        original_path = self.get_media_file_path(media)

        if not original_path.exists():
            return None

        # Generate resized filename
        stem = original_path.stem
        suffix = original_path.suffix
        resized_filename = f"{stem}_{size_name}{suffix}"
        resized_path = original_path.parent / resized_filename

        try:
            with Image.open(original_path) as img:
                # Convert RGBA to RGB for JPEG
                if img.mode == 'RGBA' and suffix.lower() in ['.jpg', '.jpeg']:
                    img = img.convert('RGB')

                # Resize maintaining aspect ratio
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                img.save(resized_path, quality=85, optimize=True)

            # Return path relative to upload folder
            return str(resized_path.relative_to(self.get_upload_folder()))
        except Exception:
            return None

    def get_media_file_path(self, media: Media) -> Path:
        """Get full filesystem path for media file.

        Args:
            media: Media instance.

        Returns:
            Full Path to file.
        """
        return self.get_upload_folder() / media.storage_path

    # ==============================================
    # CRUD Operations
    # ==============================================

    def get_media(self, media_id: int | None) -> Media | None:
        """Get Media by ID.

        Args:
            media_id: Media ID.

        Returns:
            Media instance or None.
        """
        if not media_id:
            return None
        return db.session.get(Media, media_id)

    def get_url(self, media_id: int | None, size: str = 'medium') -> str:
        """Get URL for media with specific size.

        Args:
            media_id: Media ID.
            size: Size variant (thumbnail, small, medium, large, original).

        Returns:
            URL string or empty string if not found.
        """
        media = self.get_media(media_id)
        if not media:
            return ''
        return media.get_url(size)

    def update_media(
        self,
        media: Media,
        alt_text: Optional[str] = None,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        kategorien: Optional[list[str]] = None,
    ) -> None:
        """Update media metadata.

        Args:
            media: Media instance to update.
            alt_text: New alt text.
            title: New title.
            caption: New caption.
            kategorien: New categories.
        """
        if alt_text is not None:
            media.alt_text = alt_text
        if title is not None:
            media.title = title
        if caption is not None:
            media.caption = caption
        if kategorien is not None:
            media.kategorien = kategorien

        db.session.commit()

    def delete_media(self, media: Media) -> None:
        """Delete media file and all variants.

        Args:
            media: Media instance to delete.
        """
        upload_folder = self.get_upload_folder()

        # Delete original file
        original_path = upload_folder / media.storage_path
        if original_path.exists():
            original_path.unlink()

        # Delete resized variants
        for size_name in IMAGE_SIZES:
            path_attr = f'path_{size_name}'
            relative_path = getattr(media, path_attr, None)
            if relative_path:
                variant_path = upload_folder / relative_path
                if variant_path.exists():
                    variant_path.unlink()

        # Delete database record
        db.session.delete(media)
        db.session.commit()

    # ==============================================
    # Query Methods
    # ==============================================

    def get_media_list(
        self,
        media_type: Optional[str] = None,
        uploaded_by_id: Optional[int] = None,
        kategorie: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Media]:
        """Get filtered list of media files.

        Args:
            media_type: Filter by type (image, document, other).
            uploaded_by_id: Filter by uploader.
            kategorie: Filter by category.
            source: Filter by source (upload, pexels, unsplash).
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of Media instances.
        """
        query = Media.query

        if media_type:
            query = query.filter(Media.media_type == media_type)
        if uploaded_by_id:
            query = query.filter(Media.uploaded_by_id == uploaded_by_id)
        if kategorie:
            query = query.filter(Media.kategorien.contains([kategorie]))
        if source:
            query = query.filter(Media.source == source)

        query = query.order_by(Media.uploaded_at.desc())

        return query.offset(offset).limit(limit).all()

    def get_images(self, limit: int = 50, offset: int = 0) -> list[Media]:
        """Get list of image files.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of image Media instances.
        """
        return self.get_media_list(
            media_type=MediaType.IMAGE.value,
            limit=limit,
            offset=offset
        )

    def search_media(self, query: str, limit: int = 20) -> list[Media]:
        """Search media by filename, title, or alt text.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of matching Media instances.
        """
        search_term = f"%{query}%"
        return Media.query.filter(
            db.or_(
                Media.original_filename.ilike(search_term),
                Media.title.ilike(search_term),
                Media.alt_text.ilike(search_term),
            )
        ).order_by(Media.uploaded_at.desc()).limit(limit).all()

    def count_media(
        self,
        media_type: Optional[str] = None,
        source: Optional[str] = None,
    ) -> int:
        """Count media files with optional filters.

        Args:
            media_type: Filter by type.
            source: Filter by source.

        Returns:
            Count of matching media.
        """
        query = Media.query

        if media_type:
            query = query.filter(Media.media_type == media_type)
        if source:
            query = query.filter(Media.source == source)

        return query.count()

    # ==============================================
    # Picker Component
    # ==============================================

    def render_picker_component(
        self,
        field_name: str = 'media_id',
        current_media_id: int | None = None,
        accept: str = 'image/*',
    ) -> str:
        """Render HTML for media picker component.

        Args:
            field_name: Name of the hidden input field.
            current_media_id: Currently selected media ID.
            accept: MIME type filter.

        Returns:
            HTML string for the picker component.
        """
        current_media = self.get_media(current_media_id) if current_media_id else None

        template = '''
        <div class="media-picker" data-field="{{ field_name }}">
            <input type="hidden" name="{{ field_name }}" value="{{ current_media.id if current_media else '' }}">

            {% if current_media %}
            <div class="media-picker-preview mb-2">
                <div class="relative inline-block">
                    <img src="{{ current_media.get_url('thumbnail') }}"
                         alt="{{ current_media.alt_text or current_media.filename }}"
                         class="rounded-lg max-h-32 object-cover">
                    <button type="button"
                            class="btn btn-sm btn-circle btn-error absolute -top-2 -right-2"
                            onclick="clearMediaPicker('{{ field_name }}')"
                            title="Entfernen">
                        <i class="ti ti-x"></i>
                    </button>
                </div>
                <p class="text-xs text-base-content/60 mt-1">{{ current_media.title or current_media.filename }}</p>
            </div>
            {% endif %}

            <button type="button"
                    class="btn btn-outline btn-sm"
                    onclick="openMediaPicker('{{ field_name }}', '{{ accept }}')"
                    title="Aus Media-Library wählen">
                <i class="ti ti-photo mr-1"></i>
                {% if current_media %}Ändern{% else %}Auswählen{% endif %}
            </button>
        </div>

        <script>
        function openMediaPicker(fieldName, accept) {
            // Open media picker modal via HTMX
            htmx.ajax('GET', '/admin/media/picker?field=' + fieldName + '&accept=' + encodeURIComponent(accept), {
                target: '#media-picker-modal-container',
                swap: 'innerHTML'
            }).then(function() {
                document.getElementById('media-picker-modal').showModal();
            });
        }

        function clearMediaPicker(fieldName) {
            const picker = document.querySelector('[data-field="' + fieldName + '"]');
            picker.querySelector('input[type="hidden"]').value = '';
            const preview = picker.querySelector('.media-picker-preview');
            if (preview) preview.remove();
            const btn = picker.querySelector('button');
            btn.innerHTML = '<i class="ti ti-photo mr-1"></i>Auswählen';
        }

        function selectMedia(fieldName, mediaId, thumbnailUrl, title) {
            const picker = document.querySelector('[data-field="' + fieldName + '"]');
            picker.querySelector('input[type="hidden"]').value = mediaId;

            // Update or create preview
            let preview = picker.querySelector('.media-picker-preview');
            if (!preview) {
                preview = document.createElement('div');
                preview.className = 'media-picker-preview mb-2';
                picker.insertBefore(preview, picker.querySelector('button'));
            }

            preview.innerHTML = `
                <div class="relative inline-block">
                    <img src="${thumbnailUrl}" alt="${title}" class="rounded-lg max-h-32 object-cover">
                    <button type="button"
                            class="btn btn-sm btn-circle btn-error absolute -top-2 -right-2"
                            onclick="clearMediaPicker('${fieldName}')"
                            title="Entfernen">
                        <i class="ti ti-x"></i>
                    </button>
                </div>
                <p class="text-xs text-base-content/60 mt-1">${title}</p>
            `;

            picker.querySelector('button:last-child').innerHTML = '<i class="ti ti-photo mr-1"></i>Ändern';

            // Close modal
            document.getElementById('media-picker-modal').close();
        }
        </script>
        '''

        return render_template_string(
            template,
            field_name=field_name,
            current_media=current_media,
            accept=accept
        )


# Singleton instance for convenience
media_service = MediaService()
