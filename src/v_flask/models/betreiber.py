"""Betreiber model for multi-tenancy and theming."""

from v_flask.extensions import db


class Betreiber(db.Model):
    """Betreiber (operator) model for CI/theming settings.

    Each application has one Betreiber that defines:
        - Branding (name, logo, website)
        - Legal texts (impressum, datenschutz)
        - CI colors and fonts

    Usage:
        from v_flask.models import Betreiber

        betreiber = Betreiber(
            name='My Company',
            website='https://example.com',
            primary_color='#3b82f6',
            font_family='Inter'
        )
        db.session.add(betreiber)
        db.session.commit()

    In templates:
        {% set b = get_betreiber() %}
        <a href="{{ b.website }}">{{ b.name }}</a>
    """

    __tablename__ = 'betreiber'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(500))
    website = db.Column(db.String(500))  # Betreiber-Website URL
    email = db.Column(db.String(200))  # Contact email for notifications
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
            'website': self.website,
            'email': self.email,
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
