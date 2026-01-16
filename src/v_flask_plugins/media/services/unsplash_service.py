"""Unsplash API integration for importing stock photos.

Provides search and import functionality for Unsplash stock photos.
Photos are downloaded, resized to multiple variants, and stored
in the media library with proper attribution.

Unsplash License: https://unsplash.com/license
- Free to use for commercial and non-commercial purposes
- Attribution is not required but appreciated
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from PIL import Image
from flask import current_app

from v_flask.extensions import db
from v_flask_plugins.media.models import Media, MediaType, MediaSource


UNSPLASH_API_URL = "https://api.unsplash.com"


def get_access_key() -> str | None:
    """Get Unsplash access key from config."""
    return current_app.config.get('UNSPLASH_ACCESS_KEY')


def is_configured() -> bool:
    """Check if Unsplash API is configured."""
    return bool(get_access_key())


def search_photos(
    query: str,
    per_page: int = 15,
    page: int = 1,
    orientation: str | None = None,
) -> dict:
    """Search Unsplash for photos.

    Args:
        query: Search query string
        per_page: Number of results per page (max 30)
        page: Page number
        orientation: Filter by orientation (landscape, portrait, squarish)

    Returns:
        Dict with photos array and pagination info, or error dict
    """
    access_key = get_access_key()
    if not access_key:
        return {'error': 'Unsplash access key not configured', 'photos': []}

    headers = {'Authorization': f'Client-ID {access_key}'}
    params = {
        'query': query,
        'per_page': min(per_page, 30),
        'page': page,
    }
    if orientation:
        # Unsplash uses 'squarish' instead of 'square'
        if orientation == 'square':
            orientation = 'squarish'
        params['orientation'] = orientation

    try:
        response = requests.get(
            f"{UNSPLASH_API_URL}/search/photos",
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Normalize response format to match Pexels
        return {
            'photos': data.get('results', []),
            'total_results': data.get('total', 0),
            'page': page,
        }
    except requests.RequestException as e:
        current_app.logger.error(f"Unsplash API error: {e}")
        return {'error': str(e), 'photos': []}


def get_editorial_photos(per_page: int = 15, page: int = 1) -> dict:
    """Get editorial photos from Unsplash (curated/latest).

    Args:
        per_page: Number of results per page
        page: Page number

    Returns:
        Dict with photos array and pagination info
    """
    access_key = get_access_key()
    if not access_key:
        return {'error': 'Unsplash access key not configured', 'photos': []}

    headers = {'Authorization': f'Client-ID {access_key}'}
    params = {
        'per_page': min(per_page, 30),
        'page': page,
        'order_by': 'popular',  # latest, oldest, popular
    }

    try:
        response = requests.get(
            f"{UNSPLASH_API_URL}/photos",
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        photos = response.json()

        return {
            'photos': photos,
            'total_results': None,  # Unsplash doesn't return total for this endpoint
            'page': page,
        }
    except requests.RequestException as e:
        current_app.logger.error(f"Unsplash API error: {e}")
        return {'error': str(e), 'photos': []}


def download_photo(photo_url: str) -> bytes | None:
    """Download a photo from Unsplash.

    Args:
        photo_url: URL of the photo to download

    Returns:
        Photo bytes or None if download failed
    """
    try:
        response = requests.get(photo_url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        current_app.logger.error(f"Failed to download Unsplash photo: {e}")
        return None


def track_download(unsplash_id: str) -> None:
    """Track a download with Unsplash API (required by their guidelines).

    Args:
        unsplash_id: The Unsplash photo ID
    """
    access_key = get_access_key()
    if not access_key:
        return

    headers = {'Authorization': f'Client-ID {access_key}'}

    try:
        # Unsplash requires tracking downloads
        requests.get(
            f"{UNSPLASH_API_URL}/photos/{unsplash_id}/download",
            headers=headers,
            timeout=5,
        )
    except requests.RequestException:
        # Non-critical, just log and continue
        pass


def import_photo(
    photo_url: str,
    unsplash_id: str,
    photographer: str,
    photographer_url: str = '',
    uploaded_by_id: int | None = None,
    kategorien: list[str] | None = None,
    alt_text: str | None = None,
) -> Media | None:
    """Download and import an Unsplash photo into the media library.

    Args:
        photo_url: URL of the photo to download (use full or raw size)
        unsplash_id: Unsplash photo ID (for deduplication)
        photographer: Photographer name for attribution
        photographer_url: URL to photographer's Unsplash profile
        uploaded_by_id: ID of the importing user
        kategorien: List of category values
        alt_text: Alt text for the image

    Returns:
        Created Media instance or None if import failed
    """
    # Check if already imported
    existing = Media.query.filter_by(
        source=MediaSource.UNSPLASH.value,
        source_id=unsplash_id
    ).first()
    if existing:
        return existing

    # Track the download with Unsplash (required by their API guidelines)
    track_download(unsplash_id)

    # Download the photo
    photo_bytes = download_photo(photo_url)
    if not photo_bytes:
        return None

    # Unsplash typically serves JPEG
    extension = 'jpg'
    if '.png' in photo_url.lower():
        extension = 'png'
    elif '.webp' in photo_url.lower():
        extension = 'webp'

    # Generate filename and storage path
    now = datetime.utcnow()
    unique_id = uuid.uuid4().hex[:8]
    filename = f"unsplash_{unsplash_id}_{unique_id}.{extension}"
    storage_path = f"{now.year}/{now.month:02d}/{filename}"

    # Get upload folder from config
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/media')
    full_path = Path(upload_folder) / storage_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Save file
    with open(full_path, 'wb') as f:
        f.write(photo_bytes)

    # Get image dimensions
    width, height = None, None
    try:
        with Image.open(full_path) as img:
            width, height = img.size
    except Exception:
        pass

    # Determine MIME type
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
    }
    mime_type = mime_types.get(extension, 'image/jpeg')

    # Build Unsplash photo URL for attribution
    source_url = f"https://unsplash.com/photos/{unsplash_id}"
    if photographer_url:
        source_url = photographer_url

    # Create Media record
    media = Media(
        filename=filename,
        original_filename=f"unsplash_{unsplash_id}.{extension}",
        storage_path=storage_path,
        mime_type=mime_type,
        media_type=MediaType.IMAGE.value,
        file_size=len(photo_bytes),
        width=width,
        height=height,
        alt_text=alt_text,
        title=f"Photo by {photographer}",
        caption=f"Foto von {photographer} auf Unsplash",
        uploaded_by_id=uploaded_by_id,
        kategorien=kategorien or [],
        source=MediaSource.UNSPLASH.value,
        source_id=unsplash_id,
        source_url=source_url,
        photographer=photographer,
    )

    db.session.add(media)
    db.session.commit()

    # Generate resized variants
    from v_flask_plugins.media.services.media_service import media_service
    media_service.generate_resized_variants(media)

    return media
