"""Core settings routes for platform configuration.

Provides admin UI for managing core settings:
- Allgemein: Basic operator information (name, website, email)
- Branding: Colors, fonts, logos, favicons
- Platzhalter: Template placeholder variables for the platform

These settings are stored in the Betreiber model and are available
to all v-flask applications.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import TYPE_CHECKING

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from v_flask.auth import admin_required
from v_flask.extensions import db
from v_flask.models import Betreiber, ColorPalette

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

# Blueprint for core settings routes
admin_settings_bp = Blueprint(
    'admin_settings',
    __name__,
    url_prefix='/admin',
    template_folder='../templates',
)

# Allowed file extensions for uploads
ALLOWED_LOGO_EXTENSIONS = {'svg', 'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_FAVICON_EXTENSIONS = {'ico', 'png', 'svg'}

# Available font families
FONT_FAMILIES = [
    ('system-ui', 'System (Standard)'),
    ('Inter', 'Inter'),
    ('Roboto', 'Roboto'),
    ('Open Sans', 'Open Sans'),
    ('Lato', 'Lato'),
    ('Poppins', 'Poppins'),
    ('Nunito', 'Nunito'),
    ('Source Sans Pro', 'Source Sans Pro'),
]

# Available logo icons (Tabler Icons)
LOGO_ICONS = [
    'ti-coffee',
    'ti-home',
    'ti-building',
    'ti-building-store',
    'ti-map-pin',
    'ti-star',
    'ti-heart',
    'ti-leaf',
    'ti-flame',
    'ti-sun',
    'ti-moon',
    'ti-bolt',
    'ti-diamond',
    'ti-crown',
    'ti-rocket',
]


def _allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def _is_valid_hex_color(color: str) -> bool:
    """Validate hex color format (#RRGGBB)."""
    if not color:
        return False
    return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))


def _save_upload(file, subdir: str, prefix: str, allowed_extensions: set) -> str | None:
    """Save an uploaded file and return the relative path.

    Args:
        file: Werkzeug FileStorage object
        subdir: Subdirectory within static/uploads
        prefix: Filename prefix (e.g., 'logo', 'favicon')
        allowed_extensions: Set of allowed file extensions

    Returns:
        Relative path to saved file, or None if save failed
    """
    if not file or file.filename == '':
        return None

    if not _allowed_file(file.filename, allowed_extensions):
        return None

    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = secure_filename(f'{prefix}_{timestamp}.{ext}')

    # Determine upload path
    upload_dir = os.path.join(current_app.static_folder or 'static', 'uploads', subdir)
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # Return relative path for storage
    return f'uploads/{subdir}/{filename}'


@admin_settings_bp.route('/settings/', methods=['GET', 'POST'])
@admin_required
def settings():
    """Core settings page with tabs: Allgemein, Branding, Platzhalter.

    GET: Display settings form
    POST: Save settings for the active tab
    """
    betreiber = Betreiber.query.first()

    if not betreiber:
        # Create default Betreiber if none exists
        betreiber = Betreiber(
            name='Default',
            primary_color='#3b82f6',
            secondary_color='#64748b',
        )
        db.session.add(betreiber)
        db.session.commit()
        # Reload to ensure object is properly attached to session
        betreiber = Betreiber.query.first()

    # Load color palettes
    palettes = ColorPalette.query.order_by(ColorPalette.category, ColorPalette.name).all()

    # Determine active tab
    active_tab = request.args.get('tab', 'allgemein')

    if request.method == 'POST':
        tab = request.form.get('_tab', 'allgemein')

        try:
            if tab == 'allgemein':
                _save_allgemein_settings(betreiber)

            elif tab == 'branding':
                _save_branding_settings(betreiber)

            elif tab == 'platzhalter':
                _save_platzhalter_settings(betreiber)

            db.session.commit()
            flash('Einstellungen gespeichert.', 'success')
            logger.info(f"Core settings saved (tab: {tab})")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving settings: {e}")
            flash(f'Fehler beim Speichern: {e}', 'error')

        return redirect(url_for('admin_settings.settings', tab=tab))

    # Prepare template context
    current_palette_id = betreiber.get_setting('palette_id')
    color_overrides = betreiber.get_setting('color_overrides', {}) or {}

    # Determine site_name and logo_icon for consistent navigation
    site_name = betreiber.get_setting('plattform_name', betreiber.name) if betreiber else 'Admin'
    logo_icon = betreiber.get_setting('logo_icon', 'ti-layout-dashboard') if betreiber else 'ti-layout-dashboard'

    return render_template(
        'v_flask/admin/core_settings.html',
        betreiber=betreiber,
        palettes=palettes,
        current_palette_id=current_palette_id,
        color_overrides=color_overrides,
        font_families=FONT_FAMILIES,
        logo_icons=LOGO_ICONS,
        active_tab=active_tab,
        # Navigation context for consistent sidebar
        site_name=site_name,
        logo_icon=logo_icon,
    )


def _save_allgemein_settings(betreiber: Betreiber) -> None:
    """Save general settings (name, website, email).

    Args:
        betreiber: Betreiber instance to update
    """
    betreiber.name = request.form.get('name', '').strip()
    betreiber.website = request.form.get('website', '').strip()
    betreiber.email = request.form.get('email', '').strip()


def _save_branding_settings(betreiber: Betreiber) -> None:
    """Save branding settings (colors, font, logo, favicon).

    Args:
        betreiber: Betreiber instance to update
    """
    # Palette selection
    palette_id = request.form.get('palette_id')
    if palette_id:
        betreiber.set_setting('palette_id', int(palette_id))

    # Color overrides (8 semantic colors)
    color_names = ['primary', 'secondary', 'accent', 'neutral', 'info', 'success', 'warning', 'error']
    color_overrides = {}

    for color_name in color_names:
        override_value = request.form.get(f'override_{color_name}', '').strip()
        if override_value and _is_valid_hex_color(override_value):
            color_overrides[color_name] = override_value

    betreiber.set_setting('color_overrides', color_overrides)

    # Legacy color columns (for backwards compatibility)
    if color_overrides.get('primary'):
        betreiber.primary_color = color_overrides['primary']
    if color_overrides.get('secondary'):
        betreiber.secondary_color = color_overrides['secondary']

    # Font family
    font_family = request.form.get('font_family', 'system-ui').strip()
    betreiber.font_family = font_family

    # Logo icon
    logo_icon = request.form.get('logo_icon', '').strip()
    if logo_icon:
        betreiber.set_setting('logo_icon', logo_icon)

    # Logo image upload
    logo_file = request.files.get('logo_image')
    if logo_file and logo_file.filename:
        logo_path = _save_upload(logo_file, 'branding', 'logo', ALLOWED_LOGO_EXTENSIONS)
        if logo_path:
            betreiber.set_setting('logo_image', logo_path)

    # Favicon upload
    favicon_file = request.files.get('favicon')
    if favicon_file and favicon_file.filename:
        favicon_path = _save_upload(favicon_file, 'branding', 'favicon', ALLOWED_FAVICON_EXTENSIONS)
        if favicon_path:
            betreiber.set_setting('favicon', favicon_path)

    # Auto-generated favicon from icon (base64 PNG)
    auto_favicon_data = request.form.get('auto_favicon_data', '').strip()
    if auto_favicon_data and auto_favicon_data.startswith('data:image/png;base64,'):
        import base64

        # Decode and save
        try:
            base64_data = auto_favicon_data.split(',')[1]
            image_data = base64.b64decode(base64_data)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'favicon_auto_{timestamp}.png'

            upload_dir = os.path.join(current_app.static_folder or 'static', 'uploads', 'branding')
            os.makedirs(upload_dir, exist_ok=True)

            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)

            betreiber.set_setting('favicon', f'uploads/branding/{filename}')
        except Exception as e:
            logger.warning(f"Failed to save auto-generated favicon: {e}")


def _save_platzhalter_settings(betreiber: Betreiber) -> None:
    """Save placeholder variable settings.

    These variables are available in templates as {{ plattform.* }}.

    Args:
        betreiber: Betreiber instance to update
    """
    betreiber.set_setting('plattform_name', request.form.get('plattform_name', '').strip())
    betreiber.set_setting('plattform_zielgruppe', request.form.get('plattform_zielgruppe', '').strip())
    betreiber.set_setting('location_bezeichnung', request.form.get('location_bezeichnung', '').strip())


def register_core_settings_routes(app: Flask) -> None:
    """Register the core settings blueprint with the app.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(admin_settings_bp)
