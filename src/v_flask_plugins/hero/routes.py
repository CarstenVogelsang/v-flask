"""Routes for the Hero plugin.

Provides:
    - Admin interface for hero section configuration
    - HTMX endpoints for live preview
    - Media picker integration for background images
"""

from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    flash,
    redirect,
    url_for,
)

from v_flask.extensions import db
from v_flask.auth import admin_required

from .models import HeroSection, HeroTemplate, PageRoute, HeroAssignment
from .services.hero_service import hero_service
from .services.route_sync_service import route_sync_service


# Admin blueprint for hero configuration
hero_admin_bp = Blueprint(
    'hero_admin',
    __name__,
    template_folder='templates'
)


# === Editor Route ===

@hero_admin_bp.route('/')
@admin_required
def editor():
    """Hero Section Editor.

    Main admin page for configuring the hero section.
    Supports media_id URL parameter for automatic image adoption from media library.
    """
    # Get or create active hero section
    hero = HeroSection.query.filter_by(active=True).first()
    if not hero:
        # Create default hero section if none exists
        hero = HeroSection(
            variant='centered',
            active=True
        )
        db.session.add(hero)
        db.session.commit()

    # Handle media adoption from media library picker
    new_media_id = request.args.get('media_id', type=int)
    if new_media_id:
        hero.media_id = new_media_id
        db.session.commit()
        flash('Bild übernommen', 'success')
        return redirect(url_for('hero_admin.editor'))

    templates = hero_service.get_all_templates()

    # Generate preview HTML for the current hero section
    preview_html = hero_service.render_hero(hero)

    return render_template(
        'hero/admin/editor.html',
        hero=hero,
        templates=templates,
        preview_html=preview_html,
        variants=[
            {'value': 'centered', 'label': 'Zentriert', 'icon': 'ti-align-center'},
            {'value': 'split', 'label': 'Geteilt', 'icon': 'ti-layout-columns'},
            {'value': 'overlay', 'label': 'Overlay', 'icon': 'ti-photo'},
        ]
    )


@hero_admin_bp.route('/save', methods=['POST'])
@admin_required
def save():
    """Save hero section configuration."""
    hero = HeroSection.query.filter_by(active=True).first()
    if not hero:
        hero = HeroSection(active=True)
        db.session.add(hero)

    # Update fields from form
    hero.variant = request.form.get('variant', 'centered')

    # Background image from media picker
    media_id = request.form.get('media_id')
    hero.media_id = int(media_id) if media_id else None

    # Text source: template or custom
    text_source = request.form.get('text_source', 'custom')

    if text_source == 'template':
        template_id = request.form.get('template_id')
        hero.template_id = int(template_id) if template_id else None
        hero.custom_title = None
        hero.custom_subtitle = None
    else:
        hero.template_id = None
        hero.custom_title = request.form.get('custom_title', '').strip()
        hero.custom_subtitle = request.form.get('custom_subtitle', '').strip()

    # CTA
    hero.cta_text = request.form.get('cta_text', '').strip() or None
    hero.cta_link = request.form.get('cta_link', '').strip() or None

    db.session.commit()
    flash('Hero Section gespeichert.', 'success')

    # HTMX request - return updated preview
    if request.headers.get('HX-Request'):
        return render_template(
            'hero/admin/_preview.html',
            hero=hero,
            preview_html=hero_service.render_hero(hero)
        )

    return redirect(url_for('hero_admin.editor'))


@hero_admin_bp.route('/preview', methods=['POST'])
@admin_required
def preview():
    """Generate live preview for hero section.

    HTMX endpoint for real-time preview updates.
    """
    variant = request.form.get('variant', 'centered')
    text_source = request.form.get('text_source', 'custom')

    if text_source == 'template':
        template_id = request.form.get('template_id')
        if template_id:
            rendered = hero_service.render_template(int(template_id))
            title = rendered['titel'] if rendered else ''
            subtitle = rendered['untertitel'] if rendered else ''
        else:
            title = subtitle = ''
    else:
        title = request.form.get('custom_title', '')
        subtitle = request.form.get('custom_subtitle', '')

    cta_text = request.form.get('cta_text', '').strip() or None
    cta_link = request.form.get('cta_link', '').strip() or None

    # Get image path from media_id or current hero
    media_id = request.form.get('media_id')
    image_path = None

    if media_id:
        from v_flask_plugins.media.models import Media
        media = db.session.get(Media, int(media_id))
        if media:
            image_path = media.get_url('large')
    else:
        # Fallback to current hero's image
        hero = HeroSection.query.filter_by(active=True).first()
        image_path = hero.image_path if hero else None

    preview_html = hero_service.render_hero_preview(
        variant=variant,
        title=title,
        subtitle=subtitle,
        cta_text=cta_text,
        cta_link=cta_link,
        image_path=image_path
    )

    return preview_html


@hero_admin_bp.route('/update-media', methods=['POST'])
@admin_required
def update_media():
    """Update hero background image via media picker.

    HTMX endpoint for media picker selection.
    """
    media_id = request.form.get('media_id')

    hero = HeroSection.query.filter_by(active=True).first()
    if hero:
        hero.media_id = int(media_id) if media_id else None
        db.session.commit()

        if request.headers.get('HX-Request'):
            return render_template(
                'hero/admin/_image_preview.html',
                hero=hero
            )

    return redirect(url_for('hero_admin.editor'))


# === Template Management (Optional) ===

@hero_admin_bp.route('/templates')
@admin_required
def list_templates():
    """List all hero templates."""
    templates = HeroTemplate.query.order_by(
        HeroTemplate.is_default.desc(),
        HeroTemplate.name
    ).all()

    return render_template(
        'hero/admin/templates.html',
        templates=templates
    )


@hero_admin_bp.route('/templates/new', methods=['GET', 'POST'])
@admin_required
def create_template():
    """Create a new hero template."""
    if request.method == 'POST':
        template = HeroTemplate(
            slug=request.form.get('slug', '').strip(),
            name=request.form.get('name', '').strip(),
            titel=request.form.get('titel', '').strip(),
            untertitel=request.form.get('untertitel', '').strip(),
            is_default=bool(request.form.get('is_default')),
        )
        db.session.add(template)
        db.session.commit()
        flash('Template erstellt.', 'success')
        return redirect(url_for('hero_admin.list_templates'))

    return render_template('hero/admin/template_form.html')


@hero_admin_bp.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_template(template_id: int):
    """Edit an existing hero template."""
    template = db.session.get(HeroTemplate, template_id)
    if not template:
        flash('Template nicht gefunden.', 'error')
        return redirect(url_for('hero_admin.list_templates'))

    if request.method == 'POST':
        template.slug = request.form.get('slug', '').strip()
        template.name = request.form.get('name', '').strip()
        template.titel = request.form.get('titel', '').strip()
        template.untertitel = request.form.get('untertitel', '').strip()
        template.is_default = bool(request.form.get('is_default'))
        template.active = bool(request.form.get('active', True))

        db.session.commit()
        flash('Template aktualisiert.', 'success')
        return redirect(url_for('hero_admin.list_templates'))

    return render_template(
        'hero/admin/template_form.html',
        template=template
    )


@hero_admin_bp.route('/templates/<int:template_id>/delete', methods=['POST'])
@admin_required
def delete_template(template_id: int):
    """Delete a hero template."""
    template = db.session.get(HeroTemplate, template_id)
    if template:
        # Check if template is in use
        in_use = HeroSection.query.filter_by(template_id=template_id).count()
        if in_use > 0:
            flash(
                f'Template wird von {in_use} Hero Section(s) verwendet und kann nicht gelöscht werden.',
                'error'
            )
        else:
            db.session.delete(template)
            db.session.commit()
            flash('Template gelöscht.', 'success')

    return redirect(url_for('hero_admin.list_templates'))


@hero_admin_bp.route('/templates/preview', methods=['POST'])
@admin_required
def preview_template():
    """Preview template text with placeholders rendered.

    HTMX endpoint for live template preview.
    """
    titel = request.form.get('titel', '')
    untertitel = request.form.get('untertitel', '')

    rendered = hero_service.render_preview(titel, untertitel)

    return render_template(
        'hero/admin/_template_preview.html',
        rendered=rendered
    )


# =============================================================================
# Hero Section CRUD (NEW - Multiple Hero Sections)
# =============================================================================

@hero_admin_bp.route('/sections')
@admin_required
def list_sections():
    """List all hero sections.

    New management view for multiple hero sections with assignments.
    """
    sections = hero_service.get_all_hero_sections()

    return render_template(
        'hero/admin/list.html',
        sections=sections,
    )


@hero_admin_bp.route('/sections/new', methods=['GET', 'POST'])
@admin_required
def create_section():
    """Create a new hero section."""
    if request.method == 'POST':
        hero = HeroSection(
            name=request.form.get('name', '').strip() or None,
            variant=request.form.get('variant', 'centered'),
            active=bool(request.form.get('active')),
        )

        # Text source
        text_source = request.form.get('text_source', 'custom')
        if text_source == 'template':
            template_id = request.form.get('template_id')
            hero.template_id = int(template_id) if template_id else None
        else:
            hero.custom_title = request.form.get('custom_title', '').strip()
            hero.custom_subtitle = request.form.get('custom_subtitle', '').strip()

        # CTA
        hero.cta_text = request.form.get('cta_text', '').strip() or None
        hero.cta_link = request.form.get('cta_link', '').strip() or None

        # Media
        media_id = request.form.get('media_id')
        hero.media_id = int(media_id) if media_id else None

        db.session.add(hero)
        db.session.commit()

        flash('Hero Section erstellt.', 'success')
        return redirect(url_for('hero_admin.edit_section', section_id=hero.id))

    templates = hero_service.get_all_templates()
    variants = [
        {'value': 'centered', 'label': 'Zentriert', 'icon': 'ti-align-center'},
        {'value': 'split', 'label': 'Geteilt', 'icon': 'ti-layout-columns'},
        {'value': 'overlay', 'label': 'Overlay', 'icon': 'ti-photo'},
    ]

    return render_template(
        'hero/admin/section_form.html',
        hero=None,
        templates=templates,
        variants=variants,
        available_routes=route_sync_service.get_assignable_routes(),
    )


@hero_admin_bp.route('/sections/<int:section_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_section(section_id: int):
    """Edit a hero section with page assignments."""
    hero = hero_service.get_hero_section(section_id)
    if not hero:
        flash('Hero Section nicht gefunden.', 'error')
        return redirect(url_for('hero_admin.list_sections'))

    if request.method == 'POST':
        hero.name = request.form.get('name', '').strip() or None
        hero.variant = request.form.get('variant', 'centered')
        hero.active = bool(request.form.get('active'))

        # Text source
        text_source = request.form.get('text_source', 'custom')
        if text_source == 'template':
            template_id = request.form.get('template_id')
            hero.template_id = int(template_id) if template_id else None
            hero.custom_title = None
            hero.custom_subtitle = None
        else:
            hero.template_id = None
            hero.custom_title = request.form.get('custom_title', '').strip()
            hero.custom_subtitle = request.form.get('custom_subtitle', '').strip()

        # CTA
        hero.cta_text = request.form.get('cta_text', '').strip() or None
        hero.cta_link = request.form.get('cta_link', '').strip() or None

        # Media
        media_id = request.form.get('media_id')
        hero.media_id = int(media_id) if media_id else None

        db.session.commit()
        flash('Hero Section gespeichert.', 'success')

        # HTMX request - stay on page
        if request.headers.get('HX-Request'):
            return render_template(
                'hero/admin/_section_saved.html',
                hero=hero
            )

        return redirect(url_for('hero_admin.edit_section', section_id=hero.id))

    templates = hero_service.get_all_templates()
    variants = [
        {'value': 'centered', 'label': 'Zentriert', 'icon': 'ti-align-center'},
        {'value': 'split', 'label': 'Geteilt', 'icon': 'ti-layout-columns'},
        {'value': 'overlay', 'label': 'Overlay', 'icon': 'ti-photo'},
    ]
    assignments = hero_service.get_assignments_for_hero(section_id)
    assigned_route_ids = {a.page_route_id for a in assignments}
    available_routes = [
        r for r in route_sync_service.get_assignable_routes()
        if r.id not in assigned_route_ids
    ]

    return render_template(
        'hero/admin/section_form.html',
        hero=hero,
        templates=templates,
        variants=variants,
        assignments=assignments,
        available_routes=available_routes,
        preview_html=hero_service.render_hero(hero),
    )


@hero_admin_bp.route('/sections/<int:section_id>/delete', methods=['POST'])
@admin_required
def delete_section(section_id: int):
    """Delete a hero section."""
    hero = hero_service.get_hero_section(section_id)
    if hero:
        db.session.delete(hero)
        db.session.commit()
        flash('Hero Section gelöscht.', 'success')

    return redirect(url_for('hero_admin.list_sections'))


# =============================================================================
# Route Management (Page Discovery)
# =============================================================================

@hero_admin_bp.route('/routes')
@admin_required
def list_routes():
    """List available page routes for hero assignment with filtering."""
    # Filter-Parameter (Default: nur hero_assignable=yes)
    hero_assignable_param = request.args.get('hero_assignable', 'yes')
    blueprint_param = request.args.get('blueprint', '')

    # Query aufbauen
    query = PageRoute.query

    if hero_assignable_param == 'yes':
        query = query.filter_by(hero_assignable=True)
    elif hero_assignable_param == 'no':
        query = query.filter_by(hero_assignable=False)
    # 'all' → kein Filter

    if blueprint_param:
        query = query.filter_by(blueprint=blueprint_param)

    routes = query.order_by(
        PageRoute.route_type,
        PageRoute.blueprint,
        PageRoute.display_name
    ).all()

    # Verfügbare Blueprints für Dropdown (immer alle, unabhängig von Filtern)
    available_blueprints = db.session.query(
        PageRoute.blueprint
    ).distinct().order_by(PageRoute.blueprint).all()
    available_blueprints = [bp[0] for bp in available_blueprints if bp[0]]

    # Blueprint-Namen Mapping für schönere Anzeige
    blueprint_names = {
        'datenschutz': 'Datenschutz',
        'datenschutz_admin': 'Datenschutz (Admin)',
        'impressum': 'Impressum',
        'impressum_admin': 'Impressum (Admin)',
        'kontakt': 'Kontakt-Formular',
        'kontakt_admin': 'Kontakt (Admin)',
        'fragebogen': 'Fragebogen',
        'fragebogen_admin': 'Fragebogen (Admin)',
        'media_admin': 'Media (Admin)',
        'hero_admin': 'Hero (Admin)',
        'public': 'System (Öffentlich)',
        'admin': 'System (Admin)',
        'auth': 'System (Auth)',
        'api': 'System (API)',
    }

    filters = {
        'hero_assignable': hero_assignable_param,
        'blueprint': blueprint_param,
    }

    return render_template(
        'hero/admin/routes.html',
        routes=routes,
        filters=filters,
        available_blueprints=available_blueprints,
        blueprint_names=blueprint_names,
    )


@hero_admin_bp.route('/routes/sync', methods=['POST'])
@admin_required
def sync_routes():
    """Sync Flask routes with database.

    HTMX endpoint for "Seiten synchronisieren" button.
    After sync, resets filter to show all routes so user sees new ones.
    """
    stats = route_sync_service.sync_routes(current_app)

    flash(
        f'Routen synchronisiert: {stats["added"]} neu, '
        f'{stats["removed"]} entfernt, {stats["unchanged"]} unverändert.',
        'success'
    )

    if request.headers.get('HX-Request'):
        # Nach Sync: Alle Routes zeigen (auch nicht-zuweisbare)
        routes = PageRoute.query.order_by(
            PageRoute.route_type,
            PageRoute.blueprint,
            PageRoute.display_name
        ).all()

        # Blueprint-Namen für Tabelle
        blueprint_names = {
            'datenschutz': 'Datenschutz',
            'datenschutz_admin': 'Datenschutz (Admin)',
            'impressum': 'Impressum',
            'impressum_admin': 'Impressum (Admin)',
            'kontakt': 'Kontakt-Formular',
            'kontakt_admin': 'Kontakt (Admin)',
            'fragebogen': 'Fragebogen',
            'fragebogen_admin': 'Fragebogen (Admin)',
            'media_admin': 'Media (Admin)',
            'hero_admin': 'Hero (Admin)',
            'public': 'System (Öffentlich)',
            'admin': 'System (Admin)',
            'auth': 'System (Auth)',
            'api': 'System (API)',
        }

        return render_template(
            'hero/admin/_route_list.html',
            routes=routes,
            blueprint_names=blueprint_names,
        )

    return redirect(url_for('hero_admin.list_routes'))


@hero_admin_bp.route('/routes/<int:route_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_route(route_id: int):
    """Edit route display name."""
    route = db.session.get(PageRoute, route_id)
    if not route:
        flash('Route nicht gefunden.', 'error')
        return redirect(url_for('hero_admin.list_routes'))

    if request.method == 'POST':
        route.display_name = request.form.get('display_name', '').strip() or None
        route.hero_assignable = bool(request.form.get('hero_assignable'))
        db.session.commit()
        flash('Route aktualisiert.', 'success')

        if request.headers.get('HX-Request'):
            return f'''
            <td class="font-medium">{route.display_name or route.endpoint}</td>
            <td class="font-mono text-sm">{route.endpoint}</td>
            <td class="font-mono text-xs text-base-content/60">{route.rule}</td>
            <td>
                <span class="badge badge-{'success' if route.hero_assignable else 'ghost'}">
                    {'Ja' if route.hero_assignable else 'Nein'}
                </span>
            </td>
            '''

        return redirect(url_for('hero_admin.list_routes'))

    return render_template(
        'hero/admin/route_form.html',
        route=route,
    )


# =============================================================================
# Hero Assignment Management
# =============================================================================

@hero_admin_bp.route('/sections/<int:hero_id>/assign', methods=['POST'])
@admin_required
def assign_hero(hero_id: int):
    """Assign hero to a page route.

    HTMX endpoint for adding assignment.
    """
    hero = db.session.get(HeroSection, hero_id)
    if not hero:
        return '<div class="alert alert-error">Hero Section nicht gefunden.</div>'

    route_id = request.form.get('route_id', type=int)
    slot = request.form.get('slot_position', 'hero_top')

    if not route_id:
        return '<div class="alert alert-error">Keine Seite ausgewählt.</div>'

    assignment = hero_service.assign_hero_to_route(
        hero_id=hero_id,
        route_id=route_id,
        slot=slot
    )

    if assignment:
        # Return updated assignments list
        assignments = hero_service.get_assignments_for_hero(hero_id)
        assigned_route_ids = {a.page_route_id for a in assignments}
        available_routes = [
            r for r in route_sync_service.get_assignable_routes()
            if r.id not in assigned_route_ids
        ]

        return render_template(
            'hero/admin/_assignments.html',
            hero=hero,
            assignments=assignments,
            available_routes=available_routes,
        )

    return '<div class="alert alert-error">Zuweisung fehlgeschlagen.</div>'


@hero_admin_bp.route('/assignment/<int:assignment_id>/remove', methods=['POST'])
@admin_required
def remove_assignment(assignment_id: int):
    """Remove hero assignment.

    HTMX endpoint for removing assignment.
    """
    assignment = db.session.get(HeroAssignment, assignment_id)
    if not assignment:
        return '<div class="alert alert-error">Zuweisung nicht gefunden.</div>'

    hero = db.session.get(HeroSection, assignment.hero_section_id)
    hero_service.remove_assignment(assignment_id)

    # Return updated assignments list
    assignments = hero_service.get_assignments_for_hero(hero.id)
    assigned_route_ids = {a.page_route_id for a in assignments}
    available_routes = [
        r for r in route_sync_service.get_assignable_routes()
        if r.id not in assigned_route_ids
    ]

    return render_template(
        'hero/admin/_assignments.html',
        hero=hero,
        assignments=assignments,
        available_routes=available_routes,
    )
