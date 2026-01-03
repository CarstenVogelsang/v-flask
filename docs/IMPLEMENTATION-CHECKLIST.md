# V-Flask Implementierungs-Checkliste

## Phase 1: Core-Models

- [x] User Model extrahiert
- [x] Rolle Model extrahiert
- [ ] Permission Model erstellt
- [ ] rolle_permission Zuordnung erstellt
- [ ] Betreiber Model erstellt
- [ ] Config Model extrahiert
- [ ] LookupWert Model extrahiert
- [ ] Modul + ModulZugriff extrahiert
- [ ] AuditLog Model extrahiert

## Phase 2: Auth-System

- [ ] permission_required Decorator implementiert
- [ ] Wildcard-Support für Permissions
- [x] Login-Manager Integration

## Phase 3: Plugin-System (SPÄTER)

- [ ] PluginRegistry implementiert
- [ ] PluginManifest Basisklasse
- [ ] Dependency-Prüfung
- [ ] Topologische Sortierung

## Phase 4: Migrations

- [ ] MigrationManager implementiert
- [ ] CLI-Befehle registriert
- [ ] Core-Migrations erstellt

## Phase 5: Theming

- [ ] CSS-Variablen definiert
- [ ] base.html Template
- [ ] Betreiber-Context-Processor

## Phase 6: Tests & Dokumentation

- [ ] Unit Tests geschrieben
- [ ] Integration Tests
- [x] README.md
- [x] ARCHITECTURE.md
- [x] AUTH-SYSTEM.md

---

## Bekannte Einschränkungen

- **Template-Overrides:** Host-Apps können Templates überschreiben
- **URL-Endpoints:** Decorators erwarten `main.index` als Fallback
- **Datenbank:** PostgreSQL oder SQLite mit SQLAlchemy
- **Abwärtskompatibilität:** Breaking Changes nicht erlaubt
