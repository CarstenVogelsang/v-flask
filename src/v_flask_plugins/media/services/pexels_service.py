"""Pexels API integration for importing stock photos.

Provides search and import functionality for Pexels stock photos.
Photos are downloaded, resized to multiple variants, and stored
in the media library with proper attribution.
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


PEXELS_API_URL = "https://api.pexels.com/v1"


def get_api_key() -> str | None:
    """Get Pexels API key from config."""
    return current_app.config.get('PEXELS_API_KEY')


def is_configured() -> bool:
    """Check if Pexels API is configured."""
    return bool(get_api_key())


def search_photos(
    query: str,
    per_page: int = 15,
    page: int = 1,
    orientation: str | None = None,
) -> dict:
    """Search Pexels for photos.

    Args:
        query: Search query string
        per_page: Number of results per page (max 80)
        page: Page number
        orientation: Filter by orientation (landscape, portrait, square)

    Returns:
        Dict with photos array and pagination info, or error dict
    """
    api_key = get_api_key()
    if not api_key:
        return {'error': 'Pexels API key not configured', 'photos': []}

    headers = {'Authorization': api_key}
    params = {
        'query': query,
        'per_page': min(per_page, 80),
        'page': page,
    }
    if orientation:
        params['orientation'] = orientation

    try:
        response = requests.get(
            f"{PEXELS_API_URL}/search",
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        current_app.logger.error(f"Pexels API error: {e}")
        return {'error': str(e), 'photos': []}


def get_curated_photos(per_page: int = 15, page: int = 1) -> dict:
    """Get curated photos from Pexels (trending/featured).

    Args:
        per_page: Number of results per page
        page: Page number

    Returns:
        Dict with photos array and pagination info
    """
    api_key = get_api_key()
    if not api_key:
        return {'error': 'Pexels API key not configured', 'photos': []}

    headers = {'Authorization': api_key}
    params = {'per_page': min(per_page, 80), 'page': page}

    try:
        response = requests.get(
            f"{PEXELS_API_URL}/curated",
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        current_app.logger.error(f"Pexels API error: {e}")
        return {'error': str(e), 'photos': []}


def download_photo(photo_url: str) -> bytes | None:
    """Download a photo from Pexels.

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
        current_app.logger.error(f"Failed to download Pexels photo: {e}")
        return None


def import_photo(
    photo_url: str,
    pexels_id: str,
    photographer: str,
    photographer_url: str = '',
    uploaded_by_id: int | None = None,
    kategorien: list[str] | None = None,
    alt_text: str | None = None,
) -> Media | None:
    """Download and import a Pexels photo into the media library.

    Args:
        photo_url: URL of the photo to download (use large or original size)
        pexels_id: Pexels photo ID (for deduplication)
        photographer: Photographer name for attribution
        photographer_url: URL to photographer's Pexels profile
        uploaded_by_id: ID of the importing user
        kategorien: List of category values
        alt_text: Alt text for the image

    Returns:
        Created Media instance or None if import failed
    """
    # Check if already imported
    existing = Media.query.filter_by(
        source=MediaSource.PEXELS.value,
        source_id=pexels_id
    ).first()
    if existing:
        return existing

    # Download the photo
    photo_bytes = download_photo(photo_url)
    if not photo_bytes:
        return None

    # Determine file extension from URL
    extension = 'jpg'
    if '.png' in photo_url.lower():
        extension = 'png'
    elif '.webp' in photo_url.lower():
        extension = 'webp'

    # Generate filename and storage path
    now = datetime.utcnow()
    unique_id = uuid.uuid4().hex[:8]
    filename = f"pexels_{pexels_id}_{unique_id}.{extension}"
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

    # Build Pexels photo URL for attribution
    source_url = f"https://www.pexels.com/photo/{pexels_id}/"
    if photographer_url:
        # Photographer URL is more specific for attribution
        source_url = photographer_url

    # Create Media record
    media = Media(
        filename=filename,
        original_filename=f"pexels_{pexels_id}.{extension}",
        storage_path=storage_path,
        mime_type=mime_type,
        media_type=MediaType.IMAGE.value,
        file_size=len(photo_bytes),
        width=width,
        height=height,
        alt_text=alt_text,
        title=f"Photo by {photographer}",
        caption=f"Foto von {photographer} auf Pexels",
        uploaded_by_id=uploaded_by_id,
        kategorien=kategorien or [],
        source=MediaSource.PEXELS.value,
        source_id=pexels_id,
        source_url=source_url,
        photographer=photographer,
    )

    db.session.add(media)
    db.session.commit()

    # Generate resized variants
    from v_flask_plugins.media.services.media_service import media_service
    media_service.generate_resized_variants(media)

    return media
