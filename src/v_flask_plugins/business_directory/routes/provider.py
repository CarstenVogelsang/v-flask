"""Provider Self-Service Routes.

Dashboard for business owners to manage their entries.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from v_flask.extensions import db

from ..models import DirectoryEntry, ClaimRequest

provider_bp = Blueprint(
    'business_directory_provider',
    __name__,
    template_folder='../templates'
)


@provider_bp.route('/')
@login_required
def dashboard():
    """Provider dashboard - overview of own entries."""
    # Get user's entries
    entries = DirectoryEntry.query.filter_by(
        owner_id=current_user.id
    ).order_by(DirectoryEntry.name).all()

    # Get pending claims by this user
    pending_claims = ClaimRequest.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).all()

    return render_template(
        'business_directory/provider/dashboard.html',
        entries=entries,
        pending_claims=pending_claims
    )


@provider_bp.route('/entry/<int:entry_id>')
@login_required
def view_entry(entry_id):
    """View own entry details."""
    entry = db.session.get(DirectoryEntry, entry_id)

    if not entry or entry.owner_id != current_user.id:
        flash('Eintrag nicht gefunden oder keine Berechtigung.', 'error')
        return redirect(url_for('.dashboard'))

    return render_template(
        'business_directory/provider/entry_view.html',
        entry=entry
    )


@provider_bp.route('/entry/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    """Edit own entry."""
    entry = db.session.get(DirectoryEntry, entry_id)

    if not entry or entry.owner_id != current_user.id:
        flash('Eintrag nicht gefunden oder keine Berechtigung.', 'error')
        return redirect(url_for('.dashboard'))

    if request.method == 'POST':
        # Update basic fields
        entry.kurzbeschreibung = request.form.get('kurzbeschreibung', '').strip()
        entry.telefon = request.form.get('telefon', '').strip()
        entry.email = request.form.get('email', '').strip()
        entry.website = request.form.get('website', '').strip()

        # Update type-specific data
        directory_type = entry.directory_type
        if directory_type and directory_type.field_schema:
            data = entry.data or {}
            for field_name in directory_type.field_schema.keys():
                value = request.form.get(f'data_{field_name}', '').strip()
                if value:
                    data[field_name] = value
                elif field_name in data:
                    del data[field_name]
            entry.data = data

        db.session.commit()
        flash('Änderungen wurden gespeichert.', 'success')
        return redirect(url_for('.view_entry', entry_id=entry_id))

    return render_template(
        'business_directory/provider/entry_edit.html',
        entry=entry
    )


@provider_bp.route('/claim')
@login_required
def claim_list():
    """List available entries to claim."""
    # Show entries without owner that could be claimed
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()

    query = DirectoryEntry.query.filter(
        DirectoryEntry.owner_id.is_(None),
        DirectoryEntry.active == True  # noqa: E712
    )

    if search:
        query = query.filter(
            db.or_(
                DirectoryEntry.name.ilike(f'%{search}%'),
                DirectoryEntry.strasse.ilike(f'%{search}%'),
            )
        )

    entries = query.order_by(DirectoryEntry.name).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template(
        'business_directory/provider/claim_list.html',
        entries=entries,
        search=search
    )


@provider_bp.route('/claim/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def claim_entry(entry_id):
    """Submit a claim for an entry."""
    entry = db.session.get(DirectoryEntry, entry_id)

    if not entry:
        flash('Eintrag nicht gefunden.', 'error')
        return redirect(url_for('.claim_list'))

    if entry.owner_id:
        flash('Dieser Eintrag hat bereits einen Eigentümer.', 'error')
        return redirect(url_for('.claim_list'))

    # Check for existing pending claim
    if ClaimRequest.has_pending_claim(entry_id, current_user.id):
        flash('Sie haben bereits einen offenen Claim für diesen Eintrag.', 'warning')
        return redirect(url_for('.dashboard'))

    if request.method == 'POST':
        claim = ClaimRequest(
            entry_id=entry_id,
            user_id=current_user.id,
            nachweis_typ=request.form.get('nachweis_typ', '').strip(),
            nachweis_url=request.form.get('nachweis_url', '').strip(),
            nachweis_text=request.form.get('nachweis_text', '').strip(),
        )

        db.session.add(claim)
        db.session.commit()

        flash(
            f'Ihr Claim für "{entry.name}" wurde eingereicht und wird geprüft.',
            'success'
        )
        return redirect(url_for('.dashboard'))

    return render_template(
        'business_directory/provider/claim_form.html',
        entry=entry
    )


@provider_bp.route('/claim/<int:claim_id>/cancel', methods=['POST'])
@login_required
def cancel_claim(claim_id):
    """Cancel a pending claim."""
    claim = db.session.get(ClaimRequest, claim_id)

    if not claim or claim.user_id != current_user.id:
        flash('Claim nicht gefunden oder keine Berechtigung.', 'error')
        return redirect(url_for('.dashboard'))

    if not claim.is_pending:
        flash('Dieser Claim kann nicht mehr abgebrochen werden.', 'error')
        return redirect(url_for('.dashboard'))

    entry_name = claim.entry.name
    db.session.delete(claim)
    db.session.commit()

    flash(f'Claim für "{entry_name}" wurde abgebrochen.', 'info')
    return redirect(url_for('.dashboard'))
