# Plugin-Entwicklung für KI-Agenten

Diese Dokumentation richtet sich an KI-Agenten (Claude Code), die v-flask Plugins entwickeln sollen.

## Quick-Start Checkliste

Beim Erstellen eines neuen Plugins MÜSSEN folgende Schritte durchgeführt werden:

```
□ 1. Plugin-Verzeichnis erstellen unter src/v_flask_plugins/<name>/
□ 2. __init__.py mit PluginManifest-Klasse erstellen
□ 3. Models definieren (Tabellen-Prefix: <name>_ verwenden)
□ 4. Blueprints erstellen (public + admin)
□ 5. Templates erstellen mit CSRF-Token in allen Formularen
□ 6. UI-Slots konfigurieren (footer_links, admin_menu, admin_dashboard_widgets)
□ 7. Plugin in plugins_marketplace.json eintragen
□ 8. docs/ Ordner mit SPEC.md, TECH.md, PROGRESS.md erstellen
□ 9. Testen: Plugin über Admin-UI aktivieren
```

---

## Pflicht-Regeln

### CSRF-Schutz (KRITISCH)

**Jedes HTML-Formular mit `method="post"` MUSS ein CSRF-Token enthalten:**

```html
<form action="{{ url_for('mein_plugin_admin.aktion') }}" method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- Formular-Felder -->
    <button type="submit">Speichern</button>
</form>
```

**AJAX-Requests MÜSSEN den CSRF-Token im Header senden:**

```javascript
fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
    },
    body: JSON.stringify(data)
});
```

### Lazy Imports

**Imports in `get_models()` und `get_blueprints()` MÜSSEN lazy sein:**

```python
# RICHTIG - Lazy Import innerhalb der Methode
def get_models(self):
    from .models import MeinModel
    return [MeinModel]

# FALSCH - Import auf Modul-Ebene
from .models import MeinModel  # Verursacht zirkuläre Imports!
```

### Permission-Schutz

**Alle Admin-Routes MÜSSEN geschützt sein:**

```python
from v_flask.auth import permission_required, admin_required

@mein_admin_bp.route('/liste')
@permission_required('mein_plugin.view')
def liste():
    ...

@mein_admin_bp.route('/bearbeiten/<int:id>', methods=['POST'])
@admin_required  # Oder spezifische Permission
def bearbeiten(id):
    ...
```

---

## Plugin-Struktur (Vorlage)

```
src/v_flask_plugins/mein_plugin/
├── __init__.py          # PluginManifest + Export
├── models.py            # SQLAlchemy Models
├── routes.py            # Blueprints (public + admin)
├── services.py          # Business Logic (optional)
├── docs/                # Plugin-Dokumentation (PFLICHT)
│   ├── SPEC.md          # Anforderungen, User Stories
│   ├── TECH.md          # Technische Architektur
│   └── PROGRESS.md      # Phasen, Changelog
└── templates/
    └── mein_plugin/
        ├── public/      # Öffentliche Seiten
        │   └── index.html
        └── admin/       # Admin-Bereich
            ├── liste.html
            └── bearbeiten.html
```

---

## Plugin-Dokumentation (Pflicht)

Jedes Plugin MUSS einen `docs/` Ordner mit drei Dokumenten führen:

| Datei | Zweck | Aktualisieren |
|-------|-------|---------------|
| `SPEC.md` | Was soll das Plugin tun? (User Stories, Anforderungen) | Bei Scope-Änderungen |
| `TECH.md` | Wie ist es umgesetzt? (Architektur, Entscheidungen) | Bei Code-Änderungen |
| `PROGRESS.md` | Aktueller Stand (Phasen POC→MVP→V1, Changelog) | **Bei JEDER Änderung** |

### Phasen-Modell

| Phase | Ziel | Typische Aufgaben |
|-------|------|-------------------|
| **POC** | Grundfunktion nachweisen | Plugin-Struktur, Basis-Model, erste Route |
| **MVP** | Nutzbar für erste User | CRUD komplett, Validierung, UI-Slots |
| **V1** | Production-ready | Error Handling, Tests, Performance |

### Template: docs/SPEC.md

```markdown
# [Plugin-Name] - Spezifikation

## Übersicht
[1-2 Sätze: Was macht dieses Plugin?]

## Zielgruppe
- [Wer nutzt das Plugin?]

## User Stories
- Als [Rolle] möchte ich [Funktion], damit [Nutzen]
- ...

## Funktionale Anforderungen
| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | [Beschreibung] | Must | POC |
| F2 | [Beschreibung] | Should | MVP |

## Nicht-funktionale Anforderungen
- Performance: [z.B. < 100ms Antwortzeit]
- Sicherheit: [z.B. Admin-only]

## Abgrenzung (Out of Scope)
- [Was das Plugin NICHT tut]
```

### Template: docs/TECH.md

```markdown
# [Plugin-Name] - Technische Dokumentation

## Architektur-Übersicht
[Komponenten-Diagramm in ASCII oder Mermaid]

## Komponenten

### Models
| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| [Name] | [prefix_name] | [Zweck] |

### Routes
| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| /admin/[name]/ | GET | Admin | [Zweck] |

### Templates
| Template | Zweck |
|----------|-------|
| [name]/admin/list.html | Admin-Übersicht |

## UI-Slots
| Slot | Konfiguration |
|------|---------------|
| admin_menu | {name, icon, url} |

## Abhängigkeiten
- v-flask Core (Auth, DB)
- [Weitere Plugins falls nötig]

## Technische Entscheidungen
| Entscheidung | Begründung |
|--------------|------------|
| [z.B. Soft Delete statt Hard Delete] | [Warum] |
```

### Template: docs/PROGRESS.md

```markdown
# [Plugin-Name] - Fortschritt

## Aktuelle Phase: POC

## Phasen-Übersicht

### Phase 1: POC (Proof of Concept)
**Ziel:** Grundfunktion nachweisen

- [ ] Plugin-Struktur erstellt
- [ ] Basis-Model definiert
- [ ] Admin-Route funktioniert
- [ ] Erstes Template rendert

**Status:** 🟡 In Arbeit

### Phase 2: MVP (Minimum Viable Product)
**Ziel:** Nutzbar für erste User

- [ ] CRUD komplett
- [ ] Validierung implementiert
- [ ] UI-Slots konfiguriert
- [ ] CSRF-Schutz verifiziert

**Status:** ⚪ Nicht begonnen

### Phase 3: V1 (Erste Release-Version)
**Ziel:** Production-ready

- [ ] Error Handling
- [ ] Tests geschrieben
- [ ] Dokumentation vollständig
- [ ] Performance optimiert

**Status:** ⚪ Nicht begonnen

---

## Changelog

### [DATUM] - POC gestartet
- ✅ Plugin-Struktur angelegt
- ✅ [Was wurde umgesetzt]
```

### Anweisungen für KI-Agenten

**Bei Plugin-Erstellung:**
1. Erstelle `docs/` Ordner im Plugin-Verzeichnis
2. Erstelle alle drei Dateien mit den Templates oben
3. Fülle SPEC.md basierend auf User-Anforderungen
4. Setze PROGRESS.md auf "Phase 1: POC"

**Bei Plugin-Änderungen:**
1. Lies zuerst `docs/PROGRESS.md` um aktuellen Stand zu verstehen
2. Führe Code-Änderungen durch
3. Aktualisiere `docs/PROGRESS.md`:
   - Hake erledigte Tasks ab (`- [x]`)
   - Füge Changelog-Eintrag mit Datum hinzu
   - Aktualisiere Phase-Status falls nötig
4. Aktualisiere `docs/TECH.md` bei Architektur-Änderungen

---

## Komplette Plugin-Vorlage (Copy-Paste)

### `__init__.py`

```python
"""Mein Plugin - Kurze Beschreibung."""
from pathlib import Path
from v_flask.plugins import PluginManifest


class MeinPlugin(PluginManifest):
    """Plugin für XYZ-Funktionalität."""

    # Pflicht-Metadaten
    name = 'mein_plugin'
    version = '1.0.0'
    description = 'Kurze Beschreibung des Plugins'
    author = 'v-flask'

    # Optional: Marketplace-Metadaten
    license = 'MIT'
    categories = ['forms', 'admin']  # Kategorien für Filterung
    tags = ['beispiel', 'demo']      # Schlagwörter
    min_v_flask_version = '1.0.0'

    # Optional: Abhängigkeiten
    dependencies = []  # z.B. ['auth', 'email']

    # Admin-Navigation
    admin_category = 'general'  # Kategorie in Admin-Sidebar

    # UI-Slots für automatische Integration
    ui_slots = {
        'footer_links': [
            {
                'label': 'Mein Link',
                'url': 'mein_plugin.public_index',
                'icon': 'ti ti-star',
                'order': 100,
            }
        ],
        'admin_menu': [
            {
                'label': 'Mein Plugin',
                'url': 'mein_plugin_admin.liste',
                'icon': 'ti ti-list',
                'permission': 'admin.*',
                'order': 50,
            }
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Mein Plugin',
                'description': 'Verwaltung von XYZ',
                'url': 'mein_plugin_admin.liste',
                'icon': 'ti-star',
                'color_hex': '#6366f1',
            }
        ],
    }

    def get_models(self):
        """SQLAlchemy Models zurückgeben (Lazy Import!)."""
        from .models import MeinModel
        return [MeinModel]

    def get_blueprints(self):
        """Blueprints mit URL-Prefix zurückgeben (Lazy Import!)."""
        from .routes import mein_bp, mein_admin_bp
        return [
            (mein_bp, '/mein-plugin'),
            (mein_admin_bp, '/admin/mein-plugin'),
        ]

    def get_template_folder(self):
        """Template-Verzeichnis zurückgeben."""
        return Path(__file__).parent / 'templates'

    def on_init(self, app):
        """Wird beim App-Start aufgerufen."""
        app.logger.info(f'Plugin {self.name} v{self.version} initialisiert')
```

### `models.py`

```python
"""Datenbank-Models für Mein Plugin."""
from datetime import datetime
from v_flask import db


class MeinModel(db.Model):
    """Beispiel-Model."""

    __tablename__ = 'mein_plugin_eintraege'  # Prefix: mein_plugin_

    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(200), nullable=False)
    inhalt = db.Column(db.Text)
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    aktualisiert_am = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MeinModel {self.id}: {self.titel}>'
```

### `routes.py`

```python
"""Routes für Mein Plugin."""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from v_flask.auth import permission_required

# Public Blueprint
mein_bp = Blueprint(
    'mein_plugin',
    __name__,
    template_folder='templates'
)

# Admin Blueprint
mein_admin_bp = Blueprint(
    'mein_plugin_admin',
    __name__,
    template_folder='templates'
)


# === Public Routes ===

@mein_bp.route('/')
def public_index():
    """Öffentliche Startseite."""
    return render_template('mein_plugin/public/index.html')


# === Admin Routes ===

@mein_admin_bp.route('/')
@permission_required('admin.*')
def liste():
    """Admin-Liste aller Einträge."""
    from .models import MeinModel
    eintraege = MeinModel.query.order_by(MeinModel.erstellt_am.desc()).all()
    return render_template(
        'mein_plugin/admin/liste.html',
        eintraege=eintraege
    )


@mein_admin_bp.route('/neu', methods=['GET', 'POST'])
@permission_required('admin.*')
def neu():
    """Neuen Eintrag erstellen."""
    if request.method == 'POST':
        from .models import MeinModel
        from v_flask import db

        eintrag = MeinModel(
            titel=request.form['titel'],
            inhalt=request.form.get('inhalt', '')
        )
        db.session.add(eintrag)
        db.session.commit()

        flash('Eintrag erfolgreich erstellt.', 'success')
        return redirect(url_for('mein_plugin_admin.liste'))

    return render_template('mein_plugin/admin/bearbeiten.html', eintrag=None)


@mein_admin_bp.route('/<int:id>/bearbeiten', methods=['GET', 'POST'])
@permission_required('admin.*')
def bearbeiten(id):
    """Eintrag bearbeiten."""
    from .models import MeinModel
    from v_flask import db

    eintrag = MeinModel.query.get_or_404(id)

    if request.method == 'POST':
        eintrag.titel = request.form['titel']
        eintrag.inhalt = request.form.get('inhalt', '')
        db.session.commit()

        flash('Eintrag erfolgreich aktualisiert.', 'success')
        return redirect(url_for('mein_plugin_admin.liste'))

    return render_template('mein_plugin/admin/bearbeiten.html', eintrag=eintrag)


@mein_admin_bp.route('/<int:id>/loeschen', methods=['POST'])
@permission_required('admin.*')
def loeschen(id):
    """Eintrag löschen."""
    from .models import MeinModel
    from v_flask import db

    eintrag = MeinModel.query.get_or_404(id)
    db.session.delete(eintrag)
    db.session.commit()

    flash('Eintrag erfolgreich gelöscht.', 'success')
    return redirect(url_for('mein_plugin_admin.liste'))
```

### `templates/mein_plugin/admin/liste.html`

```html
{% extends "v_flask/admin/base.html" %}

{% block title %}Mein Plugin - Liste{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs text-sm">
    <ul>
        <li><a href="{{ url_for('admin.dashboard') }}">Dashboard</a></li>
        <li>Mein Plugin</li>
    </ul>
</div>
{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">Mein Plugin</h1>
    <a href="{{ url_for('mein_plugin_admin.neu') }}" class="btn btn-primary">
        <i class="ti ti-plus mr-2"></i>
        Neuer Eintrag
    </a>
</div>

<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Titel</th>
                    <th>Erstellt</th>
                    <th>Aktionen</th>
                </tr>
            </thead>
            <tbody>
                {% for eintrag in eintraege %}
                <tr>
                    <td>{{ eintrag.id }}</td>
                    <td>{{ eintrag.titel }}</td>
                    <td>{{ eintrag.erstellt_am.strftime('%d.%m.%Y %H:%M') }}</td>
                    <td>
                        <a href="{{ url_for('mein_plugin_admin.bearbeiten', id=eintrag.id) }}"
                           class="btn btn-sm btn-ghost">
                            <i class="ti ti-edit"></i>
                        </a>
                        <form action="{{ url_for('mein_plugin_admin.loeschen', id=eintrag.id) }}"
                              method="post" class="inline">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <button type="submit" class="btn btn-sm btn-ghost text-error"
                                    onclick="return confirm('Wirklich löschen?')">
                                <i class="ti ti-trash"></i>
                            </button>
                        </form>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="4" class="text-center text-gray-500">
                        Keine Einträge vorhanden.
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

### `templates/mein_plugin/admin/bearbeiten.html`

```html
{% extends "v_flask/admin/base.html" %}

{% block title %}
{{ 'Bearbeiten' if eintrag else 'Neu' }} - Mein Plugin
{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs text-sm">
    <ul>
        <li><a href="{{ url_for('admin.dashboard') }}">Dashboard</a></li>
        <li><a href="{{ url_for('mein_plugin_admin.liste') }}">Mein Plugin</a></li>
        <li>{{ 'Bearbeiten' if eintrag else 'Neu' }}</li>
    </ul>
</div>
{% endblock %}

{% block content %}
<div class="card bg-base-100 shadow-xl max-w-2xl">
    <div class="card-body">
        <h2 class="card-title mb-4">
            {{ 'Eintrag bearbeiten' if eintrag else 'Neuer Eintrag' }}
        </h2>

        <form method="post">
            {# CSRF-Token - PFLICHT für alle POST-Formulare! #}
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

            <div class="form-control mb-4">
                <label class="label">
                    <span class="label-text">Titel *</span>
                </label>
                <input type="text" name="titel"
                       value="{{ eintrag.titel if eintrag else '' }}"
                       class="input input-bordered" required>
            </div>

            <div class="form-control mb-6">
                <label class="label">
                    <span class="label-text">Inhalt</span>
                </label>
                <textarea name="inhalt" rows="5"
                          class="textarea textarea-bordered">{{ eintrag.inhalt if eintrag else '' }}</textarea>
            </div>

            <div class="flex gap-2">
                <button type="submit" class="btn btn-primary">
                    <i class="ti ti-check mr-2"></i>
                    Speichern
                </button>
                <a href="{{ url_for('mein_plugin_admin.liste') }}" class="btn btn-ghost">
                    Abbrechen
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
```

---

## Admin Template UI Guidelines

Dieser Abschnitt beschreibt die verbindlichen UI-Standards für alle Admin-Templates in v-flask.

### Admin View Layout Pattern

Jede Admin-Seite **MUSS** diesem Layout-Pattern folgen:

```
┌──────────────────────────────────────────────────────────────────┐
│ Breadcrumb: Dashboard > [Section] > [Current Page]               │
├──────────────────────────────────────────────────────────────────┤
│ Titel (h1)                              [Action Buttons]         │
├──────────────────────────────────────────────────────────────────┤
│ [Optional: Filter/Search Row]                                    │
├──────────────────────────────────────────────────────────────────┤
│ [Content Area]                                                   │
│ - Card mit Tabelle (Liste)                                       │
│ - Card mit Formular (Bearbeiten)                                 │
│ - Statistik-Karten (Dashboard)                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Pflicht-Elemente

| Element | Block | Pflicht | Beschreibung |
|---------|-------|---------|--------------|
| Base Template | - | ✅ | `{% extends "v_flask/admin/base.html" %}` |
| Breadcrumbs | `breadcrumbs` | ✅ | Navigation zur aktuellen Seite |
| Titel (h1) | `content` | ✅ | Seitentitel mit optionalen Action-Buttons |
| Content | `content` | ✅ | Hauptinhalt in DaisyUI-Cards |

### CSS Framework: DaisyUI (NICHT Bootstrap!)

**WICHTIG:** v-flask verwendet **DaisyUI** als CSS-Framework. Bootstrap-Klassen dürfen **NICHT** verwendet werden!

| Komponente | DaisyUI ✅ | Bootstrap ❌ |
|------------|-----------|-------------|
| Button | `btn btn-primary` | `btn btn-primary` |
| Button Outline | `btn btn-outline btn-primary` | `btn btn-outline-primary` |
| Card | `card bg-base-100 shadow-xl` | `card` |
| Card Body | `card-body` | `card-body` |
| Table | `table` | `table table-striped` |
| Badge Success | `badge badge-success` | `badge bg-success` |
| Badge Warning | `badge badge-warning` | `badge bg-warning` |
| Flex Container | `flex gap-2` | `d-flex gap-2` |
| Justify Between | `justify-between` | `justify-content-between` |
| Align Center | `items-center` | `align-items-center` |
| Alert | `alert alert-success` | `alert alert-success` |

### Template-Struktur (Referenz)

```html
{% extends "v_flask/admin/base.html" %}

{% block title %}Seitentitel{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs text-sm">
    <ul>
        <li><a href="{{ url_for('admin.dashboard') }}">Dashboard</a></li>
        <li><a href="{{ url_for('mein_plugin_admin.liste') }}">Mein Plugin</a></li>
        <li>Aktuelle Seite</li>
    </ul>
</div>
{% endblock %}

{% block content %}
{# Titelzeile mit Action-Buttons #}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">Seitentitel</h1>
    <div class="flex gap-2">
        <a href="..." class="btn btn-primary">
            <i class="ti ti-plus mr-2"></i>Neu
        </a>
    </div>
</div>

{# Hauptinhalt in Card #}
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        {# Tabelle, Formular, etc. #}
    </div>
</div>
{% endblock %}
```

### Warum ist das wichtig?

1. **Konsistenz:** Alle Admin-Seiten sehen gleich aus (Sidebar, Breadcrumbs, Layout)
2. **Navigation:** Die Admin-Sidebar wird automatisch eingebunden
3. **Styling:** DaisyUI-Themes funktionieren nur mit DaisyUI-Klassen
4. **Wartbarkeit:** Einheitliche Struktur erleichtert die Fehlersuche

### CSRF-Schutz für Formulare

**WICHTIG:** Alle POST-Formulare MÜSSEN CSRF-Schutz haben!

#### HTMX-Formulare (automatisch geschützt)

Formulare mit `hx-post` senden das CSRF-Token automatisch über den HTTP-Header `X-CSRFToken`, der aus dem Meta-Tag gelesen wird:

```html
<form hx-post="{{ url_for('mein_plugin_admin.save') }}"
      hx-target="#result">
    {# CSRF wird automatisch als Header gesendet #}
    <input type="text" name="feld" ...>
    <button type="submit">Speichern</button>
</form>
```

#### Normale POST-Formulare (Include erforderlich)

Formulare mit `method="post"` (ohne HTMX) benötigen das CSRF-Token als Hidden-Field:

```html
<form method="post" action="{{ url_for('mein_plugin_admin.save') }}">
    {% include 'v_flask/includes/_csrf.html' %}
    <input type="text" name="feld" ...>
    <button type="submit">Speichern</button>
</form>
```

Das Include `v_flask/includes/_csrf.html` fügt folgendes ein:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

#### Wann welche Methode?

| Formular-Typ | CSRF-Methode | Beispiel |
|--------------|--------------|----------|
| HTMX (`hx-post`) | Automatisch via Header | Admin-Formulare mit Live-Update |
| Normal (`method="post"`) | Include erforderlich | Stock-Import, öffentliche Formulare |
| JavaScript/Fetch | Header manuell setzen | `X-CSRFToken: document.querySelector('meta[name="csrf-token"]').content` |

---

## UI-Slot-System

UI-Slots ermöglichen die automatische Integration von Plugin-Elementen in die Host-App ohne Template-Änderungen.

### Verfügbare Slots

| Slot | Beschreibung | Verwendung |
|------|--------------|------------|
| `footer_links` | Links im Footer | Öffentliche Seiten (Kontakt, Impressum) |
| `admin_menu` | Einträge im Admin-Sidebar | Admin-Navigation |
| `admin_dashboard_widgets` | Karten auf dem Admin-Dashboard | Schnellzugriff auf Plugin |

### Slot-Konfiguration

```python
ui_slots = {
    'footer_links': [
        {
            'label': 'Kontakt',           # Angezeigter Text
            'url': 'kontakt.form',        # Flask url_for() Endpunkt
            'icon': 'ti ti-mail',         # Tabler Icon Klasse
            'order': 100,                 # Sortierung (niedriger = weiter oben)
        }
    ],
    'admin_menu': [
        {
            'label': 'Kontakt-Anfragen',
            'url': 'kontakt_admin.list_anfragen',
            'icon': 'ti ti-inbox',
            'permission': 'admin.*',      # Berechtigung (optional)
            'order': 10,
            'badge_func': 'get_unread_count',  # Funktion für Badge (optional)
        }
    ],
    'admin_dashboard_widgets': [
        {
            'name': 'Kontakt',            # Widget-Titel
            'description': 'Anfragen verwalten',
            'url': 'kontakt_admin.list_anfragen',
            'icon': 'ti-inbox',           # Ohne 'ti ' Prefix!
            'color_hex': '#3b82f6',       # Akzentfarbe
        }
    ],
}
```

### Badge-Funktionen

Für dynamische Badges (z.B. ungelesene Nachrichten):

```python
class KontaktPlugin(PluginManifest):
    # ...

    def get_unread_count(self):
        """Anzahl ungelesener Anfragen für Badge."""
        from .models import KontaktAnfrage
        return KontaktAnfrage.query.filter_by(gelesen=False).count()
```

---

## Plugin-Settings-System

Jedes Plugin kann konfigurierbare Einstellungen definieren, die über die Admin-UI (`/admin/plugins/<name>/settings`) verwaltet werden. Einstellungen werden in der Datenbank gespeichert und können jederzeit geändert werden - ohne Server-Neustart.

### Settings-Schema definieren

In deiner Plugin-Klasse implementierst du `get_settings_schema()`:

```python
class MeinPlugin(PluginManifest):
    # ... bestehende Attribute ...

    def get_settings_schema(self) -> list[dict]:
        """Definiert die konfigurierbaren Einstellungen.

        Returns:
            Liste von Setting-Definitionen mit key, label, type, etc.
        """
        return [
            {
                'key': 'api_key',
                'label': 'API Key',
                'type': 'password',  # Verfügbare Typen: siehe Tabelle unten
                'description': 'Dein API Key von example.com',
                'required': False,
                'default': '',
            },
            {
                'key': 'max_items',
                'label': 'Max. Einträge',
                'type': 'int',
                'description': 'Maximale Anzahl anzuzeigender Einträge',
                'default': 10,
                'min': 1,
                'max': 100,
            },
            {
                'key': 'enable_feature',
                'label': 'Feature aktivieren',
                'type': 'bool',
                'description': 'Aktiviert die erweiterte Funktionalität',
                'default': True,
            },
            {
                'key': 'theme',
                'label': 'Theme',
                'type': 'select',
                'options': [
                    {'value': 'light', 'label': 'Hell'},
                    {'value': 'dark', 'label': 'Dunkel'},
                    {'value': 'auto', 'label': 'Automatisch'},
                ],
                'default': 'light',
            },
        ]

    def on_settings_saved(self, settings: dict) -> None:
        """Hook: Wird nach Speichern der Einstellungen aufgerufen.

        Nutze diesen Hook für:
        - Cache leeren
        - API-Clients neu initialisieren
        - Validierung durchführen
        """
        # Beispiel: Cached API-Client zurücksetzen
        try:
            from .services import my_service
            my_service._client = None
        except (ImportError, AttributeError):
            pass
```

### Verfügbare Feld-Typen

| Type | Beschreibung | Zusätzliche Parameter |
|------|--------------|----------------------|
| `string` | Einzeiliger Text | `placeholder` |
| `password` | Passwort/API-Key (versteckt) | - |
| `int` | Ganzzahl | `min`, `max`, `default` |
| `float` | Dezimalzahl | `min`, `max`, `default` |
| `bool` | Checkbox (An/Aus) | `default` |
| `textarea` | Mehrzeiliger Text | `placeholder`, `rows` |
| `select` | Dropdown-Auswahl | `options` (Liste von `{value, label}`) |

### Settings in Services abrufen (Fallback-Pattern)

Das empfohlene Pattern für den Zugriff auf Settings verwendet eine Fallback-Kette:

```python
def get_api_key() -> str | None:
    """API Key mit Fallback-Kette abrufen.

    Priorität:
    1. Datenbank (PluginConfig) - via Admin-UI gesetzt
    2. Flask Config (.env) - Fallback für Entwicklung
    3. None - nicht konfiguriert

    Returns:
        API Key string oder None
    """
    # 1. Datenbank (PluginConfig) - höchste Priorität
    try:
        from v_flask.models import PluginConfig
        db_key = PluginConfig.get_value('mein_plugin', 'api_key')
        if db_key:
            return db_key
    except Exception:
        # PluginConfig existiert möglicherweise nicht (während Migrations)
        pass

    # 2. Flask Config (.env) - Fallback für Entwicklung
    from flask import current_app
    return current_app.config.get('MEIN_PLUGIN_API_KEY')


def is_configured() -> bool:
    """Prüft ob das Plugin konfiguriert ist."""
    return bool(get_api_key())
```

### Settings/Help-Buttons in Admin-Templates

Jedes Plugin-Admin-Template sollte Settings- und Help-Buttons neben dem Titel anzeigen:

```html
{% block content %}
{# Titelzeile mit Settings/Help-Buttons #}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold flex items-center gap-2">
        <i class="ti ti-puzzle text-primary"></i>
        <span>Mein Plugin</span>

        {# Settings Button (⚙️) - nur wenn Plugin Settings hat #}
        {% if plugin_has_settings('mein_plugin') %}
        <a href="{{ plugin_settings_url('mein_plugin') }}"
           class="btn btn-ghost btn-sm btn-circle ml-2"
           title="Einstellungen">
            <i class="ti ti-adjustments text-lg"></i>
        </a>
        {% endif %}

        {# Help Button (ℹ️) - immer anzeigen #}
        <a href="{{ plugin_help_url('mein_plugin') }}"
           class="btn btn-ghost btn-sm btn-circle"
           title="Hilfe">
            <i class="ti ti-info-circle text-lg"></i>
        </a>
    </h1>

    <div class="flex gap-2">
        {# Weitere Action-Buttons... #}
    </div>
</div>
{% endblock %}
```

### Verfügbare Template-Funktionen

Diese Funktionen stehen in allen Templates automatisch zur Verfügung:

| Funktion | Beschreibung | Rückgabe |
|----------|--------------|----------|
| `plugin_has_settings('name')` | Prüft ob Plugin Settings-Schema hat | `bool` |
| `plugin_settings_url('name')` | URL zur Settings-Seite | `str` |
| `plugin_help_url('name')` | URL zur Hilfe-Seite | `str` |

### Komplettes Beispiel: Media Plugin

```python
class MediaPlugin(PluginManifest):
    name = 'media'
    version = '1.0.0'
    description = 'Zentrale Media-Library mit Stock-Photo Integration'

    def get_settings_schema(self) -> list[dict]:
        return [
            {
                'key': 'pexels_api_key',
                'label': 'Pexels API Key',
                'type': 'password',
                'description': 'API Key von pexels.com/api - Ermöglicht Stock-Foto-Suche',
                'required': False,
            },
            {
                'key': 'unsplash_access_key',
                'label': 'Unsplash Access Key',
                'type': 'password',
                'description': 'Access Key von unsplash.com/developers',
                'required': False,
            },
            {
                'key': 'max_upload_size_mb',
                'label': 'Max. Upload-Größe (MB)',
                'type': 'int',
                'description': 'Maximale Dateigröße für Uploads in Megabyte',
                'default': 10,
                'min': 1,
                'max': 50,
            },
            {
                'key': 'auto_resize',
                'label': 'Automatisches Resizing',
                'type': 'bool',
                'description': 'Bilder automatisch in verschiedene Größen konvertieren',
                'default': True,
            },
        ]

    def on_settings_saved(self, settings: dict) -> None:
        # Clear cached API clients so they're recreated with new keys
        try:
            from .services import pexels_service, unsplash_service
            pexels_service._client = None
            unsplash_service._client = None
        except (ImportError, AttributeError):
            pass
```

---

## Marketplace-Eintrag (Lokal)

Nach der Plugin-Entwicklung muss das Plugin in `src/v_flask/data/plugins_marketplace.json` eingetragen werden:

```json
{
  "name": "mein_plugin",
  "version": "1.0.0",
  "description": "Kurze Beschreibung des Plugins",
  "package": "v_flask_plugins.mein_plugin",
  "class": "MeinPlugin",
  "author": "v-flask",
  "license": "MIT",
  "categories": ["forms", "admin"],
  "tags": ["beispiel", "demo"]
}
```

---

## Marketplace-Registrierung (Produktion)

Plugins müssen an **zwei Stellen** registriert werden:

### 1. Lokale JSON (Entwicklung)

**Datei:** `src/v_flask/data/plugins_marketplace.json`

- Für lokale Entwicklung und Tests
- Wird beim Package-Build mitgeliefert
- Eintrag mit `name`, `version`, `description`, `package`, `class`

### 2. Marketplace-Datenbank (Produktion)

**Tabelle:** `marketplace_plugin_meta`

- Für Kundenprojekte (Satelliten)
- Enthält Preise, Lizenzen, Phase, Sichtbarkeit
- Nur Plugins in dieser Tabelle sind für Kunden sichtbar

### Phasen und Sichtbarkeit

Jedes Plugin hat eine **Entwicklungsphase**, die seine Sichtbarkeit bestimmt:

| Phase | DB-Wert | Anzeige | Sichtbar für |
|-------|---------|---------|--------------|
| POC | `alpha` | "Alpha (POC)" | Nur Superadmin-Projekte |
| MVP | `beta` | "Beta (MVP)" | Nur Superadmin-Projekte |
| V1 | `v1` | "V1" | Alle Kunden |
| V2+ | `v2`, `v3`... | "V2", "V3"... | Alle Kunden |

**Wichtig:** Normale Kundenprojekte sehen nur stabile Releases (`v1`, `v2`, ...). Alpha/Beta-Plugins sind nur für interne V-Flask-Projekte sichtbar.

### Wann registrieren?

| Phase | Local JSON | Marketplace DB | Aktion |
|-------|-----------|----------------|--------|
| **POC starten** | ✅ Eintragen | ⚪ Optional | `phase: 'alpha'` |
| **MVP erreicht** | ✅ Aktuell halten | ✅ Eintragen | `phase: 'beta'`, Preis festlegen |
| **V1 Release** | ✅ Aktuell halten | ✅ `phase: 'v1'` setzen | Für alle Kunden sichtbar |

### Checkliste beim Phasen-Wechsel

**POC → MVP:**

- [ ] Plugin in Marketplace-DB eintragen (`phase: 'beta'`)
- [ ] Preis festlegen (`price_cents`)
- [ ] `is_published: true` setzen
- [ ] Optional: Screenshot hochladen

**MVP → V1:**

- [ ] `phase: 'v1'` in Marketplace-DB setzen
- [ ] Changelog in Plugin-Beschreibung aktualisieren
- [ ] Version in `__init__.py` auf `1.0.0` setzen
- [ ] Plugin ist jetzt für alle Kunden sichtbar

### Superadmin-Projekte

Interne V-Flask-Projekte (z.B. vz-frühstücken-click) können Alpha/Beta-Plugins sehen und testen:

```sql
-- Projekt als Superadmin markieren
UPDATE marketplace_project
SET is_superadmin = 1
WHERE slug = 'mein-test-projekt';
```

### Neues Plugin in Marketplace-DB eintragen

```sql
INSERT INTO marketplace_plugin_meta (
    name, display_name, description, version,
    price_cents, category, phase, is_published, has_trial,
    created_at, updated_at
)
VALUES (
    'mein_plugin',           -- Technischer Name
    'Mein Plugin',           -- Anzeigename
    'Kurze Beschreibung',    -- Beschreibung
    '0.1.0',                 -- Version
    0,                       -- Preis in Cent (0 = kostenlos)
    'core',                  -- Kategorie
    'alpha',                 -- Phase (alpha, beta, v1, v2, ...)
    1,                       -- Veröffentlicht (1 = ja)
    1,                       -- Trial möglich (1 = ja)
    datetime('now'),
    datetime('now')
);
```

---

## Häufige Fehler

### 1. CSRF-Token fehlt

**Symptom:** `400 Bad Request: CSRF token is missing`

**Lösung:** CSRF-Token zu Formular hinzufügen:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

### 2. Zirkuläre Imports

**Symptom:** `ImportError: cannot import name 'X' from partially initialized module`

**Lösung:** Lazy Imports verwenden:
```python
def get_models(self):
    from .models import MeinModel  # Import HIER, nicht oben
    return [MeinModel]
```

### 3. Blueprint nicht gefunden

**Symptom:** `werkzeug.routing.exceptions.BuildError: Could not build url for endpoint`

**Lösung:** Blueprint-Name prüfen und sicherstellen, dass Plugin aktiviert ist.

### 4. Template nicht gefunden

**Symptom:** `jinja2.exceptions.TemplateNotFound`

**Lösung:** `get_template_folder()` implementieren und Pfad prüfen.

---

## Referenzen

- [PLUGINS.md](PLUGINS.md) - Vollständige API-Referenz
- [TEMPLATES.md](TEMPLATES.md) - Template-System und Macros
- [AUTH-SYSTEM.md](AUTH-SYSTEM.md) - Permissions und Decorators
- [PLUGIN-PROMPT.md](PLUGIN-PROMPT.md) - Prompts für KI-Agenten (in anderen Projekten nutzbar)
