# Business Directory Plugin - Technische Dokumentation

## Architektur

### Plugin-Struktur
```
business_directory/
├── __init__.py              # PluginManifest
├── models/
│   ├── __init__.py          # Model-Exports
│   ├── directory_type.py    # DirectoryType (Schema-Definition)
│   ├── directory_entry.py   # DirectoryEntry (Einträge)
│   ├── registration_draft.py# Wizard-State
│   ├── claim_request.py     # Ownership-Claims
│   ├── geo_land.py          # Land
│   ├── geo_bundesland.py    # Bundesland
│   ├── geo_kreis.py         # Kreis
│   └── geo_ort.py           # Ort
├── routes/
│   ├── __init__.py          # Blueprint-Exports
│   ├── admin.py             # Entry CRUD, Review Queue
│   ├── admin_types.py       # DirectoryType CRUD
│   ├── admin_geodaten.py    # Geodaten-Import
│   ├── public.py            # Geo-Drilling, Suche
│   ├── register.py          # Self-Registration Wizard
│   ├── provider.py          # Provider Dashboard
│   └── api.py               # JSON API
├── services/
│   ├── __init__.py
│   ├── geodaten_service.py  # unternehmensdaten.org API
│   └── entry_service.py     # Entry Business Logic
├── templates/
│   └── business_directory/
│       ├── admin/
│       ├── public/
│       ├── register/
│       └── provider/
└── docs/
    ├── SPEC.md
    ├── TECH.md
    └── PROGRESS.md
```

## Datenbank-Schema

### Tabellen-Prefix
Alle Tabellen beginnen mit `business_directory_`:
- `business_directory_type`
- `business_directory_entry`
- `business_directory_registration_draft`
- `business_directory_claim_request`
- `business_directory_geo_land`
- `business_directory_geo_bundesland`
- `business_directory_geo_kreis`
- `business_directory_geo_ort`

### DirectoryType Felder
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | Integer | Primary Key |
| slug | String(100) | URL-Bezeichner, unique |
| name | String(200) | Anzeigename |
| name_singular | String(100) | Einzahl |
| name_plural | String(100) | Mehrzahl |
| icon | String(50) | Tabler Icon Klasse |
| description | Text | Beschreibung |
| field_schema | JSON | Felddefinitionen |
| registration_steps | JSON | Wizard-Konfiguration |
| display_config | JSON | Anzeige-Konfiguration |
| active | Boolean | Aktiv-Status |

### DirectoryEntry Felder
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | Integer | Primary Key |
| directory_type_id | Integer | FK → DirectoryType |
| name | String(200) | Eintragsname |
| slug | String(200) | URL-Slug |
| geo_ort_id | String(36) | FK → GeoOrt |
| strasse | String(200) | Straße |
| telefon | String(50) | Telefon |
| email | String(200) | E-Mail |
| website | String(500) | Website |
| kurzbeschreibung | Text | Beschreibung |
| data | JSON | Typenspezifische Daten |
| active | Boolean | Öffentlich sichtbar |
| verified | Boolean | Geprüft |
| self_managed | Boolean | Vom Eigentümer gepflegt |
| owner_id | Integer | FK → User |

## Blueprints & URL-Prefixes

| Blueprint | URL-Prefix | Beschreibung |
|-----------|-----------|--------------|
| business_directory_admin | /admin/verzeichnis | Entry-Verwaltung |
| business_directory_admin_types | /admin/verzeichnis/typen | Typ-Verwaltung |
| business_directory_admin_geodaten | /admin/verzeichnis/geodaten | Geodaten |
| business_directory_public | /verzeichnis | Öffentliche Seiten |
| business_directory_register | /registrieren | Self-Registration |
| business_directory_provider | /anbieter | Provider Dashboard |
| business_directory_api | /api/verzeichnis | JSON API |

## Services

### GeodatenService
```python
service = GeodatenService()

# Länder importieren
count = service.import_laender()

# Bundesländer für ein Land
count = service.import_bundeslaender(land_id)

# Kreise für ein Bundesland
count = service.import_kreise(bundesland_id)

# Orte für einen Kreis
count = service.import_orte(kreis_id)
```

### EntryService
```python
from business_directory.services import EntryService

# Eintrag erstellen
entry = EntryService.create_entry(
    directory_type=directory_type,
    name='Spielwaren Schmidt',
    geo_ort=geo_ort,
    data={'marken': ['LEGO', 'Playmobil']}
)

# Suchen
results = EntryService.search('spielwaren', directory_type_id=1)

# Nach PLZ finden
results = EntryService.find_by_plz('47533')
```

## JSON-Schemas

### field_schema
```json
{
  "oeffnungszeiten": {
    "type": "opening_hours",
    "label": "Öffnungszeiten",
    "required": true,
    "show_in_detail": true,
    "show_in_card": true
  },
  "marken": {
    "type": "multi_select",
    "label": "Geführte Marken",
    "options": ["LEGO", "Playmobil", "Ravensburger"],
    "required": false,
    "show_in_detail": true
  },
  "barrierefrei": {
    "type": "boolean",
    "label": "Barrierefrei",
    "show_in_detail": true
  }
}
```

### Field Types
| Type | Beschreibung |
|------|-------------|
| text | Einzeiliger Text |
| textarea | Mehrzeiliger Text |
| number | Zahl |
| boolean | Ja/Nein |
| select | Einzelauswahl |
| multi_select | Mehrfachauswahl |
| opening_hours | Strukturierte Öffnungszeiten |
| url | URL-Feld |
| email | E-Mail-Feld |
| phone | Telefon-Feld |

## API Endpoints

### GET /api/verzeichnis/search
Query: `?q=<text>&type=<slug>&plz=<plz>&limit=20&offset=0`

Response:
```json
{
  "success": true,
  "total": 42,
  "results": [...]
}
```

### GET /api/verzeichnis/entry/<id>
Response:
```json
{
  "success": true,
  "entry": {...}
}
```

### GET /api/verzeichnis/types
Response:
```json
{
  "success": true,
  "types": [...]
}
```

## Template-Konventionen

- Basis: `v_flask/admin/base.html` (Admin) oder `v_flask/base.html` (Public)
- CSS: DaisyUI (nicht Bootstrap)
- Icons: Tabler Icons (`ti ti-*`)
- CSRF: `{% include 'v_flask/includes/_csrf.html' %}`
