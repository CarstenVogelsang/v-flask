"""Admin Routes for Geodata Import.

Import geodata from unternehmensdaten.org API.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from v_flask.extensions import db
from v_flask.auth import admin_required

from ..models import GeoLand, GeoBundesland, GeoKreis, GeoOrt

admin_geodaten_bp = Blueprint(
    'business_directory_admin_geodaten',
    __name__,
    template_folder='../templates'
)


@admin_geodaten_bp.route('/')
@admin_required
def index():
    """Geodata overview."""
    laender = GeoLand.query.order_by(GeoLand.name).all()

    stats = {
        'laender': GeoLand.query.count(),
        'bundeslaender': GeoBundesland.query.count(),
        'kreise': GeoKreis.query.count(),
        'orte': GeoOrt.query.count(),
        'kreise_importiert': GeoKreis.query.filter_by(orte_importiert=True).count(),
    }

    return render_template(
        'business_directory/admin/geodaten/index.html',
        laender=laender,
        stats=stats
    )


@admin_geodaten_bp.route('/land/<land_id>')
@admin_required
def view_land(land_id):
    """View Bundesländer for a Land."""
    land = db.session.get(GeoLand, land_id)
    if not land:
        flash('Land nicht gefunden.', 'error')
        return redirect(url_for('.index'))

    bundeslaender = land.bundeslaender.order_by(GeoBundesland.name).all()

    return render_template(
        'business_directory/admin/geodaten/land.html',
        land=land,
        bundeslaender=bundeslaender
    )


@admin_geodaten_bp.route('/bundesland/<bundesland_id>')
@admin_required
def view_bundesland(bundesland_id):
    """View Kreise for a Bundesland."""
    bundesland = db.session.get(GeoBundesland, bundesland_id)
    if not bundesland:
        flash('Bundesland nicht gefunden.', 'error')
        return redirect(url_for('.index'))

    kreise = bundesland.kreise.order_by(GeoKreis.name).all()

    return render_template(
        'business_directory/admin/geodaten/bundesland.html',
        bundesland=bundesland,
        kreise=kreise
    )


@admin_geodaten_bp.route('/kreis/<kreis_id>')
@admin_required
def view_kreis(kreis_id):
    """View Orte for a Kreis."""
    kreis = db.session.get(GeoKreis, kreis_id)
    if not kreis:
        flash('Kreis nicht gefunden.', 'error')
        return redirect(url_for('.index'))

    orte = kreis.orte.order_by(GeoOrt.name, GeoOrt.plz).all()

    return render_template(
        'business_directory/admin/geodaten/kreis.html',
        kreis=kreis,
        orte=orte
    )


@admin_geodaten_bp.route('/import/laender', methods=['POST'])
@admin_required
def import_laender():
    """Import all Länder from API."""
    from ..services.geodaten_service import GeodatenService

    try:
        service = GeodatenService()
        count = service.import_laender()
        flash(f'{count} Länder wurden importiert.', 'success')
    except Exception as e:
        flash(f'Fehler beim Import: {str(e)}', 'error')

    return redirect(url_for('.index'))


@admin_geodaten_bp.route('/import/bundeslaender/<land_id>', methods=['POST'])
@admin_required
def import_bundeslaender(land_id):
    """Import Bundesländer for a Land."""
    from ..services.geodaten_service import GeodatenService

    land = db.session.get(GeoLand, land_id)
    if not land:
        flash('Land nicht gefunden.', 'error')
        return redirect(url_for('.index'))

    try:
        service = GeodatenService()
        count = service.import_bundeslaender(land_id)
        flash(f'{count} Bundesländer wurden für {land.name} importiert.', 'success')
    except Exception as e:
        flash(f'Fehler beim Import: {str(e)}', 'error')

    return redirect(url_for('.view_land', land_id=land_id))


@admin_geodaten_bp.route('/import/kreise/<bundesland_id>', methods=['POST'])
@admin_required
def import_kreise(bundesland_id):
    """Import Kreise for a Bundesland."""
    from ..services.geodaten_service import GeodatenService

    bundesland = db.session.get(GeoBundesland, bundesland_id)
    if not bundesland:
        flash('Bundesland nicht gefunden.', 'error')
        return redirect(url_for('.index'))

    try:
        service = GeodatenService()
        count = service.import_kreise(bundesland_id)
        flash(f'{count} Kreise wurden für {bundesland.name} importiert.', 'success')
    except Exception as e:
        flash(f'Fehler beim Import: {str(e)}', 'error')

    return redirect(url_for('.view_bundesland', bundesland_id=bundesland_id))


@admin_geodaten_bp.route('/import/orte/<kreis_id>', methods=['POST'])
@admin_required
def import_orte(kreis_id):
    """Import Orte for a Kreis."""
    from ..services.geodaten_service import GeodatenService

    kreis = db.session.get(GeoKreis, kreis_id)
    if not kreis:
        flash('Kreis nicht gefunden.', 'error')
        return redirect(url_for('.index'))

    try:
        service = GeodatenService()
        count = service.import_orte(kreis_id)
        flash(f'{count} Orte wurden für {kreis.name} importiert.', 'success')
    except Exception as e:
        flash(f'Fehler beim Import: {str(e)}', 'error')

    return redirect(url_for('.view_kreis', kreis_id=kreis_id))


@admin_geodaten_bp.route('/import/all-orte/<bundesland_id>', methods=['POST'])
@admin_required
def import_all_orte(bundesland_id):
    """Import all Orte for all Kreise in a Bundesland."""
    from ..services.geodaten_service import GeodatenService

    bundesland = db.session.get(GeoBundesland, bundesland_id)
    if not bundesland:
        flash('Bundesland nicht gefunden.', 'error')
        return redirect(url_for('.index'))

    try:
        service = GeodatenService()
        total = 0
        for kreis in bundesland.kreise.all():
            if not kreis.orte_importiert:
                count = service.import_orte(kreis.id)
                total += count

        flash(
            f'{total} Orte wurden für alle Kreise in {bundesland.name} importiert.',
            'success'
        )
    except Exception as e:
        flash(f'Fehler beim Import: {str(e)}', 'error')

    return redirect(url_for('.view_bundesland', bundesland_id=bundesland_id))
