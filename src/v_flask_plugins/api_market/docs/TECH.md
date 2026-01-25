# API Market Plugin - Technische Dokumentation

## Architektur-Übersicht

```
api_market/
├── __init__.py          # ApiMarketPlugin Manifest
├── models.py            # ExternalApi Model
├── routes.py            # Public + Admin Blueprints
├── services/
│   ├── spec_service.py  # OpenAPI Spec Fetching + Caching
│   └── code_generator.py # Code-Beispiel Generierung
├── static/              # CSS für API-Docs
└── templates/
    └── api_market/
        ├── public/      # API-Dokumentation
        └── admin/       # API-Verwaltung
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| `ExternalApi` | `external_api` | Registrierte APIs mit Spec-URL |

### Routes

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/api-market/` | GET | Public/Auth | API-Liste |
| `/api-market/<slug>` | GET | Public/Auth | API-Dokumentation |
| `/api-market/<slug>/examples/<lang>` | GET | Public | Code-Beispiele |
| `/admin/api-market/` | GET | Admin | Dashboard |
| `/admin/api-market/add` | GET/POST | Admin | API hinzufügen |
| `/admin/api-market/<id>/edit` | GET/POST | Admin | API bearbeiten |
| `/admin/api-market/<id>/refresh` | POST | Admin | Spec neu laden |

### Services

| Service | Methode | Beschreibung |
|---------|---------|--------------|
| `spec_service.fetch_spec(url)` | OpenAPI Spec abrufen |
| `spec_service.get_cached_spec(api_id)` | Gecachte Spec holen |
| `spec_service.refresh_spec(api_id)` | Cache invalidieren |
| `code_generator.generate(spec, lang)` | Code-Beispiele erzeugen |

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `navbar_items` | `{label: 'API', url: 'api_market.list_apis'}` |
| `admin_menu` | `{label: 'API Marketplace', url: 'api_market_admin.dashboard'}` |
| `admin_dashboard_widgets` | Widget mit API-Count |

## Settings-Schema

| Key | Type | Default | Beschreibung |
|-----|------|---------|--------------|
| `cache_ttl` | int | 3600 | Cache-Gültigkeit (Sekunden) |
| `code_languages` | textarea | `python, csharp, delphi` | Aktivierte Sprachen |
| `public_access` | bool | true | Öffentlicher Zugang |
| `show_usage_stats` | bool | false | Nutzungsstatistiken |

## Abhängigkeiten

- **v_flask Core**: Auth, DB
- **requests**: HTTP-Calls für Spec-Fetching
- **pyyaml**: YAML-OpenAPI-Specs parsen

## Datenbank-Schema

```sql
CREATE TABLE external_api (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    beschreibung TEXT,
    spec_url VARCHAR(500) NOT NULL,
    spec_cached JSON,
    spec_cached_at DATETIME,
    base_url VARCHAR(500),
    auth_type VARCHAR(50),  -- 'api_key', 'bearer', 'basic'
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME,
    updated_at DATETIME
);
```

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Live Spec-Fetch statt Upload | APIs ändern sich, immer aktuelle Docs |
| Caching in DB | Einfach, keine Redis-Dependency |
| Code-Generierung on-demand | Specs können groß sein, besser lazy |
