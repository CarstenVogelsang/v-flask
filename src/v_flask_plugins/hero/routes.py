"""Routes for the Hero plugin.

Provides:
    - Admin interface for hero section configuration
    - HTMX endpoints for live preview
    - Media picker integration for background images
"""

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
)

from v_flask.extensions import db
from v_flask.auth import admin_required

from .models import HeroSection, HeroTemplate
from .services.hero_service import hero_service


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

    templates = hero_service.get_all_templates()

    return render_template(
        'hero/admin/editor.html',
        hero=hero,
        templates=templates,
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
