"""Privacy policy generator for the Datenschutz plugin.

Generates a complete, DSGVO-compliant privacy policy (Datenschutzerklärung)
from the DatenschutzConfig and activated Bausteine.
"""

from datetime import datetime

from jinja2 import Environment, BaseLoader

from v_flask_plugins.datenschutz.bausteine import (
    KATEGORIEN,
    get_all_bausteine,
    get_baustein_by_id,
)
from v_flask_plugins.datenschutz.models import DatenschutzConfig


class DatenschutzGenerator:
    """Generates privacy policy HTML from configuration and Bausteine.

    The generator:
    1. Creates mandatory sections (Verantwortlicher, Betroffenenrechte)
    2. Adds sections for each activated Baustein
    3. Renders Baustein templates with config values
    4. Organizes sections by category
    """

    def __init__(self, config: DatenschutzConfig):
        """Initialize generator with configuration.

        Args:
            config: The DatenschutzConfig with activated Bausteine
        """
        self.config = config
        self.jinja_env = Environment(loader=BaseLoader())

    def generate_html(self) -> str:
        """Generate complete privacy policy as HTML.

        Returns:
            HTML string with full privacy policy
        """
        sections = []

        # 1. Header
        sections.append(self._section_header())

        # 2. Verantwortlicher (mandatory)
        sections.append(self._section_verantwortlicher())

        # 3. Datenschutzbeauftragter (if applicable)
        if self.config.dsb_vorhanden:
            sections.append(self._section_datenschutzbeauftragter())

        # 4. Activated Bausteine, grouped by category
        sections.extend(self._generate_baustein_sections())

        # 5. Stand / Aktualität
        sections.append(self._section_aktualitaet())

        return '\n\n'.join(sections)

    def generate_text(self) -> str:
        """Generate privacy policy as plain text.

        Useful for email footers or text-based displays.

        Returns:
            Plain text version of the privacy policy
        """
        import re

        html = self.generate_html()

        # Convert headings
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n\n\1\n' + '=' * 40, html)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n\n\1\n' + '-' * 30, text)

        # Convert paragraphs
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n', text, flags=re.DOTALL)

        # Convert lists
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'  - \1', text)
        text = re.sub(r'</?[ou]l[^>]*>', '', text)

        # Convert links
        text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'\2 (\1)', text)

        # Convert strong/bold
        text = re.sub(r'<strong>(.*?)</strong>', r'*\1*', text)

        # Remove remaining tags
        text = re.sub(r'<[^>]+>', '', text)

        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _section_header(self) -> str:
        """Generate the main header."""
        return '<h2>Datenschutzerklärung</h2>'

    def _section_verantwortlicher(self) -> str:
        """Generate Verantwortlicher section (DSGVO Art. 13 Abs. 1 lit. a)."""
        parts = ['<h3>Verantwortlicher</h3>']
        parts.append('<p>Verantwortlicher für die Datenverarbeitung auf dieser Website:</p>')
        parts.append('<p>')

        if self.config.verantwortlicher_name:
            parts.append(f'<strong>{self.config.verantwortlicher_name}</strong><br>')

        address = self.config.get_verantwortlicher_adresse()
        if address:
            parts.append(address.replace('\n', '<br>'))
            parts.append('<br>')

        if self.config.verantwortlicher_email:
            parts.append(f'<br>E-Mail: <a href="mailto:{self.config.verantwortlicher_email}">')
            parts.append(f'{self.config.verantwortlicher_email}</a>')

        if self.config.verantwortlicher_telefon:
            parts.append(f'<br>Telefon: {self.config.verantwortlicher_telefon}')

        parts.append('</p>')
        return ''.join(parts)

    def _section_datenschutzbeauftragter(self) -> str:
        """Generate Datenschutzbeauftragter section (DSGVO Art. 13 Abs. 1 lit. b)."""
        parts = ['<h3>Datenschutzbeauftragter</h3>']

        if self.config.dsb_extern:
            parts.append('<p>Wir haben einen externen Datenschutzbeauftragten bestellt:</p>')
        else:
            parts.append('<p>Unser Datenschutzbeauftragter:</p>')

        parts.append('<p>')
        if self.config.dsb_name:
            parts.append(f'{self.config.dsb_name}<br>')
        if self.config.dsb_email:
            parts.append(f'E-Mail: <a href="mailto:{self.config.dsb_email}">')
            parts.append(f'{self.config.dsb_email}</a>')
        if self.config.dsb_telefon:
            parts.append(f'<br>Telefon: {self.config.dsb_telefon}')
        parts.append('</p>')

        return ''.join(parts)

    def _generate_baustein_sections(self) -> list[str]:
        """Generate sections for all activated Bausteine.

        Groups Bausteine by category and renders their templates.

        Returns:
            List of HTML sections
        """
        sections = []
        aktivierte = self.config.aktivierte_bausteine or []

        # Get all activated Bausteine
        bausteine = [
            get_baustein_by_id(bid) for bid in aktivierte
        ]
        bausteine = [b for b in bausteine if b is not None]

        # Also add mandatory (non-optional) Bausteine if not already included
        all_bausteine = get_all_bausteine()
        for b in all_bausteine:
            if not b.optional and b.id not in aktivierte:
                bausteine.append(b)

        # Group by category
        by_category = {}
        for b in bausteine:
            if b.kategorie not in by_category:
                by_category[b.kategorie] = []
            by_category[b.kategorie].append(b)

        # Sort categories by order
        sorted_categories = sorted(
            by_category.keys(),
            key=lambda k: KATEGORIEN.get(k, {}).get('order', 999)
        )

        # Generate sections
        for kategorie in sorted_categories:
            category_bausteine = by_category[kategorie]
            # Sort Bausteine within category by order
            category_bausteine.sort(key=lambda b: b.order)

            for baustein in category_bausteine:
                section = self._render_baustein(baustein)
                if section:
                    sections.append(section)

        return sections

    def _render_baustein(self, baustein) -> str | None:
        """Render a single Baustein template.

        Args:
            baustein: The Baustein to render

        Returns:
            Rendered HTML or None if rendering fails
        """
        try:
            # Check for custom text override
            custom_text = self.config.get_custom_text(baustein.id)
            if custom_text:
                return custom_text

            # Get Baustein-specific configuration
            baustein_config = self.config.get_baustein_config(baustein.id)

            # Build context for template rendering
            context = {
                'config': self.config,
                **baustein_config,
            }

            # Render template
            template = self.jinja_env.from_string(baustein.text_template)
            rendered = template.render(**context)

            # Convert Markdown headings to HTML
            rendered = self._markdown_to_html(rendered)

            return rendered

        except Exception as e:
            # Return error indicator in development
            return f'<!-- Error rendering {baustein.id}: {e} -->'

    def _markdown_to_html(self, text: str) -> str:
        """Convert simple Markdown to HTML.

        Handles:
        - ### headings → <h3>
        - **bold** → <strong>
        - [text](url) → <a href="url">text</a>
        - Line breaks

        Args:
            text: Markdown text

        Returns:
            HTML string
        """
        import re

        # Headings
        text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)

        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

        # Lists (simple)
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)

        # Paragraphs: wrap consecutive non-tag lines
        lines = text.strip().split('\n')
        result = []
        in_paragraph = False
        paragraph_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                # Empty line ends paragraph
                if paragraph_lines:
                    result.append('<p>' + '<br>\n'.join(paragraph_lines) + '</p>')
                    paragraph_lines = []
                in_paragraph = False
            elif stripped.startswith('<h') or stripped.startswith('<li'):
                # Tag line - close paragraph first
                if paragraph_lines:
                    result.append('<p>' + '<br>\n'.join(paragraph_lines) + '</p>')
                    paragraph_lines = []
                result.append(stripped)
                in_paragraph = False
            else:
                # Regular text line
                paragraph_lines.append(stripped)
                in_paragraph = True

        # Close final paragraph
        if paragraph_lines:
            result.append('<p>' + '<br>\n'.join(paragraph_lines) + '</p>')

        return '\n'.join(result)

    def _section_aktualitaet(self) -> str:
        """Generate the 'Stand' (last updated) section."""
        date_str = datetime.now().strftime('%d.%m.%Y')
        if self.config.letzte_aktualisierung:
            date_str = self.config.letzte_aktualisierung.strftime('%d.%m.%Y')

        return f'''<h3>Aktualität und Änderung dieser Datenschutzerklärung</h3>
<p>Diese Datenschutzerklärung ist aktuell gültig und hat den Stand: <strong>{date_str}</strong></p>
<p>Durch die Weiterentwicklung unserer Website und Angebote oder aufgrund geänderter
gesetzlicher bzw. behördlicher Vorgaben kann es notwendig werden, diese
Datenschutzerklärung zu ändern.</p>'''
