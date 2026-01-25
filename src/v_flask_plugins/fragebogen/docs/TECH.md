# Fragebogen Plugin - Technische Dokumentation

## Architektur

```
fragebogen/
├── __init__.py              # Plugin-Manifest (FragebogenPlugin)
├── models.py                # SQLAlchemy Models
├── routes/
│   ├── __init__.py
│   ├── admin.py             # Admin-Routen
│   └── public.py            # Öffentliche Wizard-Routen
├── services/
│   ├── __init__.py
│   ├── fragebogen_service.py   # Haupt-Service
│   ├── participant_source.py   # Dynamischer Teilnehmer-Resolver
│   └── export_service.py       # XLSX-Export
├── templates/
│   └── fragebogen/
│       ├── admin/           # Admin-Templates
│       └── wizard/          # Public Wizard Templates
└── docs/
    ├── SPEC.md              # Spezifikation
    └── TECH.md              # Technische Docs
```

## Services

### FragebogenService

Haupt-Service für CRUD-Operationen und Fragebogen-Logik.

```python
from v_flask_plugins.fragebogen.services import get_fragebogen_service

service = get_fragebogen_service()

# Fragebogen erstellen
fragebogen = service.create_fragebogen(
    titel="Umfrage",
    definition=schema_dict,
    user_id=current_user.id
)

# Definition validieren
result = service.validate_definition(schema_dict)
if not result.valid:
    print(result.errors)

# Teilnehmer hinzufügen
teilnahme = service.add_teilnehmer(
    fragebogen=fragebogen,
    teilnehmer_id=kunde.id,
    teilnehmer_typ='kunde'
)

# Einladungen versenden
result = service.send_einladungen(fragebogen)
print(f"Gesendet: {result.sent_count}, Fehler: {result.failed_count}")
```

### TeilnehmerResolver

Interface für die Auflösung von Teilnehmerdaten aus beliebigen Models.

```python
from v_flask_plugins.fragebogen.services import TeilnehmerResolver

class KundeResolver(TeilnehmerResolver):
    def get_email(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        kunde = Kunde.query.get(teilnehmer_id)
        return kunde.email if kunde else None

    def get_name(self, teilnehmer_id: int, teilnehmer_typ: str) -> str | None:
        kunde = Kunde.query.get(teilnehmer_id)
        return kunde.firmierung if kunde else None

    def get_prefill_value(self, teilnehmer_id, teilnehmer_typ, prefill_key):
        if prefill_key == 'kunde.branche':
            kunde = Kunde.query.get(teilnehmer_id)
            return kunde.branche
        return None

# Service konfigurieren
service = get_fragebogen_service()
service.set_teilnehmer_resolver(KundeResolver())
```

### DynamicParticipantResolver

Automatischer Resolver basierend auf ParticipantSourceConfig.

```python
from v_flask_plugins.fragebogen.services import get_dynamic_participant_resolver

resolver = get_dynamic_participant_resolver()

# Daten abrufen
email = resolver.get_email(kunde_id, 'kunde')
name = resolver.get_name(kunde_id, 'kunde')
greeting = resolver.get_greeting(kunde_id, 'kunde')

# Cache leeren nach Config-Änderungen
from v_flask_plugins.fragebogen.services import reset_dynamic_participant_resolver
reset_dynamic_participant_resolver()
```

### Export Service

XLSX-Export für Fragebogen-Antworten.

```python
from v_flask_plugins.fragebogen.services import get_export_service, ExportOptions

service = get_export_service()

options = ExportOptions(
    include_timestamps=True,
    include_incomplete=False
)

xlsx_buffer = service.export_to_xlsx(fragebogen, options)

# In Flask-Route
from flask import Response
return Response(
    xlsx_buffer.getvalue(),
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    headers={'Content-Disposition': 'attachment; filename="export.xlsx"'}
)
```

## Greeting Generator

Standalone-Funktion für personalisierte Begrüßungen.

```python
from v_flask_plugins.fragebogen.services import generate_greeting

# Standard-Format
greeting = generate_greeting('Herr', 'Dr.', 'Müller')
# -> "Sehr geehrter Herr Dr. Müller"

# Mit Template
greeting = generate_greeting(
    anrede='Frau',
    titel='Prof.',
    name='Schmidt',
    template='Guten Tag {{ anrede }} {{ titel }} {{ name }}'
)
# -> "Guten Tag Frau Prof. Schmidt"
```

## Field-Mapping

Das Field-Mapping unterstützt einfache und zusammengesetzte Felder.

### Einfaches Feld
```json
{"email": "email_address"}
```
Liest `model.email_address`.

### Zusammengesetztes Feld
```json
{
  "name": {
    "fields": ["vorname", "nachname"],
    "separator": " "
  }
}
```
Kombiniert `model.vorname` + " " + `model.nachname`.

## Installation

### Basis
```bash
pip install v-flask
```

### Mit Export-Funktion
```bash
pip install v-flask[export]
```

## Migrations

Bei neuen Installationen werden die Tabellen automatisch erstellt.

Für bestehende Installationen mit v-flask < 0.2.0:
```bash
flask db upgrade
```

Neue Tabelle für ParticipantSourceConfig:
```sql
CREATE TABLE fragebogen_participant_source_config (
    id INTEGER PRIMARY KEY,
    model_path VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    field_mapping JSON NOT NULL,
    greeting_template TEXT,
    query_filter JSON,
    is_default BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME
);
```

## Dependencies

- **Pflicht**: Flask, SQLAlchemy, Flask-Login
- **Optional**: openpyxl (für XLSX-Export)
- **Optional**: jinja2 (für Greeting-Templates, meist bereits vorhanden)
