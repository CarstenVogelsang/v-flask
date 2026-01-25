"""Admin Routes for DirectoryType Management.

CRUD operations for directory types (e.g., "Händler", "Hersteller").
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from v_flask.extensions import db
from v_flask.auth import admin_required

from ..models import DirectoryType

admin_types_bp = Blueprint(
    'business_directory_admin_types',
    __name__,
    template_folder='../templates'
)


@admin_types_bp.route('/')
@admin_required
def list_types():
    """List all directory types."""
    types = DirectoryType.query.order_by(DirectoryType.name).all()
    return render_template(
        'business_directory/admin/types/list.html',
        types=types
    )


@admin_types_bp.route('/new', methods=['GET', 'POST'])
@admin_required
def create_type():
    """Create a new directory type."""
    if request.method == 'POST':
        directory_type = DirectoryType(
            slug=request.form.get('slug', '').strip(),
            name=request.form.get('name', '').strip(),
            name_singular=request.form.get('name_singular', '').strip(),
            name_plural=request.form.get('name_plural', '').strip(),
            icon=request.form.get('icon', 'ti-building-store').strip(),
            description=request.form.get('description', '').strip(),
        )

        # Validate required fields
        if not directory_type.slug or not directory_type.name:
            flash('Slug und Name sind erforderlich.', 'error')
            return render_template(
                'business_directory/admin/types/form.html',
                directory_type=directory_type,
                is_new=True
            )

        # Check for duplicate slug
        if DirectoryType.get_by_slug(directory_type.slug):
            flash('Ein Verzeichnistyp mit diesem Slug existiert bereits.', 'error')
            return render_template(
                'business_directory/admin/types/form.html',
                directory_type=directory_type,
                is_new=True
            )

        db.session.add(directory_type)
        db.session.commit()
        flash(f'Verzeichnistyp "{directory_type.name}" wurde erstellt.', 'success')
        return redirect(url_for('.edit_type', type_id=directory_type.id))

    return render_template(
        'business_directory/admin/types/form.html',
        directory_type=DirectoryType(),
        is_new=True
    )


@admin_types_bp.route('/<int:type_id>')
@admin_required
def edit_type(type_id):
    """Edit a directory type."""
    directory_type = db.session.get(DirectoryType, type_id)
    if not directory_type:
        flash('Verzeichnistyp nicht gefunden.', 'error')
        return redirect(url_for('.list_types'))

    return render_template(
        'business_directory/admin/types/form.html',
        directory_type=directory_type,
        is_new=False
    )


@admin_types_bp.route('/<int:type_id>/update', methods=['POST'])
@admin_required
def update_type(type_id):
    """Update a directory type."""
    directory_type = db.session.get(DirectoryType, type_id)
    if not directory_type:
        flash('Verzeichnistyp nicht gefunden.', 'error')
        return redirect(url_for('.list_types'))

    # Update basic fields
    directory_type.name = request.form.get('name', '').strip()
    directory_type.name_singular = request.form.get('name_singular', '').strip()
    directory_type.name_plural = request.form.get('name_plural', '').strip()
    directory_type.icon = request.form.get('icon', 'ti-building-store').strip()
    directory_type.description = request.form.get('description', '').strip()
    directory_type.active = 'active' in request.form

    # Slug can't be changed after creation (used in URLs)

    if not directory_type.name:
        flash('Name ist erforderlich.', 'error')
        return render_template(
            'business_directory/admin/types/form.html',
            directory_type=directory_type,
            is_new=False
        )

    db.session.commit()
    flash(f'Verzeichnistyp "{directory_type.name}" wurde aktualisiert.', 'success')
    return redirect(url_for('.edit_type', type_id=type_id))


@admin_types_bp.route('/<int:type_id>/schema', methods=['GET', 'POST'])
@admin_required
def edit_schema(type_id):
    """Edit the field schema for a directory type."""
    directory_type = db.session.get(DirectoryType, type_id)
    if not directory_type:
        flash('Verzeichnistyp nicht gefunden.', 'error')
        return redirect(url_for('.list_types'))

    if request.method == 'POST':
        import json
        try:
            schema_json = request.form.get('field_schema', '{}')
            directory_type.field_schema = json.loads(schema_json)
            db.session.commit()
            flash('Feld-Schema wurde aktualisiert.', 'success')
        except json.JSONDecodeError:
            flash('Ungültiges JSON-Format.', 'error')

        return redirect(url_for('.edit_schema', type_id=type_id))

    return render_template(
        'business_directory/admin/types/schema.html',
        directory_type=directory_type
    )


@admin_types_bp.route('/<int:type_id>/registration', methods=['GET', 'POST'])
@admin_required
def edit_registration(type_id):
    """Edit the registration steps for a directory type."""
    directory_type = db.session.get(DirectoryType, type_id)
    if not directory_type:
        flash('Verzeichnistyp nicht gefunden.', 'error')
        return redirect(url_for('.list_types'))

    if request.method == 'POST':
        import json
        try:
            steps_json = request.form.get('registration_steps', '{}')
            directory_type.registration_steps = json.loads(steps_json)
            db.session.commit()
            flash('Registrierungs-Schritte wurden aktualisiert.', 'success')
        except json.JSONDecodeError:
            flash('Ungültiges JSON-Format.', 'error')

        return redirect(url_for('.edit_registration', type_id=type_id))

    return render_template(
        'business_directory/admin/types/registration.html',
        directory_type=directory_type
    )


@admin_types_bp.route('/<int:type_id>/display', methods=['GET', 'POST'])
@admin_required
def edit_display(type_id):
    """Edit the display configuration for a directory type."""
    directory_type = db.session.get(DirectoryType, type_id)
    if not directory_type:
        flash('Verzeichnistyp nicht gefunden.', 'error')
        return redirect(url_for('.list_types'))

    if request.method == 'POST':
        import json
        try:
            display_json = request.form.get('display_config', '{}')
            directory_type.display_config = json.loads(display_json)
            db.session.commit()
            flash('Anzeige-Konfiguration wurde aktualisiert.', 'success')
        except json.JSONDecodeError:
            flash('Ungültiges JSON-Format.', 'error')

        return redirect(url_for('.edit_display', type_id=type_id))

    return render_template(
        'business_directory/admin/types/display.html',
        directory_type=directory_type
    )


@admin_types_bp.route('/<int:type_id>/delete', methods=['POST'])
@admin_required
def delete_type(type_id):
    """Delete a directory type."""
    directory_type = db.session.get(DirectoryType, type_id)
    if not directory_type:
        flash('Verzeichnistyp nicht gefunden.', 'error')
        return redirect(url_for('.list_types'))

    # Check for existing entries
    if directory_type.entries.count() > 0:
        flash(
            f'Verzeichnistyp "{directory_type.name}" kann nicht gelöscht werden, '
            f'da noch {directory_type.entries.count()} Einträge existieren.',
            'error'
        )
        return redirect(url_for('.edit_type', type_id=type_id))

    name = directory_type.name
    db.session.delete(directory_type)
    db.session.commit()
    flash(f'Verzeichnistyp "{name}" wurde gelöscht.', 'success')
    return redirect(url_for('.list_types'))
