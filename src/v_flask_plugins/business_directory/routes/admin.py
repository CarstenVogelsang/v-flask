"""Admin Routes for DirectoryEntry Management.

CRUD operations for directory entries and review queue.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from v_flask.extensions import db
from v_flask.auth import admin_required, permission_required

from ..models import DirectoryType, DirectoryEntry, ClaimRequest

admin_bp = Blueprint(
    'business_directory_admin',
    __name__,
    template_folder='../templates'
)


@admin_bp.route('/')
@permission_required('business_directory.read')
def dashboard():
    """Admin dashboard with overview statistics."""
    types = DirectoryType.query.filter_by(active=True).all()

    stats = {
        'total_entries': DirectoryEntry.query.count(),
        'active_entries': DirectoryEntry.query.filter_by(active=True).count(),
        'pending_entries': DirectoryEntry.query.filter_by(active=False).count(),
        'pending_claims': ClaimRequest.get_pending_count(),
        'types': types,
    }

    return render_template(
        'business_directory/admin/dashboard.html',
        stats=stats
    )


@admin_bp.route('/entries')
@permission_required('business_directory.read')
def list_entries():
    """List all directory entries with filters."""
    # Query parameters
    type_id = request.args.get('type', type=int)
    status = request.args.get('status', 'all')
    search = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    # Base query
    query = DirectoryEntry.query

    # Filter by type
    if type_id:
        query = query.filter_by(directory_type_id=type_id)

    # Filter by status
    if status == 'active':
        query = query.filter_by(active=True)
    elif status == 'inactive':
        query = query.filter_by(active=False)
    elif status == 'verified':
        query = query.filter_by(verified=True)
    elif status == 'self_managed':
        query = query.filter_by(self_managed=True)

    # Search
    if search:
        query = query.filter(
            db.or_(
                DirectoryEntry.name.ilike(f'%{search}%'),
                DirectoryEntry.email.ilike(f'%{search}%'),
                DirectoryEntry.strasse.ilike(f'%{search}%'),
            )
        )

    # Pagination
    entries = query.order_by(DirectoryEntry.name).paginate(
        page=page, per_page=25, error_out=False
    )

    types = DirectoryType.query.filter_by(active=True).all()

    return render_template(
        'business_directory/admin/entries/list.html',
        entries=entries,
        types=types,
        current_type=type_id,
        current_status=status,
        search=search
    )


@admin_bp.route('/entries/new', methods=['GET', 'POST'])
@permission_required('business_directory.create')
def create_entry():
    """Create a new directory entry."""
    types = DirectoryType.query.filter_by(active=True).all()

    if not types:
        flash('Bitte erstellen Sie zuerst einen Verzeichnistyp.', 'warning')
        return redirect(url_for('business_directory_admin_types.create_type'))

    if request.method == 'POST':
        type_id = request.form.get('directory_type_id', type=int)
        directory_type = db.session.get(DirectoryType, type_id)

        if not directory_type:
            flash('Ungültiger Verzeichnistyp.', 'error')
            return redirect(url_for('.create_entry'))

        entry = DirectoryEntry(
            directory_type_id=type_id,
            name=request.form.get('name', '').strip(),
            strasse=request.form.get('strasse', '').strip(),
            telefon=request.form.get('telefon', '').strip(),
            email=request.form.get('email', '').strip(),
            website=request.form.get('website', '').strip(),
            kurzbeschreibung=request.form.get('kurzbeschreibung', '').strip(),
            active='active' in request.form,
            verified='verified' in request.form,
        )

        # Generate slug
        entry.generate_slug()

        # Parse dynamic fields from field_schema
        if directory_type.field_schema:
            data = {}
            for field_name, field_def in directory_type.field_schema.items():
                value = request.form.get(f'data_{field_name}')
                if value:
                    data[field_name] = value
            entry.data = data

        db.session.add(entry)
        db.session.commit()

        flash(f'Eintrag "{entry.name}" wurde erstellt.', 'success')
        return redirect(url_for('.edit_entry', entry_id=entry.id))

    return render_template(
        'business_directory/admin/entries/form.html',
        entry=DirectoryEntry(),
        types=types,
        is_new=True
    )


@admin_bp.route('/entries/<int:entry_id>')
@permission_required('business_directory.read')
def edit_entry(entry_id):
    """Edit a directory entry."""
    entry = db.session.get(DirectoryEntry, entry_id)
    if not entry:
        flash('Eintrag nicht gefunden.', 'error')
        return redirect(url_for('.list_entries'))

    types = DirectoryType.query.filter_by(active=True).all()

    return render_template(
        'business_directory/admin/entries/form.html',
        entry=entry,
        types=types,
        is_new=False
    )


@admin_bp.route('/entries/<int:entry_id>/update', methods=['POST'])
@permission_required('business_directory.update')
def update_entry(entry_id):
    """Update a directory entry."""
    entry = db.session.get(DirectoryEntry, entry_id)
    if not entry:
        flash('Eintrag nicht gefunden.', 'error')
        return redirect(url_for('.list_entries'))

    # Update basic fields
    entry.name = request.form.get('name', '').strip()
    entry.strasse = request.form.get('strasse', '').strip()
    entry.telefon = request.form.get('telefon', '').strip()
    entry.email = request.form.get('email', '').strip()
    entry.website = request.form.get('website', '').strip()
    entry.kurzbeschreibung = request.form.get('kurzbeschreibung', '').strip()
    entry.active = 'active' in request.form
    entry.verified = 'verified' in request.form

    # Regenerate slug if name changed
    entry.generate_slug()

    # Parse dynamic fields from field_schema
    directory_type = entry.directory_type
    if directory_type and directory_type.field_schema:
        data = entry.data or {}
        for field_name, field_def in directory_type.field_schema.items():
            value = request.form.get(f'data_{field_name}')
            if value:
                data[field_name] = value
            elif field_name in data:
                del data[field_name]
        entry.data = data

    db.session.commit()
    flash(f'Eintrag "{entry.name}" wurde aktualisiert.', 'success')
    return redirect(url_for('.edit_entry', entry_id=entry_id))


@admin_bp.route('/entries/<int:entry_id>/delete', methods=['POST'])
@permission_required('business_directory.delete')
def delete_entry(entry_id):
    """Delete a directory entry."""
    entry = db.session.get(DirectoryEntry, entry_id)
    if not entry:
        flash('Eintrag nicht gefunden.', 'error')
        return redirect(url_for('.list_entries'))

    name = entry.name
    db.session.delete(entry)
    db.session.commit()
    flash(f'Eintrag "{name}" wurde gelöscht.', 'success')
    return redirect(url_for('.list_entries'))


@admin_bp.route('/entries/<int:entry_id>/activate', methods=['POST'])
@permission_required('business_directory.update')
def activate_entry(entry_id):
    """Activate a directory entry."""
    entry = db.session.get(DirectoryEntry, entry_id)
    if not entry:
        flash('Eintrag nicht gefunden.', 'error')
        return redirect(url_for('.list_entries'))

    entry.active = True
    db.session.commit()
    flash(f'Eintrag "{entry.name}" wurde aktiviert.', 'success')

    # Return to referring page or list
    return redirect(request.referrer or url_for('.list_entries'))


@admin_bp.route('/entries/<int:entry_id>/deactivate', methods=['POST'])
@permission_required('business_directory.update')
def deactivate_entry(entry_id):
    """Deactivate a directory entry."""
    entry = db.session.get(DirectoryEntry, entry_id)
    if not entry:
        flash('Eintrag nicht gefunden.', 'error')
        return redirect(url_for('.list_entries'))

    entry.active = False
    db.session.commit()
    flash(f'Eintrag "{entry.name}" wurde deaktiviert.', 'success')

    return redirect(request.referrer or url_for('.list_entries'))


# --- Review Queue ---

@admin_bp.route('/review')
@permission_required('business_directory.update')
def review_queue():
    """Review queue for pending entries and claims."""
    pending_entries = DirectoryEntry.query.filter_by(active=False).order_by(
        DirectoryEntry.created_at.asc()
    ).limit(50).all()

    pending_claims = ClaimRequest.get_pending()

    return render_template(
        'business_directory/admin/review/queue.html',
        pending_entries=pending_entries,
        pending_claims=pending_claims
    )


@admin_bp.route('/claims/<int:claim_id>')
@permission_required('business_directory.update')
def view_claim(claim_id):
    """View a claim request."""
    claim = db.session.get(ClaimRequest, claim_id)
    if not claim:
        flash('Claim nicht gefunden.', 'error')
        return redirect(url_for('.review_queue'))

    return render_template(
        'business_directory/admin/review/claim_detail.html',
        claim=claim
    )


@admin_bp.route('/claims/<int:claim_id>/approve', methods=['POST'])
@permission_required('business_directory.update')
def approve_claim(claim_id):
    """Approve a claim request."""
    from flask_login import current_user

    claim = db.session.get(ClaimRequest, claim_id)
    if not claim:
        flash('Claim nicht gefunden.', 'error')
        return redirect(url_for('.review_queue'))

    claim.approve(current_user)
    flash(
        f'Claim für "{claim.entry.name}" wurde genehmigt. '
        f'Eigentümer ist jetzt {claim.user.email}.',
        'success'
    )
    return redirect(url_for('.review_queue'))


@admin_bp.route('/claims/<int:claim_id>/reject', methods=['POST'])
@permission_required('business_directory.update')
def reject_claim(claim_id):
    """Reject a claim request."""
    from flask_login import current_user

    claim = db.session.get(ClaimRequest, claim_id)
    if not claim:
        flash('Claim nicht gefunden.', 'error')
        return redirect(url_for('.review_queue'))

    reason = request.form.get('reason', '').strip()
    claim.reject(current_user, reason)
    flash(f'Claim für "{claim.entry.name}" wurde abgelehnt.', 'info')
    return redirect(url_for('.review_queue'))
