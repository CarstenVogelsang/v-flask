"""CTA Admin Routes.

Provides admin interface for managing CTA sections, templates,
and route assignments.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from v_flask.extensions import db
from v_flask.auth import permission_required

from v_flask_plugins.cta.models import CtaTemplate, CtaSection, CtaAssignment
from v_flask_plugins.cta.services.cta_service import (
    cta_service,
    AVAILABLE_PLACEHOLDERS,
)

cta_admin_bp = Blueprint('cta_admin', __name__)


# =============================================================================
# CTA Sections
# =============================================================================

@cta_admin_bp.route('/')
@login_required
@permission_required('admin.*')
def list_sections():
    """List all CTA sections."""
    sections = CtaSection.query.order_by(CtaSection.name).all()
    return render_template(
        'cta/admin/list.html',
        sections=sections,
    )


@cta_admin_bp.route('/neu/', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def create_section():
    """Create a new CTA section."""
    templates = CtaTemplate.query.filter_by(active=True).order_by(CtaTemplate.name).all()

    if request.method == 'POST':
        section = CtaSection(
            name=request.form.get('name', '').strip(),
            variant=request.form.get('variant', 'card'),
            template_id=request.form.get('template_id') or None,
            custom_title=request.form.get('custom_title', '').strip() or None,
            custom_description=request.form.get('custom_description', '').strip() or None,
            cta_text=request.form.get('cta_text', '').strip() or None,
            cta_link=request.form.get('cta_link', '').strip() or None,
            active=bool(request.form.get('active')),
        )

        if not section.name:
            flash('Name ist erforderlich.', 'error')
        else:
            db.session.add(section)
            db.session.commit()
            flash('CTA Section erstellt.', 'success')
            return redirect(url_for('cta_admin.edit_section', section_id=section.id))

    return render_template(
        'cta/admin/section_form.html',
        section=None,
        templates=templates,
        placeholders=AVAILABLE_PLACEHOLDERS,
    )


@cta_admin_bp.route('/<int:section_id>/edit/', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def edit_section(section_id: int):
    """Edit a CTA section."""
    section = CtaSection.query.get_or_404(section_id)
    templates = CtaTemplate.query.filter_by(active=True).order_by(CtaTemplate.name).all()

    # Get assignable routes (excluding admin blueprints)
    excluded = ['admin', 'auth', 'two_fa', 'plugins_admin', 'users_admin',
                'roles_admin', 'admin_settings', 'plugin_settings']
    routes = cta_service.get_assignable_routes(exclude_blueprints=excluded)

    if request.method == 'POST':
        section.name = request.form.get('name', '').strip()
        section.variant = request.form.get('variant', 'card')
        section.template_id = request.form.get('template_id') or None
        section.custom_title = request.form.get('custom_title', '').strip() or None
        section.custom_description = request.form.get('custom_description', '').strip() or None
        section.cta_text = request.form.get('cta_text', '').strip() or None
        section.cta_link = request.form.get('cta_link', '').strip() or None
        section.active = bool(request.form.get('active'))

        if not section.name:
            flash('Name ist erforderlich.', 'error')
        else:
            db.session.commit()
            flash('CTA Section aktualisiert.', 'success')

    return render_template(
        'cta/admin/section_form.html',
        section=section,
        templates=templates,
        routes=routes,
        placeholders=AVAILABLE_PLACEHOLDERS,
    )


@cta_admin_bp.route('/<int:section_id>/delete/', methods=['POST'])
@login_required
@permission_required('admin.*')
def delete_section(section_id: int):
    """Delete a CTA section."""
    section = CtaSection.query.get_or_404(section_id)
    name = section.name

    db.session.delete(section)
    db.session.commit()

    flash(f'CTA Section "{name}" gelöscht.', 'success')
    return redirect(url_for('cta_admin.list_sections'))


# =============================================================================
# CTA Assignments
# =============================================================================

@cta_admin_bp.route('/<int:section_id>/assign/', methods=['POST'])
@login_required
@permission_required('admin.*')
def assign_route(section_id: int):
    """Assign CTA section to a route."""
    section = CtaSection.query.get_or_404(section_id)

    route_id = request.form.get('route_id', type=int)
    slot = request.form.get('slot', 'after_content')
    priority = request.form.get('priority', 50, type=int)

    if route_id:
        assignment = cta_service.assign_cta_to_route(
            cta_id=section_id,
            route_id=route_id,
            slot=slot,
            priority=priority,
        )

        if assignment:
            flash('Seitenzuweisung erstellt.', 'success')
        else:
            flash('Fehler bei der Zuweisung.', 'error')

    return redirect(url_for('cta_admin.edit_section', section_id=section_id))


@cta_admin_bp.route('/assignment/<int:assignment_id>/delete/', methods=['POST'])
@login_required
@permission_required('admin.*')
def delete_assignment(assignment_id: int):
    """Delete a CTA assignment."""
    assignment = CtaAssignment.query.get_or_404(assignment_id)
    section_id = assignment.cta_section_id

    db.session.delete(assignment)
    db.session.commit()

    flash('Seitenzuweisung entfernt.', 'success')
    return redirect(url_for('cta_admin.edit_section', section_id=section_id))


# =============================================================================
# CTA Templates
# =============================================================================

@cta_admin_bp.route('/templates/')
@login_required
@permission_required('admin.*')
def list_templates():
    """List all CTA templates."""
    templates = CtaTemplate.query.order_by(CtaTemplate.name).all()
    return render_template(
        'cta/admin/templates.html',
        templates=templates,
    )


@cta_admin_bp.route('/templates/neu/', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def create_template():
    """Create a new CTA template."""
    if request.method == 'POST':
        slug = request.form.get('slug', '').strip().lower().replace(' ', '_')
        name = request.form.get('name', '').strip()
        titel = request.form.get('titel', '').strip()
        beschreibung = request.form.get('beschreibung', '').strip()

        # Validate
        if not all([slug, name, titel, beschreibung]):
            flash('Alle Felder sind erforderlich.', 'error')
        elif CtaTemplate.query.filter_by(slug=slug).first():
            flash('Slug bereits vergeben.', 'error')
        else:
            template = CtaTemplate(
                slug=slug,
                name=name,
                titel=titel,
                beschreibung=beschreibung,
                active=True,
            )
            db.session.add(template)
            db.session.commit()
            flash('Template erstellt.', 'success')
            return redirect(url_for('cta_admin.list_templates'))

    return render_template(
        'cta/admin/template_form.html',
        template=None,
        placeholders=AVAILABLE_PLACEHOLDERS,
    )


@cta_admin_bp.route('/templates/<int:template_id>/edit/', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def edit_template(template_id: int):
    """Edit a CTA template."""
    template = CtaTemplate.query.get_or_404(template_id)

    if request.method == 'POST':
        template.name = request.form.get('name', '').strip()
        template.titel = request.form.get('titel', '').strip()
        template.beschreibung = request.form.get('beschreibung', '').strip()
        template.active = bool(request.form.get('active'))

        if not all([template.name, template.titel, template.beschreibung]):
            flash('Alle Felder sind erforderlich.', 'error')
        else:
            db.session.commit()
            flash('Template aktualisiert.', 'success')

    return render_template(
        'cta/admin/template_form.html',
        template=template,
        placeholders=AVAILABLE_PLACEHOLDERS,
    )


@cta_admin_bp.route('/templates/<int:template_id>/delete/', methods=['POST'])
@login_required
@permission_required('admin.*')
def delete_template(template_id: int):
    """Delete a CTA template."""
    template = CtaTemplate.query.get_or_404(template_id)

    # Check if in use
    if template.cta_sections.count() > 0:
        flash('Template wird noch verwendet und kann nicht gelöscht werden.', 'error')
        return redirect(url_for('cta_admin.list_templates'))

    name = template.name
    db.session.delete(template)
    db.session.commit()

    flash(f'Template "{name}" gelöscht.', 'success')
    return redirect(url_for('cta_admin.list_templates'))


# =============================================================================
# Preview (HTMX)
# =============================================================================

@cta_admin_bp.route('/preview/', methods=['POST'])
@login_required
@permission_required('admin.*')
def preview():
    """Generate preview HTML for live editing."""
    titel = request.form.get('titel', '')
    beschreibung = request.form.get('beschreibung', '')
    variant = request.form.get('variant', 'card')

    rendered = cta_service.render_preview(titel, beschreibung, variant)

    return render_template(
        'cta/admin/_preview.html',
        rendered=rendered,
        variant=variant,
    )
