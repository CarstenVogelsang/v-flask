"""Routes for the Datenschutz plugin.

Provides:
    - Public route: /datenschutz/ - displays the privacy policy
    - Admin routes: /admin/datenschutz/ - editor for configuration
"""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from v_flask.auth.decorators import permission_required
from v_flask.extensions import db

from v_flask_plugins.datenschutz.bausteine import KATEGORIEN, get_all_bausteine
from v_flask_plugins.datenschutz.detector import DienstErkennung
from v_flask_plugins.datenschutz.generator import DatenschutzGenerator
from v_flask_plugins.datenschutz.models import DatenschutzConfig
from v_flask_plugins.datenschutz.validators import DatenschutzValidator

# Public Blueprint
datenschutz_bp = Blueprint(
    'datenschutz',
    __name__,
    template_folder='templates',
)

# Admin Blueprint
datenschutz_admin_bp = Blueprint(
    'datenschutz_admin',
    __name__,
    template_folder='templates',
)


# =============================================================================
# Public Routes
# =============================================================================


@datenschutz_bp.route('/')
def public():
    """Display the public privacy policy page."""
    config = db.session.query(DatenschutzConfig).first()

    if not config:
        # No configuration yet - show placeholder
        return render_template(
            'datenschutz/public.html',
            datenschutz_html='<p>Die Datenschutzerklärung wird noch erstellt.</p>',
        )

    generator = DatenschutzGenerator(config)
    datenschutz_html = generator.generate_html()

    return render_template(
        'datenschutz/public.html',
        datenschutz_html=datenschutz_html,
        config=config,
    )


# =============================================================================
# Admin Routes
# =============================================================================


@datenschutz_admin_bp.route('/')
@permission_required('admin.*')
def editor():
    """Display the admin editor for the privacy policy."""
    config = db.session.query(DatenschutzConfig).first()

    if not config:
        # Create initial configuration
        config = DatenschutzConfig()
        db.session.add(config)
        db.session.commit()

    # Detect services
    detector = DienstErkennung(current_app)
    detected = detector.detect_all()
    detected_ids = [s.baustein_id for s in detected]

    # Validate
    validator = DatenschutzValidator(config, detected_ids)
    validation = validator.validate()
    completeness = validator.get_completeness_score()

    # Get all Bausteine grouped by category
    all_bausteine = get_all_bausteine()
    bausteine_by_kategorie = {}
    for baustein in all_bausteine:
        if baustein.kategorie not in bausteine_by_kategorie:
            bausteine_by_kategorie[baustein.kategorie] = []
        bausteine_by_kategorie[baustein.kategorie].append(baustein)

    # Sort categories
    sorted_kategorien = sorted(
        KATEGORIEN.items(),
        key=lambda x: x[1].get('order', 999)
    )

    # Get Betreiber for "Import from Impressum" feature
    betreiber = None
    try:
        from v_flask.models import Betreiber
        betreiber = db.session.query(Betreiber).first()
    except Exception:
        pass

    # Generate preview
    generator = DatenschutzGenerator(config)
    preview_html = generator.generate_html()

    return render_template(
        'datenschutz/admin/editor.html',
        config=config,
        kategorien=sorted_kategorien,
        bausteine_by_kategorie=bausteine_by_kategorie,
        detected_services=detected,
        detected_ids=detected_ids,
        validation=validation,
        completeness=completeness,
        betreiber=betreiber,
        preview_html=preview_html,
    )


@datenschutz_admin_bp.route('/save', methods=['POST'])
@permission_required('admin.*')
def save():
    """Save the privacy policy configuration."""
    config = db.session.query(DatenschutzConfig).first()

    if not config:
        config = DatenschutzConfig()
        db.session.add(config)

    # Create version snapshot before saving
    try:
        from flask_login import current_user
        changed_by = current_user.email if current_user.is_authenticated else None
    except Exception:
        changed_by = None

    if config.id:  # Only if already saved once
        config.create_version_snapshot(changed_by)

    # Update Verantwortlicher
    config.verantwortlicher_name = request.form.get('verantwortlicher_name', '').strip()
    config.verantwortlicher_strasse = request.form.get('verantwortlicher_strasse', '').strip()
    config.verantwortlicher_plz = request.form.get('verantwortlicher_plz', '').strip()
    config.verantwortlicher_ort = request.form.get('verantwortlicher_ort', '').strip()
    config.verantwortlicher_land = request.form.get('verantwortlicher_land', 'Deutschland').strip()
    config.verantwortlicher_email = request.form.get('verantwortlicher_email', '').strip()
    config.verantwortlicher_telefon = request.form.get('verantwortlicher_telefon', '').strip()

    # Update DSB
    config.dsb_vorhanden = 'dsb_vorhanden' in request.form
    if config.dsb_vorhanden:
        config.dsb_name = request.form.get('dsb_name', '').strip()
        config.dsb_email = request.form.get('dsb_email', '').strip()
        config.dsb_telefon = request.form.get('dsb_telefon', '').strip()
        config.dsb_extern = 'dsb_extern' in request.form
    else:
        config.dsb_name = None
        config.dsb_email = None
        config.dsb_telefon = None
        config.dsb_extern = False

    # Update activated Bausteine
    aktivierte = request.form.getlist('bausteine')

    # Ensure mandatory Bausteine are always included (defense in depth)
    # Even if JavaScript fails or is disabled, we enforce this server-side
    for baustein in get_all_bausteine():
        if not baustein.optional and baustein.id not in aktivierte:
            aktivierte.append(baustein.id)

    config.aktivierte_bausteine = aktivierte

    # Update Baustein-specific config
    baustein_config = {}
    for baustein in get_all_bausteine():
        if baustein.pflichtfelder:
            baustein_values = {}
            for feld in baustein.pflichtfelder:
                key = f'baustein_{baustein.id}_{feld}'
                value = request.form.get(key, '').strip()
                if value:
                    baustein_values[feld] = value
            if baustein_values:
                baustein_config[baustein.id] = baustein_values
    config.baustein_config = baustein_config

    db.session.commit()

    flash('Datenschutzerklärung gespeichert.', 'success')
    return redirect(url_for('datenschutz_admin.editor'))


@datenschutz_admin_bp.route('/import-from-impressum', methods=['POST'])
@permission_required('admin.*')
def import_from_impressum():
    """Import Verantwortlicher data from Betreiber (Impressum)."""
    config = db.session.query(DatenschutzConfig).first()

    if not config:
        config = DatenschutzConfig()
        db.session.add(config)

    try:
        from v_flask.models import Betreiber
        betreiber = db.session.query(Betreiber).first()

        if betreiber:
            config.verantwortlicher_name = betreiber.name
            config.verantwortlicher_strasse = betreiber.strasse
            config.verantwortlicher_plz = betreiber.plz
            config.verantwortlicher_ort = betreiber.ort
            config.verantwortlicher_land = betreiber.land or 'Deutschland'
            config.verantwortlicher_email = betreiber.email
            config.verantwortlicher_telefon = betreiber.telefon

            db.session.commit()
            flash('Daten aus Impressum übernommen.', 'success')
        else:
            flash('Kein Betreiber gefunden.', 'warning')

    except Exception as e:
        flash(f'Fehler beim Import: {e}', 'danger')

    return redirect(url_for('datenschutz_admin.editor'))


@datenschutz_admin_bp.route('/preview')
@permission_required('admin.*')
def preview():
    """Generate live preview (for HTMX)."""
    config = db.session.query(DatenschutzConfig).first()

    if not config:
        return '<p>Keine Konfiguration vorhanden.</p>'

    # Create a temporary config with form values for preview
    # (This allows preview without saving)
    # For now, just return the current saved preview
    generator = DatenschutzGenerator(config)
    return generator.generate_html()


@datenschutz_admin_bp.route('/versions')
@permission_required('admin.*')
def versions():
    """Display version history."""
    config = db.session.query(DatenschutzConfig).first()

    if not config:
        return redirect(url_for('datenschutz_admin.editor'))

    versions = config.versionen
    versions.sort(key=lambda v: v.created_at, reverse=True)

    return render_template(
        'datenschutz/admin/versions.html',
        config=config,
        versions=versions,
    )
