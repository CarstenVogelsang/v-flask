# Projektverwaltung Plugin - Technische Dokumentation

## Architektur-Übersicht

```
projektverwaltung/
├── __init__.py          # ProjektverwaltungPlugin Manifest
├── models.py            # Projekt, Komponente, Task, etc. (27KB)
├── routes/
│   ├── admin.py         # Admin-UI mit Kanban
│   └── api.py           # REST-API für Claude Code
├── services/
│   ├── task_service.py  # Task-Logik
│   └── changelog_service.py  # Changelog-Generierung
├── static/              # Kanban CSS/JS
└── templates/
    └── projektverwaltung/
        └── admin/       # Kanban-Board, Projekt-Views
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| `Projekt` | `pv_projekt` | Container für Komponenten |
| `Komponente` | `pv_komponente` | PRD/Modul mit Markdown |
| `Task` | `pv_task` | Arbeitseinheit mit Status |
| `TaskKommentar` | `pv_task_kommentar` | Review-Kommentare |
| `ChangelogEintrag` | `pv_changelog` | Generierte Einträge |

### Admin Routes

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/admin/projekte/` | GET | Projekt-Übersicht |
| `/admin/projekte/<id>` | GET | Projekt-Details mit Kanban |
| `/admin/projekte/<id>/komponenten` | GET | Komponenten-Liste |
| `/admin/projekte/tasks/<id>` | GET/POST | Task-Details |
| `/admin/projekte/tasks/<id>/move` | POST | Task-Status ändern |

### API Routes

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `GET /api/projekte` | Liste aller Projekte |
| `GET /api/projekte/<id>` | Projekt-Details |
| `GET /api/komponenten/<id>/prd` | PRD als Markdown |
| `GET /api/komponenten/<id>/tasks` | Tasks einer Komponente |
| `GET /api/tasks/<id>` | Task-Details |
| `GET /api/tasks/by-nummer/<nr>` | Task per Nummer (PRD011-T020) |
| `POST /api/tasks/<id>/erledigen` | Task abschließen |
| `GET /api/tasks/<id>/prompt` | KI-Prompt generieren |
| `GET /api/tasks/<id>/review-prompt` | Review-Prompt |

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `admin_menu` | `{label: 'Projektverwaltung', badge_func: 'get_open_tasks_count'}` |
| `admin_dashboard_widgets` | Widget mit offenen Tasks |

## Settings-Schema

| Key | Type | Default | Beschreibung |
|-----|------|---------|--------------|
| `default_task_status` | select | `backlog` | Standard-Status |
| `changelog_auto_generate` | bool | true | Auto-Changelog |
| `archive_completed_after_days` | int | 30 | Auto-Archivierung |
| `api_enabled` | bool | true | REST-API aktiv |

## LookupWerte Seeding

Das Plugin erstellt beim Init automatisch Task-Typen:

```python
task_typen = [
    ('funktion', 'Funktion', '#3b82f6', 'ti-code'),
    ('verbesserung', 'Verbesserung', '#10b981', 'ti-trending-up'),
    ('fehlerbehebung', 'Fehlerbehebung', '#ef4444', 'ti-bug'),
    # ...
]
```

## Abhängigkeiten

- **v_flask Core**: Auth, DB, LookupWert
- **SortableJS**: Drag & Drop (CDN)

## Datenbank-Schema (Auszug)

```sql
CREATE TABLE pv_projekt (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE,
    beschreibung TEXT,
    ist_intern BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'aktiv',
    created_at DATETIME
);

CREATE TABLE pv_komponente (
    id INTEGER PRIMARY KEY,
    projekt_id INTEGER REFERENCES pv_projekt(id),
    name VARCHAR(200) NOT NULL,
    prd_nummer VARCHAR(20) UNIQUE,  -- z.B. "PRD011"
    inhalt_markdown TEXT,
    status VARCHAR(20) DEFAULT 'entwurf',
    version INTEGER DEFAULT 1
);

CREATE TABLE pv_task (
    id INTEGER PRIMARY KEY,
    komponente_id INTEGER REFERENCES pv_komponente(id),
    task_nummer VARCHAR(30),  -- z.B. "PRD011-T020"
    titel VARCHAR(200) NOT NULL,
    beschreibung TEXT,
    typ VARCHAR(50),  -- FK auf LookupWert
    status VARCHAR(20) DEFAULT 'backlog',
    prioritaet INTEGER DEFAULT 50,
    erstellt_am DATETIME,
    erledigt_am DATETIME
);
```

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| PRD-Nummer Auto-Generierung | Eindeutige IDs für API-Zugriff |
| Task-Nummer kombiniert | Komponente + Task für Navigation |
| LookupWert für Typen | Zentrale Konfiguration, UI-Farben |
| SortableJS via CDN | Bewährte Library, kleiner Footprint |
