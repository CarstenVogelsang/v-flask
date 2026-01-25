# Hero Plugin - Technische Dokumentation

## Architektur-Übersicht

```
hero/
├── __init__.py          # HeroPlugin Manifest, Context Processor
├── models.py            # HeroSection, HeroTemplate, HeroAssignment
├── routes.py            # Admin Blueprint (23KB, umfangreich)
├── slot_provider.py     # Content-Slot Integration
├── services/
│   └── hero_service.py  # Rendering-Logik, Placeholder-Ersetzung
└── templates/
    └── hero/
        ├── admin/       # Admin-Oberfläche
        └── variants/    # Layout-Templates (centered, split, overlay)
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| `HeroSection` | `hero_section` | Hero-Konfiguration mit Variante, Bild, Text, CTA |
| `HeroTemplate` | `hero_template` | Wiederverwendbare Text-Vorlagen |
| `HeroAssignment` | `hero_assignment` | Zuweisung von Hero zu Page + Slot |
| `PageRoute` | `page_route` | (Core) Registrierte Seiten-Endpoints |

### Routes

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/admin/hero/` | GET | Admin | Liste aller Hero Sections |
| `/admin/hero/neu` | GET/POST | Admin | Neue Hero Section erstellen |
| `/admin/hero/<id>` | GET/POST | Admin | Hero Section bearbeiten |
| `/admin/hero/<id>/delete` | POST | Admin | Hero Section löschen |
| `/admin/hero/assignments` | GET | Admin | Seitenzuweisungen verwalten |
| `/admin/hero/templates` | GET | Admin | Text-Templates verwalten |

### Services

| Service | Methode | Beschreibung |
|---------|---------|--------------|
| `hero_service.get_active_hero()` | Liefert aktive Hero Section |
| `hero_service.render_active_hero()` | Rendert Hero als HTML (Legacy) |
| `hero_service.render_hero_slot(endpoint, slot)` | Rendert Hero für Endpoint/Slot |
| `hero_service.render_with_context(hero, context)` | Ersetzt Platzhalter und rendert |

### Templates

| Template | Zweck |
|----------|-------|
| `hero/admin/list.html` | Admin-Liste aller Hero Sections |
| `hero/admin/edit.html` | Bearbeiten-Formular mit Preview |
| `hero/admin/assignments.html` | Seitenzuweisungen |
| `hero/variants/centered.html` | Zentriertes Layout |
| `hero/variants/split.html` | Geteiltes Layout |
| `hero/variants/overlay.html` | Overlay Layout |

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `admin_menu` | `{label: 'Hero Sections', icon: 'ti ti-photo', url: 'hero_admin.list_sections'}` |

## Context Processor

Das Plugin registriert drei Template-Funktionen:

```python
# Legacy: Rendert die "aktive" Hero Section
{{ render_hero_section() }}

# Liefert das Hero-Model (für eigenes Rendering)
{% set hero = get_active_hero() %}

# Neu: Route-basiertes Rendering mit Slot
{{ render_hero_slot('hero_top') }}
```

## Content-Slot-Provider

Ab v1.0 registriert sich das Hero-Plugin als Content-Slot-Provider:

```python
from v_flask import content_slot_registry
from v_flask_plugins.hero.slot_provider import hero_slot_provider
content_slot_registry.register(hero_slot_provider)
```

## Abhängigkeiten

- **v_flask Core**: Auth, DB, Models
- **media Plugin**: Bildverwaltung (Required)
- **content_slots**: Slot-System (Core, Optional für Legacy)

## Datenbank-Schema

```sql
-- Hero Sections
CREATE TABLE hero_section (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    variant VARCHAR(20) NOT NULL DEFAULT 'centered',
    media_id INTEGER REFERENCES media(id),
    image_path VARCHAR(500),  -- Legacy
    template_id INTEGER REFERENCES hero_template(id),
    custom_title VARCHAR(200),
    custom_subtitle TEXT,
    cta_text VARCHAR(100),
    cta_link VARCHAR(500),
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
);

-- Text Templates
CREATE TABLE hero_template (
    id INTEGER PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    titel VARCHAR(200) NOT NULL,
    untertitel TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
);

-- Page Assignments
CREATE TABLE hero_assignment (
    id INTEGER PRIMARY KEY,
    hero_section_id INTEGER NOT NULL REFERENCES hero_section(id),
    page_route_id INTEGER NOT NULL REFERENCES page_route(id),
    slot_position VARCHAR(50) DEFAULT 'hero_top',
    priority INTEGER DEFAULT 100,
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    UNIQUE(page_route_id, slot_position)
);
```

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Media-Plugin statt Direktupload | Zentrale Bildverwaltung, Thumbnails, Stock-Integration |
| PageRoute in Core | Shared Model für Hero, CTA und andere Content-Plugins |
| Jinja2 für Platzhalter | Bekannte Syntax, sichere Sandbox |
| HTMX für Live-Preview | Bessere UX ohne Full-Page-Reload |
