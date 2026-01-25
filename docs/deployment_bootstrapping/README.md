# VRS Deployment & Bootstrapping Dokumentation

> **Für:** Claude Code (agentische KI) zur Implementierung  
> **Version:** 1.0  
> **Datum:** Januar 2026

---

## Dokumentenübersicht

| Dokument | Beschreibung | Für wen |
|----------|--------------|---------|
| [VRS_DEPLOYMENT_SPEC.md](./VRS_DEPLOYMENT_SPEC.md) | Hauptspezifikation mit Gesamtübersicht | Alle |
| [VRS_MODELS_SPEC.md](./VRS_MODELS_SPEC.md) | SQLAlchemy Model-Definitionen | Backend-Entwicklung |
| [VRS_ORCHESTRATOR_SPEC.md](./VRS_ORCHESTRATOR_SPEC.md) | Provisioning-Logik & API-Clients | Backend-Entwicklung |
| [VRS_API_INTEGRATIONS.md](./VRS_API_INTEGRATIONS.md) | Externe API-Dokumentation (INWX, Coolify, Hetzner) | Backend-Entwicklung |

---

## Zusammenfassung

### Was wird gebaut?

Ein **automatisiertes Provisionierungs-System** für VRS SaaS-Projekte:

```
Kunde bestellt → DNS wird konfiguriert → Coolify deployed → vrs-core startet → Projekt ist live
```

### Kernkomponenten

1. **Marketplace Admin UI** – Sachbearbeiter verwalten Projekte
2. **Orchestrator Service** – Koordiniert die Provisionierung
3. **INWX Client** – DNS & Domain-Management
4. **Coolify Client** – Container-Deployment
5. **vrs-core Bootstrap** – Automatischer Plugin-Download

### Technologie-Stack

| Bereich | Technologie |
|---------|-------------|
| Backend | Python/Flask (vrs-marketplace) |
| Datenbank | PostgreSQL |
| DNS | INWX API (JSON-RPC) |
| Deployment | Coolify API (REST) |
| Server | Hetzner Cloud VPS |
| SSL | Let's Encrypt (via Traefik) |

---

## Implementierungsreihenfolge (Empfehlung)

### Phase 1: Models & Basis

1. Neue Enums erstellen (`enums.py`)
2. Neue Models erstellen:
   - `BaseDomain`
   - `ProjectDomain`
   - `Server`
   - `ProvisioningLog`
   - `PreviewAccess`
3. `Project` Model erweitern
4. Alembic-Migrationen erstellen
5. Seed-Daten für `BaseDomain` und `Server`

### Phase 2: API Clients

1. `INWXClient` implementieren
2. `CoolifyClient` implementieren
3. Tests für beide Clients

### Phase 3: Orchestrator

1. `ProjectProvisioner` implementieren
2. Server-Selection-Strategien
3. Async Task Queue Setup

### Phase 4: Integration

1. API-Endpoints für Projekt-Erstellung
2. Admin-UI für Sachbearbeiter
3. E-Mail-Benachrichtigungen

### Phase 5: vrs-core Bootstrap

1. Auto-Bootstrap bei Start
2. Plugin-Download-Logik
3. Health-Check Endpoint

---

## Kritische Hinweise für Claude Code

### 1. Bestehende Models

Die Dateien `project.py`, `license.py`, `plugin_price.py`, `project_type.py`, `license_history.py` existieren bereits. **Nicht überschreiben**, sondern erweitern!

### 2. Bundle-Model

Das `Bundle`-Model in `VRS_MODELS_SPEC.md` ist ein **Vorschlag**. Bitte prüfen, ob bereits Planungen/Code für Bundles existieren und entsprechend anpassen.

### 3. Enums statt Strings

Status-Felder verwenden SQLAlchemy `Enum`, nicht String-Felder. Siehe `enums.py` in `VRS_MODELS_SPEC.md`.

### 4. Async

Der Orchestrator verwendet `async/await`. Flask benötigt ggf. `flask[async]` oder einen async-kompatiblen Wrapper.

### 5. Secrets

Niemals Credentials in Code committen. Alle sensiblen Daten aus Environment-Variablen laden.

### 6. Test-APIs

INWX und Coolify haben Test-Umgebungen. Während der Entwicklung diese nutzen!

- INWX OT&E: `https://api.ote.domrobot.com/jsonrpc/`
- Coolify: Eigene Test-Instanz empfohlen

---

## Offene Punkte (für spätere Phasen)

Diese Punkte sind dokumentiert aber **nicht in v1 enthalten**:

1. **E-Mail-Integration (Brevo)** – MX/SPF/DKIM Records
2. **Automatische Hetzner-Server-Erstellung** – Via Coolify Hetzner-Integration
3. **Stripe-Abos** – Detaillierte Billing-Integration
4. **Domain-Transfer-Monitoring** – Kann mehrere Tage dauern

---

## Fragen?

Bei Unklarheiten die Hauptspezifikation (`VRS_DEPLOYMENT_SPEC.md`) konsultieren. Die Dokumente sind hierarchisch aufgebaut:

```
VRS_DEPLOYMENT_SPEC.md        ← Überblick & Konzepte
    ├── VRS_MODELS_SPEC.md    ← Datenmodell
    ├── VRS_ORCHESTRATOR_SPEC.md  ← Implementierung
    └── VRS_API_INTEGRATIONS.md   ← API-Details
```
