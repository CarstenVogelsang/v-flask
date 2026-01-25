# VRS Platform Architecture Plan

> **Umbenennung:** v-flask → vrs-core (Vogelsang Retail Service)

## Übersicht

Trennung des monolithischen v-flask Repositories in zwei separate Repositories für SaaS-Deployment.

## Aktuelle Situation

```text
v-flask/                          # Monolithisches Repository
├── src/v_flask/                  # Core Framework (kostenlos)
├── src/v_flask_plugins/          # Plugins (kostenpflichtig!)
└── marketplace/                  # Marketplace Server (zentral)
```

**Probleme:**

1. Bei Deployment landet alles beim Kunden (auch kostenpflichtige Plugins)
2. Keine klare Trennung zwischen Core und kostenpflichtigen Komponenten
3. Kunden könnten theoretisch auf Plugin-Quellcode zugreifen

## Neue Repository-Struktur

### Repository 1: `vrs-core` (öffentlich/kostenlos)

```text
vrs-core/
├── src/vrs_core/
│   ├── __init__.py              # VRS Klasse (ehemals VFlask)
│   ├── plugins/
│   │   ├── manifest.py          # PluginManifest Basisklasse
│   │   ├── registry.py          # PluginRegistry
│   │   ├── manager.py           # PluginManager
│   │   └── marketplace_client.py # Client für Marketplace-API
│   ├── auth/                    # Auth-System
│   ├── admin/                   # Admin-Basis
│   └── templates/               # Core-Templates
├── src/vrs_bootstrap/
│   ├── __init__.py
│   ├── wizard.py                # Setup-Wizard Logik
│   ├── routes.py                # /setup/ Routes
│   └── templates/
│       └── wizard/              # Setup-Wizard UI
├── pyproject.toml
└── docs/
    └── MIGRATION.md             # Migration von v-flask
```

**Enthält:**

- Core Framework (User, Auth, Config, Admin-Basis)
- Plugin-System (Manifest, Registry, Manager)
- Marketplace-Client (API-Consumer)
- Setup-Wizard für Bootstrap

**Enthält NICHT:**

- Plugins (kontakt, crm, katalog, etc.)
- Marketplace-Server
- Plugin-Quellcode

### Repository 2: `vrs-marketplace` (privat)

```text
vrs-marketplace/
├── server/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── api.py           # /api/plugins, /api/projects
│   │   │   └── admin.py         # Admin-Interface
│   │   └── models/
│   │       ├── plugin.py
│   │       ├── license.py
│   │       └── project.py
│   └── pyproject.toml
├── plugins/
│   ├── kontakt/
│   ├── crm/
│   ├── katalog/
│   ├── shop/
│   ├── pim/
│   └── ... (alle anderen)
└── docs/
```

**Enthält:**

- Marketplace-Server (API + Admin)
- Alle kostenpflichtigen Plugins
- Lizenz-Verwaltung
- Projekt-Verwaltung

---

## Betroffene Projekte (Migration erforderlich)

| Projekt              | Pfad                          | Aktion              |
| -------------------- | ----------------------------- | ------------------- |
| mfr_preiser          | `/projektz/mfr_preiser`       | v-flask → vrs-core  |
| vz_fruehstueckenclick| `/projektz/vz_fruehstueckenclick` | v-flask → vrs-core |
| vz_spielwaren        | `/projektz/vz_spielwaren`     | v-flask → vrs-core  |

---

## Bootstrap-Flow (Neues Projekt)

### Phase 1: Kunde bestellt Projekt

```text
1. Kunde besucht marketplace.vrs.gmbh
2. Login / Registrierung
3. "Neues Projekt starten oder vorhandenes Projekt übernehmen (wir bieten fertige Demo-Projekte zur Übernahme als Abo an)"
4. Fragebogen:
   - Projekttyp? (Verzeichnis / Hersteller-Portal / Webseite /Cityserver-Instanz)
   - Projektname?
   - Domain?
   - Je nach Projekttyp gibt es Plugin-Bundles mit Gesamtpreis (Summe der Plugin-Preise) zur Auswahl
5. Bestätigung + Zahlung (Stripe oder Rechnung)
```

### Phase 2: Automatisches Deployment

```json
1. Marketplace speichert Projekt-Konfiguration (modell projects vorhanden, muss erweitert werden)
   - project_id: uuid
   - project_type: "verzeichnis"
   - domain: "steuerberater.tel"
   - plugins: ["kontakt", "crm", "verzeichnis"]
   - status: "pending"

2. Marketplace ruft Coolify API auf (Beispiel, noch zu evaluieren):
   POST /api/v1/applications
   {
     "name": "steuerberater-tel",
     "git_repository": "github.com/vrs/vrs-core",
     "environment_variables": {
       "VRS_PROJECT_ID": "<project_id>",
       "VRS_MARKETPLACE_URL": "https://marketplace.vrs.gmbh",
       "VRS_MARKETPLACE_KEY": "<api_key>"
     }
   }

3. Coolify deployt vrs-core Docker-Image
4. vrs-core startet, erkennt VRS_PROJECT_ID
5. vrs-core ruft Marketplace API auf und lädt Plugins herunter
6. Datenbank-Migration läuft
7. Projekt ist bereit unter der gewählten Domain
   - Admin-Login und Schulungstermin-Buchungslink wird per E-Mail versendet


```

### Phase 3: Automatischer Plugin-Download


```text
1. vrs-core startet
2. Prüft: Ist Projekt konfiguriert?
   - Nein → Zeige Setup-Wizard (manueller Flow)
   - Ja → Automatischer Plugin-Download

3. Automatischer Flow:
   a) vrs-core ruft Marketplace-API auf
      GET /api/projects/<project_id>/config
      → Liefert: plugins, settings, etc.

   b) Für jedes Plugin:
      POST /api/plugins/<name>/download
      → Liefert: Plugin-ZIP

   c) Plugins werden installiert

   d) Datenbank-Migration läuft

   e) Projekt ist bereit

4. Manueller Flow (Setup-Wizard):
   - User öffnet Browser
   - Sieht Setup-Wizard
   - Wählt Projekttyp + Plugins
   - System lädt Plugins vom Marketplace
```

---

## Implementierungsschritte

### Schritt 1: Repository-Trennung

1. **vrs-core Repository erstellen**
   - Neues Git Repository
   - Core-Code aus v-flask kopieren
   - Plugins entfernen
   - Umbenennung: v_flask → vrs_core
   - pyproject.toml anpassen

2. **vrs-marketplace Repository erstellen**
   - Neues Git Repository
   - Marketplace-Code aus v-flask/marketplace kopieren
   - Alle Plugins aus v_flask_plugins kopieren
   - Anpassungen für standalone Betrieb

3. **v-flask archivieren**
   - README mit Hinweis auf vrs-core
   - Keine weiteren Updates

### Schritt 2: Bootstrap-System

1. **Setup-Wizard in vrs-core**
   - `/setup/` Route
   - Projekttyp-Auswahl
   - Plugin-Auswahl
   - API-Calls zum Marketplace

2. **Automatischer Bootstrap**
   - Environment-Variable `VRS_PROJECT_ID`
   - Startup-Script prüft Konfiguration
   - Automatischer Plugin-Download

### Schritt 3: Projekt-Migration

1. **pyproject.toml aktualisieren**

   ```toml
   dependencies = ["vrs-core[all]"]

   [tool.uv.sources]
   vrs-core = { path = "../vrs-core", editable = true }
   ```

2. **Imports ändern**

   ```python
   # Alt:
   from v_flask import VFlask, db
   from v_flask_plugins.crm import CRMPlugin

   # Neu:
   from vrs_core import VRS, db
   # Plugins werden dynamisch geladen
   ```

3. **Testen**

### Schritt 4: Coolify-Integration

1. **Marketplace API erweitern**
   - `POST /api/projects` - Projekt anlegen
   - `POST /api/projects/<id>/deploy` - Deployment triggern

2. **Coolify API Integration**
   - API-Key Konfiguration
   - Automatisches Deployment

---

## Kritische Dateien

| Datei | Repository | Aktion |
| ----- | ---------- | ------ |
| `src/vrs_core/__init__.py` | vrs-core | NEU: VRS Klasse |
| `src/vrs_core/plugins/marketplace_client.py` | vrs-core | Anpassen |
| `src/vrs_bootstrap/wizard.py` | vrs-core | NEU: Setup-Wizard |
| `server/app/routes/api.py` | vrs-marketplace | Erweitern |
| `mfr_preiser/pyproject.toml` | mfr_preiser | Migration |
| `vz_fruehstueckenclick/pyproject.toml` | vz_fruehstueckenclick | Migration |
| `vz_spielwaren/pyproject.toml` | vz_spielwaren | Migration |

---

## Verifikation

1. **vrs-core standalone:** Projekt startet ohne Plugins, zeigt Setup-Wizard
2. **Marketplace-API:** `/api/plugins` liefert Plugin-Liste
3. **Plugin-Download:** Plugin kann heruntergeladen und installiert werden
4. **Bootstrap-Flow:** Neues Projekt wird automatisch konfiguriert
5. **Migration:** Bestehende Projekte laufen mit vrs-core

---

## Coolify Deployment-Modell

### Aktuelles Verständnis

```text
Kundenprojekt-Repo (z.B. vz_steuerberater)
├── pyproject.toml
│   └── dependencies = ["vrs-core"]
├── app/
│   └── __init__.py
└── ...

         ↓ Coolify klont Repo

Nixpacks erkennt Python-Projekt
         ↓ installiert Dependencies

vrs-core wird von [???] geladen
         ↓

Docker-Container wird gebaut
         ↓

Container startet auf Server
```

### Offene Frage: Woher kommt vrs-core?

| Option | Pro | Contra |
| ------ | --- | ------ |
| **Git URL** | Einfach, keine Infrastruktur | Zugriff auf Git-Repo nötig |
| **PyPI** | Standard, pip install funktioniert | Öffentlich oder PyPI-Account nötig |
| **Private Registry** | Volle Kontrolle | Infrastruktur-Aufwand |

---

## Offene Fragen

1. **Package-Distribution:** Soll vrs-core auf PyPI oder eigenem Server?
2. **Plugin-Updates:** Wie werden Plugin-Updates signalisiert?
3. **Lizenz-Prüfung:** Online-Validierung bei jedem Start oder Offline-Token?
4. **Multi-Tenancy:** Ein Marketplace für alle Kunden oder kundenspezifisch?
5. **Coolify-Details:** Wie genau funktioniert Nixpacks mit uv/pip? Können Git-Dependencies aufgelöst werden?

---

## Nächste Schritte

1. **Coolify-Recherche:** Detaillierte Analyse des Nixpacks-Buildprozesses
2. **Repository-Trennung beginnen:** vrs-core erstellen
3. **Migration testen:** Ein Projekt (z.B. mfr_preiser) auf vrs-core umstellen
