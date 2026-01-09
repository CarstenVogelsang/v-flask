"""Routes for the Kontakt plugin.

Provides:
    - Public contact form at /kontakt
    - Admin interface for viewing submissions at /admin/kontakt
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for

from v_flask.extensions import db
from v_flask.auth import admin_required

from .models import KontaktAnfrage

# Public blueprint for contact form
kontakt_bp = Blueprint(
    'kontakt',
    __name__,
    template_folder='templates'
)

# Admin blueprint for managing contact submissions
kontakt_admin_bp = Blueprint(
    'kontakt_admin',
    __name__,
    template_folder='templates'
)


# --- Public Routes ---

@kontakt_bp.route('/', methods=['GET', 'POST'])
def form():
    """Display and process the contact form."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        nachricht = request.form.get('nachricht', '').strip()

        # Basic validation
        errors = []
        if not name:
            errors.append('Bitte gib deinen Namen ein.')
        if not email:
            errors.append('Bitte gib deine E-Mail-Adresse ein.')
        elif '@' not in email:
            errors.append('Bitte gib eine gültige E-Mail-Adresse ein.')
        if not nachricht:
            errors.append('Bitte gib eine Nachricht ein.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'kontakt/form.html',
                name=name,
                email=email,
                nachricht=nachricht
            )

        # Save to database
        anfrage = KontaktAnfrage(
            name=name,
            email=email,
            nachricht=nachricht
        )
        db.session.add(anfrage)
        db.session.commit()

        flash('Vielen Dank für deine Nachricht! Wir melden uns bald.', 'success')
        return redirect(url_for('kontakt.form'))

    return render_template('kontakt/form.html')


# --- Admin Routes ---

@kontakt_admin_bp.route('/')
@admin_required
def list_anfragen():
    """List all contact submissions."""
    anfragen = db.session.query(KontaktAnfrage).order_by(
        KontaktAnfrage.created_at.desc()
    ).all()

    unread_count = sum(1 for a in anfragen if not a.gelesen)

    return render_template(
        'kontakt/admin/list.html',
        anfragen=anfragen,
        unread_count=unread_count
    )


@kontakt_admin_bp.route('/<int:anfrage_id>')
@admin_required
def detail(anfrage_id: int):
    """View a single contact submission."""
    anfrage = db.session.get(KontaktAnfrage, anfrage_id)
    if not anfrage:
        flash('Anfrage nicht gefunden.', 'error')
        return redirect(url_for('kontakt_admin.list_anfragen'))

    # Mark as read
    if not anfrage.gelesen:
        anfrage.mark_as_read()
        db.session.commit()

    return render_template('kontakt/admin/detail.html', anfrage=anfrage)


@kontakt_admin_bp.route('/<int:anfrage_id>/toggle-read', methods=['POST'])
@admin_required
def toggle_read(anfrage_id: int):
    """Toggle the read status of a submission."""
    anfrage = db.session.get(KontaktAnfrage, anfrage_id)
    if anfrage:
        anfrage.gelesen = not anfrage.gelesen
        db.session.commit()
        status = 'gelesen' if anfrage.gelesen else 'ungelesen'
        flash(f'Anfrage als {status} markiert.', 'info')

    return redirect(url_for('kontakt_admin.list_anfragen'))


@kontakt_admin_bp.route('/<int:anfrage_id>/delete', methods=['POST'])
@admin_required
def delete(anfrage_id: int):
    """Delete a contact submission."""
    anfrage = db.session.get(KontaktAnfrage, anfrage_id)
    if anfrage:
        db.session.delete(anfrage)
        db.session.commit()
        flash('Anfrage gelöscht.', 'success')

    return redirect(url_for('kontakt_admin.list_anfragen'))
