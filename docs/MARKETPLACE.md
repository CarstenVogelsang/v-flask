# V-Flask Plugin Marketplace

Der V-Flask Plugin Marketplace ermöglicht die zentrale Bereitstellung und Verteilung von Plugins an Satellitenprojekte. Dieses Dokument beschreibt Architektur, Konfiguration und Nutzung.

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SATELLITEN-PROJEKT (z.B. UDO UI, Frühstückenclick)                      │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │  /admin/plugins/marketplace                                         │ │
│ │  - Zeigt ALLE Plugins aus Remote-Marketplace-API                    │ │
│ │  - Status: lizenziert/nicht lizenziert, installiert/nicht           │ │
│ │  - Buttons: "Installieren" → Download + Entpacken                   │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              │ HTTPS (X-API-Key Header)                  │
│                              ▼                                           │
├─────────────────────────────────────────────────────────────────────────┤
│ V-FLASK MARKETPLACE SERVER (marketplace.v-flask.de)                     │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │  API Endpoints:                                                     │ │
│ │  GET  /api/plugins              → Plugin-Liste                      │ │
│ │  GET  /api/plugins/{name}       → Plugin-Details                    │ │
│ │  GET  /api/projects/me          → Projekt-Info                      │ │
│ │  GET  /api/projects/me/licenses → Gekaufte Plugins                  │ │
│ │  POST /api/plugins/{name}/download → ZIP (nur mit Lizenz!)          │ │
│ │                                                                     │ │
│ │  Admin-Bereich (/admin):                                            │ │
│ │  - Projekte verwalten (API-Keys generieren)                         │ │
│ │  - Lizenzen verwalten (Projekt X hat Plugin Y)                      │ │
│ │  - Plugin-Metadaten (Preise, Beschreibungen)                        │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              │ Direkter Dateizugriff                     │
│                              ▼                                           │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │  src/v_flask_plugins/ (im v-flask Repo)                             │ │
│ │  - Plugin-Quelltexte werden bei Download zu ZIP gepackt             │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Architektur

### Monorepo-Ansatz

Der Marketplace ist Teil des v-flask Repositories:

```
v-flask/
├── src/v_flask/              # Framework-Package
│   └── plugins/
│       ├── marketplace_client.py   # API-Client für Satelliten
│       ├── downloader.py           # ZIP-Download + Entpacken
│       └── admin_routes.py         # Marketplace-UI in Admin
│
├── src/v_flask_plugins/      # Plugin-Quelltexte
│   ├── kontakt/
│   ├── impressum/
│   ├── datenschutz/
│   └── ...
│
└── marketplace/              # Marketplace-Server (Flask-App)
    ├── app/
    │   ├── models/           # Project, License, PluginMeta, Order
    │   ├── routes/
    │   │   ├── api.py        # REST API
    │   │   ├── admin.py      # Admin-UI
    │   │   └── shop.py       # Öffentlicher Shop
    │   └── services/
    │       ├── plugin_scanner.py   # Scannt v_flask_plugins/
    │       └── plugin_packager.py  # Erstellt ZIP-Archive
    └── pyproject.toml
```

### Vorteile

1. **Direkter Plugin-Zugriff**: Marketplace kann Plugins direkt aus `v_flask_plugins/` zippen
2. **Keine Synchronisation**: Kein separates Repo für Plugins nötig
3. **Einheitliche Versionierung**: Plugin-Versionen über Git-Tags
4. **v-flask nutzt sich selbst**: Marketplace-App verwendet v-flask Auth, UI-Slots, etc.

---

## Für Satellitenprojekt-Entwickler

### 1. Konfiguration

Füge diese Variablen zu deiner `.env` hinzu:

```bash
# V-Flask Marketplace
VFLASK_MARKETPLACE_URL=https://marketplace.v-flask.de/api
VFLASK_PROJECT_API_KEY=vf_proj_xxxxxxxxxxxxxxxxxxxxx
```

Und erweitere deine `config.py`:

```python
class Config:
    # V-Flask Marketplace
    VFLASK_MARKETPLACE_URL = os.environ.get('VFLASK_MARKETPLACE_URL', '')
    VFLASK_PROJECT_API_KEY = os.environ.get('VFLASK_PROJECT_API_KEY', '')
```

### 2. Marketplace-UI nutzen

Nach der Konfiguration erscheint der "Marketplace"-Button in `/admin/plugins/`:

1. **Navigiere zu** `/admin/plugins/`
2. **Klicke auf** "Marketplace" (Button oben rechts)
3. **Sieh alle verfügbaren Plugins** mit Status:
   - ✓ Installiert (grün)
   - 🆓 Kostenlos (info)
   - 🔐 Lizenziert (gelb)
   - 🔒 Lizenz erforderlich (rot)
4. **Klicke auf "Installieren"** bei lizenzierten Plugins

### 3. Programmatische Nutzung

```python
from v_flask.plugins import MarketplaceClient, PluginDownloader

# Client erstellen
client = MarketplaceClient(
    base_url="https://marketplace.v-flask.de/api",
    api_key="vf_proj_xxxxx"
)

# Verfügbare Plugins abrufen
plugins = client.get_available_plugins()
for p in plugins:
    print(f"{p['name']}: {p['description']}")

# Eigene Lizenzen prüfen
licenses = client.get_my_licenses()

# Plugin herunterladen und installieren
downloader = PluginDownloader(client=client)
downloader.install_plugin('kontakt')
```

---

## Für Marketplace-Admins

### Marketplace-Server starten

```bash
cd marketplace/
uv sync
uv run flask run --port 5001
```

Öffne http://localhost:5001/admin und logge dich ein.

**Standard-Credentials (Entwicklung):**
- Email: `admin@marketplace.local`
- Passwort: `admin123`

### Projekte verwalten

1. **Navigiere zu** `/admin/projects`
2. **Neues Projekt anlegen:**
   - Name (z.B. "Frühstückenclick")
   - Owner-Email
   - → API-Key wird automatisch generiert
3. **API-Key** an Projektentwickler weitergeben

### Lizenzen vergeben

1. **Navigiere zu** `/admin/licenses`
2. **Lizenz vergeben:**
   - Projekt auswählen
   - Plugin auswählen
   - Optional: Notizen hinzufügen
3. Das Projekt kann das Plugin nun herunterladen

### Plugin-Preise setzen

1. **Navigiere zu** `/admin/plugins`
2. **Plugin bearbeiten:**
   - Display-Name
   - Beschreibung
   - Preis (in Euro)
   - Featured/Published Status

---

## API-Referenz

### Öffentliche Endpoints (kein Auth)

#### GET /api/plugins
Liste aller veröffentlichten Plugins.

```json
{
  "plugins": [
    {
      "name": "kontakt",
      "display_name": "Kontakt",
      "description": "Kontaktformular mit Admin-Bereich",
      "version": "1.1.0",
      "price_cents": 0,
      "is_free": true,
      "is_featured": false
    }
  ]
}
```

#### GET /api/plugins/{name}
Details eines Plugins.

### Authentifizierte Endpoints (X-API-Key Header)

#### GET /api/projects/me
Projekt-Informationen des API-Key-Inhabers.

```json
{
  "id": 1,
  "name": "Frühstückenclick",
  "slug": "fruehstueckenclick",
  "is_active": true
}
```

#### GET /api/projects/me/licenses
Alle Lizenzen des Projekts.

```json
{
  "licenses": [
    {
      "plugin_name": "kontakt",
      "purchased_at": "2026-01-17T12:00:00Z",
      "expires_at": null
    }
  ]
}
```

#### POST /api/plugins/{name}/download
ZIP-Archiv des Plugins herunterladen.

**Voraussetzungen:**
- Gültiger API-Key
- Lizenz für das Plugin ODER Plugin ist kostenlos

**Response:** ZIP-Datei (application/zip)

---

## Datenmodelle

### Project (Satellitenprojekt)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | int | Primary Key |
| name | str | Projektname |
| slug | str | URL-Slug |
| api_key | str | `vf_proj_xxx...` |
| owner_email | str | Kontakt-Email |
| is_active | bool | Aktiv/Inaktiv |
| created_at | datetime | Erstelldatum |

### License (Lizenz)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | int | Primary Key |
| project_id | FK | → Project |
| plugin_name | str | Plugin-Identifier |
| purchased_at | datetime | Kaufdatum |
| expires_at | datetime | Ablaufdatum (optional) |
| order_id | FK | → Order (optional) |

### PluginMeta (Plugin-Metadaten)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | int | Primary Key |
| name | str | Plugin-Identifier |
| display_name | str | Anzeigename |
| description | str | Kurzbeschreibung |
| price_cents | int | Preis in Cent |
| is_published | bool | Im Shop sichtbar |
| is_featured | bool | Hervorgehoben |

---

## Deployment

### Lokal (Entwicklung)

```bash
# Terminal 1: Marketplace-Server
cd marketplace/
uv run flask run --port 5001

# Terminal 2: Satellitenprojekt
cd ../mein-projekt/
VFLASK_MARKETPLACE_URL=http://localhost:5001/api \
VFLASK_PROJECT_API_KEY=vf_proj_xxx \
uv run flask run --port 5000
```

### Production (Coolify)

1. **Marketplace deployen:**
   - Dockerfile im `marketplace/` Verzeichnis
   - Environment: `DATABASE_URL`, `SECRET_KEY`
   - Domain: `marketplace.v-flask.de`

2. **Satellitenprojekte konfigurieren:**
   ```bash
   VFLASK_MARKETPLACE_URL=https://marketplace.v-flask.de/api
   VFLASK_PROJECT_API_KEY=vf_proj_xxx
   ```

---

## Troubleshooting

### "Marketplace nicht konfiguriert"

Die Config-Variablen werden nicht geladen:

1. Prüfe `.env`:
   ```bash
   VFLASK_MARKETPLACE_URL=http://localhost:5001/api
   VFLASK_PROJECT_API_KEY=vf_proj_xxx
   ```

2. Prüfe `config.py`:
   ```python
   VFLASK_MARKETPLACE_URL = os.environ.get('VFLASK_MARKETPLACE_URL', '')
   VFLASK_PROJECT_API_KEY = os.environ.get('VFLASK_PROJECT_API_KEY', '')
   ```

3. Server neu starten

### "Plugin nicht lizenziert"

- Prüfe im Marketplace-Admin, ob das Projekt eine Lizenz hat
- Kostenlose Plugins (price_cents = 0) brauchen keine Lizenz

### Marketplace-Server nicht erreichbar

```bash
# Prüfe ob Server läuft
curl http://localhost:5001/api/plugins

# Prüfe Firewall/Netzwerk bei Remote-Server
curl https://marketplace.v-flask.de/api/plugins
```

---

## Siehe auch

- [PLUGINS.md](PLUGINS.md) - Plugin-System Übersicht
- [PLUGIN-DEVELOPMENT.md](PLUGIN-DEVELOPMENT.md) - Eigene Plugins entwickeln
- [AUTH-SYSTEM.md](AUTH-SYSTEM.md) - Permission-System für Admin-Zugriff
