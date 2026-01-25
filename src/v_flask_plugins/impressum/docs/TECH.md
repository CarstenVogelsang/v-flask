# Impressum Plugin - Technische Dokumentation

## Architektur-Übersicht

```
impressum/
├── __init__.py          # ImpressumPlugin Manifest, Context Processor
├── generator.py         # ImpressumGenerator (HTML-Ausgabe)
├── validators.py        # ImpressumValidator (Pflichtfeld-Prüfung)
├── routes.py            # Public + Admin Blueprints
└── templates/
    └── impressum/
        ├── public/      # Öffentliche Impressum-Seite
        └── admin/       # Editor mit Live-Vorschau
```

## Komponenten

### Models

Das Plugin verwendet das bestehende `Betreiber`-Model aus dem Core. Es werden keine eigenen Models definiert.

### Generator

```python
class ImpressumGenerator:
    """Generiert Impressum-HTML aus Betreiber-Daten."""

    def __init__(self, betreiber: Betreiber):
        self.betreiber = betreiber

    def generate_html(self) -> str:
        """Generiert vollständiges Impressum als HTML."""
        ...
```

### Validator

```python
class ImpressumValidator:
    """Prüft Betreiber-Daten auf Vollständigkeit."""

    def validate(self) -> ValidationResult:
        """Prüft Pflichtfelder und gibt Fehler/Warnungen zurück."""
        ...
```

### Routes

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/impressum/` | GET | Public | Impressum anzeigen |
| `/admin/impressum/` | GET | Admin | Editor mit Vorschau |
| `/admin/impressum/` | POST | Admin | Betreiber-Daten speichern |
| `/admin/impressum/preview` | GET | Admin | HTMX Preview-Endpoint |

### Templates

| Template | Zweck |
|----------|-------|
| `impressum/public/view.html` | Öffentliche Impressum-Seite |
| `impressum/admin/editor.html` | Admin-Editor mit Live-Vorschau |

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `footer_links` | `{label: 'Impressum', icon: 'ti ti-file-certificate', url: 'impressum.public'}` |
| `admin_menu` | `{label: 'Impressum', icon: 'ti ti-file-certificate', url: 'impressum_admin.editor'}` |

## Context Processor

```jinja2
{# Impressum-HTML generieren #}
{{ get_impressum_html() }}

{# Validierungsergebnis abrufen #}
{% set validation = get_impressum_validation() %}
{% if validation.errors %}...{% endif %}
```

## Settings-Schema

| Key | Type | Default | Beschreibung |
|-----|------|---------|--------------|
| `show_visdp` | bool | false | V.i.S.d.P. anzeigen |
| `show_streitschlichtung` | bool | true | EU-Streitschlichtung anzeigen |
| `custom_disclaimer` | textarea | (leer) | Eigener Haftungsausschluss |

## Abhängigkeiten

- **v_flask Core**: Betreiber Model, Auth, DB
- **markupsafe**: Sichere HTML-Ausgabe

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Kein eigenes Model | Betreiber-Daten zentral im Core, vermeidet Dopplung |
| Generator + Validator | Klare Trennung von Ausgabe und Prüfung |
| HTMX Live-Vorschau | Bessere UX beim Bearbeiten |
