"""Public Routes for Geo-Drilling.

Public-facing routes for browsing the directory hierarchy.
URL structure: /<type>/<bundesland>/<kreis>/<ort>/<entry>/
"""

from flask import Blueprint, render_template, abort, request
from v_flask.extensions import db

from ..models import (
    DirectoryType,
    DirectoryEntry,
    GeoLand,
    GeoBundesland,
    GeoKreis,
    GeoOrt,
)

public_bp = Blueprint(
    'business_directory_public',
    __name__,
    template_folder='../templates'
)


@public_bp.route('/')
def index():
    """Directory overview - list all active directory types."""
    types = DirectoryType.query.filter_by(active=True).order_by(
        DirectoryType.name
    ).all()

    return render_template(
        'business_directory/public/index.html',
        types=types
    )


@public_bp.route('/<type_slug>/')
def type_index(type_slug):
    """Directory type overview - list Bundesländer with entries.

    URL: /haendler/ or /hersteller/
    """
    directory_type = DirectoryType.get_by_slug(type_slug)
    if not directory_type or not directory_type.active:
        abort(404)

    # Get Bundesländer with active entries for this type
    bundeslaender = GeoBundesland.query.join(
        GeoKreis
    ).join(
        GeoOrt
    ).join(
        DirectoryEntry
    ).filter(
        DirectoryEntry.directory_type_id == directory_type.id,
        DirectoryEntry.active == True  # noqa: E712
    ).distinct().order_by(GeoBundesland.name).all()

    return render_template(
        'business_directory/public/type_index.html',
        directory_type=directory_type,
        bundeslaender=bundeslaender
    )


@public_bp.route('/<type_slug>/<bundesland_slug>/')
def bundesland(type_slug, bundesland_slug):
    """Bundesland page - list Kreise with entries.

    URL: /haendler/nordrhein-westfalen/
    """
    directory_type = DirectoryType.get_by_slug(type_slug)
    if not directory_type or not directory_type.active:
        abort(404)

    bundesland = GeoBundesland.get_by_slug(bundesland_slug)
    if not bundesland:
        abort(404)

    # Get Kreise with active entries for this type
    kreise = GeoKreis.query.filter_by(
        bundesland_id=bundesland.id
    ).join(
        GeoOrt
    ).join(
        DirectoryEntry
    ).filter(
        DirectoryEntry.directory_type_id == directory_type.id,
        DirectoryEntry.active == True  # noqa: E712
    ).distinct().order_by(GeoKreis.name).all()

    return render_template(
        'business_directory/public/bundesland.html',
        directory_type=directory_type,
        bundesland=bundesland,
        kreise=kreise
    )


@public_bp.route('/<type_slug>/<bundesland_slug>/<kreis_slug>/')
def kreis(type_slug, bundesland_slug, kreis_slug):
    """Kreis page - list Orte or directly show entries.

    URL: /haendler/nordrhein-westfalen/kleve/
    """
    directory_type = DirectoryType.get_by_slug(type_slug)
    if not directory_type or not directory_type.active:
        abort(404)

    bundesland = GeoBundesland.get_by_slug(bundesland_slug)
    if not bundesland:
        abort(404)

    kreis = GeoKreis.get_by_slug(kreis_slug, bundesland.id)
    if not kreis:
        abort(404)

    # Get Orte with active entries for this type
    orte = GeoOrt.query.filter_by(
        kreis_id=kreis.id,
        ist_hauptort=True
    ).join(
        DirectoryEntry
    ).filter(
        DirectoryEntry.directory_type_id == directory_type.id,
        DirectoryEntry.active == True  # noqa: E712
    ).distinct().order_by(GeoOrt.name).all()

    # Also get total entry count
    entry_count = DirectoryEntry.query.join(
        GeoOrt
    ).filter(
        GeoOrt.kreis_id == kreis.id,
        DirectoryEntry.directory_type_id == directory_type.id,
        DirectoryEntry.active == True  # noqa: E712
    ).count()

    return render_template(
        'business_directory/public/kreis.html',
        directory_type=directory_type,
        bundesland=bundesland,
        kreis=kreis,
        orte=orte,
        entry_count=entry_count
    )


@public_bp.route('/<type_slug>/<bundesland_slug>/<kreis_slug>/<ort_slug>/')
def ort(type_slug, bundesland_slug, kreis_slug, ort_slug):
    """Ort page - list all entries in this location.

    URL: /haendler/nordrhein-westfalen/kleve/kleve/
    """
    directory_type = DirectoryType.get_by_slug(type_slug)
    if not directory_type or not directory_type.active:
        abort(404)

    bundesland = GeoBundesland.get_by_slug(bundesland_slug)
    if not bundesland:
        abort(404)

    kreis = GeoKreis.get_by_slug(kreis_slug, bundesland.id)
    if not kreis:
        abort(404)

    ort = GeoOrt.get_by_slug(ort_slug, kreis.id)
    if not ort:
        abort(404)

    # Get all PLZ variants for this Ort name
    ort_ids = [o.id for o in GeoOrt.query.filter_by(
        kreis_id=kreis.id,
        name=ort.name
    ).all()]

    # Get entries
    entries = DirectoryEntry.query.filter(
        DirectoryEntry.geo_ort_id.in_(ort_ids),
        DirectoryEntry.directory_type_id == directory_type.id,
        DirectoryEntry.active == True  # noqa: E712
    ).order_by(DirectoryEntry.name).all()

    return render_template(
        'business_directory/public/ort.html',
        directory_type=directory_type,
        bundesland=bundesland,
        kreis=kreis,
        ort=ort,
        entries=entries
    )


@public_bp.route('/<type_slug>/<bundesland_slug>/<kreis_slug>/<ort_slug>/<entry_slug>/')
def entry_detail(type_slug, bundesland_slug, kreis_slug, ort_slug, entry_slug):
    """Entry detail page.

    URL: /haendler/nordrhein-westfalen/kleve/kleve/spielwaren-schmidt/
    """
    directory_type = DirectoryType.get_by_slug(type_slug)
    if not directory_type or not directory_type.active:
        abort(404)

    bundesland = GeoBundesland.get_by_slug(bundesland_slug)
    if not bundesland:
        abort(404)

    kreis = GeoKreis.get_by_slug(kreis_slug, bundesland.id)
    if not kreis:
        abort(404)

    ort = GeoOrt.get_by_slug(ort_slug, kreis.id)
    if not ort:
        abort(404)

    # Get entry
    entry = DirectoryEntry.query.filter_by(
        slug=entry_slug,
        directory_type_id=directory_type.id,
        active=True
    ).first()

    if not entry:
        abort(404)

    # Verify entry is in the correct location
    if entry.geo_ort and entry.geo_ort.hauptort != ort:
        abort(404)

    return render_template(
        'business_directory/public/entry_detail.html',
        directory_type=directory_type,
        bundesland=bundesland,
        kreis=kreis,
        ort=ort,
        entry=entry
    )


@public_bp.route('/<type_slug>/search')
def search(type_slug):
    """Search entries within a directory type.

    URL: /haendler/search?q=spielwaren&plz=47533
    """
    directory_type = DirectoryType.get_by_slug(type_slug)
    if not directory_type or not directory_type.active:
        abort(404)

    # Search parameters
    q = request.args.get('q', '').strip()
    plz = request.args.get('plz', '').strip()
    page = request.args.get('page', 1, type=int)

    # Base query
    query = DirectoryEntry.query.filter_by(
        directory_type_id=directory_type.id,
        active=True
    )

    # Text search
    if q:
        query = query.filter(
            db.or_(
                DirectoryEntry.name.ilike(f'%{q}%'),
                DirectoryEntry.kurzbeschreibung.ilike(f'%{q}%'),
            )
        )

    # PLZ filter
    if plz:
        query = query.join(GeoOrt).filter(GeoOrt.plz == plz)

    # Pagination
    entries = query.order_by(DirectoryEntry.name).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template(
        'business_directory/public/search.html',
        directory_type=directory_type,
        entries=entries,
        q=q,
        plz=plz
    )
