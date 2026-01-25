"""Public routes for the Katalog plugin.

Provides catalog browsing, PDF viewing, and download functionality.
"""

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    send_file,
)
from flask_login import current_user

from v_flask_plugins.katalog.models import KatalogKategorie, KatalogPDF
from v_flask_plugins.katalog.services import PDFService

katalog_bp = Blueprint(
    'katalog',
    __name__,
    template_folder='../templates'
)


def get_pdf_service() -> PDFService:
    """Get PDF service from app extensions."""
    return current_app.extensions.get('katalog_pdf_service')


@katalog_bp.route('/')
def index():
    """Display catalog overview with categories and PDFs."""
    categories = KatalogKategorie.get_active()

    # Get uncategorized PDFs
    uncategorized = KatalogPDF.query.filter_by(
        is_active=True,
        kategorie_id=None
    ).order_by(KatalogPDF.sort_order).all()

    return render_template(
        'katalog/index.html',
        categories=categories,
        uncategorized=uncategorized,
        pdf_service=get_pdf_service(),
    )


@katalog_bp.route('/kategorie/<slug>')
def category(slug: str):
    """Display PDFs in a specific category."""
    kategorie = KatalogKategorie.query.filter_by(
        slug=slug,
        is_active=True
    ).first_or_404()

    pdfs = KatalogPDF.query.filter_by(
        kategorie_id=kategorie.id,
        is_active=True
    ).order_by(KatalogPDF.sort_order, KatalogPDF.year.desc()).all()

    return render_template(
        'katalog/category.html',
        kategorie=kategorie,
        pdfs=pdfs,
        pdf_service=get_pdf_service(),
    )


@katalog_bp.route('/view/<pdf_id>')
def view(pdf_id: str):
    """Display PDF in browser viewer."""
    pdf = KatalogPDF.query.filter_by(
        id=pdf_id,
        is_active=True
    ).first_or_404()

    # Increment view counter
    pdf.increment_view_count()

    service = get_pdf_service()

    return render_template(
        'katalog/viewer.html',
        pdf=pdf,
        pdf_url=service.get_file_url(pdf),
        download_url=service.get_download_url(pdf),
    )


@katalog_bp.route('/download/<pdf_id>')
def download(pdf_id: str):
    """Download a PDF file."""
    pdf = KatalogPDF.query.filter_by(
        id=pdf_id,
        is_active=True
    ).first_or_404()

    service = get_pdf_service()

    # Check login requirement
    if service.require_login() and not current_user.is_authenticated:
        from flask import flash, redirect, url_for
        flash('Bitte melden Sie sich an, um Kataloge herunterzuladen.', 'warning')
        return redirect(url_for('auth.login', next=url_for('katalog.download', pdf_id=pdf_id)))

    # Increment download counter
    pdf.increment_download_count()

    # Get file path
    file_path = service.get_file_path(pdf.file_path)
    if not file_path.exists():
        abort(404)

    # Generate download filename
    download_name = f'{pdf.title}.pdf'

    return send_file(
        file_path,
        as_attachment=True,
        download_name=download_name,
        mimetype='application/pdf'
    )


@katalog_bp.route('/pdf/<pdf_id>')
def serve_pdf(pdf_id: str):
    """Serve PDF file for inline viewing."""
    pdf = KatalogPDF.query.filter_by(
        id=pdf_id,
        is_active=True
    ).first_or_404()

    service = get_pdf_service()
    file_path = service.get_file_path(pdf.file_path)

    if not file_path.exists():
        abort(404)

    return send_file(
        file_path,
        mimetype='application/pdf'
    )


@katalog_bp.route('/cover/<pdf_id>')
def serve_cover(pdf_id: str):
    """Serve cover image for a PDF."""
    pdf = KatalogPDF.query.filter_by(
        id=pdf_id,
        is_active=True
    ).first_or_404()

    if not pdf.cover_image_path:
        abort(404)

    service = get_pdf_service()
    file_path = service.get_file_path(pdf.cover_image_path)

    if not file_path.exists():
        abort(404)

    # Determine mimetype from extension
    ext = file_path.suffix.lower()
    mimetypes = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
    }
    mimetype = mimetypes.get(ext, 'image/jpeg')

    return send_file(file_path, mimetype=mimetype)
