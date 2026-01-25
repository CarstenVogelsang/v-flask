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

## Spracherkennung

Der Benutzer verwendet Spracheingabe. Folgende Wörter werden häufig falsch transkribiert:

| Falsch erkannt | Gemeint |
|----------------|---------|
| cloth, cloud   | Claude  |
| Tasse, Tassen  | Tasks   |

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

## Test-Projekt (Frühstückenclick)

**Pfad:** `/Users/cvogelsang/projektz/vz_fruehstueckenclick/`

Wird zum Testen von v-flask Plugins und Features verwendet.

## Marketplace

**Pfad:** `/Users/cvogelsang/projektz/v-flask/marketplace/`

### Admin-Credentials

Die Standard-Credentials für lokale Entwicklung findest du in `marketplace/README.md`.

> ⚠️ **WICHTIG:** Niemals den Admin-User überschreiben oder neu erstellen, es sei denn, der Benutzer fordert dich explizit dazu auf!

## Technische Dokumentation

Detaillierte Spezifikationen findest du in:

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Package-Struktur, Models
- **[docs/AUTH-SYSTEM.md](docs/AUTH-SYSTEM.md)** - Permission-System, Decorators
- **[docs/COMPONENTS.md](docs/COMPONENTS.md)** - Wiederverwendbare UI-Komponenten (Icon Picker, Markdown Editor, etc.)
- **[docs/IMPLEMENTATION-CHECKLIST.md](docs/IMPLEMENTATION-CHECKLIST.md)** - Implementierungs-Status

## Admin Template Guidelines

Für Plugin-Entwicklung und Admin-Template-Erstellung siehe:

→ **[docs/PLUGIN-DEVELOPMENT.md](docs/PLUGIN-DEVELOPMENT.md)** - Section "Admin Template UI Guidelines"

Dort findest du:
- Admin View Layout Pattern (Breadcrumb → Titel → Content)
- Pflicht-Elemente (Base Template, Blocks)
- DaisyUI vs Bootstrap Mapping
- Template-Struktur Referenz
