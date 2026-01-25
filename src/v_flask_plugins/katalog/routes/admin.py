"""Admin routes for the Katalog plugin.

Provides PDF and category management functionality.
"""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from v_flask.auth import permission_required
from v_flask.extensions import db
from v_flask_plugins.katalog.models import (
    KatalogKategorie,
    KatalogPDF,
    generate_unique_slug,
)
from v_flask_plugins.katalog.services import PDFService

katalog_admin_bp = Blueprint(
    'katalog_admin',
    __name__,
    template_folder='../templates'
)


def get_pdf_service() -> PDFService:
    """Get PDF service from app extensions."""
    return current_app.extensions.get('katalog_pdf_service')


# ============================================================================
# PDF Management
# ============================================================================

@katalog_admin_bp.route('/')
@katalog_admin_bp.route('/pdfs')
@login_required
@permission_required('admin.*')
def list_pdfs():
    """List all PDF catalogs."""
    pdfs = KatalogPDF.query.order_by(
        KatalogPDF.sort_order,
        KatalogPDF.created_at.desc()
    ).all()

    categories = KatalogKategorie.query.order_by(KatalogKategorie.sort_order).all()

    return render_template(
        'katalog/admin/list.html',
        pdfs=pdfs,
        categories=categories,
    )


@katalog_admin_bp.route('/pdfs/neu', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def new_pdf():
    """Upload a new PDF catalog."""
    categories = KatalogKategorie.query.filter_by(is_active=True).order_by(
        KatalogKategorie.sort_order
    ).all()

    if request.method == 'POST':
        service = get_pdf_service()

        # Validate required fields
        title = request.form.get('title', '').strip()
        if not title:
            flash('Bitte geben Sie einen Titel ein.', 'error')
            return render_template('katalog/admin/form.html', categories=categories, pdf=None)

        # Handle PDF upload
        pdf_file = request.files.get('pdf_file')
        if not pdf_file or not pdf_file.filename:
            flash('Bitte wählen Sie eine PDF-Datei aus.', 'error')
            return render_template('katalog/admin/form.html', categories=categories, pdf=None)

        try:
            file_path, file_size = service.save_pdf(pdf_file, pdf_file.filename)
        except ValueError as e:
            flash(str(e), 'error')
            return render_template('katalog/admin/form.html', categories=categories, pdf=None)

        # Handle optional cover image
        cover_path = None
        cover_file = request.files.get('cover_image')
        if cover_file and cover_file.filename:
            try:
                cover_path = service.save_cover_image(cover_file, cover_file.filename)
            except ValueError as e:
                flash(f'Cover-Bild Fehler: {e}', 'warning')

        # Create PDF record
        kategorie_id = request.form.get('kategorie_id') or None
        year = request.form.get('year')

        pdf = KatalogPDF(
            title=title,
            description=request.form.get('description', '').strip() or None,
            file_path=file_path,
            file_size=file_size,
            cover_image_path=cover_path,
            kategorie_id=kategorie_id if kategorie_id else None,
            year=int(year) if year and year.isdigit() else None,
            sort_order=int(request.form.get('sort_order', 0)),
            is_active=request.form.get('is_active') == 'on',
        )

        db.session.add(pdf)
        db.session.commit()

        flash(f'Katalog "{title}" wurde erfolgreich hochgeladen.', 'success')
        return redirect(url_for('katalog_admin.list_pdfs'))

    return render_template(
        'katalog/admin/form.html',
        categories=categories,
        pdf=None,
    )


@katalog_admin_bp.route('/pdfs/<pdf_id>', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def edit_pdf(pdf_id: str):
    """Edit an existing PDF catalog."""
    pdf = KatalogPDF.query.get_or_404(pdf_id)
    categories = KatalogKategorie.query.filter_by(is_active=True).order_by(
        KatalogKategorie.sort_order
    ).all()

    if request.method == 'POST':
        service = get_pdf_service()

        # Update basic fields
        pdf.title = request.form.get('title', '').strip() or pdf.title
        pdf.description = request.form.get('description', '').strip() or None

        kategorie_id = request.form.get('kategorie_id')
        pdf.kategorie_id = kategorie_id if kategorie_id else None

        year = request.form.get('year')
        pdf.year = int(year) if year and year.isdigit() else None

        pdf.sort_order = int(request.form.get('sort_order', 0))
        pdf.is_active = request.form.get('is_active') == 'on'

        # Handle new PDF upload (optional replacement)
        pdf_file = request.files.get('pdf_file')
        if pdf_file and pdf_file.filename:
            try:
                # Delete old file
                service.delete_file(pdf.file_path)
                # Save new file
                file_path, file_size = service.save_pdf(pdf_file, pdf_file.filename)
                pdf.file_path = file_path
                pdf.file_size = file_size
            except ValueError as e:
                flash(f'PDF-Fehler: {e}', 'error')
                return render_template('katalog/admin/form.html', categories=categories, pdf=pdf)

        # Handle cover image update
        cover_file = request.files.get('cover_image')
        if cover_file and cover_file.filename:
            try:
                # Delete old cover
                if pdf.cover_image_path:
                    service.delete_file(pdf.cover_image_path)
                # Save new cover
                pdf.cover_image_path = service.save_cover_image(cover_file, cover_file.filename)
            except ValueError as e:
                flash(f'Cover-Bild Fehler: {e}', 'warning')

        # Handle cover deletion
        if request.form.get('delete_cover') == 'on' and pdf.cover_image_path:
            service.delete_file(pdf.cover_image_path)
            pdf.cover_image_path = None

        db.session.commit()

        flash(f'Katalog "{pdf.title}" wurde aktualisiert.', 'success')
        return redirect(url_for('katalog_admin.list_pdfs'))

    return render_template(
        'katalog/admin/form.html',
        categories=categories,
        pdf=pdf,
    )


@katalog_admin_bp.route('/pdfs/<pdf_id>/delete', methods=['POST'])
@login_required
@permission_required('admin.*')
def delete_pdf(pdf_id: str):
    """Delete a PDF catalog."""
    pdf = KatalogPDF.query.get_or_404(pdf_id)
    service = get_pdf_service()

    title = pdf.title

    # Delete files
    service.delete_file(pdf.file_path)
    if pdf.cover_image_path:
        service.delete_file(pdf.cover_image_path)

    # Delete record
    db.session.delete(pdf)
    db.session.commit()

    flash(f'Katalog "{title}" wurde gelöscht.', 'success')
    return redirect(url_for('katalog_admin.list_pdfs'))


# ============================================================================
# Category Management
# ============================================================================

@katalog_admin_bp.route('/kategorien')
@login_required
@permission_required('admin.*')
def list_categories():
    """List all categories."""
    categories = KatalogKategorie.query.order_by(KatalogKategorie.sort_order).all()
    return render_template(
        'katalog/admin/categories.html',
        categories=categories,
    )


@katalog_admin_bp.route('/kategorien/neu', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def new_category():
    """Create a new category."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Bitte geben Sie einen Namen ein.', 'error')
            return render_template('katalog/admin/category_form.html', kategorie=None)

        kategorie = KatalogKategorie(
            name=name,
            slug=generate_unique_slug(name),
            description=request.form.get('description', '').strip() or None,
            icon=request.form.get('icon', 'ti ti-book').strip(),
            sort_order=int(request.form.get('sort_order', 0)),
            is_active=request.form.get('is_active') == 'on',
        )

        db.session.add(kategorie)
        db.session.commit()

        flash(f'Kategorie "{name}" wurde erstellt.', 'success')
        return redirect(url_for('katalog_admin.list_categories'))

    return render_template(
        'katalog/admin/category_form.html',
        kategorie=None,
    )


@katalog_admin_bp.route('/kategorien/<kategorie_id>', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def edit_category(kategorie_id: str):
    """Edit an existing category."""
    kategorie = KatalogKategorie.query.get_or_404(kategorie_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Bitte geben Sie einen Namen ein.', 'error')
            return render_template('katalog/admin/category_form.html', kategorie=kategorie)

        # Update slug only if name changed
        if name != kategorie.name:
            kategorie.slug = generate_unique_slug(name)

        kategorie.name = name
        kategorie.description = request.form.get('description', '').strip() or None
        kategorie.icon = request.form.get('icon', 'ti ti-book').strip()
        kategorie.sort_order = int(request.form.get('sort_order', 0))
        kategorie.is_active = request.form.get('is_active') == 'on'

        db.session.commit()

        flash(f'Kategorie "{name}" wurde aktualisiert.', 'success')
        return redirect(url_for('katalog_admin.list_categories'))

    return render_template(
        'katalog/admin/category_form.html',
        kategorie=kategorie,
    )


@katalog_admin_bp.route('/kategorien/<kategorie_id>/delete', methods=['POST'])
@login_required
@permission_required('admin.*')
def delete_category(kategorie_id: str):
    """Delete a category (PDFs become uncategorized)."""
    kategorie = KatalogKategorie.query.get_or_404(kategorie_id)
    name = kategorie.name

    # PDFs in this category will have kategorie_id set to NULL (ondelete='SET NULL')
    db.session.delete(kategorie)
    db.session.commit()

    flash(f'Kategorie "{name}" wurde gelöscht. PDFs sind nun ohne Kategorie.', 'success')
    return redirect(url_for('katalog_admin.list_categories'))
