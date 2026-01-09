# v-flask

Flask Core Extension - Wiederverwendbares Basis-Paket für Flask-Anwendungen.

## Features

- **User Model** - Flask-Login Integration mit Rollen-System
- **Config Model** - Key-Value Store für Anwendungskonfiguration
- **LookupWert Model** - Dynamische Typen, Icons, Farben
- **Modul Model** - Dashboard Registry für modulare Apps
- **AuditLog** - Zentrales Logging für Benutzeraktionen
- **Auth-Decorators** - @admin_required, @mitarbeiter_required
- **Templates** - Wiederverwendbare Jinja2-Templates und Macros
- **Theming** - CSS Custom Properties für dynamisches Branding
- **CLI-Befehle** - flask init-db, flask seed, flask create-admin

## Installation

```bash
# Mit uv (empfohlen)
uv add v-flask

# Oder mit pip
pip install v-flask
```

## Verwendung

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from v_flask import VFlask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)
v = VFlask(app, db)

# Models importieren
from v_flask.models import User, Rolle, Config, LookupWert

# Services nutzen
from v_flask.services import log_event

# Auth-Decorators
from v_flask.auth import admin_required, mitarbeiter_required

@app.route('/admin')
@admin_required
def admin_dashboard():
    return 'Admin only!'
```

### Templates

Templates erweitern das v-flask Basistemplate:

```jinja2
{% extends "v_flask/base.html" %}

{% block content %}
    {% from "v_flask/macros/breadcrumb.html" import breadcrumb %}
    {{ breadcrumb([
        {'label': 'Dashboard', 'url': '/', 'icon': 'ti-home'},
        {'label': 'Kunden'}
    ]) }}

    <h1>Kundenliste</h1>
{% endblock %}
```

Siehe [docs/TEMPLATES.md](docs/TEMPLATES.md) für die vollständige Dokumentation.

### CLI-Befehle

```bash
# Datenbank initialisieren
flask init-db

# Core-Daten seeden (Rollen, Permissions)
flask seed

# Admin-Benutzer erstellen
flask create-admin
```

Siehe [docs/CLI.md](docs/CLI.md) für die vollständige Dokumentation.

## Abhängigkeiten

- Flask >= 3.0
- Flask-SQLAlchemy >= 3.1
- Flask-Login >= 0.6
- Flask-Migrate >= 4.0

### Optionale Abhängigkeiten

```bash
# Für Markdown-Rendering in Templates
uv add v-flask[markdown]
```

## Entwicklung

```bash
# Repository klonen
git clone <repo-url>
cd v-flask

# Dependencies installieren
uv sync

# Tests ausführen
uv run pytest
```

## Lizenz

MIT License - Carsten Vogelsang
