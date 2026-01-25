# Kontakt Plugin - Technische Dokumentation

## Architektur-Übersicht

```
kontakt/
├── __init__.py          # KontaktPlugin Manifest, get_unread_count
├── models.py            # KontaktAnfrage Model
├── routes.py            # Public + Admin Blueprints
└── templates/
    └── kontakt/
        ├── public/      # Kontaktformular
        └── admin/       # Anfragen-Verwaltung
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| `KontaktAnfrage` | `kontakt_anfrage` | Kontaktformular-Einreichungen |

### Routes

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/kontakt/` | GET | Public | Kontaktformular anzeigen |
| `/kontakt/` | POST | Public | Formular absenden |
| `/admin/kontakt/` | GET | Admin | Liste aller Anfragen |
| `/admin/kontakt/<id>` | GET | Admin | Anfrage-Details |
| `/admin/kontakt/<id>/read` | POST | Admin | Als gelesen markieren |
| `/admin/kontakt/<id>/delete` | POST | Admin | Anfrage löschen |

### Templates

| Template | Zweck |
|----------|-------|
| `kontakt/public/form.html` | Kontaktformular |
| `kontakt/public/success.html` | Erfolgsseite |
| `kontakt/admin/list.html` | Admin-Liste |
| `kontakt/admin/detail.html` | Anfrage-Details |

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `footer_links` | `{label: 'Kontakt', icon: 'ti ti-mail', url: 'kontakt.form'}` |
| `admin_menu` | `{label: 'Kontakt-Anfragen', icon: 'ti ti-inbox', badge_func: 'get_unread_count'}` |
| `admin_dashboard_widgets` | Widget mit Badge für ungelesene Anfragen |

## Badge-Funktion

```python
def get_unread_count(self) -> int:
    """Anzahl ungelesener Anfragen für Badge."""
    return KontaktAnfrage.query.filter_by(gelesen=False).count()
```

## Settings-Schema

| Key | Type | Default | Beschreibung |
|-----|------|---------|--------------|
| `email_recipient` | string | (leer) | E-Mail für Benachrichtigungen |
| `email_notifications` | bool | false | Benachrichtigungen aktivieren |
| `require_phone` | bool | false | Telefon als Pflichtfeld |
| `success_message` | textarea | Standard | Erfolgs-Nachricht |

## Abhängigkeiten

- **v_flask Core**: Auth, DB
- **Keine externen Abhängigkeiten**

## Datenbank-Schema

```sql
CREATE TABLE kontakt_anfrage (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(200) NOT NULL,
    nachricht TEXT NOT NULL,
    gelesen BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

## Jinja-Filter

Das Plugin registriert den `nl2br` Filter:

```jinja2
{{ anfrage.nachricht|nl2br }}
```

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Keine eigene E-Mail-Logik | Nutzt zentrale E-Mail-Funktionalität der Host-App |
| Einfaches Model | Bewusst simpel gehalten, erweiterbar bei Bedarf |
| Badge via badge_func | Dynamische Anzeige ohne eigenen API-Call |
