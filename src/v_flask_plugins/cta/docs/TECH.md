# CTA Plugin - Technische Dokumentation

## Architektur-Übersicht

```
cta/
├── __init__.py          # CtaPlugin Manifest, Settings-Schema
├── models.py            # CtaSection, CtaTemplate, CtaAssignment
├── routes.py            # Admin Blueprint (10KB)
├── slot_provider.py     # Content-Slot Integration
├── services/
│   └── cta_service.py   # Rendering-Logik, Placeholder-Ersetzung
└── templates/
    └── cta/
        ├── admin/       # Admin-Oberfläche
        └── variants/    # Design-Templates (card, alert, floating)
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| `CtaSection` | `plugin_cta_section` | CTA-Konfiguration mit Variante, Text, Button |
| `CtaTemplate` | `plugin_cta_template` | Wiederverwendbare Text-Vorlagen |
| `CtaAssignment` | `plugin_cta_assignment` | Zuweisung von CTA zu Page + Slot |
| `PageRoute` | `page_route` | (Core) Registrierte Seiten-Endpoints |

### Routes

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/admin/cta/` | GET | Admin | Liste aller CTA Sections |
| `/admin/cta/neu` | GET/POST | Admin | Neue CTA Section erstellen |
| `/admin/cta/<id>` | GET/POST | Admin | CTA Section bearbeiten |
| `/admin/cta/<id>/delete` | POST | Admin | CTA Section löschen |
| `/admin/cta/assignments` | GET | Admin | Seitenzuweisungen verwalten |
| `/admin/cta/templates` | GET | Admin | Text-Templates verwalten |

### Services

| Service | Methode | Beschreibung |
|---------|---------|--------------|
| `cta_service.get_cta_for_slot(endpoint, slot)` | Findet CTA für Endpoint/Slot |
| `cta_service.render_cta(cta, context)` | Rendert CTA mit Platzhaltern |
| `cta_service.get_placeholder_context()` | Liefert Platzhalter-Werte aus Settings |

### Templates

| Template | Zweck |
|----------|-------|
| `cta/admin/list.html` | Admin-Liste aller CTA Sections |
| `cta/admin/edit.html` | Bearbeiten-Formular mit Preview |
| `cta/admin/assignments.html` | Seitenzuweisungen |
| `cta/variants/card.html` | Card-Design |
| `cta/variants/alert.html` | Alert-Design |
| `cta/variants/floating.html` | Floating-Design |

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `admin_menu` | `{label: 'CTA Sections', icon: 'ti ti-click', url: 'cta_admin.list_sections'}` |

## Content-Slot-Provider

Das CTA-Plugin registriert sich als Content-Slot-Provider:

```python
from v_flask import content_slot_registry
from v_flask_plugins.cta.slot_provider import cta_slot_provider
content_slot_registry.register(cta_slot_provider)
```

**Verwendung im Template:**

```jinja2
{{ render_content_slot('after_content', context={'ort': ort}) }}
```

## Settings-Schema

| Key | Type | Default | Beschreibung |
|-----|------|---------|--------------|
| `default_variant` | select | `card` | Standard-Design für neue CTAs |
| `plattform_name` | string | (leer) | Plattformname für Platzhalter |
| `plattform_zielgruppe` | string | `Café, Restaurant oder Hotel` | Zielgruppe |
| `location_bezeichnung` | string | `Lokal` | Location-Bezeichnung |
| `excluded_blueprints` | textarea | `admin\nauth...` | Ausgeschlossene Blueprints |

## Abhängigkeiten

- **v_flask Core**: Auth, DB, Models, content_slots
- **PageRoute**: Shared Model aus Core

## Datenbank-Schema

```sql
-- CTA Text Templates
CREATE TABLE plugin_cta_template (
    id INTEGER PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    titel VARCHAR(200) NOT NULL,
    beschreibung TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
);

-- CTA Sections
CREATE TABLE plugin_cta_section (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    variant VARCHAR(20) NOT NULL DEFAULT 'card',
    template_id INTEGER REFERENCES plugin_cta_template(id),
    custom_title VARCHAR(200),
    custom_description TEXT,
    cta_text VARCHAR(100),
    cta_link VARCHAR(500),
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
);

-- Page Assignments
CREATE TABLE plugin_cta_assignment (
    id INTEGER PRIMARY KEY,
    cta_section_id INTEGER NOT NULL REFERENCES plugin_cta_section(id),
    page_route_id INTEGER NOT NULL REFERENCES page_route(id),
    slot_position VARCHAR(50) DEFAULT 'after_content',
    priority INTEGER DEFAULT 50,
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    UNIQUE(page_route_id, slot_position)
);
```

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Tabellen-Prefix `plugin_cta_` | Vermeidet Namenskonflikte, klar als Plugin erkennbar |
| PageRoute aus Core | Shared Model mit Hero-Plugin |
| Jinja2 für Platzhalter | Sichere Sandbox, bekannte Syntax |
| Settings für Platzhalter-Werte | Zentrale Konfiguration statt hardcoded Werte |
