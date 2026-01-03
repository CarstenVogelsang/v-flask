"""Betreiber model for multi-tenancy and theming."""

from v_flask.extensions import db


class Betreiber(db.Model):
    """Betreiber (operator) model for CI/theming settings.

    Each application has one Betreiber that defines:
        - Branding (name, logo)
        - Legal texts (impressum, datenschutz)
        - CI colors and fonts

    Usage:
        from v_flask.models import Betreiber

        betreiber = Betreiber(
            name='My Company',
            primary_color='#3b82f6',
            font_family='Inter'
        )
        db.session.add(betreiber)
        db.session.commit()

    In templates:
        {% set b = get_betreiber() %}
        <img src="{{ b.logo_url }}" alt="{{ b.name }}">
    """

    __tablename__ = 'betreiber'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(500))
    impressum = db.Column(db.Text)
    datenschutz = db.Column(db.Text)

    # CI settings
    primary_color = db.Column(db.String(7), default='#3b82f6')
    secondary_color = db.Column(db.String(7), default='#64748b')
    font_family = db.Column(db.String(100), default='Inter')

    def __repr__(self) -> str:
        return f'<Betreiber {self.name}>'

    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'logo_url': self.logo_url,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'font_family': self.font_family,
        }

    def get_css_variables(self) -> str:
        """Return CSS variables for theming.

        Usage in template:
            <style>{{ betreiber.get_css_variables()|safe }}</style>
        """
        return f""":root {{
    --v-primary: {self.primary_color};
    --v-secondary: {self.secondary_color};
    --v-font-family: '{self.font_family}', sans-serif;
}}"""
