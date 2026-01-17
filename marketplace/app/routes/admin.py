"""Admin routes for marketplace management.

Handles:
- Project management (create, edit, delete, API key regeneration)
- License management (grant, revoke)
- Plugin metadata management (pricing, publishing)
"""
import secrets
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from v_flask import db
from v_flask.auth import permission_required
from app.models import Project, License, PluginMeta, Order

admin_bp = Blueprint(
    'marketplace_admin',
    __name__,
    template_folder='../templates/admin'
)


@admin_bp.context_processor
def inject_admin_config():
    """Inject marketplace-specific admin configuration into templates."""
    return {
        'admin_dashboard_url': 'marketplace_admin.dashboard',
        'admin_title': 'Marketplace Admin',
    }


# ============================================================================
# Dashboard
# ============================================================================

@admin_bp.route('/')
@login_required
@permission_required('admin.*')
def dashboard():
    """Marketplace admin dashboard."""
    projects_count = db.session.query(Project).count()
    licenses_count = db.session.query(License).count()
    plugins_count = db.session.query(PluginMeta).filter_by(is_published=True).count()
    orders_count = db.session.query(Order).filter_by(status='completed').count()

    recent_orders = db.session.query(Order).order_by(
        Order.created_at.desc()
    ).limit(5).all()

    return render_template(
        'dashboard.html',
        projects_count=projects_count,
        licenses_count=licenses_count,
        plugins_count=plugins_count,
        orders_count=orders_count,
        recent_orders=recent_orders,
    )


# ============================================================================
# Projects
# ============================================================================

@admin_bp.route('/projects')
@login_required
@permission_required('admin.*')
def project_list():
    """List all projects."""
    projects = db.session.query(Project).order_by(Project.name).all()
    return render_template('projects/list.html', projects=projects)


@admin_bp.route('/projects/new', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def project_create():
    """Create a new project."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        owner_email = request.form.get('owner_email', '').strip()

        if not name or not owner_email:
            flash('Name und E-Mail sind erforderlich.', 'error')
            return render_template('projects/form.html', project=None)

        # Generate unique slug
        slug = name.lower().replace(' ', '-').replace('_', '-')
        existing = db.session.query(Project).filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{secrets.token_hex(4)}"

        # Generate API key
        api_key = f"vf_proj_{secrets.token_urlsafe(32)}"

        project = Project(
            name=name,
            slug=slug,
            owner_email=owner_email,
            api_key=api_key,
        )
        db.session.add(project)
        db.session.commit()

        flash(f'Projekt "{name}" erstellt. API-Key: {api_key}', 'success')
        return redirect(url_for('marketplace_admin.project_detail', project_id=project.id))

    return render_template('projects/form.html', project=None)


@admin_bp.route('/projects/<int:project_id>')
@login_required
@permission_required('admin.*')
def project_detail(project_id: int):
    """View project details."""
    project = db.session.get(Project, project_id)
    if not project:
        flash('Projekt nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.project_list'))

    return render_template('projects/detail.html', project=project)


@admin_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def project_edit(project_id: int):
    """Edit a project."""
    project = db.session.get(Project, project_id)
    if not project:
        flash('Projekt nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.project_list'))

    if request.method == 'POST':
        project.name = request.form.get('name', '').strip() or project.name
        project.owner_email = request.form.get('owner_email', '').strip() or project.owner_email
        project.is_active = request.form.get('is_active') == 'on'

        db.session.commit()
        flash('Projekt aktualisiert.', 'success')
        return redirect(url_for('marketplace_admin.project_detail', project_id=project.id))

    return render_template('projects/form.html', project=project)


@admin_bp.route('/projects/<int:project_id>/regenerate-key', methods=['POST'])
@login_required
@permission_required('admin.*')
def project_regenerate_key(project_id: int):
    """Regenerate API key for a project."""
    project = db.session.get(Project, project_id)
    if not project:
        flash('Projekt nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.project_list'))

    new_key = f"vf_proj_{secrets.token_urlsafe(32)}"
    project.api_key = new_key
    db.session.commit()

    flash(f'Neuer API-Key generiert: {new_key}', 'success')
    return redirect(url_for('marketplace_admin.project_detail', project_id=project.id))


# ============================================================================
# Licenses
# ============================================================================

@admin_bp.route('/licenses')
@login_required
@permission_required('admin.*')
def license_list():
    """List all licenses."""
    licenses = db.session.query(License).order_by(License.purchased_at.desc()).all()
    return render_template('licenses/list.html', licenses=licenses)


@admin_bp.route('/licenses/grant', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def license_grant():
    """Grant a new license to a project."""
    projects = db.session.query(Project).filter_by(is_active=True).order_by(Project.name).all()
    plugins = db.session.query(PluginMeta).filter_by(is_published=True).order_by(PluginMeta.name).all()

    if request.method == 'POST':
        project_id = request.form.get('project_id', type=int)
        plugin_name = request.form.get('plugin_name', '').strip()
        notes = request.form.get('notes', '').strip()

        if not project_id or not plugin_name:
            flash('Projekt und Plugin sind erforderlich.', 'error')
            return render_template(
                'licenses/form.html',
                projects=projects,
                plugins=plugins,
                license=None
            )

        # Check if license already exists
        existing = db.session.query(License).filter_by(
            project_id=project_id,
            plugin_name=plugin_name
        ).first()

        if existing:
            flash('Lizenz existiert bereits für dieses Projekt/Plugin.', 'error')
            return render_template(
                'licenses/form.html',
                projects=projects,
                plugins=plugins,
                license=None
            )

        license = License(
            project_id=project_id,
            plugin_name=plugin_name,
            notes=notes or 'Manuell vergeben',
        )
        db.session.add(license)
        db.session.commit()

        flash(f'Lizenz für "{plugin_name}" vergeben.', 'success')
        return redirect(url_for('marketplace_admin.license_list'))

    return render_template(
        'licenses/form.html',
        projects=projects,
        plugins=plugins,
        license=None
    )


@admin_bp.route('/licenses/<int:license_id>/revoke', methods=['POST'])
@login_required
@permission_required('admin.*')
def license_revoke(license_id: int):
    """Revoke a license."""
    license = db.session.get(License, license_id)
    if not license:
        flash('Lizenz nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.license_list'))

    db.session.delete(license)
    db.session.commit()

    flash('Lizenz widerrufen.', 'success')
    return redirect(url_for('marketplace_admin.license_list'))


# ============================================================================
# Plugins
# ============================================================================

@admin_bp.route('/plugins')
@login_required
@permission_required('admin.*')
def plugin_list():
    """List all plugins with their marketplace metadata."""
    plugins = db.session.query(PluginMeta).order_by(PluginMeta.name).all()
    return render_template('plugins/list.html', plugins=plugins)


@admin_bp.route('/plugins/<int:plugin_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def plugin_edit(plugin_id: int):
    """Edit plugin marketplace metadata (pricing, description)."""
    plugin = db.session.get(PluginMeta, plugin_id)
    if not plugin:
        flash('Plugin nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.plugin_list'))

    if request.method == 'POST':
        plugin.display_name = request.form.get('display_name', '').strip() or plugin.display_name
        plugin.description = request.form.get('description', '').strip()
        plugin.long_description = request.form.get('long_description', '').strip()

        # Parse price (expecting format like "99,00" or "99.00")
        price_str = request.form.get('price', '0').strip().replace(',', '.')
        try:
            price_euros = float(price_str)
            plugin.price_cents = int(price_euros * 100)
        except ValueError:
            plugin.price_cents = 0

        plugin.is_published = request.form.get('is_published') == 'on'
        plugin.is_featured = request.form.get('is_featured') == 'on'

        db.session.commit()
        flash('Plugin aktualisiert.', 'success')
        return redirect(url_for('marketplace_admin.plugin_list'))

    return render_template('plugins/form.html', plugin=plugin)
