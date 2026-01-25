# PRD: Admin-UI Marketplace Erweiterung

**Version:** 1.0
**Datum:** 2026-01-17
**Status:** In Umsetzung

---

## 1. Überblick

### Ziel

Erweiterung des V-Flask Marketplace Admin-UIs um die Verwaltung von:
- **Projekttypen** (CRUD)
- **Plugin-Preise** pro Projekttyp (Preismatrix mit Inline-Editing)
- **Plugin-Versionen** (CRUD mit Changelog)
- **Lizenz-Historie** (Read-only Audit-Trail)

### Kontext

Diese Erweiterung komplettiert die Migration des Plugin-Marketplaces von UDO-API nach V-Flask. Die neuen Models (ProjectType, PluginPrice, PluginVersion, LicenseHistory) wurden bereits erstellt und die API-Endpoints sind funktionsfähig.

### Tech-Stack (bestehend)

| Komponente | Version | Verwendung |
|------------|---------|------------|
| DaisyUI | 4.12 | CSS-Framework |
| Tailwind CSS | 3.x | Utility-First CSS |
| HTMX | 1.9 | Dynamische Updates ohne JS |
| Tabler Icons | - | Icon-Set |
| Flask-Login | - | Authentifizierung |

---

## 2. Features im Detail

### 2.1 Projekttyp-Verwaltung

Ermöglicht die Verwaltung von Projekttypen wie "Einzelkunde", "Branchenverzeichnis", "City Server" und "Intern".

#### Routes

| Methode | Route | Beschreibung |
|---------|-------|--------------|
| GET | `/admin/project-types` | Liste aller Projekttypen |
| GET | `/admin/project-types/new` | Formular: Neuen Typ anlegen |
| POST | `/admin/project-types/new` | Typ erstellen |
| GET | `/admin/project-types/<id>/edit` | Formular: Typ bearbeiten |
| POST | `/admin/project-types/<id>/edit` | Typ aktualisieren |
| POST | `/admin/project-types/<id>/toggle` | Aktiv/Inaktiv toggle (HTMX) |

#### Formular-Felder

| Feld | Typ | Validierung | Beschreibung |
|------|-----|-------------|--------------|
| code | Text | Required, Unique, Slug | Interner Code (z.B. `einzelkunde`) |
| name | Text | Required | Anzeigename (z.B. "Einzelkunde") |
| description | Textarea | Optional | Beschreibung |
| trial_days | Number | Required, >= 0 | Anzahl Testtage |
| is_free | Checkbox | - | Kostenloser Typ |
| is_active | Checkbox | - | Aktiv/Inaktiv |
| sort_order | Number | Required | Reihenfolge in Listen |

#### UI-Mockup (Liste)

```
┌─────────────────────────────────────────────────────────────┐
│ Projekttypen                                    [+ Neu]     │
├─────────────────────────────────────────────────────────────┤
│ Code           │ Name              │ Trial │ Status │ Aktion│
├────────────────┼───────────────────┼───────┼────────┼───────┤
│ einzelkunde    │ Einzelkunde       │ 30    │ ●      │ ✎ ⚙  │
│ business_dir   │ Branchenverz.     │ 14    │ ●      │ ✎ ⚙  │
│ city_server    │ City Server       │ 30    │ ●      │ ✎ ⚙  │
│ intern         │ Intern            │ 0     │ ●      │ ✎ ⚙  │
└────────────────┴───────────────────┴───────┴────────┴───────┘
```

---

### 2.2 Preismatrix (Inline-Editing)

Eine Tabelle, die alle Preise für ein Plugin nach Projekttyp und Abrechnungszyklus anzeigt. Jede Zelle ist direkt editierbar.

#### Routes

| Methode | Route | Beschreibung |
|---------|-------|--------------|
| GET | `/admin/plugins/<id>/prices` | Preismatrix-Ansicht |
| POST | `/admin/plugins/<id>/prices` | HTMX: Preis speichern |

#### UI-Mockup

```
┌─────────────────────────────────────────────────────────────────────┐
│ Preise für: CRM Plugin                          [← Zurück zu Plugins]│
├─────────────────────────────────────────────────────────────────────┤
│                 │ Einzelkunde │ Branchenverz. │ City Server │ Intern │
├─────────────────┼─────────────┼───────────────┼─────────────┼────────┤
│ Einmalig        │ [100,00 €]  │ [500,00 €]    │ [300,00 €]  │ [0 €]  │
│ Monatlich       │ [10,00 €]   │ [50,00 €]     │ [30,00 €]   │ [0 €]  │
│ Jährlich        │ [100,00 €]  │ [500,00 €]    │ [300,00 €]  │ [0 €]  │
├─────────────────┴─────────────┴───────────────┴─────────────┴────────┤
│ Setup-Gebühren                                                       │
├─────────────────┬─────────────┬───────────────┬─────────────┬────────┤
│ Einrichtung     │ [0 €]       │ [100,00 €]    │ [50,00 €]   │ [0 €]  │
└─────────────────┴─────────────┴───────────────┴─────────────┴────────┘
```

#### Interaktion

1. Klick auf Zelle aktiviert Input-Feld
2. Bei Fokus-Verlust (blur) → HTMX POST
3. Visuelles Feedback:
   - Grüner Rahmen = Gespeichert
   - Roter Rahmen = Fehler
   - Spinner während Speichern

#### HTMX-Implementierung

```html
<input type="text"
       name="price_cents"
       value="100,00"
       hx-post="/admin/plugins/1/prices"
       hx-trigger="blur"
       hx-vals='{"project_type_id": 1, "billing_cycle": "once"}'
       hx-swap="outerHTML"
       class="input input-bordered input-sm w-24">
```

---

### 2.3 Plugin-Versionen

Manuelle Verwaltung von Plugin-Versionen mit Changelog und Release-Notes.

#### Routes

| Methode | Route | Beschreibung |
|---------|-------|--------------|
| GET | `/admin/plugins/<id>/versions` | Liste der Versionen |
| GET | `/admin/plugins/<id>/versions/new` | Neue Version anlegen |
| POST | `/admin/plugins/<id>/versions/new` | Version erstellen |
| GET | `/admin/versions/<id>/edit` | Version bearbeiten |
| POST | `/admin/versions/<id>/edit` | Version aktualisieren |
| POST | `/admin/versions/<id>/set-current` | Als aktuelle Version markieren (HTMX) |

#### Formular-Felder

| Feld | Typ | Validierung | Beschreibung |
|------|-----|-------------|--------------|
| version | Text | Required, SemVer | Version (z.B. "1.2.0") |
| changelog | Textarea | Optional | Technisches Changelog |
| release_notes | Textarea | Optional | Öffentliche Release-Notes |
| min_v_flask_version | Text | Optional | Mindest-Framework-Version |
| is_stable | Checkbox | - | Stabile Version |
| is_breaking_change | Checkbox | - | Breaking Change |

#### UI-Mockup (Liste)

```
┌─────────────────────────────────────────────────────────────────┐
│ Versionen: CRM Plugin                           [+ Neue Version] │
├─────────────────────────────────────────────────────────────────┤
│ Version │ Status      │ Downloads │ Veröffentlicht │ Aktionen   │
├─────────┼─────────────┼───────────┼────────────────┼────────────┤
│ 1.2.0   │ ● Aktuell   │ 1.234     │ 17.01.2026     │ ✎          │
│ 1.1.0   │ ○ Stabil    │ 5.678     │ 01.12.2025     │ ✎ [Aktiv]  │
│ 1.0.0   │ ○ Stabil    │ 12.345    │ 15.10.2025     │ ✎ [Aktiv]  │
│ 0.9.0   │ ⚠ Beta      │ 234       │ 01.09.2025     │ ✎ [Aktiv]  │
└─────────┴─────────────┴───────────┴────────────────┴────────────┘
```

---

### 2.4 Lizenz-Historie

Read-only Audit-Trail für alle Lizenz-Statusänderungen. Zwei Ansichten:
1. **Global**: Alle Änderungen aller Lizenzen
2. **Detail**: Änderungen einer spezifischen Lizenz

#### Routes

| Methode | Route | Beschreibung |
|---------|-------|--------------|
| GET | `/admin/history` | Globale Historie |
| GET | `/admin/licenses/<id>/history` | Historie einer Lizenz |

#### UI-Mockup (Global)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Lizenz-Historie                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Filter: [Alle Aktionen ▼] [Datum von] [Datum bis] [Suchen]          │
├─────────────────────────────────────────────────────────────────────┤
│ 17.01.2026 14:32 │ trial_started │ Projekt A / CRM Plugin          │
│                  │ → trial       │ von: system                      │
├──────────────────┼───────────────┼──────────────────────────────────│
│ 17.01.2026 10:15 │ renewed       │ Projekt B / Newsletter Plugin   │
│                  │ active→active │ von: admin@example.com           │
├──────────────────┼───────────────┼──────────────────────────────────│
│ 16.01.2026 18:00 │ trial_expired │ Projekt C / Analytics Plugin    │
│                  │ trial→expired │ von: system (Automatic expiration)│
└──────────────────┴───────────────┴──────────────────────────────────┘
```

#### UI-Mockup (Detail - Timeline)

```
┌─────────────────────────────────────────────────────────────────┐
│ Historie: Projekt A / CRM Plugin                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ● 17.01.2026 14:32 - Trial gestartet                           │
│  │  Status: → trial                                              │
│  │  Läuft ab: 31.01.2026                                         │
│  │  von: system                                                  │
│  │                                                               │
│  ○ (Zukünftige Ereignisse...)                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Filter-Optionen

| Filter | Werte |
|--------|-------|
| Action | Alle, trial_started, trial_converted, trial_expired, renewed, suspended, revoked |
| Datum | Von/Bis Datepicker |
| Performer | Freitext-Suche |

---

## 3. Navigation

### Neue Menüpunkte in Admin-Sidebar

```
Dashboard
├── Übersicht
│
Marketplace
├── Plugins
├── Projekte
├── Lizenzen
├── Projekttypen (NEU)    ← ti-category
├── Lizenz-Historie (NEU) ← ti-history
│
Bestellungen
└── ...
```

### Plugin-Aktionen erweitern

Auf der Plugin-Detail-Seite zusätzliche Buttons:

```
[Bearbeiten] [Preise verwalten] [Versionen] [Löschen]
```

---

## 4. Templates

### Neue Template-Struktur

```
templates/admin/
├── project_types/
│   ├── list.html          # Projekttyp-Liste
│   └── form.html          # Projekttyp-Formular (Create/Edit)
├── plugins/
│   ├── prices.html        # Preismatrix (NEU)
│   └── versions/
│       ├── list.html      # Versions-Liste
│       └── form.html      # Versions-Formular
└── licenses/
    └── history.html       # Globale Historie (NEU)
```

### Partials (HTMX)

```
templates/admin/partials/
├── price_cell.html        # Einzelne Preis-Zelle für Inline-Edit
├── history_row.html       # Historie-Zeile für Lazy-Loading
└── version_row.html       # Versions-Zeile mit Toggle-Button
```

---

## 5. Kritische Dateien

| Datei | Aktion | Beschreibung |
|-------|--------|--------------|
| `app/routes/admin.py` | ERWEITERN | Neue Routes hinzufügen |
| `app/templates/admin/base.html` | ERWEITERN | Navigation anpassen |
| `app/templates/admin/project_types/*.html` | NEU | Projekttyp-Templates |
| `app/templates/admin/plugins/prices.html` | NEU | Preismatrix |
| `app/templates/admin/plugins/versions/*.html` | NEU | Versions-Templates |
| `app/templates/admin/licenses/history.html` | NEU | Historie-Template |

---

## 6. Verifikation

### Manuelle Tests

```bash
# Admin-UI starten
cd /Users/cvogelsang/projektz/v-flask/marketplace
uv run flask run --port 5001

# Im Browser testen:
1. http://localhost:5001/admin/project-types
   → Liste mit 4 Projekttypen sichtbar
   → Neu-Button funktioniert
   → Edit-Button öffnet Formular
   → Toggle ändert Status

2. http://localhost:5001/admin/plugins/1/prices
   → Preismatrix wird angezeigt
   → Inline-Edit speichert bei Fokus-Verlust
   → Visuelles Feedback funktioniert

3. http://localhost:5001/admin/plugins/1/versions
   → Versions-Liste wird angezeigt
   → Neue Version kann angelegt werden
   → "Als aktuell markieren" funktioniert

4. http://localhost:5001/admin/history
   → Globale Historie wird angezeigt
   → Filter funktionieren
   → Links zu Lizenz-Details funktionieren

5. http://localhost:5001/admin/licenses/1/history
   → Timeline-Darstellung korrekt
   → Alle Einträge sichtbar
```

---

## 7. Abgrenzung

### Nicht im Scope

- Automatische Versionierung beim Plugin-Upload
- Preisänderungs-Historie
- Export-Funktionen (CSV, PDF)
- Batch-Operationen für Preise
- E-Mail-Benachrichtigungen für Trials

### Zukünftige Erweiterungen

- Drag & Drop für Sortierung
- Bulk-Price-Import via CSV
- Versions-Diff-Ansicht
- Audit-Log-Export
