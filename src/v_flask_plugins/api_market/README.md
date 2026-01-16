# API Market Plugin

Ein API-Marketplace Plugin für v-flask Anwendungen.

## Features

- **Automatische Dokumentation** aus OpenAPI-Specs (live abgerufen)
- **Code-Beispiele** in Python, C#, Delphi (auto-generiert)
- **Admin-Interface** zum Verwalten von APIs
- **Caching** der OpenAPI-Specs für Performance

## Installation

```python
from v_flask import VFlask
from v_flask_plugins.api_market import ApiMarketPlugin

v_flask = VFlask()
v_flask.register_plugin(ApiMarketPlugin())
v_flask.init_app(app)
```

## Konfiguration

```python
# config.py
API_MARKET_CACHE_TTL = 3600  # Spec-Cache TTL in Sekunden (Standard: 1 Stunde)
API_MARKET_CODE_LANGUAGES = ['python', 'csharp', 'delphi']  # Sprachen für Code-Beispiele
```

## Routes

### Public

| Route | Beschreibung |
|-------|--------------|
| `/api-market/` | Marketplace-Übersicht |
| `/api-market/<slug>` | API Quickstart-Doku |
| `/api-market/<slug>/docs` | Vollständige API-Dokumentation |
| `/api-market/my-keys` | Eigene API-Keys (Login erforderlich) |

### Admin

| Route | Beschreibung |
|-------|--------------|
| `/admin/api-market/` | Dashboard |
| `/admin/api-market/add` | API hinzufügen |
| `/admin/api-market/<id>` | API bearbeiten |
| `/admin/api-market/<id>/refresh` | Spec neu laden |
| `/admin/api-market/<id>/delete` | API löschen |

## Modelle

### ExternalApi

Speichert Metadaten und gecachte OpenAPI-Specs.

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `name` | String | Anzeigename der API |
| `slug` | String | URL-sicherer Identifier |
| `spec_url` | String | URL zur OpenAPI-Spec |
| `spec_data` | Text | Gecachte Spec (JSON) |
| `base_url` | String | API Basis-URL |
| `status` | String | active/inactive/maintenance |

## Services

### OpenAPI Fetcher

```python
from v_flask_plugins.api_market.services import fetch_openapi_spec

spec = fetch_openapi_spec('https://api.example.com/openapi.json')
```

### Code Generator

```python
from v_flask_plugins.api_market.services import generate_code_example

code = generate_code_example(endpoint, api, 'python')
```

## Abhängigkeiten

- `requests` - HTTP-Client für Spec-Abruf
- Optional: `pyyaml` - für YAML-Specs

## Lizenz

MIT
