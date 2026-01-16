"""Impressum text generator for German legal requirements."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from v_flask.models import Betreiber


class ImpressumGenerator:
    """Generates legally compliant German Impressum from Betreiber data.

    The generator creates HTML-formatted Impressum text based on:
    - Company information (name, address, legal form)
    - Contact details (phone, email)
    - Legal registration (Handelsregister)
    - Tax information (USt-IdNr)
    - Optional sections (V.i.S.d.P., Streitschlichtung)

    Usage:
        from v_flask.models import Betreiber
        from v_flask_plugins.impressum.generator import ImpressumGenerator

        betreiber = Betreiber.query.first()
        generator = ImpressumGenerator(betreiber)

        html = generator.generate_html()
        text = generator.generate_text()
    """

    def __init__(self, betreiber: Betreiber):
        """Initialize the generator with Betreiber data.

        Args:
            betreiber: Betreiber instance containing all company data.
        """
        self.betreiber = betreiber

    def generate_html(self) -> str:
        """Generate HTML-formatted Impressum.

        Returns:
            HTML string with all applicable sections.
        """
        sections = []

        # Pflichtangaben
        sections.append(self._section_header())
        sections.append(self._section_anbieter())
        sections.append(self._section_vertretung())
        sections.append(self._section_kontakt())

        if self._has_register():
            sections.append(self._section_register())

        if self._has_ust_idnr():
            sections.append(self._section_steuern())

        # Optionale Angaben
        if self._option('show_visdp') and self.betreiber.inhaltlich_verantwortlich:
            sections.append(self._section_visdp())

        if self._option('show_streitschlichtung'):
            sections.append(self._section_streitschlichtung())

        return '\n\n'.join(filter(None, sections))

    def generate_text(self) -> str:
        """Generate plain-text Impressum (for email footers, etc.).

        Returns:
            Plain text string with all applicable sections.
        """
        # Remove HTML tags from generated content
        html = self.generate_html()
        # Simple HTML to text conversion
        text = html.replace('<h2>', '').replace('</h2>', '\n')
        text = text.replace('<h3>', '').replace('</h3>', '\n')
        text = text.replace('<p>', '').replace('</p>', '\n')
        text = text.replace('<br>', '\n').replace('<br/>', '\n')
        text = text.replace('<strong>', '').replace('</strong>', '')
        text = text.replace('\n\n\n', '\n\n')
        return text.strip()

    def _option(self, key: str, default: bool = False) -> bool:
        """Get an impressum option value.

        Args:
            key: Option key (e.g., 'show_visdp')
            default: Default value if not set

        Returns:
            Boolean option value.
        """
        return self.betreiber.get_impressum_option(key, default)

    def _has_register(self) -> bool:
        """Check if Handelsregister info is available."""
        return bool(
            self.betreiber.handelsregister_gericht and
            self.betreiber.handelsregister_nummer
        )

    def _has_ust_idnr(self) -> bool:
        """Check if USt-IdNr is available."""
        return bool(self.betreiber.ust_idnr)

    # === Section Generators ===

    def _section_header(self) -> str:
        """Generate the header section."""
        return '<h2>Angaben gemäß § 5 TMG</h2>'

    def _section_anbieter(self) -> str:
        """Generate the company/provider section."""
        b = self.betreiber
        lines = []

        # Company name with legal form
        company_name = b.get_company_name_with_rechtsform()
        lines.append(f'<p><strong>{company_name}</strong>')

        # Address
        if b.strasse:
            lines.append(f'<br>{b.strasse}')
        if b.plz and b.ort:
            lines.append(f'<br>{b.plz} {b.ort}')
        if b.land and b.land != 'Deutschland':
            lines.append(f'<br>{b.land}')

        lines.append('</p>')
        return ''.join(lines)

    def _section_vertretung(self) -> str:
        """Generate the legal representation section."""
        b = self.betreiber

        if not b.geschaeftsfuehrer:
            return ''

        title = self._get_vertretung_title()

        return f'''<h3>{title}</h3>
<p>{b.geschaeftsfuehrer}</p>'''

    def _get_vertretung_title(self) -> str:
        """Get appropriate title for legal representation based on rechtsform."""
        rechtsform = (self.betreiber.rechtsform or '').upper()

        if rechtsform in ('GMBH', 'UG', 'UG (HAFTUNGSBESCHRÄNKT)'):
            return 'Vertreten durch den Geschäftsführer'
        elif rechtsform == 'AG':
            return 'Vertreten durch den Vorstand'
        elif rechtsform == 'GMBH & CO. KG':
            return 'Vertreten durch die persönlich haftende Gesellschafterin'
        else:
            return 'Vertreten durch'

    def _section_kontakt(self) -> str:
        """Generate the contact section."""
        b = self.betreiber
        lines = ['<h3>Kontakt</h3>', '<p>']

        if b.telefon:
            lines.append(f'Telefon: {b.telefon}<br>')
        if b.fax:
            lines.append(f'Fax: {b.fax}<br>')
        if b.email:
            lines.append(f'E-Mail: {b.email}')

        lines.append('</p>')
        return ''.join(lines)

    def _section_register(self) -> str:
        """Generate the Handelsregister section."""
        b = self.betreiber

        if not self._has_register():
            return ''

        return f'''<h3>Registereintrag</h3>
<p>Eingetragen im Handelsregister.<br>
Registergericht: {b.handelsregister_gericht}<br>
Registernummer: {b.handelsregister_nummer}</p>'''

    def _section_steuern(self) -> str:
        """Generate the tax information section."""
        b = self.betreiber
        lines = []

        if b.ust_idnr:
            lines.append('<h3>Umsatzsteuer-ID</h3>')
            lines.append(f'<p>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG:<br>')
            lines.append(f'{b.ust_idnr}</p>')

        if b.wirtschafts_idnr:
            lines.append('<h3>Wirtschafts-Identifikationsnummer</h3>')
            lines.append(f'<p>{b.wirtschafts_idnr}</p>')

        return ''.join(lines)

    def _section_visdp(self) -> str:
        """Generate the V.i.S.d.P. section (responsible for content)."""
        b = self.betreiber

        if not b.inhaltlich_verantwortlich:
            return ''

        lines = [
            '<h3>Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h3>',
            f'<p>{b.inhaltlich_verantwortlich}'
        ]

        # Include address if available
        address = b.get_full_address()
        if address:
            for line in address.split('\n'):
                lines.append(f'<br>{line}')

        lines.append('</p>')
        return ''.join(lines)

    def _section_streitschlichtung(self) -> str:
        """Generate the dispute resolution section."""
        # Get custom text or use default
        custom_text = self._option('streitschlichtung_text')

        if custom_text:
            return f'''<h3>Streitschlichtung</h3>
<p>{custom_text}</p>'''

        # Default text
        return '''<h3>Streitschlichtung</h3>
<p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:
<a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener">https://ec.europa.eu/consumers/odr/</a></p>
<p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren
vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>'''
