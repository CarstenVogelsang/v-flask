"""Admin routes for Fragebogen plugin.

Provides:
    - /admin/fragebogen/ - List all questionnaires
    - /admin/fragebogen/neu - Create new questionnaire
    - /admin/fragebogen/<id> - View questionnaire detail
    - /admin/fragebogen/<id>/edit - Edit questionnaire
    - /admin/fragebogen/<id>/status - Change status (activate/close)
    - /admin/fragebogen/<id>/teilnehmer - Manage participants
    - /admin/fragebogen/<id>/auswertung - View statistics
    - /admin/fragebogen/<id>/duplicate - Create new version
"""

from __future__ import annotations

import json

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from v_flask.auth import permission_required
from v_flask.extensions import db
from v_flask_plugins.fragebogen.models import (
    Fragebogen,
    FragebogenStatus,
    FragebogenTeilnahme,
)
from v_flask_plugins.fragebogen.services import get_fragebogen_service

admin_bp = Blueprint(
    'fragebogen_admin',
    __name__,
    template_folder='../templates'
)


@admin_bp.route('/')
@login_required
@permission_required('admin.*')
def index():
    """List all questionnaires."""
    # Filter options
    show_archived = request.args.get('archived', 'false') == 'true'
    status_filter = request.args.get('status', 'all')

    query = db.session.query(Fragebogen)

    if not show_archived:
        query = query.filter_by(archiviert=False)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    frageboegen = query.order_by(Fragebogen.erstellt_am.desc()).all()

    return render_template(
        'fragebogen/admin/index.html',
        frageboegen=frageboegen,
        show_archived=show_archived,
        status_filter=status_filter,
        FragebogenStatus=FragebogenStatus
    )


@admin_bp.route('/neu', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def create():
    """Create a new questionnaire."""
    service = get_fragebogen_service()

    if request.method == 'POST':
        titel = request.form.get('titel', '').strip()
        beschreibung = request.form.get('beschreibung', '').strip()
        definition_str = request.form.get('definition_json', '{}')
        erlaubt_anonym = request.form.get('erlaubt_anonym') == 'on'

        # Parse JSON definition
        try:
            definition = json.loads(definition_str)
        except json.JSONDecodeError as e:
            flash(f'Ungültiges JSON: {e}', 'error')
            return render_template(
                'fragebogen/admin/form.html',
                fragebogen=None,
                titel=titel,
                beschreibung=beschreibung,
                definition_json=definition_str,
                erlaubt_anonym=erlaubt_anonym
            )

        # Validate
        if not titel:
            flash('Titel ist erforderlich', 'error')
            return render_template(
                'fragebogen/admin/form.html',
                fragebogen=None,
                titel=titel,
                beschreibung=beschreibung,
                definition_json=definition_str,
                erlaubt_anonym=erlaubt_anonym
            )

        result = service.validate_definition(definition)
        if not result.valid:
            for error in result.errors:
                flash(error, 'error')
            return render_template(
                'fragebogen/admin/form.html',
                fragebogen=None,
                titel=titel,
                beschreibung=beschreibung,
                definition_json=definition_str,
                erlaubt_anonym=erlaubt_anonym
            )

        # Create
        fragebogen = service.create_fragebogen(
            titel=titel,
            beschreibung=beschreibung or None,
            definition=definition,
            erstellt_von_id=current_user.id,
            erlaubt_anonym=erlaubt_anonym
        )

        flash(f'Fragebogen "{titel}" erstellt', 'success')
        return redirect(url_for('fragebogen_admin.detail', fragebogen_id=fragebogen.id))

    # GET: Empty form
    default_definition = {
        "version": 2,
        "seiten": [
            {
                "id": "s1",
                "titel": "Seite 1",
                "fragen": [
                    {
                        "id": "q1",
                        "typ": "text",
                        "frage": "Ihre erste Frage",
                        "pflicht": True
                    }
                ]
            }
        ]
    }

    return render_template(
        'fragebogen/admin/form.html',
        fragebogen=None,
        titel='',
        beschreibung='',
        definition_json=json.dumps(default_definition, indent=2, ensure_ascii=False),
        erlaubt_anonym=False
    )


@admin_bp.route('/<int:fragebogen_id>')
@login_required
@permission_required('admin.*')
def detail(fragebogen_id: int):
    """View questionnaire detail."""
    fragebogen = db.session.get(Fragebogen, fragebogen_id)
    if not fragebogen:
        flash('Fragebogen nicht gefunden', 'error')
        return redirect(url_for('fragebogen_admin.index'))

    # Get participant statistics
    teilnahmen = fragebogen.teilnahmen
    stats = {
        'gesamt': len(teilnahmen),
        'eingeladen': sum(1 for t in teilnahmen if t.is_eingeladen),
        'gestartet': sum(1 for t in teilnahmen if t.is_gestartet),
        'abgeschlossen': sum(1 for t in teilnahmen if t.is_abgeschlossen),
        'anonym': sum(1 for t in teilnahmen if t.is_anonym),
    }

    return render_template(
        'fragebogen/admin/detail.html',
        fragebogen=fragebogen,
        stats=stats,
        teilnahmen=teilnahmen
    )


@admin_bp.route('/<int:fragebogen_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def edit(fragebogen_id: int):
    """Edit a questionnaire (only in ENTWURF status)."""
    fragebogen = db.session.get(Fragebogen, fragebogen_id)
    if not fragebogen:
        flash('Fragebogen nicht gefunden', 'error')
        return redirect(url_for('fragebogen_admin.index'))

    if not fragebogen.is_entwurf:
        flash('Nur Entwürfe können bearbeitet werden', 'warning')
        return redirect(url_for('fragebogen_admin.detail', fragebogen_id=fragebogen_id))

    service = get_fragebogen_service()

    if request.method == 'POST':
        titel = request.form.get('titel', '').strip()
        beschreibung = request.form.get('beschreibung', '').strip()
        definition_str = request.form.get('definition_json', '{}')
        erlaubt_anonym = request.form.get('erlaubt_anonym') == 'on'

        # Parse JSON
        try:
            definition = json.loads(definition_str)
        except json.JSONDecodeError as e:
            flash(f'Ungültiges JSON: {e}', 'error')
            return render_template(
                'fragebogen/admin/form.html',
                fragebogen=fragebogen,
                titel=titel,
                beschreibung=beschreibung,
                definition_json=definition_str,
                erlaubt_anonym=erlaubt_anonym
            )

        # Validate
        if not titel:
            flash('Titel ist erforderlich', 'error')
            return render_template(
                'fragebogen/admin/form.html',
                fragebogen=fragebogen,
                titel=titel,
                beschreibung=beschreibung,
                definition_json=definition_str,
                erlaubt_anonym=erlaubt_anonym
            )

        result = service.validate_definition(definition)
        if not result.valid:
            for error in result.errors:
                flash(error, 'error')
            return render_template(
                'fragebogen/admin/form.html',
                fragebogen=fragebogen,
                titel=titel,
                beschreibung=beschreibung,
                definition_json=definition_str,
                erlaubt_anonym=erlaubt_anonym
            )

        # Update
        service.update_fragebogen(
            fragebogen=fragebogen,
            titel=titel,
            beschreibung=beschreibung or None,
            definition=definition,
            erlaubt_anonym=erlaubt_anonym
        )

        flash('Fragebogen gespeichert', 'success')
        return redirect(url_for('fragebogen_admin.detail', fragebogen_id=fragebogen.id))

    # GET: Prefill form
    return render_template(
        'fragebogen/admin/form.html',
        fragebogen=fragebogen,
        titel=fragebogen.titel,
        beschreibung=fragebogen.beschreibung or '',
        definition_json=json.dumps(
            fragebogen.definition_json, indent=2, ensure_ascii=False
        ),
        erlaubt_anonym=fragebogen.erlaubt_anonym
    )


@admin_bp.route('/<int:fragebogen_id>/status', methods=['POST'])
@login_required
@permission_required('admin.*')
def change_status(fragebogen_id: int):
    """Change questionnaire status (activate/close/reactivate)."""
    fragebogen = db.session.get(Fragebogen, fragebogen_id)
    if not fragebogen:
        return jsonify({'success': False, 'error': 'Nicht gefunden'}), 404

    action = request.form.get('action') or request.json.get('action')

    try:
        if action == 'aktivieren':
            if not fragebogen.is_entwurf:
                raise ValueError('Nur Entwürfe können aktiviert werden')
            fragebogen.aktivieren()
            db.session.commit()
            flash('Fragebogen aktiviert', 'success')

        elif action == 'schliessen':
            if not fragebogen.is_aktiv:
                raise ValueError('Nur aktive Fragebögen können geschlossen werden')
            fragebogen.schliessen()
            db.session.commit()
            flash('Fragebogen geschlossen', 'success')

        elif action == 'reaktivieren':
            fragebogen.reaktivieren()
            db.session.commit()
            flash('Fragebogen reaktiviert', 'success')

        elif action == 'archivieren':
            fragebogen.archivieren()
            db.session.commit()
            flash('Fragebogen archiviert', 'success')

        elif action == 'dearchivieren':
            fragebogen.dearchivieren()
            db.session.commit()
            flash('Fragebogen wiederhergestellt', 'success')

        else:
            raise ValueError(f'Unbekannte Aktion: {action}')

    except ValueError as e:
        flash(str(e), 'error')

    # Return JSON for AJAX or redirect for form
    if request.is_json:
        return jsonify({
            'success': True,
            'status': fragebogen.status,
            'archiviert': fragebogen.archiviert
        })

    return redirect(url_for('fragebogen_admin.detail', fragebogen_id=fragebogen_id))


@admin_bp.route('/<int:fragebogen_id>/teilnehmer')
@login_required
@permission_required('admin.*')
def teilnehmer(fragebogen_id: int):
    """View and manage participants."""
    fragebogen = db.session.get(Fragebogen, fragebogen_id)
    if not fragebogen:
        flash('Fragebogen nicht gefunden', 'error')
        return redirect(url_for('fragebogen_admin.index'))

    return render_template(
        'fragebogen/admin/teilnehmer.html',
        fragebogen=fragebogen,
        teilnahmen=fragebogen.teilnahmen
    )


@admin_bp.route('/<int:fragebogen_id>/einladungen', methods=['POST'])
@login_required
@permission_required('admin.*')
def send_einladungen(fragebogen_id: int):
    """Send invitation emails to participants."""
    fragebogen = db.session.get(Fragebogen, fragebogen_id)
    if not fragebogen:
        return jsonify({'success': False, 'error': 'Nicht gefunden'}), 404

    service = get_fragebogen_service()

    # Get selected participants or all unsent
    teilnahme_ids = request.form.getlist('teilnahme_ids')
    if teilnahme_ids:
        teilnahmen = [
            db.session.get(FragebogenTeilnahme, int(tid))
            for tid in teilnahme_ids
        ]
        teilnahmen = [t for t in teilnahmen if t is not None]
    else:
        teilnahmen = None  # Will default to all unsent

    result = service.send_einladungen(fragebogen, teilnahmen)

    if result.success:
        flash(f'{result.sent_count} Einladungen gesendet', 'success')
    else:
        for error in result.errors[:5]:  # Show first 5 errors
            flash(error, 'error')
        if result.sent_count > 0:
            flash(f'{result.sent_count} Einladungen erfolgreich, {result.failed_count} fehlgeschlagen', 'warning')

    return redirect(url_for('fragebogen_admin.teilnehmer', fragebogen_id=fragebogen_id))


@admin_bp.route('/<int:fragebogen_id>/auswertung')
@login_required
@permission_required('admin.*')
def auswertung(fragebogen_id: int):
    """View questionnaire statistics."""
    fragebogen = db.session.get(Fragebogen, fragebogen_id)
    if not fragebogen:
        flash('Fragebogen nicht gefunden', 'error')
        return redirect(url_for('fragebogen_admin.index'))

    service = get_fragebogen_service()
    stats = service.get_auswertung(fragebogen)

    return render_template(
        'fragebogen/admin/auswertung.html',
        fragebogen=fragebogen,
        stats=stats
    )


@admin_bp.route('/<int:fragebogen_id>/export')
@login_required
@permission_required('admin.*')
def export_xlsx(fragebogen_id: int):
    """Export questionnaire answers as XLSX."""
    fragebogen = db.session.get(Fragebogen, fragebogen_id)
    if not fragebogen:
        flash('Fragebogen nicht gefunden', 'error')
        return redirect(url_for('fragebogen_admin.index'))

    # TODO: Implement XLSX export
    flash('XLSX-Export noch nicht implementiert', 'info')
    return redirect(url_for('fragebogen_admin.auswertung', fragebogen_id=fragebogen_id))


@admin_bp.route('/<int:fragebogen_id>/duplicate', methods=['POST'])
@login_required
@permission_required('admin.*')
def duplicate(fragebogen_id: int):
    """Create a new version of the questionnaire."""
    fragebogen = db.session.get(Fragebogen, fragebogen_id)
    if not fragebogen:
        flash('Fragebogen nicht gefunden', 'error')
        return redirect(url_for('fragebogen_admin.index'))

    service = get_fragebogen_service()

    try:
        new_titel = request.form.get('titel')
        new_fragebogen = service.duplicate_fragebogen(
            fragebogen=fragebogen,
            user_id=current_user.id,
            new_titel=new_titel
        )
        flash(
            f'Neue Version {new_fragebogen.version_nummer} erstellt',
            'success'
        )
        return redirect(url_for('fragebogen_admin.detail', fragebogen_id=new_fragebogen.id))

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('fragebogen_admin.detail', fragebogen_id=fragebogen_id))


@admin_bp.route('/<int:fragebogen_id>/anonym-link', methods=['POST'])
@login_required
@permission_required('admin.*')
def create_anonymous_link(fragebogen_id: int):
    """Create an anonymous participation link."""
    fragebogen = db.session.get(Fragebogen, fragebogen_id)
    if not fragebogen:
        return jsonify({'success': False, 'error': 'Nicht gefunden'}), 404

    if not fragebogen.erlaubt_anonym:
        return jsonify({
            'success': False,
            'error': 'Anonyme Teilnahme nicht erlaubt'
        }), 400

    service = get_fragebogen_service()

    try:
        teilnahme = service.create_anonymous_teilnahme(fragebogen)
        link = url_for(
            'fragebogen_public.wizard',
            token=teilnahme.token,
            _external=True
        )
        return jsonify({
            'success': True,
            'link': link,
            'token': teilnahme.token
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
