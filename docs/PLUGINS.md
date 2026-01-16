# Plugin-System

Das v-flask Plugin-System ermöglicht die modulare Erweiterung von Flask-Anwendungen mit wiederverwendbaren Komponenten.

## Übersicht

Ein Plugin kann folgende Komponenten bereitstellen:

| Komponente | Methode | Beschreibung |
|------------|---------|--------------|
| Models | `get_models()` | SQLAlchemy Models |
| Blueprints | `get_blueprints()` | Flask Blueprints mit URL-Prefix |
| CLI Commands | `get_cli_commands()` | Click-Kommandos |
| Templates | `get_template_folder()` | Jinja2 Templates |
| Static Files | `get_static_folder()` | Statische Dateien (CSS, JS, Bilder) |
| Init Hook | `on_init(app)` | Initialisierungs-Callback |

## Plugin erstellen

### 1. Plugin-Manifest definieren

Erstelle eine Klasse, die von `PluginManifest` erbt:

```python
from v_flask.plugins import PluginManifest

class MeinPlugin(PluginManifest):
    # Pflichtangaben
    name = 'mein-plugin'           # Eindeutiger Name
    version = '1.0.0'              # Semantic Versioning
    description = 'Beschreibung'   # Kurzbeschreibung
    author = 'Dein Name'           # Autor

    # Optional: Abhängigkeiten von anderen Plugins
    dependencies = ['auth', 'email']  # Liste von Plugin-Namen

    def get_models(self):
        """SQLAlchemy Models zurückgeben."""
        from .models import MeinModel
        return [MeinModel]

    def get_blueprints(self):
        """Blueprints mit URL-Prefix zurückgeben."""
        from .routes import mein_bp
        return [
            (mein_bp, '/mein-plugin'),
        ]

    def on_init(self, app):
        """Wird beim App-Start aufgerufen."""
        app.logger.info(f'Plugin {self.name} initialisiert')
```

### 2. Plugin registrieren

```python
from flask import Flask
from v_flask import VFlask
from meine_plugins import MeinPlugin

app = Flask(__name__)

v_flask = VFlask()
v_flask.register_plugin(MeinPlugin())
v_flask.init_app(app)
```

**Wichtig:** Plugins müssen VOR `init_app()` registriert werden!

## Abhängigkeiten

Plugins können von anderen Plugins abhängen:

```python
class EmailPlugin(PluginManifest):
    name = 'email'
    # ...

class NewsletterPlugin(PluginManifest):
    name = 'newsletter'
    dependencies = ['email']  # Hängt von 'email' ab
    # ...
```

Die Plugins werden automatisch in der richtigen Reihenfolge geladen (topologische Sortierung).

### Fehlerbehandlung

```python
from v_flask.plugins.registry import (
    MissingDependencyError,    # Abhängigkeit nicht registriert
    CircularDependencyError,   # Zirkuläre Abhängigkeit
)
```

## Beispiel: Kontakt-Plugin

v-flask enthält ein Demo-Plugin für Kontaktformulare:

```python
from v_flask import VFlask
from v_flask_plugins.kontakt import KontaktPlugin

v_flask = VFlask()
v_flask.register_plugin(KontaktPlugin())
v_flask.init_app(app)
```

### Bereitgestellte Funktionen

- **Public Route:** `/kontakt/` - Kontaktformular
- **Admin Routes:**
  - `/admin/kontakt/` - Anfragen-Liste
  - `/admin/kontakt/<id>` - Anfrage-Detail
- **Model:** `KontaktAnfrage` - Speichert Anfragen mit Lese-Status

### Templates

Das Plugin stellt eigene Templates bereit:
- `kontakt/form.html` - Öffentliches Formular
- `kontakt/admin/list.html` - Admin-Übersicht
- `kontakt/admin/detail.html` - Admin-Detailansicht

## Plugin-Struktur

Empfohlene Verzeichnisstruktur für Plugins:

```
mein_plugin/
├── __init__.py        # PluginManifest-Klasse
├── models.py          # SQLAlchemy Models
├── routes.py          # Flask Blueprints
├── forms.py           # WTForms (optional)
├── services.py        # Business Logic (optional)
├── templates/
│   └── mein_plugin/
│       ├── public.html
│       └── admin/
│           └── list.html
└── static/            # CSS, JS (optional)
    └── mein_plugin/
        └── style.css
```

## Templates

Plugin-Templates werden automatisch dem Jinja2-Loader hinzugefügt.

### Template-Vererbung

Plugin-Templates können v-flask Basis-Templates erweitern:

```html
{% extends "v_flask/base.html" %}

{% block title %}Mein Plugin{% endblock %}

{% block content %}
<h1>Plugin-Inhalt</h1>
{% endblock %}
```

### Eigene Jinja-Filter

Im `on_init()` Hook können eigene Filter registriert werden:

```python
def on_init(self, app):
    @app.template_filter('mein_filter')
    def mein_filter(value):
        return value.upper()
```

## CLI Commands

Plugins können eigene CLI-Befehle bereitstellen:

```python
import click

class MeinPlugin(PluginManifest):
    # ...

    def get_cli_commands(self):
        @click.command('mein-befehl')
        def mein_befehl():
            """Mein CLI-Befehl."""
            click.echo('Hallo von meinem Plugin!')

        return [mein_befehl]
```

Aufruf: `flask mein-befehl`

## Datenbank-Migrationen

Plugin-Models werden automatisch von SQLAlchemy erkannt. Für Migrationen:

```bash
# Migration erstellen (nach Plugin-Registrierung)
flask db migrate -m "Add mein-plugin models"

# Migration anwenden
flask db upgrade
```

## Best Practices

### 1. Lazy Imports

Importiere Models und Blueprints erst in den `get_*()` Methoden:

```python
# Gut: Lazy Import
def get_models(self):
    from .models import MeinModel
    return [MeinModel]

# Schlecht: Top-Level Import
from .models import MeinModel  # Kann zirkuläre Imports verursachen
```

### 2. Namespace für Templates

Verwende den Plugin-Namen als Template-Ordner:

```
templates/
└── mein_plugin/      # Namespace = Plugin-Name
    └── page.html
```

### 3. Admin-Routes schützen

Verwende v-flask Auth-Decorators:

```python
from v_flask.auth import admin_required

@admin_bp.route('/admin/mein-plugin/')
@admin_required
def admin_list():
    # Nur für Admins
    ...
```

### 4. Validierung

Das Plugin wird bei der Registrierung validiert:

```python
plugin = MeinPlugin()
plugin.validate()  # Wirft ValueError bei fehlenden Pflichtfeldern
```

### 5. CSRF-Schutz

**Alle POST-Formulare MÜSSEN ein CSRF-Token enthalten.** Die Host-App aktiviert Flask-WTF CSRFProtect, daher müssen Plugin-Templates das Token senden.

#### In HTML-Formularen

```html
<form action="{{ url_for('mein_admin.aktion') }}" method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- Formular-Felder -->
    <button type="submit">Speichern</button>
</form>
```

#### In AJAX-Requests

Das CSRF-Token ist im Meta-Tag der Basis-Templates verfügbar:

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

**Fehler bei fehlendem Token:** `400 Bad Request: CSRF token is missing`

## API-Referenz

### PluginManifest

```python
class PluginManifest:
    # Pflichtattribute
    name: str               # Plugin-Name
    version: str            # Version (z.B. '1.0.0')
    description: str        # Beschreibung
    author: str             # Autor

    # Optional
    dependencies: list[str] = []

    # Methoden zum Überschreiben
    def get_models(self) -> list[type]: ...
    def get_blueprints(self) -> list[tuple[Blueprint, str]]: ...
    def get_cli_commands(self) -> list: ...
    def get_template_folder(self) -> Path | None: ...
    def get_static_folder(self) -> Path | None: ...
    def on_init(self, app: Flask) -> None: ...
```

### PluginRegistry

```python
class PluginRegistry:
    def register(plugin: PluginManifest) -> None
    def get(name: str) -> PluginManifest | None
    def all() -> list[PluginManifest]
    def resolve_dependencies() -> list[PluginManifest]
    def init_plugins(app: Flask) -> None
```

### VFlask Integration

```python
v_flask = VFlask()
v_flask.register_plugin(plugin)  # Vor init_app()
v_flask.plugin_registry          # Zugriff auf Registry
```

## Zukünftige Features

- [ ] Marktplatz-API für Plugin-Installation
- [ ] Plugin-Aktivierung via Admin-Interface
- [ ] Plugin-Updates
- [ ] Plugin-Deinstallation
