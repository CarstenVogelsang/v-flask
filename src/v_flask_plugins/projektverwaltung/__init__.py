"""Projektverwaltung Plugin for v-flask.

A complete project management plugin with Kanban board:
- Projects and components (PRDs) management
- Kanban board with drag & drop
- Task comments with review workflow
- Changelog generation
- REST API for Claude Code integration
- AI prompt generator for tasks

Usage:
    from v_flask import VFlask
    from v_flask_plugins.projektverwaltung import ProjektverwaltungPlugin

    v_flask = VFlask()
    v_flask.register_plugin(ProjektverwaltungPlugin())
    v_flask.init_app(app)
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class ProjektverwaltungPlugin(PluginManifest):
    """Project management plugin with Kanban board for v-flask applications.

    Provides:
        - Project and component (PRD) management
        - Kanban board with 5 columns (Backlog, Geplant, In Arbeit, Review, Erledigt)
        - Task comments for review workflow
        - Automatic changelog generation
        - REST API for Claude Code integration
        - AI prompt generator
    """

    name = 'projektverwaltung'
    version = '1.0.0'
    description = 'Projektmanagement mit Kanban-Board und KI-Integration'
    author = 'v-flask'

    # No dependencies on other plugins
    dependencies = []

    # Marketplace metadata
    long_description = '''
Ein vollständiges Projektmanagement-Plugin für v-flask Anwendungen.

**Features:**
- Projekte und Komponenten (PRDs) verwalten
- Kanban-Board mit Drag-and-Drop
- Task-Kommentare mit Review-Workflow
- Changelog-Generierung bei Task-Abschluss
- REST API für Claude Code Integration
- KI-Prompt-Generator für Tasks

**Models:**
- Projekt: Container für Komponenten (intern/Kundenprojekt)
- Komponente: PRD/Modul/Entity mit Markdown-Inhalt
- Task: Arbeitseinheit mit Kanban-Status
- TaskKommentar: Review-Workflow
- ChangelogEintrag: Automatische Dokumentation

**API-Endpoints:**
- GET /api/projekte - Projektliste
- GET /api/komponenten/{id}/prd - PRD als Markdown
- GET /api/tasks/{id}/prompt - KI-Prompt generieren
- GET /api/tasks/{id}/review-prompt - Review-Prompt generieren
'''
    license = 'MIT'
    categories = ['projects', 'productivity']
    tags = ['projekt', 'kanban', 'task', 'prd', 'changelog', 'api', 'claude']
    min_v_flask_version = '0.2.0'

    # Admin navigation: appears under "Inhalte" category
    admin_category = 'content'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'admin_menu': [
            {
                'label': 'Projektverwaltung',
                'url': 'projektverwaltung_admin.index',
                'icon': 'ti ti-folder',
                'badge_func': 'get_open_tasks_count',
                'permission': 'admin.*',
                'order': 10,
            }
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Projektverwaltung',
                'description': 'Offene Tasks verwalten',
                'icon': 'ti-layout-kanban',
                'url': 'projektverwaltung_admin.index',
                'badge_func': 'get_open_tasks_count',
                'color_hex': '#3b82f6',
                'order': 50,
            }
        ],
    }

    def get_open_tasks_count(self) -> int:
        """Get count of tasks in progress.

        Used by ui_slots badge_func to display active task count in admin UI.
        """
        try:
            from v_flask.extensions import db
            from v_flask_plugins.projektverwaltung.models import Task
            return db.session.query(Task).filter_by(status='in_arbeit').count()
        except Exception:
            return 0

    def get_models(self):
        """Return all plugin models."""
        from v_flask_plugins.projektverwaltung.models import (
            Projekt,
            Komponente,
            Task,
            TaskKommentar,
            ChangelogEintrag,
        )
        return [Projekt, Komponente, Task, TaskKommentar, ChangelogEintrag]

    def get_blueprints(self):
        """Return admin and API blueprints."""
        from v_flask_plugins.projektverwaltung.routes import admin_bp, api_bp
        return [
            (admin_bp, '/admin/projekte'),
            (api_bp, '/api'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_static_folder(self):
        """Return path to plugin static files."""
        return Path(__file__).parent / 'static'

    def get_settings_schema(self) -> list[dict]:
        """Define available settings for the Projektverwaltung plugin.

        Returns:
            List of setting definitions for project management options.
        """
        return [
            {
                'key': 'default_task_status',
                'label': 'Standard-Status für neue Tasks',
                'type': 'select',
                'description': 'Status, mit dem neue Tasks erstellt werden',
                'options': [
                    {'value': 'backlog', 'label': 'Backlog'},
                    {'value': 'geplant', 'label': 'Geplant'},
                ],
                'default': 'backlog',
            },
            {
                'key': 'changelog_auto_generate',
                'label': 'Changelog automatisch erstellen',
                'type': 'bool',
                'description': 'Bei Task-Abschluss automatisch Changelog-Eintrag erstellen',
                'default': True,
            },
            {
                'key': 'archive_completed_after_days',
                'label': 'Erledigte Tasks archivieren nach (Tage)',
                'type': 'int',
                'description': 'Erledigte Tasks nach X Tagen automatisch archivieren (0 = nie)',
                'default': 30,
                'min': 0,
                'max': 365,
            },
            {
                'key': 'api_enabled',
                'label': 'REST-API aktivieren',
                'type': 'bool',
                'description': 'API-Endpoints für Claude Code Integration aktivieren',
                'default': True,
            },
        ]

    def on_init(self, app):
        """Initialize plugin: seed LookupWerte for task types."""
        self._seed_lookup_werte(app)

    def _seed_lookup_werte(self, app):
        """Seed task type lookup values if they don't exist."""
        try:
            from v_flask.extensions import db
            from v_flask.models import LookupWert

            task_typen = [
                ('funktion', 'Funktion', '#3b82f6', 'ti-code'),
                ('verbesserung', 'Verbesserung', '#10b981', 'ti-trending-up'),
                ('fehlerbehebung', 'Fehlerbehebung', '#ef4444', 'ti-bug'),
                ('technisch', 'Technisch', '#6366f1', 'ti-tool'),
                ('sicherheit', 'Sicherheit', '#f59e0b', 'ti-shield'),
                ('recherche', 'Recherche', '#8b5cf6', 'ti-search'),
                ('dokumentation', 'Dokumentation', '#64748b', 'ti-file-text'),
                ('test', 'Test', '#14b8a6', 'ti-flask'),
            ]

            with app.app_context():
                for code, name, farbe, icon in task_typen:
                    existing = LookupWert.query.filter_by(
                        kategorie='task_typ', code=code
                    ).first()
                    if not existing:
                        wert = LookupWert(
                            kategorie='task_typ',
                            code=code,
                            name=name,
                            farbe=farbe,
                            icon=icon,
                        )
                        db.session.add(wert)

                db.session.commit()
        except Exception:
            # Don't fail plugin init if seeding fails
            pass

    def get_help_texts(self):
        """Return help texts for the plugin."""
        return [
            {
                'schluessel': 'projektverwaltung.kanban',
                'titel': 'Kanban-Board Hilfe',
                'inhalt_markdown': '''## Kanban-Board

Das Kanban-Board zeigt Tasks in 5 Spalten:
- **Backlog**: Noch nicht geplante Tasks
- **Geplant**: Für Implementierung vorgesehen
- **In Arbeit**: Wird aktuell bearbeitet
- **Review**: In Prüfung
- **Erledigt**: Abgeschlossen

### Drag & Drop
Tasks können per Drag & Drop zwischen Spalten verschoben werden.

### Quick Add
Im Backlog-Bereich kannst du neue Tasks schnell anlegen.

### Task-Archivierung
Erledigte Tasks können archiviert werden, um das Board übersichtlich zu halten.
''',
            },
            {
                'schluessel': 'projektverwaltung.api',
                'titel': 'API-Dokumentation',
                'inhalt_markdown': '''## API-Endpoints

Die Projektverwaltung bietet eine REST-API für die Integration mit Claude Code.

### Projekte & Komponenten
- `GET /api/projekte` - Projektliste
- `GET /api/projekte/{id}` - Projekt-Details
- `GET /api/komponenten/{id}/prd` - PRD als Markdown
- `GET /api/komponenten/{id}/tasks` - Tasks einer Komponente

### Tasks
- `GET /api/tasks/{id}` - Task-Details
- `GET /api/tasks/by-nummer/PRD011-T020` - Task per Nummer
- `POST /api/tasks/{id}/erledigen` - Task abschließen
- `GET /api/tasks/{id}/prompt` - KI-Prompt generieren
- `GET /api/tasks/{id}/review-prompt` - Review-Prompt

### Beispiel
```bash
curl http://localhost:5000/api/komponenten/1/prd
```
''',
            },
        ]


# Export the plugin class
__all__ = ['ProjektverwaltungPlugin']
