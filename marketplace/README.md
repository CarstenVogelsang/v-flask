# V-Flask Plugin Marketplace

Zentraler Marketplace für die Verwaltung und Distribution von V-Flask Plugins.

---

## 📋 Features

- **Projekt-Verwaltung**: Registrierung von Satellitenprojekten mit API-Keys
- **Lizenz-Management**: Manuelle und automatische Lizenzvergabe
- **Plugin-Katalog**: Öffentliche Übersicht aller verfügbaren Plugins
- **API für Satelliten**: REST-API für Plugin-Download und Lizenzprüfung
- **Preismatrix**: Differenzierte Preise pro Projekttyp und Abrechnungszyklus
- **Stripe-Integration**: (geplant) Automatische Zahlungsabwicklung

---

## 🚀 Quick-Start (Projekt wieder aufnehmen)

Wenn du nach einer Pause das Projekt wieder startest:

```bash
# 1. In den Marketplace-Ordner wechseln
cd /Users/cvogelsang/projektz/v-flask/marketplace

# 2. Server starten (Port wird aus .env gelesen: 5800)
uv run flask run --debug
```

**Fertig!** → http://localhost:5800

**Admin:** → http://localhost:5800/admin/

---

## 🛠️ Erstinstallation (nur einmalig)

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
uv run flask db upgrade
uv run flask init-marketplace  # Plugins aus v_flask_plugins scannen
```

### 4. Admin-User erstellen

```bash
uv run flask create-admin --email admin@marketplace.local --vorname Admin --nachname User --password marketplace2026
```

### 5. Erstes Projekt anlegen

```bash
uv run flask create-project "UDO UI" admin@example.com
# Gibt API-Key aus
```

---

## 💻 Entwicklungsserver

### Server starten

```bash
# Server starten (Port 5800 aus .env)
uv run flask run --debug

# Alternative: Mit manuell aktivierter venv
source .venv/bin/activate && flask run
```

**URLs:**
- Frontend: http://localhost:5800
- Admin: http://localhost:5800/admin/

### Server stoppen

```bash
# Im Terminal: Ctrl+C drücken

# Oder von anderem Terminal aus:
pkill -f "flask run"

# Alternativ: Nach Port stoppen
lsof -ti:5800 | xargs kill
```

---

## 🔐 Admin-Zugang

**Standard-Credentials (lokale Entwicklung):**

| Feld     | Wert                       |
|----------|----------------------------|
| URL      | http://localhost:5800/admin/ |
| E-Mail   | admin@marketplace.local  |
| Passwort | marketplace2026          |

> ⚠️ **Hinweis:** Diese Credentials sind nur für lokale Entwicklung. In Production eigene Credentials verwenden!

---

## 🖥️ Verfügbare CLI-Commands

| Command | Beschreibung |
|---------|--------------|
| `flask init-marketplace` | Plugins aus v_flask_plugins scannen und registrieren |
| `flask create-admin` | Admin-Benutzer erstellen |
| `flask create-project` | Satellitenprojekt mit API-Key anlegen |
| `flask db upgrade` | Datenbank-Migrationen ausführen |

---

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
