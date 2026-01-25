"""API Routes for Directory Search.

JSON API for search and autocomplete functionality.
"""

from flask import Blueprint, jsonify, request
from v_flask.extensions import db

from ..models import DirectoryType, DirectoryEntry, GeoOrt, GeoKreis, GeoBundesland

api_bp = Blueprint(
    'business_directory_api',
    __name__,
    template_folder='../templates'
)


@api_bp.route('/search')
def search():
    """Search entries across all or specific directory types.

    Query parameters:
        q: Search query (name, description)
        type: Directory type slug filter
        plz: PLZ filter
        lat, lng, radius: Location-based search (km)
        limit: Max results (default 20, max 100)
        offset: Pagination offset
    """
    q = request.args.get('q', '').strip()
    type_slug = request.args.get('type', '').strip()
    plz = request.args.get('plz', '').strip()
    limit = min(request.args.get('limit', 20, type=int), 100)
    offset = request.args.get('offset', 0, type=int)

    # Base query - only active entries
    query = DirectoryEntry.query.filter_by(active=True)

    # Filter by type
    if type_slug:
        directory_type = DirectoryType.get_by_slug(type_slug)
        if directory_type:
            query = query.filter_by(directory_type_id=directory_type.id)

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

    # Get total count
    total = query.count()

    # Apply pagination
    entries = query.order_by(DirectoryEntry.name).offset(offset).limit(limit).all()

    return jsonify({
        'success': True,
        'total': total,
        'limit': limit,
        'offset': offset,
        'results': [_serialize_entry(entry) for entry in entries]
    })


@api_bp.route('/entry/<int:entry_id>')
def get_entry(entry_id):
    """Get a single entry by ID."""
    entry = db.session.get(DirectoryEntry, entry_id)

    if not entry or not entry.active:
        return jsonify({
            'success': False,
            'error': 'Entry not found'
        }), 404

    return jsonify({
        'success': True,
        'entry': _serialize_entry(entry, full=True)
    })


@api_bp.route('/autocomplete')
def autocomplete():
    """Autocomplete for entry names.

    Query parameters:
        q: Search query (min 2 characters)
        type: Directory type slug filter
        limit: Max results (default 10)
    """
    q = request.args.get('q', '').strip()
    type_slug = request.args.get('type', '').strip()
    limit = min(request.args.get('limit', 10, type=int), 50)

    if len(q) < 2:
        return jsonify({'success': True, 'results': []})

    query = DirectoryEntry.query.filter(
        DirectoryEntry.active == True,  # noqa: E712
        DirectoryEntry.name.ilike(f'%{q}%')
    )

    if type_slug:
        directory_type = DirectoryType.get_by_slug(type_slug)
        if directory_type:
            query = query.filter_by(directory_type_id=directory_type.id)

    entries = query.order_by(DirectoryEntry.name).limit(limit).all()

    return jsonify({
        'success': True,
        'results': [
            {
                'id': entry.id,
                'name': entry.name,
                'type': entry.directory_type.name if entry.directory_type else None,
                'location': entry.geo_ort.full_name if entry.geo_ort else None,
            }
            for entry in entries
        ]
    })


@api_bp.route('/plz/<plz>')
def lookup_plz(plz):
    """Lookup location by PLZ.

    Returns all Orte with this PLZ.
    """
    orte = GeoOrt.query.filter_by(plz=plz).all()

    if not orte:
        return jsonify({
            'success': False,
            'error': 'PLZ not found'
        }), 404

    return jsonify({
        'success': True,
        'plz': plz,
        'orte': [
            {
                'id': ort.id,
                'name': ort.name,
                'kreis': ort.kreis.name if ort.kreis else None,
                'bundesland': ort.kreis.bundesland.name if ort.kreis and ort.kreis.bundesland else None,
                'lat': ort.lat,
                'lng': ort.lng,
            }
            for ort in orte
        ]
    })


@api_bp.route('/types')
def list_types():
    """List all active directory types."""
    types = DirectoryType.query.filter_by(active=True).order_by(
        DirectoryType.name
    ).all()

    return jsonify({
        'success': True,
        'types': [
            {
                'id': t.id,
                'slug': t.slug,
                'name': t.name,
                'name_singular': t.name_singular,
                'name_plural': t.name_plural,
                'icon': t.icon,
                'entry_count': t.entries.filter_by(active=True).count(),
            }
            for t in types
        ]
    })


@api_bp.route('/stats')
def stats():
    """Get directory statistics."""
    types = DirectoryType.query.filter_by(active=True).all()

    return jsonify({
        'success': True,
        'stats': {
            'total_entries': DirectoryEntry.query.filter_by(active=True).count(),
            'total_types': len(types),
            'by_type': {
                t.slug: {
                    'name': t.name,
                    'count': t.entries.filter_by(active=True).count()
                }
                for t in types
            },
            'by_bundesland': _get_bundesland_stats(),
        }
    })


def _serialize_entry(entry: DirectoryEntry, full: bool = False) -> dict:
    """Serialize an entry to JSON."""
    result = {
        'id': entry.id,
        'name': entry.name,
        'slug': entry.slug,
        'type': {
            'slug': entry.directory_type.slug,
            'name': entry.directory_type.name,
        } if entry.directory_type else None,
        'kurzbeschreibung': entry.kurzbeschreibung,
        'location': None,
        'verified': entry.verified,
    }

    # Add location info
    if entry.geo_ort:
        ort = entry.geo_ort
        result['location'] = {
            'ort': ort.name,
            'plz': ort.plz,
            'kreis': ort.kreis.name if ort.kreis else None,
            'bundesland': ort.kreis.bundesland.name if ort.kreis and ort.kreis.bundesland else None,
            'lat': ort.lat,
            'lng': ort.lng,
        }

    if full:
        # Add full details
        result.update({
            'strasse': entry.strasse,
            'telefon': entry.telefon,
            'email': entry.email,
            'website': entry.website,
            'data': entry.data or {},
            'self_managed': entry.self_managed,
        })

    return result


def _get_bundesland_stats() -> dict:
    """Get entry count by Bundesland."""
    result = {}

    bundeslaender = GeoBundesland.query.all()
    for bl in bundeslaender:
        count = DirectoryEntry.query.join(GeoOrt).join(GeoKreis).filter(
            GeoKreis.bundesland_id == bl.id,
            DirectoryEntry.active == True  # noqa: E712
        ).count()
        if count > 0:
            result[bl.slug] = {
                'name': bl.name,
                'count': count
            }

    return result
