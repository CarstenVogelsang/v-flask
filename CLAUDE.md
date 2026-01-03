# V-Flask Framework

**Wiederverwendbare Flask-Komponenten für SaaS-Anwendungen**

## Übersicht

V-Flask ist eine modulare Flask-Extension mit Core-Funktionalitäten:
- User/Rolle-System mit granularen Permissions (RBAC)
- Config Key-Value Store
- Betreiber-Model für Multi-Tenancy/Theming
- AuditLog für Benutzeraktionen
- Auth-Decorators (`@permission_required`)

## Kommunikation

**Wir duzen uns!** Bitte verwende in allen Antworten die Du-Form.

## Befehle

```bash
uv sync              # Dependencies installieren
uv run pytest        # Tests ausführen
uv run pytest -v     # Verbose Tests
```

## Konventionen

- **Sprache Docs:** Deutsch
- **Sprache Code:** Englisch (Variablen, Funktionen, Kommentare)
- **Deutsche Texte:** Echte Umlaute (ä, ü, ö, ß)
- **Package Manager:** uv
- **Python:** 3.11+
- **Type Hints:** Wo sinnvoll

## Quell-Projekt

**Pfad:** `/Users/cvogelsang/projekte_ev/ev_pricat_converter/`

> ⚠️ **WICHTIG:** Das Quell-Projekt wird NIEMALS geändert! Nur LESEN!

## Technische Dokumentation

Detaillierte Spezifikationen findest du in:

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Package-Struktur, Models
- **[docs/AUTH-SYSTEM.md](docs/AUTH-SYSTEM.md)** - Permission-System, Decorators
- **[docs/IMPLEMENTATION-CHECKLIST.md](docs/IMPLEMENTATION-CHECKLIST.md)** - Implementierungs-Status
