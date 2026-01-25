"""API routes for satellite projects.

Provides:
- Plugin catalog with pricing
- Project types
- License verification and history
- Trial management
- Plugin download (ZIP)
"""
from functools import wraps
from flask import Blueprint, jsonify, request, current_app, send_file

from v_flask import db
from app.models import (
    Project, ProjectType, PluginCategory, PluginMeta, PluginVersion, License, LicenseHistory,
)
from app.services.trial import start_plugin_trial
from app.services.pricing import get_plugin_price_matrix

api_bp = Blueprint('api', __name__)


def require_api_key(f):
    """Decorator to require valid API key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        project = db.session.query(Project).filter_by(
            api_key=api_key,
            is_active=True
        ).first()

        if not project:
            return jsonify({'error': 'Invalid or inactive API key'}), 401

        # Add project to request context
        request.project = project
        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# Plugin Catalog (public)
# ============================================================================

@api_bp.route('/plugins')
def list_plugins():
    """List all published plugins.

    Returns plugin metadata. Filters by development phase:
    - Without API key: Only stable plugins (v1+)
    - With superadmin API key: All plugins including alpha/beta

    Query params:
        api_key: Optional API key for authentication
    """
    # Check if caller is a superadmin project
    include_dev = False
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if api_key:
        project = db.session.query(Project).filter_by(
            api_key=api_key,
            is_active=True
        ).first()
        if project and project.can_see_dev_plugins:
            include_dev = True

    # Build query
    query = db.session.query(PluginMeta).filter_by(is_published=True)

    # Filter by phase: only show stable plugins (v1+) unless superadmin
    if not include_dev:
        query = query.filter(PluginMeta.phase.like('v%'))

    plugins = query.order_by(PluginMeta.name).all()

    return jsonify({
        'plugins': [
            {
                'name': p.name,
                'display_name': p.display_name,
                'description': p.description,
                'version': p.version,
                'price_cents': p.price_cents,
                'price_display': p.price_display,
                'is_free': p.is_free,
                'is_featured': p.is_featured,
                # Category info
                'category': p.category,  # Legacy string field
                'category_info': {
                    'code': p.category_rel.code,
                    'name_de': p.category_rel.name_de,
                    'icon': p.category_rel.icon,
                    'color_hex': p.category_rel.color_hex,
                } if p.category_rel else None,
                # Icon and phase
                'icon': p.icon,
                'has_trial': p.has_trial,
                'phase': p.phase,
                'phase_display': p.phase_display,
                'phase_badge': p.phase_badge,
            }
            for p in plugins
        ]
    })


@api_bp.route('/plugins/<plugin_name>')
def get_plugin(plugin_name: str):
    """Get plugin details.

    Returns full plugin metadata including long description.
    Only returns dev plugins (alpha/beta) for superadmin projects.
    """
    # Check if caller is a superadmin project
    include_dev = False
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if api_key:
        project = db.session.query(Project).filter_by(
            api_key=api_key,
            is_active=True
        ).first()
        if project and project.can_see_dev_plugins:
            include_dev = True

    plugin = db.session.query(PluginMeta).filter_by(
        name=plugin_name,
        is_published=True
    ).first()

    if not plugin:
        return jsonify({'error': 'Plugin not found'}), 404

    # Check phase visibility
    if not include_dev and not plugin.is_stable:
        return jsonify({'error': 'Plugin not found'}), 404

    # Get price matrix for differentiated pricing
    prices = get_plugin_price_matrix(plugin.id)

    return jsonify({
        'name': plugin.name,
        'display_name': plugin.display_name,
        'description': plugin.description,
        'long_description': plugin.long_description,
        'version': plugin.version,
        'price_cents': plugin.price_cents,
        'price_display': plugin.price_display,
        'is_free': plugin.is_free,
        'is_featured': plugin.is_featured,
        'screenshot_url': plugin.screenshot_url,
        # Category info
        'category': plugin.category,  # Legacy string field
        'category_info': {
            'code': plugin.category_rel.code,
            'name_de': plugin.category_rel.name_de,
            'icon': plugin.category_rel.icon,
            'color_hex': plugin.category_rel.color_hex,
            'description_de': plugin.category_rel.description_de,
        } if plugin.category_rel else None,
        # Icon and other fields
        'icon': plugin.icon,
        'min_v_flask_version': plugin.min_v_flask_version,
        'has_trial': plugin.has_trial,
        'prices': prices,  # Differentiated pricing per project type
        'phase': plugin.phase,
        'phase_display': plugin.phase_display,
        'phase_badge': plugin.phase_badge,
    })


# ============================================================================
# Project Info (authenticated)
# ============================================================================

@api_bp.route('/projects/me')
@require_api_key
def get_current_project():
    """Get current project info based on API key."""
    project = request.project

    # Project type info
    project_type_info = None
    if project.project_type:
        project_type_info = {
            'code': project.project_type.code,
            'name': project.project_type.name,
            'trial_days': project.project_type.trial_days,
        }

    return jsonify({
        'id': project.id,
        'name': project.name,
        'slug': project.slug,
        'owner_email': project.owner_email,
        'is_active': project.is_active,
        # New fields
        'project_type': project_type_info,
        'is_in_trial': project.is_in_trial,
        'trial_days_remaining': project.trial_days_remaining,
    })


@api_bp.route('/projects/me/licenses')
@require_api_key
def get_project_licenses():
    """Get all active licenses for current project."""
    project = request.project
    licenses = project.active_licenses

    return jsonify({
        'licenses': [
            {
                'id': lic.id,
                'plugin_name': lic.plugin_name,
                'purchased_at': lic.purchased_at.isoformat(),
                'expires_at': lic.expires_at.isoformat() if lic.expires_at else None,
                'is_perpetual': lic.is_perpetual,
                # New fields
                'status': lic.status,
                'status_display': lic.status_display,
                'billing_cycle': lic.billing_cycle,
                'next_billing_date': lic.next_billing_date.isoformat() if lic.next_billing_date else None,
                'is_trial': lic.is_trial,
            }
            for lic in licenses
        ]
    })


# ============================================================================
# Plugin Download (authenticated + licensed)
# ============================================================================

@api_bp.route('/plugins/<plugin_name>/download', methods=['POST'])
@require_api_key
def download_plugin(plugin_name: str):
    """Download plugin as ZIP archive.

    Requires:
    - Valid API key
    - Active license for the plugin (or plugin is free)
    """
    project = request.project

    # Check if plugin exists
    plugin = db.session.query(PluginMeta).filter_by(
        name=plugin_name,
        is_published=True
    ).first()

    if not plugin:
        return jsonify({'error': 'Plugin not found'}), 404

    # Check license (skip for free plugins)
    if not plugin.is_free:
        if not project.has_license_for(plugin_name):
            return jsonify({
                'error': 'No active license for this plugin',
                'plugin': plugin_name,
                'price_cents': plugin.price_cents,
            }), 403

    # Package and send plugin
    from app.services.plugin_packager import package_plugin

    try:
        zip_path = package_plugin(plugin_name)
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f'{plugin_name}-{plugin.version}.zip',
            mimetype='application/zip'
        )
    except FileNotFoundError:
        return jsonify({'error': 'Plugin source not found'}), 500
    except Exception as e:
        current_app.logger.error(f'Plugin packaging failed: {e}')
        return jsonify({'error': 'Plugin packaging failed'}), 500


# ============================================================================
# Project Types (public)
# ============================================================================

@api_bp.route('/project-types')
def list_project_types():
    """List all active project types.

    Returns project types with their trial configurations.
    Used by onboarding to let users choose their project type.
    """
    types = db.session.query(ProjectType).filter_by(
        is_active=True
    ).order_by(ProjectType.sort_order).all()

    return jsonify({
        'project_types': [
            {
                'id': t.id,
                'code': t.code,
                'name': t.name,
                'description': t.description,
                'trial_days': t.trial_days,
                'is_free': t.is_free,
                'has_trial': t.has_trial,
            }
            for t in types
        ]
    })


@api_bp.route('/plugin-categories')
def list_plugin_categories():
    """List all plugin categories.

    Returns categories with their display info for filter UI.
    """
    categories = PluginCategory.get_all_ordered()

    return jsonify({
        'categories': [
            {
                'id': c.id,
                'code': c.code,
                'name_de': c.name_de,
                'description_de': c.description_de,
                'icon': c.icon,
                'color_hex': c.color_hex,
            }
            for c in categories
        ]
    })


# ============================================================================
# Plugin Prices and Versions (public)
# ============================================================================

@api_bp.route('/plugins/<plugin_name>/prices')
def get_plugin_prices(plugin_name: str):
    """Get price matrix for a plugin.

    Returns prices grouped by project type.
    """
    plugin = db.session.query(PluginMeta).filter_by(
        name=plugin_name,
        is_published=True
    ).first()

    if not plugin:
        return jsonify({'error': 'Plugin not found'}), 404

    prices = get_plugin_price_matrix(plugin.id)

    return jsonify({
        'plugin_name': plugin_name,
        'base_price_cents': plugin.price_cents,
        'prices': prices,
    })


@api_bp.route('/plugins/<plugin_name>/versions')
def get_plugin_versions(plugin_name: str):
    """Get version history for a plugin.

    Returns all versions, newest first.
    """
    plugin = db.session.query(PluginMeta).filter_by(
        name=plugin_name,
        is_published=True
    ).first()

    if not plugin:
        return jsonify({'error': 'Plugin not found'}), 404

    versions = PluginVersion.get_for_plugin(plugin.id, only_stable=False)

    return jsonify({
        'plugin_name': plugin_name,
        'current_version': plugin.version,
        'versions': [
            {
                'version': v.version,
                'changelog': v.changelog,
                'release_notes': v.release_notes,
                'min_v_flask_version': v.min_v_flask_version,
                'is_stable': v.is_stable,
                'is_current': v.is_current,
                'is_breaking_change': v.is_breaking_change,
                'download_count': v.download_count,
                'released_at': v.released_at.isoformat() if v.released_at else None,
            }
            for v in versions
        ]
    })


# ============================================================================
# Trial Management (authenticated)
# ============================================================================

@api_bp.route('/plugins/<plugin_name>/trial', methods=['POST'])
@require_api_key
def start_trial(plugin_name: str):
    """Start a trial for a plugin.

    Creates a trial license for the current project.

    Returns:
        201: Trial started successfully
        400: Trial not allowed or already exists
        404: Plugin not found
    """
    project = request.project

    # Check if plugin exists
    plugin = db.session.query(PluginMeta).filter_by(
        name=plugin_name,
        is_published=True
    ).first()

    if not plugin:
        return jsonify({'error': 'Plugin not found'}), 404

    if not plugin.has_trial:
        return jsonify({'error': 'This plugin does not offer a trial'}), 400

    # Start trial
    license = start_plugin_trial(
        project_id=project.id,
        plugin_name=plugin_name,
        performed_by=project.owner_email,
    )

    if not license:
        return jsonify({
            'error': 'Could not start trial. A license may already exist.',
        }), 400

    return jsonify({
        'message': 'Trial started successfully',
        'license': {
            'id': license.id,
            'plugin_name': license.plugin_name,
            'status': license.status,
            'expires_at': license.expires_at.isoformat() if license.expires_at else None,
        }
    }), 201


# ============================================================================
# License History (authenticated)
# ============================================================================

@api_bp.route('/projects/me/licenses/<plugin_name>/history')
@require_api_key
def get_license_history(plugin_name: str):
    """Get audit trail for a license.

    Returns all history entries for the license, newest first.
    """
    project = request.project

    # Find license
    license = db.session.query(License).filter_by(
        project_id=project.id,
        plugin_name=plugin_name
    ).first()

    if not license:
        return jsonify({'error': 'License not found'}), 404

    history = LicenseHistory.get_for_license(license.id)

    return jsonify({
        'plugin_name': plugin_name,
        'license_id': license.id,
        'history': [
            {
                'action': h.action,
                'old_status': h.old_status,
                'new_status': h.new_status,
                'old_expires_at': h.old_expires_at.isoformat() if h.old_expires_at else None,
                'new_expires_at': h.new_expires_at.isoformat() if h.new_expires_at else None,
                'performed_by': h.performed_by,
                'performed_by_type': h.performed_by_type,
                'reason': h.reason,
                'created_at': h.created_at.isoformat(),
            }
            for h in history
        ]
    })
