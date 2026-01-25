# Content Plugin - Technische Dokumentation

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                        Admin UI                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ List     │  │ Wizard   │  │ Edit     │  │ Assign           │ │
│  │ Blocks   │  │ Step 1-3 │  │ Block    │  │ to Pages         │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Services                                  │
│  ┌──────────────────┐       ┌──────────────────┐                │
│  │ ContentService   │       │ SnippetService   │                │
│  │ - render_slot()  │       │ - get_snippets() │                │
│  │ - get_layouts()  │       │ - create()       │                │
│  └──────────────────┘       └──────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Models                                    │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │ ContentBlock │  │ ContentAssignment │  │ TextSnippet       │  │
│  │ (content)    │──│ (page binding)    │  │ (reusable texts)  │  │
│  └──────────────┘  └──────────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Content Slots                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ContentSlotProvider                                       │   │
│  │ - slots: ['before_content', 'after_content', 'sidebar']  │   │
│  │ - priority: 40                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| ContentBlock | `content_block` | Inhaltsbaustein mit Intention, Layout und Daten |
| ContentAssignment | `content_assignment` | Verknüpfung Block ↔ PageRoute |
| TextSnippet | `content_text_snippet` | Wiederverwendbare Textbausteine |

### Routes

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/admin/content/` | GET | Admin | Baustein-Liste |
| `/admin/content/neu` | GET | Admin | Wizard Step 1 |
| `/admin/content/neu/<intention>` | GET | Admin | Wizard Step 2 |
| `/admin/content/neu/<intention>/<layout>` | GET | Admin | Wizard Step 3 |
| `/admin/content/speichern` | POST | Admin | Baustein speichern |
| `/admin/content/<id>/bearbeiten` | GET | Admin | Baustein bearbeiten |
| `/admin/content/<id>/zuweisen` | GET | Admin | Seitenzuweisung |
| `/admin/content/textbausteine` | GET | Admin | Textbausteine verwalten |
| `/admin/content/api/snippets` | GET | Admin | API: Snippets laden |
| `/admin/content/api/layouts/<intention>` | GET | Admin | API: Layouts für Intention |

### Templates

| Template | Zweck |
|----------|-------|
| `content/admin/list.html` | Admin-Übersicht aller Bausteine |
| `content/admin/create_step1.html` | Wizard: Intention wählen |
| `content/admin/create_step2.html` | Wizard: Layout wählen |
| `content/admin/create_step3.html` | Wizard: Inhalte eingeben |
| `content/admin/edit.html` | Baustein bearbeiten |
| `content/admin/assign.html` | Seitenzuweisung |
| `content/layouts/banner_text.html` | Rendering: Banner + Text |
| `content/layouts/bild_links.html` | Rendering: Bild links |
| `content/layouts/bild_rechts.html` | Rendering: Bild rechts |
| `content/layouts/nur_text.html` | Rendering: Nur Text |

## Datenstrukturen

### ContentBlock.content_data (JSON)

```json
{
  "titel": "Über uns",
  "text": "Wir sind ein...",
  "bilder": [
    {"media_id": 42, "position": 0}
  ]
}
```

### intentions.json

```json
[
  {
    "id": "ueber_uns",
    "name": "Über uns",
    "beschreibung": "Stellen Sie Ihr Unternehmen vor",
    "icon": "ti-users",
    "layouts": ["banner_text", "bild_links", "bild_rechts", "nur_text"]
  }
]
```

### layouts.json

```json
[
  {
    "id": "bild_links",
    "name": "Bild links, Text rechts",
    "beschreibung": "Bild auf der linken Seite, Text rechts daneben",
    "icon": "ti-layout-sidebar-left-collapse",
    "felder": ["bild", "titel", "text"],
    "template": "layouts/bild_links.html"
  }
]
```

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| admin_menu | Label: "Inhaltsbausteine", Icon: ti-layout-grid |
| admin_dashboard_widgets | Color: #8b5cf6 |

## Abhängigkeiten

- **v-flask Core:** Auth, DB, Content Slots, PageRoute
- **Media Plugin:** Für Bildauswahl und -darstellung

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Template-basiert statt WYSIWYG | Konsistentes Design, einfachere Bedienung |
| JSON für content_data | Flexibilität bei Layout-spezifischen Feldern |
| Snippets in JSON-Dateien | Einfache Pflege, Git-versionierbar |
| Separate Assignment-Tabelle | Ermöglicht n:m ohne Redundanz |
| Priority 40 im Slot-System | Niedriger als Hero (100) und CTA (50) |

## Slot-Integration

Der `ContentSlotProvider` registriert sich beim App-Start:

```python
# in __init__.py on_init()
from v_flask import content_slot_registry
from v_flask_plugins.content.slot_provider import content_slot_provider
content_slot_registry.register(content_slot_provider)
```

Unterstützte Slots:
- `before_content` - Vor dem Hauptinhalt
- `after_content` - Nach dem Hauptinhalt
- `sidebar` - Sidebar-Bereich
