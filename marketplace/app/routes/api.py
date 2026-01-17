"""API routes for satellite projects.

Provides:
- Plugin catalog
- License verification
- Plugin download (ZIP)
"""
from functools import wraps
from flask import Blueprint, jsonify, request, current_app, send_file

from v_flask import db
from app.models import Project, PluginMeta, License

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

    Returns plugin metadata without requiring authentication.
    Used by satellite projects to display available plugins.
    """
    plugins = db.session.query(PluginMeta).filter_by(
        is_published=True
    ).order_by(PluginMeta.name).all()

    return jsonify({
        'plugins': [
            {
                'name': p.name,
                'display_name': p.display_name,
                'description': p.description,
                'version': p.version,
                'price_cents': p.price_cents,
                'is_free': p.is_free,
                'is_featured': p.is_featured,
            }
            for p in plugins
        ]
    })


@api_bp.route('/plugins/<plugin_name>')
def get_plugin(plugin_name: str):
    """Get plugin details.

    Returns full plugin metadata including long description.
    """
    plugin = db.session.query(PluginMeta).filter_by(
        name=plugin_name,
        is_published=True
    ).first()

    if not plugin:
        return jsonify({'error': 'Plugin not found'}), 404

    return jsonify({
        'name': plugin.name,
        'display_name': plugin.display_name,
        'description': plugin.description,
        'long_description': plugin.long_description,
        'version': plugin.version,
        'price_cents': plugin.price_cents,
        'is_free': plugin.is_free,
        'is_featured': plugin.is_featured,
        'screenshot_url': plugin.screenshot_url,
    })


# ============================================================================
# Project Info (authenticated)
# ============================================================================

@api_bp.route('/projects/me')
@require_api_key
def get_current_project():
    """Get current project info based on API key."""
    project = request.project

    return jsonify({
        'id': project.id,
        'name': project.name,
        'slug': project.slug,
        'owner_email': project.owner_email,
        'is_active': project.is_active,
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
                'plugin_name': lic.plugin_name,
                'purchased_at': lic.purchased_at.isoformat(),
                'expires_at': lic.expires_at.isoformat() if lic.expires_at else None,
                'is_perpetual': lic.is_perpetual,
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
