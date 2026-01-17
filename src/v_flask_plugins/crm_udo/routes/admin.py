"""Admin routes for CRM UDO plugin.

Provides UI for managing companies, organisations, and contacts.
All data is fetched from UDO API.
"""
from __future__ import annotations

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
import httpx

from v_flask.auth import permission_required

from ..api_client import crm_client

# Note: @udo_api_login_required is no longer needed since UDO UI now uses
# Unified Login where authentication is handled via Flask-Login.


admin_bp = Blueprint(
    'crm_udo_admin',
    __name__,
    template_folder='../templates'
)


# ============ Dashboard ============


@admin_bp.route('/')
@permission_required('admin.*')
def index():
    """CRM Dashboard - overview with stats."""
    try:
        unternehmen_count = crm_client.get_unternehmen_count()
    except httpx.HTTPError as e:
        flash(f'API-Fehler: {e}', 'error')
        unternehmen_count = 0

    return render_template(
        'crm_udo/admin/index.html',
        unternehmen_count=unternehmen_count,
    )


# ============ Unternehmen ============


@admin_bp.route('/unternehmen')
@permission_required('admin.*')
def unternehmen_list():
    """List companies with pagination and search."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    suche = request.args.get('suche', '', type=str).strip()

    try:
        result = crm_client.list_unternehmen(
            suche=suche if suche else None,
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        items = result.get('items', [])
        total = result.get('total', 0)
    except httpx.HTTPError as e:
        flash(f'API-Fehler: {e}', 'error')
        items = []
        total = 0

    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'crm_udo/admin/unternehmen_list.html',
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        suche=suche,
    )


@admin_bp.route('/unternehmen/<unternehmen_id>')
@permission_required('admin.*')
def unternehmen_detail(unternehmen_id: str):
    """Show company details with contacts."""
    try:
        unternehmen = crm_client.get_unternehmen(unternehmen_id)
        kontakte_result = crm_client.list_kontakte(unternehmen_id)
        kontakte = kontakte_result.get('items', [])
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            flash('Unternehmen nicht gefunden.', 'error')
            return redirect(url_for('crm_udo_admin.unternehmen_list'))
        flash(f'API-Fehler: {e}', 'error')
        return redirect(url_for('crm_udo_admin.unternehmen_list'))
    except httpx.HTTPError as e:
        flash(f'API-Fehler: {e}', 'error')
        return redirect(url_for('crm_udo_admin.unternehmen_list'))

    return render_template(
        'crm_udo/admin/unternehmen_detail.html',
        unternehmen=unternehmen,
        kontakte=kontakte,
    )


@admin_bp.route('/unternehmen/neu', methods=['GET', 'POST'])
@permission_required('admin.*')
def unternehmen_neu():
    """Create new company."""
    if request.method == 'POST':
        data = {
            'kurzname': request.form.get('kurzname', '').strip(),
            'firmierung': request.form.get('firmierung', '').strip() or None,
            'strasse': request.form.get('strasse', '').strip() or None,
            'strasse_hausnr': request.form.get('strasse_hausnr', '').strip() or None,
            'geo_ort_id': request.form.get('geo_ort_id', '').strip() or None,
        }

        if not data['kurzname']:
            flash('Kurzname ist erforderlich.', 'error')
            return render_template(
                'crm_udo/admin/unternehmen_form.html',
                unternehmen=data,
                is_new=True,
            )

        try:
            result = crm_client.create_unternehmen(data)
            flash('Unternehmen erfolgreich erstellt.', 'success')
            return redirect(url_for(
                'crm_udo_admin.unternehmen_detail',
                unternehmen_id=result['id']
            ))
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get('detail', str(e))
            flash(f'Fehler beim Erstellen: {error_detail}', 'error')
        except httpx.HTTPError as e:
            flash(f'API-Fehler: {e}', 'error')

        return render_template(
            'crm_udo/admin/unternehmen_form.html',
            unternehmen=data,
            is_new=True,
        )

    return render_template(
        'crm_udo/admin/unternehmen_form.html',
        unternehmen={},
        is_new=True,
    )


@admin_bp.route('/unternehmen/<unternehmen_id>/edit', methods=['GET', 'POST'])
@permission_required('admin.*')
def unternehmen_edit(unternehmen_id: str):
    """Edit company."""
    if request.method == 'POST':
        data = {
            'kurzname': request.form.get('kurzname', '').strip(),
            'firmierung': request.form.get('firmierung', '').strip() or None,
            'strasse': request.form.get('strasse', '').strip() or None,
            'strasse_hausnr': request.form.get('strasse_hausnr', '').strip() or None,
            'geo_ort_id': request.form.get('geo_ort_id', '').strip() or None,
        }

        if not data['kurzname']:
            flash('Kurzname ist erforderlich.', 'error')
            data['id'] = unternehmen_id
            return render_template(
                'crm_udo/admin/unternehmen_form.html',
                unternehmen=data,
                is_new=False,
            )

        try:
            crm_client.update_unternehmen(unternehmen_id, data)
            flash('Unternehmen erfolgreich aktualisiert.', 'success')
            return redirect(url_for(
                'crm_udo_admin.unternehmen_detail',
                unternehmen_id=unternehmen_id
            ))
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get('detail', str(e))
            flash(f'Fehler beim Speichern: {error_detail}', 'error')
        except httpx.HTTPError as e:
            flash(f'API-Fehler: {e}', 'error')

        data['id'] = unternehmen_id
        return render_template(
            'crm_udo/admin/unternehmen_form.html',
            unternehmen=data,
            is_new=False,
        )

    # GET: Load existing data
    try:
        unternehmen = crm_client.get_unternehmen(unternehmen_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            flash('Unternehmen nicht gefunden.', 'error')
            return redirect(url_for('crm_udo_admin.unternehmen_list'))
        flash(f'API-Fehler: {e}', 'error')
        return redirect(url_for('crm_udo_admin.unternehmen_list'))
    except httpx.HTTPError as e:
        flash(f'API-Fehler: {e}', 'error')
        return redirect(url_for('crm_udo_admin.unternehmen_list'))

    return render_template(
        'crm_udo/admin/unternehmen_form.html',
        unternehmen=unternehmen,
        is_new=False,
    )


@admin_bp.route('/unternehmen/<unternehmen_id>/delete', methods=['POST'])
@permission_required('admin.*')
def unternehmen_delete(unternehmen_id: str):
    """Delete company."""
    try:
        crm_client.delete_unternehmen(unternehmen_id)
        flash('Unternehmen erfolgreich gelöscht.', 'success')
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            flash('Unternehmen nicht gefunden.', 'error')
        else:
            error_detail = e.response.json().get('detail', str(e))
            flash(f'Fehler beim Löschen: {error_detail}', 'error')
    except httpx.HTTPError as e:
        flash(f'API-Fehler: {e}', 'error')

    return redirect(url_for('crm_udo_admin.unternehmen_list'))


# ============ Kontakte ============


@admin_bp.route('/unternehmen/<unternehmen_id>/kontakte/neu', methods=['GET', 'POST'])
@permission_required('admin.*')
def kontakt_neu(unternehmen_id: str):
    """Create new contact for a company."""
    if request.method == 'POST':
        data = {
            'vorname': request.form.get('vorname', '').strip(),
            'nachname': request.form.get('nachname', '').strip(),
            'typ': request.form.get('typ', '').strip() or None,
            'titel': request.form.get('titel', '').strip() or None,
            'anrede': request.form.get('anrede', '').strip() or None,
            'position': request.form.get('position', '').strip() or None,
            'abteilung': request.form.get('abteilung', '').strip() or None,
            'telefon': request.form.get('telefon', '').strip() or None,
            'mobil': request.form.get('mobil', '').strip() or None,
            'fax': request.form.get('fax', '').strip() or None,
            'email': request.form.get('email', '').strip() or None,
            'notizen': request.form.get('notizen', '').strip() or None,
            'ist_hauptkontakt': request.form.get('ist_hauptkontakt') == 'on',
        }

        if not data['vorname'] or not data['nachname']:
            flash('Vor- und Nachname sind erforderlich.', 'error')
            return redirect(url_for(
                'crm_udo_admin.unternehmen_detail',
                unternehmen_id=unternehmen_id
            ))

        try:
            crm_client.create_kontakt(unternehmen_id, data)
            flash('Kontakt erfolgreich erstellt.', 'success')
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get('detail', str(e))
            flash(f'Fehler beim Erstellen: {error_detail}', 'error')
        except httpx.HTTPError as e:
            flash(f'API-Fehler: {e}', 'error')

        return redirect(url_for(
            'crm_udo_admin.unternehmen_detail',
            unternehmen_id=unternehmen_id
        ))

    # GET: redirect to detail page (form is in modal)
    return redirect(url_for(
        'crm_udo_admin.unternehmen_detail',
        unternehmen_id=unternehmen_id
    ))


@admin_bp.route(
    '/unternehmen/<unternehmen_id>/kontakte/<kontakt_id>/edit',
    methods=['POST']
)
@permission_required('admin.*')
def kontakt_edit(unternehmen_id: str, kontakt_id: str):
    """Update contact."""
    data = {
        'vorname': request.form.get('vorname', '').strip(),
        'nachname': request.form.get('nachname', '').strip(),
        'typ': request.form.get('typ', '').strip() or None,
        'titel': request.form.get('titel', '').strip() or None,
        'anrede': request.form.get('anrede', '').strip() or None,
        'position': request.form.get('position', '').strip() or None,
        'abteilung': request.form.get('abteilung', '').strip() or None,
        'telefon': request.form.get('telefon', '').strip() or None,
        'mobil': request.form.get('mobil', '').strip() or None,
        'fax': request.form.get('fax', '').strip() or None,
        'email': request.form.get('email', '').strip() or None,
        'notizen': request.form.get('notizen', '').strip() or None,
        'ist_hauptkontakt': request.form.get('ist_hauptkontakt') == 'on',
    }

    if not data['vorname'] or not data['nachname']:
        flash('Vor- und Nachname sind erforderlich.', 'error')
        return redirect(url_for(
            'crm_udo_admin.unternehmen_detail',
            unternehmen_id=unternehmen_id
        ))

    try:
        crm_client.update_kontakt(unternehmen_id, kontakt_id, data)
        flash('Kontakt erfolgreich aktualisiert.', 'success')
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get('detail', str(e))
        flash(f'Fehler beim Speichern: {error_detail}', 'error')
    except httpx.HTTPError as e:
        flash(f'API-Fehler: {e}', 'error')

    return redirect(url_for(
        'crm_udo_admin.unternehmen_detail',
        unternehmen_id=unternehmen_id
    ))


@admin_bp.route(
    '/unternehmen/<unternehmen_id>/kontakte/<kontakt_id>/delete',
    methods=['POST']
)
@permission_required('admin.*')
def kontakt_delete(unternehmen_id: str, kontakt_id: str):
    """Delete contact."""
    try:
        crm_client.delete_kontakt(unternehmen_id, kontakt_id)
        flash('Kontakt erfolgreich gelöscht.', 'success')
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            flash('Kontakt nicht gefunden.', 'error')
        else:
            error_detail = e.response.json().get('detail', str(e))
            flash(f'Fehler beim Löschen: {error_detail}', 'error')
    except httpx.HTTPError as e:
        flash(f'API-Fehler: {e}', 'error')

    return redirect(url_for(
        'crm_udo_admin.unternehmen_detail',
        unternehmen_id=unternehmen_id
    ))
