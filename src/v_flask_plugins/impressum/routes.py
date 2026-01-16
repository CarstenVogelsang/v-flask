"""Routes for the Impressum plugin.

Public routes:
    GET /impressum/ - Display generated Impressum

Admin routes:
    GET  /admin/impressum/         - Editor with live preview
    POST /admin/impressum/         - Save Impressum data
    GET  /admin/impressum/preview  - HTMX partial for live preview
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required

from v_flask.auth import permission_required
from v_flask.extensions import db
from v_flask.models import Betreiber

from .generator import ImpressumGenerator
from .validators import ImpressumValidator

# Public blueprint
impressum_bp = Blueprint(
    'impressum',
    __name__,
    template_folder='templates'
)

# Admin blueprint
impressum_admin_bp = Blueprint(
    'impressum_admin',
    __name__,
    template_folder='templates'
)


# === Public Routes ===

@impressum_bp.route('/')
def public():
    """Display the public Impressum page."""
    betreiber = db.session.query(Betreiber).first()

    if not betreiber:
        return render_template(
            'impressum/public.html',
            impressum_html='<p>Kein Impressum konfiguriert.</p>',
            betreiber=None
        )

    generator = ImpressumGenerator(betreiber)
    impressum_html = generator.generate_html()

    return render_template(
        'impressum/public.html',
        impressum_html=impressum_html,
        betreiber=betreiber
    )


# === Admin Routes ===

@impressum_admin_bp.route('/', methods=['GET'])
@login_required
@permission_required('admin.*')
def editor():
    """Display the Impressum editor with form and live preview."""
    betreiber = db.session.query(Betreiber).first()

    if not betreiber:
        flash('Bitte zuerst einen Betreiber anlegen.', 'warning')
        return redirect(url_for('impressum.public'))

    # Generate preview
    generator = ImpressumGenerator(betreiber)
    preview_html = generator.generate_html()

    # Validate
    validator = ImpressumValidator(betreiber)
    validation = validator.validate()
    completeness = validator.get_completeness_score()

    # Available rechtsformen for dropdown
    rechtsformen = [
        ('', '-- Bitte wählen --'),
        ('GmbH', 'GmbH'),
        ('UG', 'UG (haftungsbeschränkt)'),
        ('UG (haftungsbeschränkt)', 'UG (haftungsbeschränkt) - Lang'),
        ('AG', 'AG'),
        ('GmbH & Co. KG', 'GmbH & Co. KG'),
        ('KG', 'KG'),
        ('OHG', 'OHG'),
        ('GbR', 'GbR'),
        ('e.K.', 'e.K. (eingetragener Kaufmann)'),
        ('Einzelunternehmen', 'Einzelunternehmen'),
    ]

    return render_template(
        'impressum/admin/editor.html',
        betreiber=betreiber,
        preview_html=preview_html,
        validation=validation,
        completeness=completeness,
        rechtsformen=rechtsformen
    )


@impressum_admin_bp.route('/', methods=['POST'])
@login_required
@permission_required('admin.*')
def save():
    """Save Impressum data to Betreiber model."""
    betreiber = db.session.query(Betreiber).first()

    if not betreiber:
        flash('Kein Betreiber gefunden.', 'error')
        return redirect(url_for('impressum_admin.editor'))

    # Update Betreiber fields from form
    betreiber.name = request.form.get('name', '').strip() or betreiber.name
    betreiber.strasse = request.form.get('strasse', '').strip() or None
    betreiber.plz = request.form.get('plz', '').strip() or None
    betreiber.ort = request.form.get('ort', '').strip() or None
    betreiber.land = request.form.get('land', '').strip() or 'Deutschland'

    betreiber.telefon = request.form.get('telefon', '').strip() or None
    betreiber.fax = request.form.get('fax', '').strip() or None
    betreiber.email = request.form.get('email', '').strip() or None

    betreiber.rechtsform = request.form.get('rechtsform', '').strip() or None
    betreiber.geschaeftsfuehrer = request.form.get('geschaeftsfuehrer', '').strip() or None

    betreiber.handelsregister_gericht = request.form.get('handelsregister_gericht', '').strip() or None
    betreiber.handelsregister_nummer = request.form.get('handelsregister_nummer', '').strip() or None

    betreiber.ust_idnr = request.form.get('ust_idnr', '').strip() or None
    betreiber.wirtschafts_idnr = request.form.get('wirtschafts_idnr', '').strip() or None

    betreiber.inhaltlich_verantwortlich = request.form.get('inhaltlich_verantwortlich', '').strip() or None

    # Update impressum options (toggles)
    betreiber.set_impressum_option(
        'show_visdp',
        request.form.get('show_visdp') == 'on'
    )
    betreiber.set_impressum_option(
        'show_streitschlichtung',
        request.form.get('show_streitschlichtung') == 'on'
    )

    # Custom streitschlichtung text
    custom_streitschlichtung = request.form.get('streitschlichtung_text', '').strip()
    if custom_streitschlichtung:
        betreiber.set_impressum_option('streitschlichtung_text', custom_streitschlichtung)
    else:
        betreiber.set_impressum_option('streitschlichtung_text', None)

    db.session.commit()

    # Validate after save
    validator = ImpressumValidator(betreiber)
    validation = validator.validate()

    if validation.is_valid:
        flash('Impressum erfolgreich gespeichert.', 'success')
    else:
        flash('Impressum gespeichert, aber es fehlen Pflichtangaben.', 'warning')

    return redirect(url_for('impressum_admin.editor'))


@impressum_admin_bp.route('/preview')
@login_required
@permission_required('admin.*')
def preview():
    """HTMX endpoint: Return live preview HTML.

    This endpoint is called via HTMX to update the preview
    when form fields change.
    """
    betreiber = db.session.query(Betreiber).first()

    if not betreiber:
        return '<p class="text-muted">Kein Betreiber konfiguriert.</p>'

    # For live preview, temporarily apply form values
    # (without saving to database)
    temp_betreiber = _apply_form_to_betreiber(betreiber, request.args)

    generator = ImpressumGenerator(temp_betreiber)
    preview_html = generator.generate_html()

    # Also get validation for the preview
    validator = ImpressumValidator(temp_betreiber)
    validation = validator.validate()
    completeness = validator.get_completeness_score()

    return render_template(
        'impressum/admin/_preview.html',
        preview_html=preview_html,
        validation=validation,
        completeness=completeness
    )


def _apply_form_to_betreiber(betreiber: Betreiber, form_data: dict) -> Betreiber:
    """Apply form data to a copy of Betreiber for preview.

    Note: This doesn't actually copy the object, just temporarily
    modifies attributes without committing to DB.

    Args:
        betreiber: Original Betreiber instance.
        form_data: Request args/form dict.

    Returns:
        Modified Betreiber instance (same object, modified in place).
    """
    # Temporarily override fields with form data
    if 'name' in form_data:
        betreiber.name = form_data.get('name', '').strip() or betreiber.name
    if 'strasse' in form_data:
        betreiber.strasse = form_data.get('strasse', '').strip() or None
    if 'plz' in form_data:
        betreiber.plz = form_data.get('plz', '').strip() or None
    if 'ort' in form_data:
        betreiber.ort = form_data.get('ort', '').strip() or None
    if 'land' in form_data:
        betreiber.land = form_data.get('land', '').strip() or 'Deutschland'
    if 'telefon' in form_data:
        betreiber.telefon = form_data.get('telefon', '').strip() or None
    if 'fax' in form_data:
        betreiber.fax = form_data.get('fax', '').strip() or None
    if 'email' in form_data:
        betreiber.email = form_data.get('email', '').strip() or None
    if 'rechtsform' in form_data:
        betreiber.rechtsform = form_data.get('rechtsform', '').strip() or None
    if 'geschaeftsfuehrer' in form_data:
        betreiber.geschaeftsfuehrer = form_data.get('geschaeftsfuehrer', '').strip() or None
    if 'handelsregister_gericht' in form_data:
        betreiber.handelsregister_gericht = form_data.get('handelsregister_gericht', '').strip() or None
    if 'handelsregister_nummer' in form_data:
        betreiber.handelsregister_nummer = form_data.get('handelsregister_nummer', '').strip() or None
    if 'ust_idnr' in form_data:
        betreiber.ust_idnr = form_data.get('ust_idnr', '').strip() or None
    if 'wirtschafts_idnr' in form_data:
        betreiber.wirtschafts_idnr = form_data.get('wirtschafts_idnr', '').strip() or None
    if 'inhaltlich_verantwortlich' in form_data:
        betreiber.inhaltlich_verantwortlich = form_data.get('inhaltlich_verantwortlich', '').strip() or None

    # Handle toggle options
    if 'show_visdp' in form_data:
        betreiber.set_impressum_option('show_visdp', form_data.get('show_visdp') == 'true')
    if 'show_streitschlichtung' in form_data:
        betreiber.set_impressum_option('show_streitschlichtung', form_data.get('show_streitschlichtung') == 'true')

    return betreiber
