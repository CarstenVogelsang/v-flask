"""Admin routes for media library management.

Provides routes for:
- Media library browsing
- File upload
- Media detail and metadata editing
- Media picker for other plugins
- Stock photo search (Pexels, Unsplash)
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
)
from flask_login import login_required, current_user

from v_flask.extensions import db
from v_flask.auth import admin_required

from .models import Media, MediaType
from .services.media_service import media_service


# Admin blueprint for media management
media_admin_bp = Blueprint(
    'media_admin',
    __name__,
    template_folder='templates'
)


# ==============================================
# Library & CRUD Routes
# ==============================================

# Plugin label mapping for picker mode
PLUGIN_LABELS = {
    'hero_admin.editor': 'Hero Editor',
    'content_admin.edit': 'Content Editor',
    'admin_content.content_edit': 'Content Editor',
}


def get_return_to_label(endpoint: str) -> str:
    """Get human-readable label for a plugin endpoint."""
    return PLUGIN_LABELS.get(endpoint, endpoint.replace('_', ' ').replace('.', ' › ').title())


@media_admin_bp.route('/')
@admin_required
def library():
    """Media library browser.

    Supports picker mode when called with return_to parameter:
    - return_to: Flask endpoint to return to after selection (e.g., 'hero_admin.editor')
    - field: Name of the field to populate with media_id (default: 'media_id')
    """
    media_type = request.args.get('type')
    source = request.args.get('source')
    search_query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    per_page = 24

    # Picker mode parameters
    return_to = request.args.get('return_to')
    field_name = request.args.get('field', 'media_id')
    picker_mode = bool(return_to)
    return_to_label = get_return_to_label(return_to) if return_to else None

    if search_query:
        # Search mode
        media_items = media_service.search_media(search_query, limit=per_page)
        pagination = None
        total = len(media_items)
    else:
        # List mode with pagination
        query = Media.query
        if media_type:
            query = query.filter(Media.media_type == media_type)
        if source:
            query = query.filter(Media.source == source)
        query = query.order_by(Media.uploaded_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        media_items = pagination.items
        total = pagination.total

    # Count stats
    stats = {
        'total': media_service.count_media(),
        'images': media_service.count_media(media_type=MediaType.IMAGE.value),
        'pexels': media_service.count_media(source='pexels'),
        'unsplash': media_service.count_media(source='unsplash'),
    }

    return render_template(
        'media/admin/library.html',
        media_items=media_items,
        pagination=pagination,
        total=total,
        current_type=media_type,
        current_source=source,
        search_query=search_query,
        media_types=MediaType,
        stats=stats,
        # Picker mode
        picker_mode=picker_mode,
        return_to=return_to,
        return_to_label=return_to_label,
        field_name=field_name,
    )


@media_admin_bp.route('/upload', methods=['GET', 'POST'])
@admin_required
def upload():
    """Upload new media file(s)."""
    if request.method == 'POST':
        if 'file' not in request.files:
            if request.headers.get('HX-Request'):
                return '<div class="alert alert-error">Keine Datei ausgewählt.</div>', 400
            flash('Keine Datei ausgewählt.', 'error')
            return redirect(url_for('media_admin.library'))

        file = request.files['file']
        errors = media_service.validate_file(file)

        if errors:
            if request.headers.get('HX-Request'):
                return f'<div class="alert alert-error">{errors[0]}</div>', 400
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('media_admin.upload'))

        alt_text = request.form.get('alt_text', '').strip() or None
        title = request.form.get('title', '').strip() or None

        media = media_service.save_uploaded_file(
            file=file,
            uploaded_by_id=current_user.id,
            alt_text=alt_text,
            title=title,
        )

        # For HTMX/AJAX requests return JSON
        if request.headers.get('HX-Request') or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': True,
                'media': media.to_dict()
            })

        flash('Datei hochgeladen.', 'success')
        return redirect(url_for('media_admin.detail', id=media.id))

    return render_template('media/admin/upload.html')


@media_admin_bp.route('/<int:id>')
@admin_required
def detail(id: int):
    """View media details and edit metadata."""
    media = db.session.get(Media, id)
    if not media:
        flash('Datei nicht gefunden.', 'error')
        return redirect(url_for('media_admin.library'))

    return render_template(
        'media/admin/detail.html',
        media=media,
    )


@media_admin_bp.route('/<int:id>/edit', methods=['POST'])
@admin_required
def edit(id: int):
    """Update media metadata."""
    media = db.session.get(Media, id)
    if not media:
        flash('Datei nicht gefunden.', 'error')
        return redirect(url_for('media_admin.library'))

    media_service.update_media(
        media=media,
        alt_text=request.form.get('alt_text', '').strip() or None,
        title=request.form.get('title', '').strip() or None,
        caption=request.form.get('caption', '').strip() or None,
    )

    if request.headers.get('HX-Request'):
        return '<div class="alert alert-success">Gespeichert!</div>'

    flash('Metadaten aktualisiert.', 'success')
    return redirect(url_for('media_admin.detail', id=media.id))


@media_admin_bp.route('/<int:id>/delete', methods=['POST', 'DELETE'])
@admin_required
def delete(id: int):
    """Delete media file."""
    media = db.session.get(Media, id)
    if not media:
        flash('Datei nicht gefunden.', 'error')
        return redirect(url_for('media_admin.library'))

    filename = media.filename
    media_service.delete_media(media)

    if request.headers.get('HX-Request'):
        return ''

    flash(f'Datei "{filename}" gelöscht.', 'info')
    return redirect(url_for('media_admin.library'))


# ==============================================
# HTMX / API Endpoints
# ==============================================

@media_admin_bp.route('/picker')
@admin_required
def picker():
    """Media picker modal content for embedding in other plugins."""
    field_name = request.args.get('field', 'media_id')
    accept = request.args.get('accept', 'image/*')
    search_query = request.args.get('q')

    # Determine media type from accept
    media_type = None
    if 'image' in accept:
        media_type = MediaType.IMAGE.value

    if search_query:
        media_items = media_service.search_media(search_query, limit=24)
    else:
        media_items = media_service.get_media_list(media_type=media_type, limit=24)

    return render_template(
        'media/admin/_picker.html',
        media_items=media_items,
        field_name=field_name,
        accept=accept,
        search_query=search_query,
    )


@media_admin_bp.route('/search')
@admin_required
def search():
    """Search media (HTMX endpoint)."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return render_template('media/admin/_grid.html', media_items=[])

    media_items = media_service.search_media(query, limit=24)
    return render_template('media/admin/_grid.html', media_items=media_items)


@media_admin_bp.route('/grid')
@admin_required
def grid():
    """Return media grid for HTMX updates."""
    media_type = request.args.get('type')
    source = request.args.get('source')
    offset = request.args.get('offset', 0, type=int)

    media_items = media_service.get_media_list(
        media_type=media_type,
        source=source,
        limit=24,
        offset=offset
    )
    return render_template('media/admin/_grid.html', media_items=media_items)


# ==============================================
# Stock Photo Integration
# ==============================================

@media_admin_bp.route('/stock')
@admin_required
def stock_search():
    """Unified stock photo search interface (Pexels + Unsplash)."""
    provider = request.args.get('provider', 'pexels')
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    orientation = request.args.get('orientation')

    results = {}
    is_configured = False

    if provider == 'pexels':
        from .services import pexels_service
        is_configured = pexels_service.is_configured()
        if is_configured:
            if query:
                results = pexels_service.search_photos(
                    query=query,
                    per_page=15,
                    page=page,
                    orientation=orientation,
                )
            else:
                results = pexels_service.get_curated_photos(per_page=15, page=page)
    elif provider == 'unsplash':
        from .services import unsplash_service
        is_configured = unsplash_service.is_configured()
        if is_configured:
            if query:
                results = unsplash_service.search_photos(
                    query=query,
                    per_page=15,
                    page=page,
                    orientation=orientation,
                )
            else:
                results = unsplash_service.get_editorial_photos(per_page=15, page=page)

    return render_template(
        'media/admin/stock_search.html',
        provider=provider,
        query=query,
        results=results,
        page=page,
        orientation=orientation,
        is_configured=is_configured,
    )


@media_admin_bp.route('/stock/import', methods=['POST'])
@admin_required
def stock_import():
    """Import a stock photo into the media library."""
    provider = request.form.get('provider', 'pexels')
    photo_url = request.form.get('photo_url')
    photo_id = request.form.get('photo_id')
    photographer = request.form.get('photographer', 'Unknown')
    photographer_url = request.form.get('photographer_url', '')
    alt_text = request.form.get('alt_text', '').strip() or None

    if not photo_url or not photo_id:
        flash('Ungültige Anfrage.', 'error')
        return redirect(url_for('media_admin.stock_search', provider=provider))

    media = None

    if provider == 'pexels':
        from .services import pexels_service
        media = pexels_service.import_photo(
            photo_url=photo_url,
            pexels_id=photo_id,
            photographer=photographer,
            photographer_url=photographer_url,
            uploaded_by_id=current_user.id,
            alt_text=alt_text,
        )
    elif provider == 'unsplash':
        from .services import unsplash_service
        media = unsplash_service.import_photo(
            photo_url=photo_url,
            unsplash_id=photo_id,
            photographer=photographer,
            photographer_url=photographer_url,
            uploaded_by_id=current_user.id,
            alt_text=alt_text,
        )

    if media:
        flash(f'Bild "{media.title}" importiert.', 'success')
        return redirect(url_for('media_admin.detail', id=media.id))
    else:
        flash('Import fehlgeschlagen.', 'error')
        return redirect(url_for('media_admin.stock_search', provider=provider))
