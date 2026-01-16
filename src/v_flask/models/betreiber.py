"""Betreiber model for multi-tenancy and theming."""

from sqlalchemy.orm.attributes import flag_modified

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

    # Custom settings (JSON for project-specific configuration)
    custom_settings = db.Column(db.JSON, default=dict)

    # === Impressum-Felder ===

    # Anschrift
    strasse = db.Column(db.String(200))
    plz = db.Column(db.String(10))
    ort = db.Column(db.String(100))
    land = db.Column(db.String(100), default='Deutschland')

    # Kontakt (email existiert bereits oben)
    telefon = db.Column(db.String(50))
    fax = db.Column(db.String(50))

    # Rechtsform & Vertretung
    rechtsform = db.Column(db.String(50))  # 'GmbH', 'UG', 'AG', etc.
    geschaeftsfuehrer = db.Column(db.String(500))  # Komma-separiert bei mehreren

    # Handelsregister
    handelsregister_gericht = db.Column(db.String(100))  # z.B. 'Amtsgericht Düsseldorf'
    handelsregister_nummer = db.Column(db.String(50))    # z.B. 'HRB 12345'

    # Steuern
    ust_idnr = db.Column(db.String(20))           # z.B. 'DE123456789'
    wirtschafts_idnr = db.Column(db.String(20))   # optional

    # Optionale Angaben
    inhaltlich_verantwortlich = db.Column(db.String(200))  # V.i.S.d.P.

    # Impressum-Optionen (JSON für Toggle-Felder)
    impressum_optionen = db.Column(db.JSON, default=dict)

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
            'custom_settings': self.custom_settings or {},
            # Impressum fields
            'strasse': self.strasse,
            'plz': self.plz,
            'ort': self.ort,
            'land': self.land,
            'telefon': self.telefon,
            'fax': self.fax,
            'rechtsform': self.rechtsform,
            'geschaeftsfuehrer': self.geschaeftsfuehrer,
            'handelsregister_gericht': self.handelsregister_gericht,
            'handelsregister_nummer': self.handelsregister_nummer,
            'ust_idnr': self.ust_idnr,
            'wirtschafts_idnr': self.wirtschafts_idnr,
            'inhaltlich_verantwortlich': self.inhaltlich_verantwortlich,
            'impressum_optionen': self.impressum_optionen or {},
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

    def get_setting(self, key: str, default=None):
        """Get a custom setting value.

        Args:
            key: Setting key to retrieve
            default: Default value if key not found

        Returns:
            Setting value or default

        Usage:
            style = betreiber.get_setting('article_card_style', 'wide')
        """
        if self.custom_settings is None:
            return default
        return self.custom_settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """Set a custom setting value.

        Args:
            key: Setting key to set
            value: Value to store

        Usage:
            betreiber.set_setting('article_card_style', 'compact')
            db.session.commit()
        """
        if self.custom_settings is None:
            self.custom_settings = {}
        self.custom_settings[key] = value
        flag_modified(self, 'custom_settings')

    # === Impressum-Optionen Helper ===

    def get_impressum_option(self, key: str, default=None):
        """Get an impressum option value.

        Args:
            key: Option key to retrieve (e.g., 'show_visdp')
            default: Default value if key not found

        Returns:
            Option value or default

        Usage:
            if betreiber.get_impressum_option('show_visdp', False):
                # Show V.i.S.d.P. section
        """
        if self.impressum_optionen is None:
            return default
        return self.impressum_optionen.get(key, default)

    def set_impressum_option(self, key: str, value) -> None:
        """Set an impressum option value.

        Args:
            key: Option key to set (e.g., 'show_visdp')
            value: Value to store

        Usage:
            betreiber.set_impressum_option('show_visdp', True)
            db.session.commit()
        """
        if self.impressum_optionen is None:
            self.impressum_optionen = {}
        self.impressum_optionen[key] = value
        flag_modified(self, 'impressum_optionen')

    def get_full_address(self) -> str | None:
        """Get formatted full address for Impressum.

        Returns:
            Formatted address string or None if incomplete.

        Usage:
            address = betreiber.get_full_address()
            # "Musterstraße 1\\n12345 Musterstadt\\nDeutschland"
        """
        if not self.strasse or not self.plz or not self.ort:
            return None

        parts = [self.strasse, f"{self.plz} {self.ort}"]
        if self.land and self.land != 'Deutschland':
            parts.append(self.land)
        return '\n'.join(parts)

    def get_company_name_with_rechtsform(self) -> str:
        """Get company name with legal form suffix.

        Returns:
            Company name with rechtsform (e.g., 'Muster GmbH')
        """
        if self.rechtsform and self.rechtsform not in self.name:
            return f"{self.name} {self.rechtsform}"
        return self.name
