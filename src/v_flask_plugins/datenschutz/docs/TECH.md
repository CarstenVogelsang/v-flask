# Datenschutz Plugin - Technische Dokumentation

## Architektur-Übersicht

```
datenschutz/
├── __init__.py          # DatenschutzPlugin Manifest, Context Processor
├── models.py            # DatenschutzConfig, DatenschutzVersion
├── generator.py         # DatenschutzGenerator (HTML-Ausgabe)
├── detector.py          # DienstErkennung (Auto-Detection)
├── validators.py        # Vollständigkeitsprüfung
├── bausteine/           # Vordefinierte Textbausteine (Markdown)
│   ├── pflicht/
│   ├── server/
│   ├── analytics/
│   └── ...
├── routes.py            # Public + Admin Blueprints
└── templates/
    └── datenschutz/
        ├── public/      # Öffentliche Datenschutz-Seite
        └── admin/       # Editor mit Baustein-Auswahl
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| `DatenschutzConfig` | `datenschutz_config` | Aktive Konfiguration mit ausgewählten Bausteinen |
| `DatenschutzVersion` | `datenschutz_version` | Versionierte Snapshots für Audit-Trail |

### Generator

```python
class DatenschutzGenerator:
    """Generiert Datenschutzerklärung aus Config und Bausteinen."""

    def __init__(self, config: DatenschutzConfig):
        self.config = config

    def generate_html(self) -> str:
        """Generiert vollständige Datenschutzerklärung als HTML."""
        ...
```

### Detector

```python
class DienstErkennung:
    """Erkennt automatisch verwendete Dienste."""

    def detect_all(self) -> list[DetectedService]:
        """Prüft Plugins, Templates und Config auf Dienste."""
        ...
```

### Routes

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/datenschutz/` | GET | Public | Datenschutzerklärung anzeigen |
| `/admin/datenschutz/` | GET | Admin | Editor mit Bausteinen |
| `/admin/datenschutz/` | POST | Admin | Konfiguration speichern |
| `/admin/datenschutz/preview` | GET | Admin | HTMX Preview-Endpoint |
| `/admin/datenschutz/versions` | GET | Admin | Versionshistorie |

### Templates

| Template | Zweck |
|----------|-------|
| `datenschutz/public/view.html` | Öffentliche Datenschutzseite |
| `datenschutz/admin/editor.html` | Baustein-Editor |
| `datenschutz/admin/versions.html` | Versionshistorie |

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `footer_links` | `{label: 'Datenschutz', icon: 'ti ti-shield-lock', url: 'datenschutz.public'}` |
| `admin_menu` | `{label: 'Datenschutz', icon: 'ti ti-shield-lock', url: 'datenschutz_admin.editor'}` |

## Context Processor

```jinja2
{# Datenschutzerklärung generieren #}
{{ get_datenschutz_html() }}

{# Erkannte Dienste abrufen #}
{% set services = get_detected_services() %}
```

## Settings-Schema

| Key | Type | Default | Beschreibung |
|-----|------|---------|--------------|
| `auto_detect_services` | bool | true | Automatische Erkennung |
| `show_version_date` | bool | true | Versionsdatum anzeigen |
| `cookie_banner_enabled` | bool | false | Cookie-Banner aktivieren |
| `dsb_contact` | textarea | (leer) | Datenschutzbeauftragter |

## Bausteine-Struktur

```
bausteine/
├── pflicht/
│   ├── verantwortlicher.md
│   ├── betroffenenrechte.md
│   └── aufsichtsbehoerde.md
├── server/
│   ├── server_logs.md
│   └── ssl_verschluesselung.md
├── analytics/
│   ├── google_analytics.md
│   └── matomo.md
└── ...
```

## Abhängigkeiten

- **v_flask Core**: Auth, DB, Betreiber
- **markdown**: Baustein-Rendering
- **markupsafe**: Sichere HTML-Ausgabe

## Datenbank-Schema

```sql
-- Aktive Konfiguration
CREATE TABLE datenschutz_config (
    id INTEGER PRIMARY KEY,
    selected_bausteine JSON,      -- Liste aktivierter Bausteine
    custom_text TEXT,             -- Eigene Ergänzungen
    dsb_name VARCHAR(200),        -- Datenschutzbeauftragter
    dsb_email VARCHAR(200),
    updated_at DATETIME
);

-- Versionshistorie
CREATE TABLE datenschutz_version (
    id INTEGER PRIMARY KEY,
    config_snapshot JSON,         -- Komplettzustand zum Zeitpunkt
    html_content TEXT,            -- Generierter HTML-Text
    created_at DATETIME,
    created_by_id INTEGER REFERENCES user(id)
);
```

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Bausteine als Markdown | Einfach zu pflegen, versionierbar |
| Versionierung in DB | Für Compliance-Audits wichtig |
| Auto-Detection modular | Einfach erweiterbar für neue Dienste |
