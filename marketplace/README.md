# V-Flask Plugin Marketplace

Zentraler Marketplace für die Verwaltung und Distribution von V-Flask Plugins.

## Features

- **Projekt-Verwaltung**: Registrierung von Satellitenprojekten mit API-Keys
- **Lizenz-Management**: Manuelle und automatische Lizenzvergabe
- **Plugin-Katalog**: Öffentliche Übersicht aller verfügbaren Plugins
- **API für Satelliten**: REST-API für Plugin-Download und Lizenzprüfung
- **Stripe-Integration**: (geplant) Automatische Zahlungsabwicklung

## Setup

### 1. Dependencies installieren

```bash
cd marketplace
uv sync
```

### 2. Umgebungsvariablen

```bash
cp .env.example .env
# Anpassen: SECRET_KEY, DATABASE_URL
```

### 3. Datenbank initialisieren

```bash
flask db upgrade
flask init-marketplace  # Plugins aus v_flask_plugins scannen
```

### 4. Admin-User erstellen

```bash
flask create-admin admin@example.com admin123
```

### 5. Erstes Projekt anlegen

```bash
flask create-project "UDO UI" admin@example.com
# Gibt API-Key aus
```

### 6. Server starten

```bash
flask run --port 5000
```

## API Endpoints

### Öffentlich (ohne Auth)

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /api/plugins` | Liste aller Plugins |
| `GET /api/plugins/{name}` | Plugin-Details |

### Authentifiziert (API-Key in `X-API-Key` Header)

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /api/projects/me` | Projekt-Info |
| `GET /api/projects/me/licenses` | Aktive Lizenzen |
| `POST /api/plugins/{name}/download` | Plugin als ZIP herunterladen |

## Architektur

```
marketplace/
├── app/
│   ├── __init__.py         # Flask App Factory
│   ├── config.py           # Konfiguration
│   ├── models/             # SQLAlchemy Models
│   │   ├── project.py      # Satellitenprojekte
│   │   ├── plugin_meta.py  # Plugin-Metadaten (Preise)
│   │   ├── license.py      # Projekt-Plugin-Beziehungen
│   │   └── order.py        # Bestellungen (Audit)
│   ├── routes/
│   │   ├── admin.py        # Admin-UI
│   │   ├── shop.py         # Öffentlicher Shop
│   │   └── api.py          # REST-API für Satelliten
│   ├── services/
│   │   ├── plugin_scanner.py  # v_flask_plugins scannen
│   │   └── plugin_packager.py # ZIP erstellen
│   └── templates/
│       ├── admin/          # Admin-Templates
│       └── shop/           # Shop-Templates
├── pyproject.toml
└── README.md
```

## Integration in Satellitenprojekte

### Konfiguration

```python
# config.py im Satellitenprojekt
VFLASK_MARKETPLACE_URL = "https://marketplace.v-flask.de/api"
VFLASK_PROJECT_API_KEY = "vf_proj_xxxxxxxxxxxxx"
```

### Plugin herunterladen (manuell via API)

```bash
curl -X POST \
  -H "X-API-Key: vf_proj_xxx" \
  https://marketplace.v-flask.de/api/plugins/impressum/download \
  -o impressum.zip
```
