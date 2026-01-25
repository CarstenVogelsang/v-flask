# Projektverwaltung Plugin - Spezifikation

## Übersicht

Das Projektverwaltung Plugin ist ein vollständiges Projektmanagement-System mit Kanban-Board, PRD-Verwaltung (Komponenten), automatischer Changelog-Generierung und REST-API für Claude Code Integration.

## Zielgruppe

- **Projektmanager**: Projekte und Tasks verwalten
- **Entwickler**: Tasks bearbeiten, PRDs einsehen
- **KI-Agenten**: API-Zugriff für automatisierte Workflows

## User Stories

- Als Projektmanager möchte ich Tasks im Kanban-Board organisieren
- Als Entwickler möchte ich PRDs (Komponenten) als Markdown abrufen
- Als KI-Agent möchte ich Tasks per API abfragen und abschließen
- Als Team möchte ich automatisch Changelogs bei Task-Abschluss generieren

## Funktionale Anforderungen

| ID | Anforderung | Priorität | Phase |
|----|-------------|-----------|-------|
| F1 | Projekte erstellen/verwalten | Must | POC |
| F2 | Komponenten (PRDs) mit Markdown | Must | POC |
| F3 | Tasks mit Kanban-Status | Must | POC |
| F4 | Kanban-Board mit Drag & Drop | Must | MVP |
| F5 | Task-Kommentare | Should | MVP |
| F6 | Changelog-Generierung | Should | MVP |
| F7 | REST-API für Claude Code | Must | V1 |
| F8 | KI-Prompt-Generator | Should | V1 |

## Kanban-Spalten

| Status | Beschreibung |
|--------|--------------|
| `backlog` | Noch nicht geplante Tasks |
| `geplant` | Für Implementierung vorgesehen |
| `in_arbeit` | Wird aktuell bearbeitet |
| `review` | In Prüfung |
| `erledigt` | Abgeschlossen |

## Task-Typen

- Funktion (Feature)
- Verbesserung (Enhancement)
- Fehlerbehebung (Bug)
- Technisch (Tech Debt)
- Sicherheit (Security)
- Recherche (Research)
- Dokumentation (Docs)
- Test

## Nicht-funktionale Anforderungen

- **UX**: Flüssiges Drag & Drop
- **API**: RESTful, JSON-Responses
- **Sicherheit**: API nur für authentifizierte User

## Abgrenzung (Out of Scope)

- Zeiterfassung
- Ressourcenplanung
- Gantt-Charts
- Multi-User Assignments
