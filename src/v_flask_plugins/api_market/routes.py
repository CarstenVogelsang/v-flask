"""Routes for the API Market plugin.

Provides:
    - Public API documentation at /api-market
    - Admin interface for managing APIs at /admin/api-market
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app

from v_flask.extensions import db
from v_flask.auth import admin_required, login_required

from .models import ExternalApi

# Public blueprint for API documentation
api_market_bp = Blueprint(
    'api_market',
    __name__,
    template_folder='templates'
)

# Admin blueprint for managing APIs
api_market_admin_bp = Blueprint(
    'api_market_admin',
    __name__,
    template_folder='templates'
)


# --- Public Routes ---

@api_market_bp.route('/')
def list_apis():
    """Display list of available APIs."""
    apis = db.session.query(ExternalApi).filter_by(
        status='active'
    ).order_by(ExternalApi.name).all()

    return render_template('api_market/public/list.html', apis=apis)


@api_market_bp.route('/<slug>')
def api_detail(slug: str):
    """Display API quickstart documentation."""
    api = db.session.query(ExternalApi).filter_by(slug=slug, status='active').first()
    if not api:
        flash('API nicht gefunden.', 'error')
        return redirect(url_for('api_market.list_apis'))

    # Refresh spec if needed
    if api.needs_refresh(current_app.config.get('API_MARKET_CACHE_TTL', 3600)):
        try:
            from v_flask_plugins.api_market.services.openapi_fetcher import fetch_and_cache_spec
            fetch_and_cache_spec(api)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f'Failed to refresh spec for {slug}: {e}')

    return render_template('api_market/public/quickstart.html', api=api)


@api_market_bp.route('/<slug>/docs')
def api_docs(slug: str):
    """Display full API documentation."""
    api = db.session.query(ExternalApi).filter_by(slug=slug, status='active').first()
    if not api:
        flash('API nicht gefunden.', 'error')
        return redirect(url_for('api_market.list_apis'))

    return render_template('api_market/public/endpoints.html', api=api)


@api_market_bp.route('/my-keys')
@login_required
def my_keys():
    """Display user's API keys (requires login)."""
    # This will call the external API to get user's keys
    return render_template('api_market/public/my_keys.html')


# --- Admin Routes ---

@api_market_admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard for API marketplace."""
    apis = db.session.query(ExternalApi).order_by(ExternalApi.created_at.desc()).all()
    active_count = sum(1 for a in apis if a.status == 'active')

    return render_template(
        'api_market/admin/dashboard.html',
        apis=apis,
        active_count=active_count
    )


@api_market_admin_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_api():
    """Add a new API to the marketplace."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip()
        spec_url = request.form.get('spec_url', '').strip()
        base_url = request.form.get('base_url', '').strip()
        description = request.form.get('description', '').strip()

        # Basic validation
        errors = []
        if not name:
            errors.append('Name ist erforderlich.')
        if not slug:
            errors.append('Slug ist erforderlich.')
        elif db.session.query(ExternalApi).filter_by(slug=slug).first():
            errors.append('Dieser Slug wird bereits verwendet.')
        if not spec_url:
            errors.append('OpenAPI Spec URL ist erforderlich.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'api_market/admin/add.html',
                name=name, slug=slug, spec_url=spec_url,
                base_url=base_url, description=description
            )

        # Create API
        api = ExternalApi(
            name=name,
            slug=slug,
            spec_url=spec_url,
            base_url=base_url or None,
            description=description or None,
        )
        db.session.add(api)

        # Try to fetch spec immediately
        try:
            from v_flask_plugins.api_market.services.openapi_fetcher import fetch_and_cache_spec
            fetch_and_cache_spec(api)
        except Exception as e:
            current_app.logger.warning(f'Could not fetch initial spec: {e}')

        db.session.commit()
        flash(f'API "{name}" erfolgreich hinzugefügt.', 'success')
        return redirect(url_for('api_market_admin.dashboard'))

    return render_template('api_market/admin/add.html')


@api_market_admin_bp.route('/<int:api_id>', methods=['GET', 'POST'])
@admin_required
def edit_api(api_id: int):
    """Edit an existing API."""
    api = db.session.get(ExternalApi, api_id)
    if not api:
        flash('API nicht gefunden.', 'error')
        return redirect(url_for('api_market_admin.dashboard'))

    if request.method == 'POST':
        api.name = request.form.get('name', '').strip() or api.name
        api.description = request.form.get('description', '').strip()
        api.spec_url = request.form.get('spec_url', '').strip() or api.spec_url
        api.base_url = request.form.get('base_url', '').strip() or None
        api.status = request.form.get('status', 'active')
        api.icon_url = request.form.get('icon_url', '').strip() or None

        db.session.commit()
        flash('API aktualisiert.', 'success')
        return redirect(url_for('api_market_admin.dashboard'))

    return render_template('api_market/admin/edit.html', api=api)


@api_market_admin_bp.route('/<int:api_id>/refresh', methods=['POST'])
@admin_required
def refresh_spec(api_id: int):
    """Refresh the OpenAPI spec for an API."""
    api = db.session.get(ExternalApi, api_id)
    if not api:
        flash('API nicht gefunden.', 'error')
        return redirect(url_for('api_market_admin.dashboard'))

    try:
        from v_flask_plugins.api_market.services.openapi_fetcher import fetch_and_cache_spec
        fetch_and_cache_spec(api)
        db.session.commit()
        flash(f'Spec für "{api.name}" aktualisiert.', 'success')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {e}', 'error')

    return redirect(url_for('api_market_admin.dashboard'))


@api_market_admin_bp.route('/<int:api_id>/delete', methods=['POST'])
@admin_required
def delete_api(api_id: int):
    """Delete an API from the marketplace."""
    api = db.session.get(ExternalApi, api_id)
    if api:
        name = api.name
        db.session.delete(api)
        db.session.commit()
        flash(f'API "{name}" gelöscht.', 'success')

    return redirect(url_for('api_market_admin.dashboard'))
