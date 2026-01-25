"""Self-Registration Routes.

Multi-step wizard for business owners to register their entries.
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session
)
from flask_login import current_user, login_user
from werkzeug.security import generate_password_hash
import uuid

from v_flask.extensions import db
from v_flask.models import User

from ..models import DirectoryType, DirectoryEntry, RegistrationDraft, GeoOrt

register_bp = Blueprint(
    'business_directory_register',
    __name__,
    template_folder='../templates'
)


def get_or_create_draft(directory_type_id: int) -> RegistrationDraft:
    """Get existing draft or create a new one."""
    # Check for existing draft
    if current_user.is_authenticated:
        draft = RegistrationDraft.get_by_user(
            current_user.id, directory_type_id
        )
    else:
        session_id = session.get('draft_session_id')
        if session_id:
            draft = RegistrationDraft.get_by_session(
                session_id, directory_type_id
            )
        else:
            draft = None

    # Create new draft if needed
    if not draft:
        session_id = str(uuid.uuid4())
        session['draft_session_id'] = session_id

        draft = RegistrationDraft(
            directory_type_id=directory_type_id,
            session_id=session_id,
            current_step=1
        )
        db.session.add(draft)
        db.session.commit()

    # Refresh expiry
    draft.refresh_expiry()
    db.session.commit()

    return draft


@register_bp.route('/')
def select_type():
    """Select directory type to register for."""
    types = DirectoryType.query.filter_by(active=True).order_by(
        DirectoryType.name
    ).all()

    if not types:
        flash('Aktuell sind keine Registrierungen möglich.', 'info')
        return redirect(url_for('business_directory_public.index'))

    return render_template(
        'business_directory/register/select_type.html',
        types=types
    )


@register_bp.route('/<type_slug>/')
def start(type_slug):
    """Start registration for a directory type."""
    directory_type = DirectoryType.get_by_slug(type_slug)
    if not directory_type or not directory_type.active:
        flash('Dieser Verzeichnistyp existiert nicht.', 'error')
        return redirect(url_for('.select_type'))

    draft = get_or_create_draft(directory_type.id)

    return redirect(url_for(
        '.step',
        type_slug=type_slug,
        step=draft.current_step
    ))


@register_bp.route('/<type_slug>/step/<int:step>', methods=['GET', 'POST'])
def step(type_slug, step):
    """Handle a registration step."""
    directory_type = DirectoryType.get_by_slug(type_slug)
    if not directory_type or not directory_type.active:
        flash('Dieser Verzeichnistyp existiert nicht.', 'error')
        return redirect(url_for('.select_type'))

    draft = get_or_create_draft(directory_type.id)

    # Validate step number
    total_steps = draft.get_total_steps()
    if step < 1 or step > total_steps:
        return redirect(url_for('.step', type_slug=type_slug, step=1))

    # Don't allow skipping ahead
    if step > draft.current_step + 1:
        return redirect(url_for(
            '.step',
            type_slug=type_slug,
            step=draft.current_step
        ))

    if request.method == 'POST':
        # Handle step submission based on step number
        if step == 1:
            # Account step
            success = _handle_account_step(draft, request.form)
        else:
            # Entry data steps - use dynamic field handling
            success = _handle_entry_step(draft, step, request.form, directory_type)

        if success:
            draft.current_step = max(draft.current_step, step)

            if step == total_steps:
                # Final step - create entry
                return _finalize_registration(draft, directory_type, type_slug)

            db.session.commit()
            return redirect(url_for(
                '.step',
                type_slug=type_slug,
                step=step + 1
            ))

    # Get step configuration from DirectoryType
    step_config = _get_step_config(directory_type, step)

    return render_template(
        f'business_directory/register/step_{step}.html',
        directory_type=directory_type,
        draft=draft,
        step=step,
        total_steps=total_steps,
        step_config=step_config
    )


def _handle_account_step(draft: RegistrationDraft, form) -> bool:
    """Handle account creation step."""
    email = form.get('email', '').strip().lower()
    password = form.get('password', '')
    password_confirm = form.get('password_confirm', '')
    vorname = form.get('vorname', '').strip()
    nachname = form.get('nachname', '').strip()
    telefon = form.get('telefon', '').strip()
    agb = 'agb_akzeptiert' in form

    # Validation
    if not email:
        flash('E-Mail ist erforderlich.', 'error')
        return False

    if not password or len(password) < 8:
        flash('Passwort muss mindestens 8 Zeichen haben.', 'error')
        return False

    if password != password_confirm:
        flash('Passwörter stimmen nicht überein.', 'error')
        return False

    if not agb:
        flash('Sie müssen die AGB akzeptieren.', 'error')
        return False

    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user and not current_user.is_authenticated:
        flash(
            'Diese E-Mail ist bereits registriert. '
            'Bitte melden Sie sich an.',
            'warning'
        )
        return False

    # Save to draft
    draft.email = email
    draft.password_hash = generate_password_hash(password)
    draft.vorname = vorname
    draft.nachname = nachname
    draft.telefon_betreiber = telefon
    draft.agb_akzeptiert = True

    return True


def _handle_entry_step(
    draft: RegistrationDraft,
    step: int,
    form,
    directory_type: DirectoryType
) -> bool:
    """Handle entry data step."""
    # Get step configuration
    step_config = _get_step_config(directory_type, step)
    fields = step_config.get('fields', [])

    entry_data = draft.entry_data or {}

    # Process each field in this step
    for field_name in fields:
        value = form.get(field_name, '').strip()
        if value:
            entry_data[field_name] = value
        elif field_name in entry_data:
            del entry_data[field_name]

    draft.entry_data = entry_data
    return True


def _get_step_config(directory_type: DirectoryType, step: int) -> dict:
    """Get configuration for a specific step."""
    if not directory_type.registration_steps:
        # Default step configuration
        default_steps = {
            1: {'name': 'Account', 'fields': []},
            2: {'name': 'Grunddaten', 'fields': ['name', 'kurzbeschreibung']},
            3: {'name': 'Adresse', 'fields': ['strasse', 'plz', 'ort']},
            4: {'name': 'Kontakt', 'fields': ['telefon', 'email', 'website']},
            5: {'name': 'Details', 'fields': []},
            6: {'name': 'Zusammenfassung', 'fields': []},
        }
        return default_steps.get(step, {})

    steps = directory_type.registration_steps
    if isinstance(steps, list) and len(steps) >= step:
        return steps[step - 1]
    elif isinstance(steps, dict) and str(step) in steps:
        return steps[str(step)]

    return {}


def _finalize_registration(
    draft: RegistrationDraft,
    directory_type: DirectoryType,
    type_slug: str
):
    """Create user and entry from draft."""
    # Create or get user
    if current_user.is_authenticated:
        user = current_user
    else:
        user = User(
            email=draft.email,
            password_hash=draft.password_hash,
            vorname=draft.vorname,
            nachname=draft.nachname,
        )
        db.session.add(user)
        db.session.flush()  # Get user ID

    # Create entry
    entry_data = draft.entry_data or {}

    entry = DirectoryEntry(
        directory_type_id=directory_type.id,
        name=entry_data.get('name', 'Unbenannt'),
        strasse=entry_data.get('strasse'),
        telefon=entry_data.get('telefon'),
        email=entry_data.get('email'),
        website=entry_data.get('website'),
        kurzbeschreibung=entry_data.get('kurzbeschreibung'),
        owner_id=user.id,
        self_managed=True,
        active=False,  # Requires admin approval
        verified=False,
    )
    entry.generate_slug()

    # Set PLZ-based GeoOrt if possible
    plz = entry_data.get('plz')
    if plz:
        geo_ort = GeoOrt.query.filter_by(plz=plz).first()
        if geo_ort:
            entry.geo_ort_id = geo_ort.id

    # Store type-specific data
    data = {}
    if directory_type.field_schema:
        for field_name in directory_type.field_schema.keys():
            if field_name in entry_data:
                data[field_name] = entry_data[field_name]
    entry.data = data

    db.session.add(entry)

    # Delete draft
    db.session.delete(draft)

    db.session.commit()

    # Log in new user
    if not current_user.is_authenticated:
        login_user(user)

    flash(
        f'Ihr Eintrag "{entry.name}" wurde erfolgreich erstellt und wird '
        'nach Prüfung freigeschaltet.',
        'success'
    )

    return redirect(url_for(
        'business_directory_provider.dashboard'
    ))


@register_bp.route('/<type_slug>/cancel', methods=['POST'])
def cancel(type_slug):
    """Cancel registration and delete draft."""
    directory_type = DirectoryType.get_by_slug(type_slug)
    if not directory_type:
        return redirect(url_for('.select_type'))

    # Find and delete draft
    if current_user.is_authenticated:
        draft = RegistrationDraft.get_by_user(
            current_user.id, directory_type.id
        )
    else:
        session_id = session.get('draft_session_id')
        if session_id:
            draft = RegistrationDraft.get_by_session(
                session_id, directory_type.id
            )
        else:
            draft = None

    if draft:
        db.session.delete(draft)
        db.session.commit()

    flash('Registrierung wurde abgebrochen.', 'info')
    return redirect(url_for('business_directory_public.index'))
