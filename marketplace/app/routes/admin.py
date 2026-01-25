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
from v_flask.models import Config
from app.models import (
    Project, License, PluginMeta, Order,
    ProjectType, PluginPrice, PluginVersion, LicenseHistory,
    PluginCategory,
)


def normalize_icon(icon_value: str | None) -> str:
    """Ensure icon has 'ti ti-' prefix for Tabler Icons.

    Args:
        icon_value: Raw icon value from form (e.g., "ti-tag", "ti ti-tag", "tag")

    Returns:
        Normalized icon class string (e.g., "ti ti-tag")
    """
    if not icon_value:
        return 'ti ti-tag'
    icon_value = icon_value.strip()
    if icon_value.startswith('ti ti-'):
        return icon_value
    if icon_value.startswith('ti-'):
        return 'ti ' + icon_value
    return 'ti ti-' + icon_value

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

        plugin.is_published = request.form.get('is_published') == 'on'
        plugin.is_featured = request.form.get('is_featured') == 'on'
        plugin.allow_one_time_purchase = request.form.get('allow_one_time_purchase') == 'on'

        # Category assignment
        category_id = request.form.get('category_id', type=int)
        plugin.category_id = category_id if category_id else None

        db.session.commit()

        # Ensure plugin has prices for base type
        _ensure_base_type_prices(plugin_id)

        flash('Plugin aktualisiert.', 'success')
        return redirect(url_for('marketplace_admin.plugin_list'))

    categories = PluginCategory.get_all_ordered()

    # Get base type and its prices for this plugin
    base_type = db.session.query(ProjectType).filter_by(is_base_type=True).first()
    base_prices = {}
    if base_type:
        prices = db.session.query(PluginPrice).filter_by(
            plugin_id=plugin_id,
            project_type_id=base_type.id
        ).all()
        for p in prices:
            base_prices[p.billing_cycle] = p.price_cents / 100 if p.price_cents else None

    return render_template(
        'plugins/form.html',
        plugin=plugin,
        categories=categories,
        base_type=base_type,
        base_prices=base_prices,
    )


def _ensure_base_type_prices(plugin_id: int) -> None:
    """Ensure plugin has PluginPrice entries for the base project type.

    Creates empty price entries if they don't exist.
    """
    base_type = db.session.query(ProjectType).filter_by(is_base_type=True).first()
    if not base_type:
        return

    for billing_cycle in ['once', 'monthly', 'yearly']:
        existing = db.session.query(PluginPrice).filter_by(
            plugin_id=plugin_id,
            project_type_id=base_type.id,
            billing_cycle=billing_cycle
        ).first()

        if not existing:
            price = PluginPrice(
                plugin_id=plugin_id,
                project_type_id=base_type.id,
                billing_cycle=billing_cycle,
                price_cents=0,
                setup_fee_cents=0,
            )
            db.session.add(price)

    db.session.commit()


# ============================================================================
# Plugin Categories
# ============================================================================

@admin_bp.route('/categories')
@login_required
@permission_required('admin.*')
def category_list():
    """List all plugin categories."""
    categories = PluginCategory.get_all_ordered()
    return render_template('categories/list.html', categories=categories)


@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def category_create():
    """Create a new plugin category."""
    if request.method == 'POST':
        code = request.form.get('code', '').strip().lower().replace(' ', '-')
        name_de = request.form.get('name_de', '').strip()

        if not code or not name_de:
            flash('Code und Name sind erforderlich.', 'error')
            return render_template('categories/form.html', category=None)

        # Check for duplicate code
        existing = PluginCategory.get_by_code(code)
        if existing:
            flash(f'Eine Kategorie mit Code "{code}" existiert bereits.', 'error')
            return render_template('categories/form.html', category=None)

        category = PluginCategory(
            code=code,
            name_de=name_de,
            description_de=request.form.get('description_de', '').strip(),
            icon=normalize_icon(request.form.get('icon', '')),
            color_hex=request.form.get('color_hex', '#6b7280').strip(),
            sort_order=int(request.form.get('sort_order', 0)),
        )
        db.session.add(category)
        db.session.commit()

        flash(f'Kategorie "{name_de}" erstellt.', 'success')
        return redirect(url_for('marketplace_admin.category_list'))

    return render_template('categories/form.html', category=None)


@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def category_edit(category_id: int):
    """Edit a plugin category."""
    category = db.session.get(PluginCategory, category_id)
    if not category:
        flash('Kategorie nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.category_list'))

    if request.method == 'POST':
        category.name_de = request.form.get('name_de', '').strip() or category.name_de
        category.description_de = request.form.get('description_de', '').strip()
        category.icon = normalize_icon(request.form.get('icon', category.icon))
        category.color_hex = request.form.get('color_hex', category.color_hex).strip()
        category.sort_order = int(request.form.get('sort_order', category.sort_order))

        db.session.commit()
        flash('Kategorie aktualisiert.', 'success')
        return redirect(url_for('marketplace_admin.category_list'))

    return render_template('categories/form.html', category=category)


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@permission_required('admin.*')
def category_delete(category_id: int):
    """Delete a plugin category."""
    category = db.session.get(PluginCategory, category_id)
    if not category:
        flash('Kategorie nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.category_list'))

    # Check if any plugins use this category
    plugin_count = db.session.query(PluginMeta).filter_by(category_id=category_id).count()
    if plugin_count > 0:
        flash(f'Kategorie kann nicht gelöscht werden - {plugin_count} Plugin(s) verwenden sie.', 'error')
        return redirect(url_for('marketplace_admin.category_list'))

    db.session.delete(category)
    db.session.commit()
    flash(f'Kategorie "{category.name_de}" gelöscht.', 'success')
    return redirect(url_for('marketplace_admin.category_list'))


# ============================================================================
# Project Types
# ============================================================================

@admin_bp.route('/project-types')
@login_required
@permission_required('admin.*')
def project_type_list():
    """List all project types."""
    types = db.session.query(ProjectType).order_by(ProjectType.sort_order).all()
    return render_template('project_types/list.html', project_types=types)


@admin_bp.route('/project-types/new', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def project_type_create():
    """Create a new project type."""
    if request.method == 'POST':
        code = request.form.get('code', '').strip().lower().replace(' ', '_')
        name = request.form.get('name', '').strip()

        if not code or not name:
            flash('Code und Name sind erforderlich.', 'error')
            return render_template('project_types/form.html', project_type=None)

        # Check for duplicate code
        existing = db.session.query(ProjectType).filter_by(code=code).first()
        if existing:
            flash(f'Ein Projekttyp mit Code "{code}" existiert bereits.', 'error')
            return render_template('project_types/form.html', project_type=None)

        is_base_type = request.form.get('is_base_type') == 'on'

        # Ensure only one base type exists
        if is_base_type:
            db.session.query(ProjectType).filter(
                ProjectType.is_base_type == True
            ).update({'is_base_type': False})

        project_type = ProjectType(
            code=code,
            name=name,
            description=request.form.get('description', '').strip(),
            trial_days=int(request.form.get('trial_days', 14)),
            is_free=request.form.get('is_free') == 'on',
            is_active=request.form.get('is_active') == 'on',
            is_base_type=is_base_type,
            sort_order=int(request.form.get('sort_order', 0)),
        )
        db.session.add(project_type)
        db.session.commit()

        flash(f'Projekttyp "{name}" erstellt.', 'success')
        return redirect(url_for('marketplace_admin.project_type_list'))

    return render_template('project_types/form.html', project_type=None)


@admin_bp.route('/project-types/<int:type_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def project_type_edit(type_id: int):
    """Edit a project type."""
    project_type = db.session.get(ProjectType, type_id)
    if not project_type:
        flash('Projekttyp nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.project_type_list'))

    if request.method == 'POST':
        project_type.name = request.form.get('name', '').strip() or project_type.name
        project_type.description = request.form.get('description', '').strip()
        project_type.trial_days = int(request.form.get('trial_days', project_type.trial_days))
        project_type.is_free = request.form.get('is_free') == 'on'
        project_type.is_active = request.form.get('is_active') == 'on'
        project_type.sort_order = int(request.form.get('sort_order', project_type.sort_order))

        is_base_type = request.form.get('is_base_type') == 'on'

        # Ensure only one base type exists
        if is_base_type and not project_type.is_base_type:
            db.session.query(ProjectType).filter(
                ProjectType.is_base_type == True,
                ProjectType.id != project_type.id
            ).update({'is_base_type': False})

        project_type.is_base_type = is_base_type

        db.session.commit()
        flash('Projekttyp aktualisiert.', 'success')
        return redirect(url_for('marketplace_admin.project_type_list'))

    return render_template('project_types/form.html', project_type=project_type)


@admin_bp.route('/project-types/<int:type_id>/toggle', methods=['POST'])
@login_required
@permission_required('admin.*')
def project_type_toggle(type_id: int):
    """Toggle active status of a project type (HTMX)."""
    project_type = db.session.get(ProjectType, type_id)
    if not project_type:
        flash('Projekttyp nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.project_type_list'))

    project_type.is_active = not project_type.is_active
    db.session.commit()

    # Return partial for HTMX
    if request.headers.get('HX-Request'):
        status_class = 'badge-success' if project_type.is_active else 'badge-ghost'
        status_text = 'Aktiv' if project_type.is_active else 'Inaktiv'
        return f'''
        <span class="badge {status_class}">{status_text}</span>
        '''

    flash(f'Status geändert: {project_type.name}', 'success')
    return redirect(url_for('marketplace_admin.project_type_list'))


# ============================================================================
# Plugin Prices
# ============================================================================

@admin_bp.route('/plugins/<int:plugin_id>/prices', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def plugin_prices(plugin_id: int):
    """Manage plugin prices (price matrix with inline editing)."""
    plugin = db.session.get(PluginMeta, plugin_id)
    if not plugin:
        flash('Plugin nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.plugin_list'))

    project_types = db.session.query(ProjectType).filter_by(
        is_active=True
    ).order_by(ProjectType.sort_order).all()

    billing_cycles = ['once', 'monthly', 'yearly']

    # Get yearly discount from config (default 10%)
    yearly_discount = int(Config.get_value('marketplace.yearly_discount_percent', '10'))

    # Handle HTMX inline edit
    if request.method == 'POST':
        project_type_id = request.form.get('project_type_id', type=int)
        billing_cycle = request.form.get('billing_cycle', '')
        field = request.form.get('field', 'price_cents')

        # Parse price value
        value_str = request.form.get('value', '0').strip().replace(',', '.').replace('€', '').strip()
        try:
            value_euros = float(value_str)
            value_cents = int(value_euros * 100)
        except ValueError:
            value_cents = 0

        # Find or create price entry
        price = db.session.query(PluginPrice).filter_by(
            plugin_id=plugin_id,
            project_type_id=project_type_id,
            billing_cycle=billing_cycle
        ).first()

        if not price:
            price = PluginPrice(
                plugin_id=plugin_id,
                project_type_id=project_type_id,
                billing_cycle=billing_cycle,
                price_cents=0,
                setup_fee_cents=0,
            )
            db.session.add(price)

        if field == 'setup_fee_cents':
            price.setup_fee_cents = value_cents
        else:
            price.price_cents = value_cents

        # Auto-calculate yearly price when monthly is changed
        if billing_cycle == 'monthly' and field == 'price_cents':
            yearly_price = db.session.query(PluginPrice).filter_by(
                plugin_id=plugin_id,
                project_type_id=project_type_id,
                billing_cycle='yearly'
            ).first()

            if not yearly_price:
                yearly_price = PluginPrice(
                    plugin_id=plugin_id,
                    project_type_id=project_type_id,
                    billing_cycle='yearly',
                    price_cents=0,
                    setup_fee_cents=0,
                )
                db.session.add(yearly_price)

            # Formula: yearly = monthly * 12 * (1 - discount/100)
            yearly_cents = int(value_cents * 12 * (1 - yearly_discount / 100))
            yearly_price.price_cents = yearly_cents

        db.session.commit()

        # Return updated cell for HTMX
        if request.headers.get('HX-Request'):
            display_value = f'{value_cents / 100:.2f}'.replace('.', ',')
            return f'''
            <input type="text"
                   name="value"
                   value="{display_value}"
                   class="input input-bordered input-sm w-24 text-right"
                   hx-post="{url_for('marketplace_admin.plugin_prices', plugin_id=plugin_id)}"
                   hx-trigger="blur changed"
                   hx-vals='{{"project_type_id": {project_type_id}, "billing_cycle": "{billing_cycle}", "field": "{field}"}}'
                   hx-swap="outerHTML">
            '''

    # Build price matrix
    prices = db.session.query(PluginPrice).filter_by(plugin_id=plugin_id).all()
    price_matrix = {}
    for p in prices:
        key = (p.project_type_id, p.billing_cycle)
        price_matrix[key] = p

    return render_template(
        'plugins/prices.html',
        plugin=plugin,
        project_types=project_types,
        billing_cycles=billing_cycles,
        price_matrix=price_matrix,
        yearly_discount=yearly_discount,
    )


# ============================================================================
# Plugin Versions
# ============================================================================

@admin_bp.route('/plugins/<int:plugin_id>/versions')
@login_required
@permission_required('admin.*')
def plugin_version_list(plugin_id: int):
    """List all versions of a plugin."""
    plugin = db.session.get(PluginMeta, plugin_id)
    if not plugin:
        flash('Plugin nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.plugin_list'))

    versions = db.session.query(PluginVersion).filter_by(
        plugin_id=plugin_id
    ).order_by(PluginVersion.released_at.desc()).all()

    return render_template(
        'plugins/versions/list.html',
        plugin=plugin,
        versions=versions,
    )


@admin_bp.route('/plugins/<int:plugin_id>/versions/new', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def plugin_version_create(plugin_id: int):
    """Create a new plugin version."""
    plugin = db.session.get(PluginMeta, plugin_id)
    if not plugin:
        flash('Plugin nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.plugin_list'))

    if request.method == 'POST':
        version_str = request.form.get('version', '').strip()

        if not version_str:
            flash('Version ist erforderlich.', 'error')
            return render_template(
                'plugins/versions/form.html',
                plugin=plugin,
                version=None,
            )

        # Check for duplicate version
        existing = db.session.query(PluginVersion).filter_by(
            plugin_id=plugin_id,
            version=version_str
        ).first()
        if existing:
            flash(f'Version "{version_str}" existiert bereits.', 'error')
            return render_template(
                'plugins/versions/form.html',
                plugin=plugin,
                version=None,
            )

        # Unset current flag on other versions if this is the new current
        is_current = request.form.get('is_current') == 'on'
        if is_current:
            db.session.query(PluginVersion).filter_by(
                plugin_id=plugin_id
            ).update({'is_current': False})

        version = PluginVersion(
            plugin_id=plugin_id,
            version=version_str,
            changelog=request.form.get('changelog', '').strip(),
            release_notes=request.form.get('release_notes', '').strip(),
            min_v_flask_version=request.form.get('min_v_flask_version', '').strip() or None,
            is_stable=request.form.get('is_stable') == 'on',
            is_breaking_change=request.form.get('is_breaking_change') == 'on',
            is_current=is_current,
            released_at=datetime.now(timezone.utc),
        )
        db.session.add(version)

        # Update plugin's version field if this is current
        if is_current:
            plugin.version = version_str

        db.session.commit()

        flash(f'Version "{version_str}" erstellt.', 'success')
        return redirect(url_for('marketplace_admin.plugin_version_list', plugin_id=plugin_id))

    return render_template(
        'plugins/versions/form.html',
        plugin=plugin,
        version=None,
    )


@admin_bp.route('/versions/<int:version_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def plugin_version_edit(version_id: int):
    """Edit a plugin version."""
    version = db.session.get(PluginVersion, version_id)
    if not version:
        flash('Version nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.plugin_list'))

    plugin = version.plugin

    if request.method == 'POST':
        version.changelog = request.form.get('changelog', '').strip()
        version.release_notes = request.form.get('release_notes', '').strip()
        version.min_v_flask_version = request.form.get('min_v_flask_version', '').strip() or None
        version.is_stable = request.form.get('is_stable') == 'on'
        version.is_breaking_change = request.form.get('is_breaking_change') == 'on'

        db.session.commit()
        flash('Version aktualisiert.', 'success')
        return redirect(url_for('marketplace_admin.plugin_version_list', plugin_id=plugin.id))

    return render_template(
        'plugins/versions/form.html',
        plugin=plugin,
        version=version,
    )


@admin_bp.route('/versions/<int:version_id>/set-current', methods=['POST'])
@login_required
@permission_required('admin.*')
def plugin_version_set_current(version_id: int):
    """Set a version as the current version (HTMX)."""
    version = db.session.get(PluginVersion, version_id)
    if not version:
        flash('Version nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.plugin_list'))

    plugin = version.plugin

    # Unset current on all versions
    db.session.query(PluginVersion).filter_by(
        plugin_id=plugin.id
    ).update({'is_current': False})

    # Set this version as current
    version.is_current = True
    plugin.version = version.version

    db.session.commit()

    if request.headers.get('HX-Request'):
        # Trigger page reload to refresh all badges
        return '', 200, {'HX-Refresh': 'true'}

    flash(f'Version "{version.version}" ist jetzt aktuell.', 'success')
    return redirect(url_for('marketplace_admin.plugin_version_list', plugin_id=plugin.id))


# ============================================================================
# License History
# ============================================================================

@admin_bp.route('/history')
@login_required
@permission_required('admin.*')
def license_history_global():
    """Global license history (all licenses)."""
    # Get filter parameters
    action_filter = request.args.get('action', '')
    page = request.args.get('page', 1, type=int)
    per_page = 50

    query = db.session.query(LicenseHistory).order_by(LicenseHistory.created_at.desc())

    if action_filter:
        query = query.filter(LicenseHistory.action == action_filter)

    # Simple pagination
    total = query.count()
    history = query.offset((page - 1) * per_page).limit(per_page).all()

    # Get unique actions for filter dropdown
    actions = db.session.query(LicenseHistory.action).distinct().all()
    actions = [a[0] for a in actions]

    return render_template(
        'licenses/history.html',
        history=history,
        actions=actions,
        action_filter=action_filter,
        page=page,
        per_page=per_page,
        total=total,
    )


@admin_bp.route('/licenses/<int:license_id>/history')
@login_required
@permission_required('admin.*')
def license_history_detail(license_id: int):
    """History for a specific license."""
    license = db.session.get(License, license_id)
    if not license:
        flash('Lizenz nicht gefunden.', 'error')
        return redirect(url_for('marketplace_admin.license_list'))

    history = db.session.query(LicenseHistory).filter_by(
        license_id=license_id
    ).order_by(LicenseHistory.created_at.desc()).all()

    return render_template(
        'licenses/history_detail.html',
        license=license,
        history=history,
    )
