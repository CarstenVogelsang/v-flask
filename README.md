# v-flask

Flask Core Extension - Wiederverwendbares Basis-Paket für Flask-Anwendungen.

## Features

- **User Model** - Flask-Login Integration mit Rollen-System
- **Config Model** - Key-Value Store für Anwendungskonfiguration
- **LookupWert Model** - Dynamische Typen, Icons, Farben
- **Modul Model** - Dashboard Registry für modulare Apps
- **AuditLog** - Zentrales Logging für Benutzeraktionen
- **Auth-Decorators** - @admin_required, @mitarbeiter_required

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

## Abhängigkeiten

- Flask >= 3.0
- Flask-SQLAlchemy >= 3.1
- Flask-Login >= 0.6
- Flask-Migrate >= 4.0

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
