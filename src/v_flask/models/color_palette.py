"""ColorPalette model for predefined color schemes."""

from v_flask.extensions import db


class ColorPalette(db.Model):
    """Predefined color palette with 8 semantic colors.

    Colors follow the DaisyUI semantic naming convention:
    - primary: Main brand color (buttons, links, accents)
    - secondary: Supporting brand color
    - accent: Highlight color for special elements
    - neutral: Text and background tones
    - info: Informational messages (blue tones)
    - success: Success states (green tones)
    - warning: Warning states (yellow/orange tones)
    - error: Error states (red tones)

    Usage:
        from v_flask.models import ColorPalette

        # Get all palettes
        palettes = ColorPalette.query.all()

        # Get default palette
        default = ColorPalette.query.filter_by(is_default=True).first()

        # Get palettes by category
        warm_palettes = ColorPalette.query.filter_by(category='warm').all()
    """

    __tablename__ = 'color_palette'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)

    # 8 semantic colors (HEX format: #RRGGBB)
    primary = db.Column(db.String(7), nullable=False)
    secondary = db.Column(db.String(7), nullable=False)
    accent = db.Column(db.String(7), nullable=False)
    neutral = db.Column(db.String(7), nullable=False)
    info = db.Column(db.String(7), nullable=False)
    success = db.Column(db.String(7), nullable=False)
    warning = db.Column(db.String(7), nullable=False)
    error = db.Column(db.String(7), nullable=False)

    # Metadata
    is_default = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(20))  # "warm", "cool", "neutral", "vibrant"

    def __repr__(self) -> str:
        return f'<ColorPalette {self.slug}: {self.name}>'

    def to_dict(self) -> dict:
        """Return palette colors as dictionary.

        Returns:
            Dictionary with all 8 semantic colors.

        Usage:
            colors = palette.to_dict()
            primary = colors['primary']  # '#3b82f6'
        """
        return {
            'primary': self.primary,
            'secondary': self.secondary,
            'accent': self.accent,
            'neutral': self.neutral,
            'info': self.info,
            'success': self.success,
            'warning': self.warning,
            'error': self.error,
        }

    def preview_colors(self) -> list:
        """Return all 8 semantic colors for preview display.

        Returns:
            List of dicts with color name, key, and hex value.

        Usage:
            colors = palette.preview_colors()
            # [{'name': 'Primär', 'key': 'primary', 'color': '#3b82f6'}, ...]
        """
        return [
            {'name': 'Primär', 'key': 'primary', 'color': self.primary},
            {'name': 'Sekundär', 'key': 'secondary', 'color': self.secondary},
            {'name': 'Akzent', 'key': 'accent', 'color': self.accent},
            {'name': 'Neutral', 'key': 'neutral', 'color': self.neutral},
            {'name': 'Info', 'key': 'info', 'color': self.info},
            {'name': 'Erfolg', 'key': 'success', 'color': self.success},
            {'name': 'Warnung', 'key': 'warning', 'color': self.warning},
            {'name': 'Fehler', 'key': 'error', 'color': self.error},
        ]

    def get_css_variables(self) -> str:
        """Generate CSS custom properties for this palette.

        Returns:
            CSS string with :root variables.

        Usage in template:
            <style>{{ palette.get_css_variables()|safe }}</style>
        """
        return f""":root {{
    --color-primary: {self.primary};
    --color-secondary: {self.secondary};
    --color-accent: {self.accent};
    --color-neutral: {self.neutral};
    --color-info: {self.info};
    --color-success: {self.success};
    --color-warning: {self.warning};
    --color-error: {self.error};
}}"""
