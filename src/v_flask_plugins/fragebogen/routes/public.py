"""Public routes for Fragebogen plugin.

Provides magic-link access for questionnaire participation:
    - /fragebogen/t/<token> - Magic-link wizard
    - /fragebogen/t/<token>/antwort - AJAX auto-save
    - /fragebogen/t/<token>/abschliessen - Complete questionnaire
    - /fragebogen/t/<token>/danke - Thank you page
    - /fragebogen/anonym/<fragebogen_id> - Start anonymous participation
"""

from __future__ import annotations

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from v_flask.extensions import db
from v_flask_plugins.fragebogen.models import Fragebogen, FragebogenTeilnahme
from v_flask_plugins.fragebogen.services import get_fragebogen_service

public_bp = Blueprint(
    'fragebogen_public',
    __name__,
    template_folder='../templates'
)


@public_bp.route('/t/<token>')
def wizard(token: str):
    """Display the questionnaire wizard.

    Accessed via magic-link. No login required.
    """
    service = get_fragebogen_service()
    teilnahme = service.get_teilnahme_by_token(token)

    if not teilnahme:
        return render_template('fragebogen/public/invalid.html'), 404

    fragebogen = teilnahme.fragebogen

    # Check if fragebogen is still active
    if not fragebogen.is_aktiv:
        return render_template(
            'fragebogen/public/invalid.html',
            message='Dieser Fragebogen ist nicht mehr aktiv.'
        )

    # Check if already completed
    if teilnahme.is_abgeschlossen:
        return redirect(url_for('fragebogen_public.danke', token=token))

    # Start participation if not started
    if teilnahme.is_eingeladen:
        teilnahme.starten()
        db.session.commit()

    # Get existing answers
    antworten = {a.frage_id: a.antwort_json for a in teilnahme.antworten}

    # Get initial/prefill values for unanswered questions
    initial = service.get_initial_antworten(fragebogen, teilnahme)
    for frage_id, value in initial.items():
        if frage_id not in antworten:
            antworten[frage_id] = value

    # Determine current page (based on answered questions)
    current_page = _get_current_page(fragebogen, antworten)

    return render_template(
        'fragebogen/public/wizard.html',
        fragebogen=fragebogen,
        teilnahme=teilnahme,
        antworten=antworten,
        current_page=current_page,
        is_anonym=teilnahme.is_anonym
    )


@public_bp.route('/t/<token>/antwort', methods=['POST'])
def save_antwort(token: str):
    """Save an answer via AJAX (auto-save)."""
    service = get_fragebogen_service()
    teilnahme = service.get_teilnahme_by_token(token)

    if not teilnahme:
        return jsonify({'success': False, 'error': 'Token ungültig'}), 404

    if not teilnahme.fragebogen.is_aktiv:
        return jsonify({'success': False, 'error': 'Fragebogen nicht aktiv'}), 400

    if teilnahme.is_abgeschlossen:
        return jsonify({'success': False, 'error': 'Bereits abgeschlossen'}), 400

    data = request.get_json()
    frage_id = data.get('frage_id')
    antwort_json = data.get('antwort')

    if not frage_id or antwort_json is None:
        return jsonify({'success': False, 'error': 'frage_id und antwort erforderlich'}), 400

    try:
        service.save_antwort(teilnahme, frage_id, antwort_json)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@public_bp.route('/t/<token>/kontakt', methods=['POST'])
def save_kontakt(token: str):
    """Save contact data for anonymous participation."""
    service = get_fragebogen_service()
    teilnahme = service.get_teilnahme_by_token(token)

    if not teilnahme:
        return jsonify({'success': False, 'error': 'Token ungültig'}), 404

    if not teilnahme.is_anonym:
        return jsonify({'success': False, 'error': 'Nur für anonyme Teilnahme'}), 400

    data = request.get_json() or request.form
    email = data.get('kontakt_email', '').strip()
    name = data.get('kontakt_name', '').strip()
    zusatz = {}

    # Collect zusatz fields
    for key, value in data.items():
        if key.startswith('kontakt_zusatz_'):
            field_name = key.replace('kontakt_zusatz_', '')
            zusatz[field_name] = value

    if not email or not name:
        return jsonify({
            'success': False,
            'error': 'Name und E-Mail sind erforderlich'
        }), 400

    try:
        service.save_kontakt_daten(
            teilnahme=teilnahme,
            email=email,
            name=name,
            zusatz=zusatz if zusatz else None
        )
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@public_bp.route('/t/<token>/abschliessen', methods=['POST'])
def abschliessen(token: str):
    """Complete the questionnaire."""
    service = get_fragebogen_service()
    teilnahme = service.get_teilnahme_by_token(token)

    if not teilnahme:
        flash('Ungültiger Link', 'error')
        return render_template('fragebogen/public/invalid.html'), 404

    if teilnahme.is_abgeschlossen:
        return redirect(url_for('fragebogen_public.danke', token=token))

    try:
        service.complete_teilnahme(teilnahme)
        return redirect(url_for('fragebogen_public.danke', token=token))
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('fragebogen_public.wizard', token=token))


@public_bp.route('/t/<token>/danke')
def danke(token: str):
    """Thank you page after completion."""
    service = get_fragebogen_service()
    teilnahme = service.get_teilnahme_by_token(token)

    if not teilnahme:
        return render_template('fragebogen/public/invalid.html'), 404

    return render_template(
        'fragebogen/public/danke.html',
        fragebogen=teilnahme.fragebogen,
        teilnahme=teilnahme
    )


@public_bp.route('/anonym/<int:fragebogen_id>')
def start_anonymous(fragebogen_id: int):
    """Start anonymous participation for a questionnaire.

    Creates a new anonymous participation and redirects to wizard.
    """
    fragebogen = db.session.get(Fragebogen, fragebogen_id)

    if not fragebogen:
        return render_template(
            'fragebogen/public/invalid.html',
            message='Fragebogen nicht gefunden'
        ), 404

    if not fragebogen.is_aktiv:
        return render_template(
            'fragebogen/public/invalid.html',
            message='Dieser Fragebogen ist nicht mehr aktiv.'
        )

    if not fragebogen.erlaubt_anonym:
        return render_template(
            'fragebogen/public/invalid.html',
            message='Anonyme Teilnahme ist für diesen Fragebogen nicht erlaubt.'
        )

    service = get_fragebogen_service()

    try:
        teilnahme = service.create_anonymous_teilnahme(fragebogen)
        return redirect(url_for('fragebogen_public.wizard', token=teilnahme.token))
    except ValueError as e:
        return render_template(
            'fragebogen/public/invalid.html',
            message=str(e)
        ), 400


def _get_current_page(fragebogen: Fragebogen, antworten: dict) -> int:
    """Determine the current page based on answered questions.

    Returns the first page with unanswered required questions,
    or the last page if all are answered.
    """
    if not fragebogen.is_v2:
        return 0

    for page_idx, seite in enumerate(fragebogen.seiten):
        for frage in seite.get('fragen', []):
            frage_id = frage.get('id')
            if frage.get('pflicht', False):
                if frage_id not in antworten:
                    return page_idx
                antwort = antworten.get(frage_id, {})
                value = antwort.get('value') if isinstance(antwort, dict) else antwort
                if not value and value != 0 and value is not False:
                    return page_idx

    # All answered - show last page
    return len(fragebogen.seiten) - 1
