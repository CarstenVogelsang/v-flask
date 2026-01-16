# CRM UDO Plugin - Technische Dokumentation

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│  Host-App (z.B. UDO UI)                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  CRM_UDO Plugin                                            │ │
│  │  - Admin UI (/admin/crm_udo/)                              │ │
│  │  - CrmApiClient (nutzt Host-Config)                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              │ HTTP (via httpx)                  │
│                              ▼                                   │
├──────────────────────────────┼──────────────────────────────────┤
│  UDO API (FastAPI)           │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  /api/v1/unternehmen/*                                     │ │
│  │  /api/v1/kontakte/*                                        │ │
│  │  /api/v1/organisationen/*                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Plugin-Struktur

```
crm_udo/
├── __init__.py              # PluginManifest mit UI-Slots
├── api_client.py            # HTTP Client für UDO API
├── routes/
│   ├── __init__.py
│   └── admin.py             # Flask Blueprint
├── templates/
│   └── crm_udo/
│       └── admin/
│           ├── index.html
│           ├── unternehmen_list.html
│           ├── unternehmen_detail.html
│           └── unternehmen_form.html
└── docs/
    ├── SPEC.md
    ├── TECH.md
    └── PROGRESS.md
```

## API Client

### Konfiguration

Der `CrmApiClient` bezieht seine Konfiguration aus der Host-App:

```python
# URL aus Flask-Config
UDO_API_BASE_URL = "http://localhost:8001/api/v1"

# Token aus Session
udo_access_token = session.get('udo_access_token')
```

### Verfügbare Methoden

#### Unternehmen

| Methode | HTTP | Endpoint | Beschreibung |
|---------|------|----------|--------------|
| `list_unternehmen(**filters)` | GET | `/unternehmen` | Paginierte Liste |
| `get_unternehmen(id)` | GET | `/unternehmen/{id}` | Einzelnes Unternehmen |
| `create_unternehmen(data)` | POST | `/unternehmen` | Erstellen |
| `update_unternehmen(id, data)` | PATCH | `/unternehmen/{id}` | Aktualisieren |
| `delete_unternehmen(id)` | DELETE | `/unternehmen/{id}` | Löschen |
| `get_unternehmen_count()` | GET | `/unternehmen/count` | Anzahl |

#### Kontakte

| Methode | HTTP | Endpoint | Beschreibung |
|---------|------|----------|--------------|
| `list_kontakte(unternehmen_id)` | GET | `/unternehmen/{id}/kontakte` | Kontakte eines Unternehmens |
| `create_kontakt(unternehmen_id, data)` | POST | `/unternehmen/{id}/kontakte` | Erstellen |
| `update_kontakt(u_id, k_id, data)` | PATCH | `/unternehmen/{u}/kontakte/{k}` | Aktualisieren |
| `delete_kontakt(u_id, k_id)` | DELETE | `/unternehmen/{u}/kontakte/{k}` | Löschen |

### Fehlerbehandlung

```python
from httpx import HTTPError, HTTPStatusError

try:
    result = crm_client.get_unternehmen(id)
except HTTPStatusError as e:
    if e.response.status_code == 404:
        flash('Nicht gefunden', 'error')
    else:
        flash(f'API-Fehler: {e}', 'error')
except HTTPError as e:
    flash(f'Verbindungsfehler: {e}', 'error')
```

## Admin Routes

### Blueprint

```python
admin_bp = Blueprint(
    'crm_udo_admin',
    __name__,
    template_folder='../templates'
)
```

### URL-Schema

| URL | View | Template |
|-----|------|----------|
| `/admin/crm_udo/` | `index` | `index.html` |
| `/admin/crm_udo/unternehmen` | `unternehmen_list` | `unternehmen_list.html` |
| `/admin/crm_udo/unternehmen/neu` | `unternehmen_neu` | `unternehmen_form.html` |
| `/admin/crm_udo/unternehmen/<id>` | `unternehmen_detail` | `unternehmen_detail.html` |
| `/admin/crm_udo/unternehmen/<id>/edit` | `unternehmen_edit` | `unternehmen_form.html` |
| `/admin/crm_udo/unternehmen/<id>/delete` | `unternehmen_delete` | - (Redirect) |

### Berechtigungen

Alle Routes erfordern `admin.*` Permission:

```python
@admin_bp.route('/')
@permission_required('admin.*')
def index():
    ...
```

## UI-Slots

Das Plugin registriert sich im Admin-Menü und Dashboard:

```python
ui_slots = {
    'admin_menu': [{
        'label': 'CRM',
        'url': 'crm_udo_admin.index',
        'icon': 'ti ti-building-community',
        'permission': 'admin.*',
        'order': 20,
        'children': [
            {'label': 'Unternehmen', 'url': 'crm_udo_admin.unternehmen_list'},
        ]
    }],
    'admin_dashboard_widgets': [{
        'name': 'CRM',
        'description': 'Unternehmen & Kontakte verwalten',
        'url': 'crm_udo_admin.index',
        'icon': 'ti-building-community',
        'color_hex': '#0ea5e9',
    }]
}
```

## Templates

### Basis-Template

Alle Templates erweitern `v_flask/admin/base.html` und folgen dem Admin View Layout Pattern:

1. **Breadcrumbs**: Navigation im `{% block breadcrumbs %}`
2. **Titelzeile**: H1 + Action-Buttons
3. **Content**: Cards, Tabellen, Formulare

### UI-Komponenten

- **CSS Framework**: DaisyUI + Tailwind CSS
- **Icons**: Tabler Icons (`ti ti-*`)
- **Modals**: Native `<dialog>` mit DaisyUI Styling
- **Forms**: DaisyUI Form Controls mit CSRF-Token

## Host-App Integration

### In Flask App registrieren

```python
# app/__init__.py
from v_flask_plugins.crm_udo import CrmUdoPlugin
from v_flask_plugins.crm_udo.routes import admin_bp

# Plugin registrieren
v_flask.register_plugin(CrmUdoPlugin())

# Blueprint registrieren
app.register_blueprint(admin_bp, url_prefix='/admin/crm_udo')
```

### Konfiguration

```python
# config.py
UDO_API_BASE_URL = "http://localhost:8001/api/v1"
```

### Session Setup

Die Host-App muss `udo_access_token` in der Session setzen (z.B. nach Login):

```python
session['udo_access_token'] = response.get('access_token')
```
