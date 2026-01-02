# CLAUDE.md - v-flask

## Projekt

**v-flask** - Flask Core Extension Package

Wiederverwendbares Flask-Basis-Paket mit:
- User Model (Flask-Login Integration)
- Rolle Model (Admin, Mitarbeiter, Kunde)
- Config Model (Key-Value Store)
- LookupWert Model (dynamische Typen, Icons, Farben)
- Modul Model (Dashboard Registry)
- AuditLog + Logging Service
- Auth-Decorators (@admin_required, @mitarbeiter_required)
- Basis-Templates (base.html, Macros)

## Kommunikation

**Wir duzen uns!** Bitte verwende in allen Antworten die Du-Form.

## Befehle

```bash
# Setup
uv sync

# Tests
uv run pytest

# Development (in Test-App)
cd ../vz_fruehstueckenclick
uv sync  # installiert v-flask als editable
uv run python run.py
```

## Architektur

### Package-Struktur
```
v-flask/
├── pyproject.toml
├── CLAUDE.md
├── README.md
├── docs/
│   └── PRD-MIGRATION.md    # Migrations-Anleitung
├── src/
│   └── v_flask/
│       ├── __init__.py     # VFlask Extension + init_app()
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── rolle.py
│       │   ├── config.py
│       │   ├── lookup_wert.py
│       │   ├── modul.py
│       │   └── audit_log.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── logging_service.py
│       ├── auth/
│       │   ├── __init__.py
│       │   └── decorators.py
│       └── templates/
│           ├── base.html
│           └── macros/
│               ├── breadcrumb.html
│               ├── help.html
│               └── admin_tile.html
└── tests/
```

### Verwendung in Host-Apps

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from v_flask import VFlask

app = Flask(__name__)
db = SQLAlchemy(app)
v = VFlask(app, db)

# Models verfügbar:
from v_flask.models import User, Rolle, Config, LookupWert
from v_flask.services import log_event
from v_flask.auth import admin_required
```

## Referenz-Projekt

Der Code wird aus **ev_pricat_converter** extrahiert und adaptiert:
- Pfad: `/Users/cvogelsang/projekte_ev/ev_pricat_converter/`
- **NUR LESEN!** - Niemals ändern!

## Test-Projekt

Das Test-Projekt befindet sich unter:
- Pfad: `/Users/cvogelsang/projektz/vz_fruehstueckenclick/`

## Abhängiges Package

**v-flask-projektverwaltung** baut auf v-flask auf:
- Pfad: `/Users/cvogelsang/projektz/v-flask-projektverwaltung/`

## Konventionen

- **Sprache Docs:** Deutsch
- **Sprache Code:** Englisch (Variablen, Funktionen, Kommentare)
- **Deutsche Texte:** Echte Umlaute (ä, ü, ö, ß)
- **Package Manager:** uv
- **Python:** 3.11+
- **Type Hints:** Wo sinnvoll
