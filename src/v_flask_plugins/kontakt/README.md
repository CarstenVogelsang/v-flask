# Kontakt-Plugin

Kontaktformular mit Admin-Bereich für v-flask Anwendungen.

## Features

- **Öffentliches Kontaktformular** mit Server-seitiger Validierung
- **Admin-Bereich** zum Verwalten von Anfragen
- **Lese-Status-Tracking** (gelesen/ungelesen) mit visueller Markierung
- **Responsive Templates** basierend auf DaisyUI/Tailwind CSS
- **Keine externen Abhängigkeiten** - funktioniert standalone

## Installation

### 1. Plugin registrieren

In deiner Flask App Factory (`app/__init__.py`):

```python
from flask import Flask
from v_flask import VFlask
from v_flask_plugins.kontakt import KontaktPlugin

def create_app():
    app = Flask(__name__)

    v_flask = VFlask()
    v_flask.register_plugin(KontaktPlugin())  # WICHTIG: Vor init_app()!
    v_flask.init_app(app)

    return app
```

### 2. Datenbank-Migration erstellen und ausführen

```bash
flask db migrate -m "Add kontakt_anfrage table"
flask db upgrade
```

## Routes

Das Plugin stellt folgende Routes bereit:

### Öffentlich

| Route | Methode | Beschreibung |
|-------|---------|--------------|
| `/kontakt/` | GET | Kontaktformular anzeigen |
| `/kontakt/` | POST | Formular absenden |

### Admin (erfordert `admin.*` Permission)

| Route | Methode | Beschreibung |
|-------|---------|--------------|
| `/admin/kontakt/` | GET | Liste aller Anfragen |
| `/admin/kontakt/<id>` | GET | Anfrage-Details anzeigen |
| `/admin/kontakt/<id>/toggle-read` | POST | Lese-Status umschalten |
| `/admin/kontakt/<id>/delete` | POST | Anfrage löschen |

## Datenmodell

### KontaktAnfrage

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | Integer | Primärschlüssel |
| `name` | String(100) | Name des Absenders |
| `email` | String(200) | E-Mail-Adresse des Absenders |
| `nachricht` | Text | Nachrichteninhalt |
| `gelesen` | Boolean | `True` wenn gelesen, sonst `False` |
| `created_at` | DateTime | Erstellungszeitpunkt |

## Templates

Das Plugin bringt eigene Templates mit:

```
templates/
└── kontakt/
    ├── form.html           # Öffentliches Kontaktformular
    └── admin/
        ├── list.html       # Admin: Anfragen-Liste
        └── detail.html     # Admin: Anfrage-Detail
```

Die Templates erweitern `v_flask/base.html` und nutzen DaisyUI-Komponenten.

### Templates überschreiben

Du kannst die Plugin-Templates in deiner App überschreiben, indem du
gleichnamige Templates in deinem `app/templates/` Verzeichnis erstellst:

```
app/templates/
└── kontakt/
    └── form.html    # Überschreibt das Plugin-Template
```

## Konfiguration

Das Plugin funktioniert out-of-the-box ohne zusätzliche Konfiguration.

### Zukünftige Optionen (geplant)

- E-Mail-Benachrichtigungen an `Betreiber.email`
- Konfigurierbare E-Mail-Override via `Config`
- CAPTCHA-Integration

## Verwendung im Code

```python
from v_flask_plugins.kontakt.models import KontaktAnfrage
from v_flask import db

# Alle ungelesenen Anfragen abrufen
unread = db.session.query(KontaktAnfrage).filter_by(gelesen=False).all()

# Anfrage als gelesen markieren
anfrage = db.session.get(KontaktAnfrage, anfrage_id)
anfrage.mark_as_read()
db.session.commit()
```

## Abhängigkeiten

Keine - dieses Plugin hat keine Abhängigkeiten von anderen v-flask Plugins.

## Lizenz

MIT License - siehe v-flask Hauptprojekt.

## Changelog

### 1.0.0

- Initial release
- Öffentliches Kontaktformular
- Admin-Bereich mit Anfragen-Verwaltung
- Lese-Status-Tracking
