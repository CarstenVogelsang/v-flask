"""Datenschutz Bausteine (Text Modules) for privacy policy generation.

Each Baustein represents a specific data processing activity or service
with a legally compliant pre-written text.

The Baustein system supports:
- Automatic detection via plugin IDs or template patterns
- Configurable fields (e.g., tracking IDs, provider names)
- Custom text overrides
- Categorization for organized admin UI
"""

from dataclasses import dataclass, field


@dataclass
class Baustein:
    """A text module for the privacy policy.

    Attributes:
        id: Unique identifier (e.g., "google_analytics")
        kategorie: Category for grouping in UI (e.g., "analytics")
        name: Display name (e.g., "Google Analytics")
        beschreibung: Short description for admin UI
        text_template: Jinja2 template for the privacy text
        detect_plugins: Plugin IDs that trigger auto-detection
        detect_patterns: Regex patterns for template scanning
        pflichtfelder: Required config fields (e.g., ["tracking_id"])
        optional: Whether this Baustein can be omitted
        order: Sort order within category
    """

    id: str
    kategorie: str
    name: str
    beschreibung: str
    text_template: str
    detect_plugins: list[str] = field(default_factory=list)
    detect_patterns: list[str] = field(default_factory=list)
    pflichtfelder: list[str] = field(default_factory=list)
    optional: bool = True
    order: int = 100


# Category definitions for UI grouping
KATEGORIEN = {
    'basis': {
        'name': 'Basis',
        'beschreibung': 'Grundlegende Angaben für jede Website',
        'order': 1,
    },
    'kontakt': {
        'name': 'Kontakt & Kommunikation',
        'beschreibung': 'Kontaktformulare, E-Mail, Telefon',
        'order': 2,
    },
    'analytics': {
        'name': 'Analytics & Tracking',
        'beschreibung': 'Besucherstatistiken und Analyse-Tools',
        'order': 3,
    },
    'social': {
        'name': 'Social Media & Embeds',
        'beschreibung': 'YouTube, Google Maps, Social Plugins',
        'order': 4,
    },
    'marketing': {
        'name': 'Marketing',
        'beschreibung': 'Newsletter, Werbung, Remarketing',
        'order': 5,
    },
    'zahlung': {
        'name': 'E-Commerce & Zahlung',
        'beschreibung': 'Zahlungsanbieter und Bestellabwicklung',
        'order': 6,
    },
    'sonstige': {
        'name': 'Sonstige',
        'beschreibung': 'CDNs, Captcha, Login, etc.',
        'order': 7,
    },
}


def get_all_bausteine() -> list[Baustein]:
    """Get all available Bausteine from all categories."""
    from v_flask_plugins.datenschutz.bausteine.analytics import ANALYTICS_BAUSTEINE
    from v_flask_plugins.datenschutz.bausteine.basis import BASIS_BAUSTEINE
    from v_flask_plugins.datenschutz.bausteine.kontakt import KONTAKT_BAUSTEINE
    from v_flask_plugins.datenschutz.bausteine.marketing import MARKETING_BAUSTEINE
    from v_flask_plugins.datenschutz.bausteine.social import SOCIAL_BAUSTEINE
    from v_flask_plugins.datenschutz.bausteine.sonstige import SONSTIGE_BAUSTEINE
    from v_flask_plugins.datenschutz.bausteine.zahlung import ZAHLUNG_BAUSTEINE

    return (
        BASIS_BAUSTEINE
        + KONTAKT_BAUSTEINE
        + ANALYTICS_BAUSTEINE
        + SOCIAL_BAUSTEINE
        + MARKETING_BAUSTEINE
        + ZAHLUNG_BAUSTEINE
        + SONSTIGE_BAUSTEINE
    )


def get_baustein_by_id(baustein_id: str) -> Baustein | None:
    """Get a specific Baustein by its ID."""
    for baustein in get_all_bausteine():
        if baustein.id == baustein_id:
            return baustein
    return None


def get_bausteine_by_kategorie(kategorie: str) -> list[Baustein]:
    """Get all Bausteine in a specific category."""
    return [b for b in get_all_bausteine() if b.kategorie == kategorie]


def get_pflicht_bausteine() -> list[Baustein]:
    """Get all non-optional (mandatory) Bausteine."""
    return [b for b in get_all_bausteine() if not b.optional]


__all__ = [
    'Baustein',
    'KATEGORIEN',
    'get_all_bausteine',
    'get_baustein_by_id',
    'get_bausteine_by_kategorie',
    'get_pflicht_bausteine',
]
