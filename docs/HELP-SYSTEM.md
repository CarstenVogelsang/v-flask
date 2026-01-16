# Hilfesystem

Das v-flask Hilfesystem bietet kontext-sensitive Hilfe für Admin-Editoren und andere UI-Komponenten. Hilfetexte werden als Markdown in der Datenbank gespeichert und können von Plugins bereitgestellt sowie vom Administrator angepasst werden.

## Architektur

```
┌─────────────────────────────────────────────────────────┐
                    Plugin Definition                     
     get_help_texts() → [{schluessel, titel, inhalt}]      
└─────────────────────┬───────────────────────────────────┘
                      │ Seeding bei Plugin-Init
                      ▼
┌─────────────────────────────────────────────────────────┐
                   HelpText Model (DB)                    
  schluessel | titel | inhalt_markdown | aktiv | plugin  
└─────────────────────┬───────────────────────────────────┘
                      │ Context Processor
                      ▼
┌─────────────────────────────────────────────────────────┐
                  Template Integration                    
  get_help_text('impressum.editor') → HelpText           
└─────────────────────────────────────────────────────────┘
```

### Ablauf

1. **Plugin-Definition**: Plugins definieren Default-Hilfetexte in ihrer `get_help_texts()` Methode
2. **Seeding**: Beim Plugin-Init werden Hilfetexte in die Datenbank geschrieben (nur wenn noch nicht vorhanden)
3. **Template-Zugriff**: Via `get_help_text()` Context Processor können Templates Hilfetexte abrufen

## Komponenten

| Komponente | Datei | Beschreibung |
|------------|-------|--------------|
| HelpText Model | `v_flask/models/help_text.py` | SQLAlchemy Model für Hilfetexte |
| Context Processor | `v_flask/__init__.py` | `get_help_text()` Funktion für Templates |
| Plugin Manifest | `v_flask/plugins/manifest.py` | `get_help_texts()` Methode |
| Registry | `v_flask/plugins/registry.py` | `_seed_help_texts()` für Auto-Seeding |
| Macros | `v_flask/templates/v_flask/macros/help.html` | `help_icon()`, `help_modal()` |

## Wo sind Hilfetexte gespeichert?

### Datenbank (Primär)

Hilfetexte werden in der Tabelle `help_text` gespeichert:

```sql
CREATE TABLE help_text (
    id INTEGER PRIMARY KEY,
    schluessel VARCHAR(100) UNIQUE NOT NULL,  -- z.B. 'impressum.editor'
    titel VARCHAR(200) NOT NULL,               -- Modal-Titel
    inhalt_markdown TEXT NOT NULL,             -- Markdown-Inhalt
    aktiv BOOLEAN DEFAULT TRUE,                -- Aktiviert/Deaktiviert
    plugin VARCHAR(50),                        -- Quell-Plugin (optional)
    created_at DATETIME,
    updated_at DATETIME,
    updated_by_id INTEGER                      -- Letzte Bearbeitung
);
```

### Plugin-Defaults (Fallback)

Plugins liefern Default-Hilfetexte mit, die bei Installation automatisch in die Datenbank geseedet werden:

```python
# In v_flask_plugins/impressum/__init__.py
class ImpressumPlugin(PluginManifest):
    def get_help_texts(self):
        return [{
            'schluessel': 'impressum.editor',
            'titel': 'Hilfe zum Impressum',
            'inhalt_markdown': '''## Warum ein Impressum?

Nach **§ 5 TMG** sind geschäftsmäßige Online-Dienste zur Angabe
eines Impressums verpflichtet.

## Disclaimer

**Wichtig:** Dieses Tool ersetzt keine Rechtsberatung.
'''
        }]
```

Das Seeding erfolgt beim Plugin-Init durch `_seed_help_texts()` in der Registry:
- Nur neue Hilfetexte werden erstellt
- Bestehende Einträge werden **nicht** überschrieben (Admin-Anpassungen bleiben erhalten)

## Wie editiert man Hilfetexte?

### Aktueller Stand

> **TODO**: Ein Admin-UI zum Bearbeiten von Hilfetexten existiert noch nicht.

Aktuell können Hilfetexte nur direkt in der Datenbank bearbeitet werden:

```python
# Flask Shell
from v_flask.models import HelpText
from v_flask.extensions import db

# Hilfetext finden und bearbeiten
help_text = HelpText.query.filter_by(schluessel='impressum.editor').first()
help_text.inhalt_markdown = '''## Neuer Inhalt

Hier steht der **angepasste** Hilfetext.
'''
help_text.titel = 'Neuer Titel'
db.session.commit()

# Hilfetext deaktivieren
help_text.aktiv = False
db.session.commit()
```

### Geplantes Admin-UI

Für zukünftige Versionen ist ein Admin-Editor geplant:

- **Pfad**: `/admin/hilfetexte`
- **Funktionen**:
  - Liste aller Hilfetexte (mit Filter nach Plugin)
  - Markdown-Editor mit Live-Vorschau
  - Aktivieren/Deaktivieren einzelner Hilfetexte
  - Reset-Button zum Wiederherstellen des Plugin-Defaults

## Plugin-Integration

### Hilfetexte definieren

Plugins definieren ihre Default-Hilfetexte in der `get_help_texts()` Methode:

```python
from v_flask.plugins import PluginManifest

class MeinPlugin(PluginManifest):
    name = 'mein_plugin'
    version = '1.0.0'
    description = 'Mein tolles Plugin'
    author = 'Ich'

    def get_help_texts(self) -> list[dict]:
        """Return help texts to be seeded when plugin is initialized."""
        return [
            {
                'schluessel': 'mein_plugin.editor',
                'titel': 'Hilfe zum Editor',
                'inhalt_markdown': '''## Überschrift

Hier steht der Hilfetext in **Markdown**.

### Unterabschnitt

- Punkt 1
- Punkt 2
'''
            },
            {
                'schluessel': 'mein_plugin.liste',
                'titel': 'Hilfe zur Liste',
                'inhalt_markdown': '''## Listenansicht

Erklärung der Listenansicht...
'''
            }
        ]
```

### Schlüssel-Konvention

Format: `{plugin_name}.{seite}[.{bereich}]`

| Schlüssel | Beschreibung |
|-----------|--------------|
| `impressum.editor` | Impressum Admin-Editor |
| `datenschutz.editor` | Datenschutz Admin-Editor |
| `kontakt.form` | Öffentliches Kontaktformular |
| `kontakt.admin.liste` | Admin-Anfragenliste |

## Template-Verwendung

### Mit DaisyUI-Modal (empfohlen)

```jinja2
{# Im Template-Header #}
{% set help = get_help_text('impressum.editor') %}

{# Hilfe-Icon in der Titelleiste #}
<h1 class="text-2xl font-bold flex items-center gap-2">
    <i class="ti ti-file-certificate text-primary"></i>
    <span>Impressum Editor</span>
    {% if help and help.aktiv %}
    <button type="button"
            class="btn btn-ghost btn-sm btn-circle"
            onclick="help_modal.showModal()"
            title="Hilfe anzeigen">
        <i class="ti ti-help text-base-content/60 text-lg"></i>
    </button>
    {% endif %}
</h1>

{# Modal am Ende des Templates #}
{% if help and help.aktiv %}
<dialog id="help_modal" class="modal">
    <div class="modal-box max-w-2xl">
        <form method="dialog">
            <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
        </form>
        <h3 class="font-bold text-lg flex items-center gap-2 mb-4">
            <i class="ti ti-help-circle text-info"></i>
            {{ help.titel }}
        </h3>
        <div class="prose prose-sm max-w-none">
            {{ help.inhalt_markdown|markdown|safe }}
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endif %}
```

### Mit Bootstrap-Macro (veraltet)

> **Hinweis**: Das bestehende `help_icon` Macro in `v_flask/macros/help.html` verwendet Bootstrap-Syntax und ist nicht mit DaisyUI kompatibel.

```jinja2
{% from "v_flask/macros/help.html" import help_icon with context %}

<h2>
    Branchen {{ help_icon('kunden.detail.branchen', 'Hilfe zu Branchen') }}
</h2>
```

## Beispiele

### Aktuelle Verwendung

| Plugin | Schlüssel | Verwendung |
|--------|-----------|------------|
| Impressum | `impressum.editor` | Admin-Editor mit Pflichtangaben und Disclaimer |
| Datenschutz | `datenschutz.editor` | Admin-Editor mit DSGVO-Informationen |

### Hilfetext-Inhalt (Best Practice)

```markdown
## Warum ist das wichtig?

Kurze Erklärung des rechtlichen oder fachlichen Hintergrunds.

## Was muss ich ausfüllen?

- **Pflichtfeld 1** - Beschreibung
- **Pflichtfeld 2** - Beschreibung

## Tipps

Praktische Hinweise zur Verwendung.

## Disclaimer

**Wichtig:** Dieses Tool unterstützt Sie bei der Erstellung,
ersetzt jedoch keine Rechtsberatung. Für die rechtliche
Korrektheit übernehmen wir keine Haftung.
```

## Offene To-dos

### Kritisch (fehlende Funktionalität)

| To-do | Beschreibung | Priorität |
|-------|--------------|-----------|
| Admin-Editor | UI unter `/admin/hilfetexte` zum Bearbeiten | Hoch |
| Reset-Funktion | Plugin-Defaults wiederherstellen können | Mittel |

### Verbesserungen

| To-do | Beschreibung | Priorität |
|-------|--------------|-----------|
| DaisyUI-Macro | `help.html` Macro auf DaisyUI umstellen | Mittel |
| CLI-Command | `flask help-texts list/reset` für Entwickler | Niedrig |
| Export/Import | Hilfetexte als JSON exportieren/importieren | Niedrig |

## Verwandte Dokumentation

- [PLUGINS.md](PLUGINS.md) - Plugin-System Übersicht
- [ARCHITECTURE.md](ARCHITECTURE.md) - v-flask Architektur
- [TEMPLATES.md](TEMPLATES.md) - Template-System und Macros
