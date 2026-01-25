# UI/E2E Tests für V-Flask

Dieses Verzeichnis enthält End-to-End-Tests für V-Flask Plugins und Integrationen.

## Struktur

```
tests/ui/
├── README.md               # Diese Datei
├── specs/                  # Test-Spezifikationen (YAML)
│   └── *.yaml             # Einzelne Test-Definitionen
├── results/                # Test-Ergebnisse (Git-ignored)
│   └── YYYY-MM-DD_*.md    # Markdown-Reports
└── screenshots/            # Fehler-Screenshots (Git-ignored)
    └── *.png
```

## Test-Specs ausführen

Die YAML-Spezifikationen werden von Claude Code via Playwright ausgeführt:

```bash
# Interaktiv mit Claude Code
claude "Führe den E2E-Test tests/ui/specs/content-plugin-media-picker.yaml aus"
```

## Test-Spezifikation Format

Jede YAML-Spec definiert:

- **meta**: Name, Version, beteiligte Plugins/Projekte
- **prerequisites**: Benötigte Server, Credentials
- **steps**: Einzelne Testschritte mit Erwartungen
- **on_failure**: Verhalten bei Fehlern (Screenshot, Abort)

## Konventionen

1. **Keine Workarounds**: Bei Fehlern wird der echte Bug gefixt
2. **Kompletter Re-run**: Nach Fixes wird der gesamte Test wiederholt
3. **Semantische Targets**: Beschreibe UI-Elemente menschenlesbar
4. **Screenshots bei Fehlern**: Automatisch in `screenshots/` gespeichert

## Git-Ignore

Die Dateien in `results/` und `screenshots/` werden nicht versioniert:

```gitignore
tests/ui/results/
tests/ui/screenshots/
```

---

## YAML-Spec Referenz

### Vollständiges Schema

```yaml
# Test-Spezifikation für Claude Code E2E-Tests
# Format: YAML 1.2

meta:
  name: string           # Lesbare Bezeichnung des Tests
  id: string             # Eindeutige ID (kebab-case, z.B. "e2e-content-media-picker")
  version: string        # Semantic Version (z.B. "1.0")
  author: string         # Ersteller des Tests
  created: date          # Erstelldatum (YYYY-MM-DD)
  plugins: [string]      # Beteiligte V-Flask Plugins (z.B. ["content", "media"])
  projects: [string]     # Beteiligte Projekte (z.B. ["v-flask", "vz_fruehstueckenclick"])

prerequisites:
  servers:               # Benötigte Server für den Test
    - name: string       # Lesbare Bezeichnung (z.B. "Marketplace")
      command: string    # Start-Befehl (z.B. "uv run flask run --debug --port 5800")
      cwd: string        # Arbeitsverzeichnis (absoluter Pfad)
      port: number       # Port-Nummer
      health_check: url  # URL für Verfügbarkeitsprüfung (z.B. "http://localhost:5800/")

  credentials:           # Login-Daten (Key = Referenz-Name)
    <name>:              # Referenzname für steps.credentials
      email: string
      password: string

  environment:           # Benötigte Umgebungsvariablen
    <project>:           # Projektname
      <VAR_NAME>: "required" | "optional"  # Env-Variable mit Status

steps:                   # Testschritte (werden sequenziell ausgeführt)
  - id: number           # Schrittnummer (1, 2, 3, ...)
    name: string         # Beschreibung des Schritts
    action: string       # Aktionstyp (siehe unten)
    url?: string         # Für action: navigate
    target?: string      # Semantische Beschreibung des UI-Elements
    fallback_selector?: string  # CSS/Playwright-Selektor als Fallback
    value?: string       # Für action: fill, select
    credentials?: string # Referenz zu prerequisites.credentials
    condition?: string   # Für action: conditional_click
    server?: string      # Für action: restart_server
    slot?: string        # Für Seitenzuweisungen
    expect: [string]     # Erwartete Ergebnisse (Assertions)

on_failure:
  screenshot: boolean    # Screenshot bei Fehler speichern
  abort_test: boolean    # Test abbrechen bei Fehler
  log_console_errors: boolean    # Browser-Console-Errors loggen
  save_network_requests: boolean # Netzwerk-Requests speichern

cleanup: [string]        # Aufräumschritte (manuell beschrieben)

verification:            # Finale Prüfungen
  final_checks: [string] # Liste der End-Assertions
```

### Aktionstypen (action)

| Action | Beschreibung | Benötigte Felder |
|--------|--------------|------------------|
| `navigate` | Zu URL navigieren | `url` |
| `navigate_and_login` | Navigieren + Login-Formular ausfüllen | `url`, `credentials` |
| `click` | Element anklicken | `target` |
| `conditional_click` | Klicken wenn Bedingung erfüllt | `target`, `condition` |
| `fill` | Textfeld ausfüllen | `target`, `value` |
| `fill_and_submit` | Ausfüllen + Enter drücken | `target`, `value` |
| `select` | Dropdown-Option wählen | `target`, `value` |
| `restart_server` | Server neu starten | `server` |

### Semantische Targets

Statt CSS-Selektoren beschreibst du UI-Elemente menschenlesbar:

```yaml
# Gut: Semantisch
target: "Installieren-Button für Content-Plugin"
target: "Tab 'Stock-Fotos' oder 'Pexels'"
target: "Erstes Suchergebnis-Bild"

# Fallback: CSS-Selektor (wenn nötig)
target: "Speichern-Button"
fallback_selector: "button[type='submit'].btn-primary"
```

---

## Prompt-Template für neue Tests

Kopiere dieses Template, um Claude Code einen neuen E2E-Test erstellen zu lassen:

```
Erstelle einen neuen E2E-Test für [FEATURE/PLUGIN].

Referenz: tests/ui/README.md (YAML-Spec Format)
Vorlage: tests/ui/specs/content-plugin-media-picker.yaml

Der Test soll prüfen:
1. [Schritt 1]
2. [Schritt 2]
3. [Schritt 3]
4. ...

Beteiligte Projekte: [v-flask, vz_fruehstueckenclick, ...]
Voraussetzungen: [Server, API-Keys, ...]
```

### Beispiel-Prompts

**Plugin-Installation testen:**
```
Erstelle einen E2E-Test für das Katalog-Plugin.
Der Test soll prüfen:
1. Plugin installieren via Marketplace
2. Katalog-Admin aufrufen
3. Neuen Eintrag erstellen mit Bild
Beteiligte Projekte: v-flask, vz_fruehstueckenclick
```

**Feature-Test:**
```
Erstelle einen E2E-Test für den Icon-Picker.
Der Test soll prüfen:
1. Admin-Formular mit Icon-Picker öffnen
2. Icon suchen und auswählen
3. Formular speichern
4. Icon wird korrekt angezeigt
```

---

## Test-Ergebnis Format

Nach jedem Testlauf wird ein Ergebnis-Dokument in `results/` erstellt:

**Dateiname:** `YYYY-MM-DD_<test-id>.md`

### Struktur

```markdown
# Test-Ergebnis: [Test-Name]

**Spec:** `specs/<filename>.yaml`
**Datum:** YYYY-MM-DD
**Status:** ✅ PASSED | ❌ FAILED | ⚠️ PARTIAL
**Durchlauf:** N (optional: Hinweis auf vorherige Läufe)

## Zusammenfassung

| Phase | Status | Bemerkung |
|-------|--------|-----------|
| 1. [Phase] | ✅/❌ | [Details] |
| 2. [Phase] | ✅/❌ | [Details] |
| ... | ... | ... |

## Behobene Bugs (während Test)

### Bug: [Kurzbeschreibung]

**Root Cause:** [Ursache]

**Fixes:**
- [Datei]: [Änderung]

## Verifikation

- [x] [Check 1]
- [x] [Check 2]
- [ ] [Offener Punkt]
```

### Status-Definitionen

| Status | Bedeutung |
|--------|-----------|
| ✅ PASSED | Alle Steps erfolgreich |
| ❌ FAILED | Test abgebrochen wegen Fehler |
| ⚠️ PARTIAL | Teilweise erfolgreich, manuelle Intervention nötig |
| 🔄 PASSED (nach Bug-Fix) | Erfolgreich nach Fehlerbehebung |
