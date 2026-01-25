# Content-Slots System

Das Content-Slots System ermöglicht die dynamische Zuweisung von Inhalten zu definierten Positionen (Slots) auf Seiten. Im Gegensatz zu UI-Slots (für Navigation, Admin-Menüs) werden Content-Slots für seitenspezifische Inhalte wie Hero-Sections, CTAs oder Banner verwendet.

## Übersicht

### UI-Slots vs. Content-Slots

| Typ | Beschreibung | Beispiele |
|-----|--------------|-----------|
| **UI-Slots** | Statische UI-Elemente | Admin-Menü, Footer-Links |
| **Content-Slots** | Dynamische Seiteninhalte | Hero-Sections, CTA-Banner |

### Verfügbare Content-Slots

| Slot | Position | Typische Nutzer |
|------|----------|-----------------|
| `top` | Hauptbereich oben | Hero-Sections |
| `before_content` | Vor dem Hauptinhalt | Announcements |
| `after_content` | Nach dem Hauptinhalt | CTA-Boxen |
| `sidebar` | Seitenleiste | Widgets, CTAs |
| `floating` | Fixed-Position | Floating CTAs |
| `footer` | Im Footer-Bereich | Links, Mini-CTAs |

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                     v-flask Core                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              content_slots Module                    │   │
│  │  - ContentSlotRegistry                               │   │
│  │  - ContentSlotProvider (Abstract)                    │   │
│  │  - PageRoute Model                                   │   │
│  │  - render_content_slot() Context Processor           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ▲
              ┌───────────────┼───────────────┐
              │               │               │
      ┌───────┴───────┐ ┌─────┴─────┐ ┌───────┴───────┐
      │  Hero-Plugin  │ │CTA-Plugin │ │ Future Plugin │
      │  (priority=100)│ │(priority=50)│ │               │
      └───────────────┘ └───────────┘ └───────────────┘
              │               │
              └───────┬───────┘
                      ▼
              ┌───────────────┐
              │   PageRoute   │
              │  (gemeinsam)  │
              └───────────────┘
```

## ContentSlotProvider implementieren

Plugins können sich als Content-Provider für Slots registrieren:

```python
from v_flask.content_slots import ContentSlotProvider

class MeinSlotProvider(ContentSlotProvider):
    """Provider für meine Content-Slots."""

    name = 'mein_provider'
    priority = 75  # Höher = wird bevorzugt
    slots = ['after_content', 'sidebar']  # Unterstützte Slots

    def render(self, endpoint: str, slot: str, context: dict) -> str | None:
        """Rendert den Inhalt für einen Slot.

        Args:
            endpoint: Flask-Endpoint (z.B. 'public.index')
            slot: Slot-Position (z.B. 'after_content')
            context: Template-Kontext mit zusätzlichen Daten

        Returns:
            HTML-String oder None wenn kein Inhalt.
        """
        # Prüfen ob Zuweisung existiert
        assignment = self.get_assignment(endpoint, slot)
        if not assignment:
            return None

        # Inhalt rendern
        return render_template('mein_plugin/content.html', ...)

    def can_render(self, endpoint: str, slot: str) -> bool:
        """Schnelle Prüfung ob Provider für Slot zuständig sein könnte."""
        return slot in self.slots
```

## Provider registrieren

Im `on_init()` Hook des Plugins:

```python
class MeinPlugin(PluginManifest):
    def on_init(self, app):
        from v_flask import content_slot_registry
        from .slot_provider import mein_slot_provider

        content_slot_registry.register(mein_slot_provider)
```

## Template-Verwendung

### render_content_slot()

Die Funktion `render_content_slot()` wird automatisch als Context Processor bereitgestellt:

```jinja2
{# In jedem Template verfügbar #}
{{ render_content_slot('after_content', context={'ort': ort, 'kreis': kreis}) }}
```

**Parameter:**
- `slot`: Name des Slots (z.B. `'after_content'`)
- `context`: Optionaler Kontext für Platzhalter-Rendering

### Beispiel: Kreis-Seite

```jinja2
{% extends "base.html" %}

{% block content %}
    {# Hero-Slot am Seitenanfang #}
    {{ render_content_slot('top') }}

    <h1>Frühstücken in {{ kreis.name }}</h1>

    {# Locations anzeigen #}
    {% for location in locations %}
        {% include 'partials/location_card.html' %}
    {% endfor %}

    {# CTA nach dem Content #}
    {{ render_content_slot('after_content', context={'kreis': kreis}) }}
{% endblock %}
```

## PageRoute-Model

Das `PageRoute`-Model speichert alle verfügbaren Routen der Anwendung:

```python
class PageRoute(db.Model):
    __tablename__ = 'page_route'

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), unique=True, nullable=False)
    rule = db.Column(db.String(500))
    blueprint = db.Column(db.String(100))
    display_name = db.Column(db.String(200))
    hero_assignable = db.Column(db.Boolean, default=True)  # = slot_assignable
```

### Routen synchronisieren

Der `RouteSyncService` synchronisiert Flask-Routen mit der Datenbank:

```python
from v_flask.content_slots.service import RouteSyncService

service = RouteSyncService()
service.sync_routes()  # Synchronisiert alle Routen
```

## Prioritäten

Wenn mehrere Provider für denselben Slot Content liefern könnten, gewinnt der mit der höchsten Priorität:

| Plugin | Priorität | Typische Slots |
|--------|-----------|----------------|
| Hero | 100 | `top` |
| CTA | 50 | `after_content`, `floating`, `sidebar` |
| Banner | 75 | `before_content`, `after_content` |

## Bestehende Provider

### Hero-Plugin

- **Slot:** `top`
- **Priorität:** 100
- **Features:** Drei Varianten (Centered, Split, Overlay), Media-Integration

```jinja2
{{ render_content_slot('top') }}
```

### CTA-Plugin

- **Slots:** `after_content`, `floating`, `sidebar`, `before_content`, `footer`
- **Priorität:** 50
- **Features:** Drei Designs (Card, Alert, Floating), Jinja2-Platzhalter

```jinja2
{{ render_content_slot('after_content', context={'ort': ort}) }}
```

## Migration von Include zu Slots

### Vorher (statisches Include)

```jinja2
{% if locations %}
    {% include 'partials/cta_add_location.html' %}
{% else %}
    {% include 'partials/cta_no_locations.html' %}
{% endif %}
```

### Nachher (dynamische Slots)

```jinja2
{# Ein Aufruf, Admin wählt den passenden CTA #}
{{ render_content_slot('after_content', context={'kreis': kreis}) }}
```

**Vorteile:**
- Kein Template-Code-Änderung bei CTA-Wechsel
- Admins können CTAs per UI zuweisen
- Unterschiedliche CTAs pro Seite möglich

## CLI-Befehle

```bash
# Routen synchronisieren
flask routes sync

# Routen-Status anzeigen
flask routes list
```

## Fehlerbehebung

### "Kein Content in Slot"

1. Prüfen ob ein Provider registriert ist
2. Prüfen ob eine Zuweisung für Route + Slot existiert
3. Prüfen ob die zugewiesene Section aktiv ist

### "Provider nicht registriert"

Sicherstellen dass das Plugin vor `init_app()` registriert wird:

```python
v_flask.register_plugin(CtaPlugin())  # ERST registrieren
v_flask.init_app(app)                 # DANN initialisieren
```