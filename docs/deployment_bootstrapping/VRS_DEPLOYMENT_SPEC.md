# VRS Deployment & Bootstrapping – Technische Spezifikation

> **Version:** 1.0  
> **Datum:** Januar 2026  
> **Status:** Zur Implementierung freigegeben

---

## 1. Überblick

Dieses Dokument beschreibt die vollautomatische Provisionierung von VRS-Kundenprojekten. Der Prozess umfasst:

1. Kundenbestellung im VRS Marketplace
2. Domain-Handling (Registrierung, Transfer, Subdomain)
3. DNS-Konfiguration via INWX API
4. Server-Provisionierung via Coolify API (optional: Hetzner API)
5. Automatisches Bootstrapping des vrs-core Frameworks
6. Plugin-Auslieferung und Lizenzierung
7. Benachrichtigung des Kunden

**Ziel:** Minimaler manueller Aufwand. Sachbearbeiter sollen Projekte über eine Verwaltungsoberfläche provisionieren können, ohne technische Kenntnisse von Coolify, DNS oder Server-Administration.

---

## 2. Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VRS Marketplace                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Web UI    │  │  Admin UI   │  │  REST API   │  │ Orchestrator│ │
│  │  (Kunde)    │  │(Sachbearb.) │  │ (Satelliten)│  │  (Async)   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
│                                                            │        │
│                                                            ▼        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Provisioning Engine                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │  │  INWX    │  │ Coolify  │  │ Hetzner  │  │    Email     │  │  │
│  │  │  Client  │  │  Client  │  │  Client  │  │   Notifier   │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   INWX DNS   │      │   Coolify    │      │   Hetzner    │
│              │      │   Server     │      │    Cloud     │
└──────────────┘      └──────────────┘      └──────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Hetzner VPS N   │
                    │  ┌────────────┐  │
                    │  │ vrs-core   │  │
                    │  │ + Plugins  │  │
                    │  │ + Traefik  │  │
                    │  └────────────┘  │
                    └──────────────────┘
```

---

## 3. Projekt-Typen und Anwendungsfälle

### 3.1 Neue Projekte (Self-Service)

Kunde erstellt selbstständig ein neues Projekt:
1. Wählt Projekttyp (Verzeichnis, Einzelkunde, City Server, etc.)
2. Wählt Plugin-Bundle oder einzelne Plugins
3. Domain-Auswahl:
   - Subdomain unter Basis-Domain (z.B. `mein-projekt.vrs.gmbh`)
   - Neue Domain registrieren
   - Eigene Domain transferieren
4. Zahlung (Prepaid via Stripe oder Rechnung nach Vereinbarung)
5. Automatische Provisionierung

### 3.2 Demo-Projekte zur Übernahme

Vorbereitete Projekte, die Kunden übernehmen können:
1. Demo-Projekt ist bereits deployed
2. Zugang über **Preview-Protection** (Magic Link / Code)
3. Kunde bewertet das Demo
4. Bei Übernahme:
   - Preview-Protection wird deaktiviert
   - Domain wird zugewiesen (ggf. von Subdomain auf eigene Domain)
   - Abrechnung startet
5. Projekt-Eigentümerschaft wechselt

### 3.3 Bestehende Projekte (Migration)

Projekte, die bereits existieren und Domains haben:
- steuerberater.tel
- fruehstueckenclick.de
- spielwaren.xyz (etc.)

Diese werden manuell in das System importiert mit:
- Vorhandener INWX Domain-ID
- Vorhandener DNS-Record-IDs
- Bestehendem Coolify-Deployment (nach Migration)

---

## 4. Domain-Handling

### 4.1 Domain-Optionen

| Option | Beschreibung | Kosten | DNS-Handling |
|--------|--------------|--------|--------------|
| **Subdomain** | `projekt.vrs.gmbh` | Kostenlos | A-Record + CNAME(www) |
| **Neue Domain** | Registrierung über INWX | Domain-Preis | Vollständige DNS-Zone |
| **Transfer** | Von anderem Registrar | Transfer-Gebühr | Vollständige DNS-Zone |
| **Bestehend** | Bereits bei uns | - | Nur Records anpassen |

### 4.2 Basis-Domains für Subdomains

Es gibt ein Model `BaseDomain` zur Verwaltung verfügbarer Basis-Domains:

- `vrs.gmbh` (primär)
- Weitere können hinzugefügt werden

Einem Projekt wird bei Subdomain-Wahl eine Basis-Domain zugewiesen.

### 4.3 DNS-Records (Initial)

Für jedes neue Projekt werden folgende Records angelegt:

| Typ | Name | Wert | TTL |
|-----|------|------|-----|
| A | `@` oder Subdomain | Server-IP | 300 |
| CNAME | `www` | `@` | 300 |

**Später (out of scope für v1):**
- MX-Records für E-Mail (Brevo-Integration)
- TXT-Records für SPF/DKIM
- AAAA für IPv6 (wenn verfügbar)

### 4.4 Domain-Registrierung (INWX)

```
Kunde wählt "Neue Domain registrieren"
        │
        ▼
┌─────────────────────────────┐
│  Domain-Verfügbarkeit       │
│  prüfen (INWX API)          │
│  domain.check               │
└─────────────────────────────┘
        │
        ▼ verfügbar
┌─────────────────────────────┐
│  Preis anzeigen             │
│  (TLD-abhängig)             │
└─────────────────────────────┘
        │
        ▼ Kunde bestätigt
┌─────────────────────────────┐
│  Domain registrieren        │
│  domain.create              │
│  → inwx_domain_id speichern │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  DNS-Zone anlegen           │
│  nameserver.createRecord    │
│  → inwx_record_ids speichern│
└─────────────────────────────┘
```

### 4.5 Domain-Transfer (INWX)

```
Kunde wählt "Domain transferieren"
        │
        ▼
┌─────────────────────────────┐
│  Auth-Code abfragen         │
│  (vom Kunden)               │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Transfer initiieren        │
│  domain.transfer            │
│  Status: PENDING_TRANSFER   │
└─────────────────────────────┘
        │
        ▼ (async, kann Tage dauern)
┌─────────────────────────────┐
│  Transfer-Status prüfen     │
│  (Polling oder Webhook)     │
└─────────────────────────────┘
        │
        ▼ Transfer abgeschlossen
┌─────────────────────────────┐
│  DNS-Records anlegen        │
│  Deployment fortsetzen      │
└─────────────────────────────┘
```

---

## 5. Provisionierungs-Flow

### 5.1 Sequenzdiagramm

```
Kunde          Marketplace       Orchestrator      INWX         Coolify       vrs-core
  │                 │                 │              │              │              │
  │─── Bestellung ──▶                 │              │              │              │
  │                 │                 │              │              │              │
  │                 │── Queue Job ───▶│              │              │              │
  │                 │                 │              │              │              │
  │                 │                 │── DNS ──────▶│              │              │
  │                 │                 │◀─ Record ID ─│              │              │
  │                 │                 │              │              │              │
  │                 │                 │── Create ───────────────────▶              │
  │                 │                 │   Project    │              │              │
  │                 │                 │◀─ UUID ──────────────────────│              │
  │                 │                 │              │              │              │
  │                 │                 │── Create App ───────────────▶              │
  │                 │                 │   + Env Vars │              │              │
  │                 │                 │◀─ App UUID ──────────────────│              │
  │                 │                 │              │              │              │
  │                 │                 │── Deploy ───────────────────▶              │
  │                 │                 │              │              │── Build ────▶│
  │                 │                 │              │              │              │
  │                 │                 │              │              │◀── Health ───│
  │                 │                 │◀─ Running ──────────────────│              │
  │                 │                 │              │              │              │
  │◀── E-Mail ──────────────────────│              │              │              │
  │   (Login-Daten)│                 │              │              │              │
```

### 5.2 Status-Übergänge

```
DRAFT ──────────────▶ PENDING_PAYMENT
                            │
                            ▼ (Zahlung bestätigt oder Rechnung)
                     PENDING_DOMAIN
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
      (Subdomain)    (Registrierung)   (Transfer)
       sofort          ~Minuten        ~1-5 Tage
            │               │               │
            └───────────────┼───────────────┘
                            ▼
                     PROVISIONING
                            │
                            ▼ (Coolify Deployment)
                     BOOTSTRAPPING
                            │
                            ▼ (Health Check OK)
                        ACTIVE
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
       SUSPENDED                        ARCHIVED
    (Zahlungsproblem)                  (Gekündigt)
```

### 5.3 Fehlerbehandlung

Bei Fehlern während der Provisionierung:

1. Status wird auf `ERROR` gesetzt
2. `provisioning_error` enthält Details
3. Sachbearbeiter wird benachrichtigt
4. Retry-Mechanismus für transiente Fehler (max 3 Versuche)
5. Manueller Eingriff bei persistenten Fehlern

---

## 6. Preview-Protection (Demo-Projekte)

### 6.1 Konzept

Demo-Projekte und nicht-freigegebene Projekte werden durch einen vorgeschalteten Login-Screen geschützt:

- **Unabhängig** vom Backend-Login
- **Schützt** auch öffentliche Frontend-Seiten
- **Verhindert** Indexierung durch Suchmaschinen
- **Zugang** via Magic Link oder Code

### 6.2 Implementierung

```python
# In vrs-core: Middleware für Preview-Protection

class PreviewProtectionMiddleware:
    """
    Prüft bei jedem Request, ob Projekt im Preview-Modus ist.
    Falls ja: Redirect zu Preview-Login, außer:
    - Session hat gültigen Preview-Token
    - Request ist für Preview-Login-Seite selbst
    - Request ist für Health-Check Endpoint
    """
    
    def check_preview_access(self, request):
        if not current_project.preview_protection_enabled:
            return True
        
        # Ausnahmen
        if request.path in ['/preview-login', '/health', '/api/health']:
            return True
        
        # Token in Session prüfen
        token = session.get('preview_token')
        if token and self.validate_token(token):
            return True
        
        return False  # Redirect zu Preview-Login
```

### 6.3 Zugangs-Methoden

| Methode | Beschreibung |
|---------|--------------|
| **Magic Link** | Einmaliger Link per E-Mail, gültig für X Stunden |
| **Code** | 6-stelliger Code, manuell mitgeteilt |
| **Sachbearbeiter** | Kann jederzeit Preview-Protection deaktivieren |

### 6.4 SEO-Schutz

Zusätzlich zum Login-Screen:

```html
<!-- robots meta tag -->
<meta name="robots" content="noindex, nofollow">

<!-- X-Robots-Tag Header -->
X-Robots-Tag: noindex, nofollow
```

---

## 7. SSL/TLS Zertifikate

### 7.1 Strategie

- **Let's Encrypt** für alle Domains (kostenlos)
- **Automatische Erneuerung** via Traefik in Coolify
- **Jedes Projekt** terminiert SSL selbst

### 7.2 Coolify-Konfiguration

Bei Erstellung einer Application wird automatisch SSL aktiviert:

```json
{
  "domains": "https://projekt.vrs.gmbh",
  "is_force_https_enabled": true
}
```

Coolify/Traefik kümmert sich um:
- ACME Challenge (HTTP-01)
- Zertifikat-Ausstellung
- Automatische Erneuerung

---

## 8. Plugin-Auslieferung

### 8.1 Bundle-Konzept

Ein **Bundle** ist eine vordefinierte Kombination von Plugins für einen Projekttyp:

| Bundle | Projekttyp | Enthaltene Plugins | Preis |
|--------|------------|-------------------|-------|
| Verzeichnis Basic | business_directory | core, directory, kontakt | Σ Einzelpreise |
| Verzeichnis Pro | business_directory | core, directory, kontakt, crm, pim | Σ Einzelpreise |
| Website Basic | einzelkunde | core, kontakt | Σ Einzelpreise |

**Hinweis:** Das Bundle-Model ist ein Vorschlag. Es muss mit bereits existierender Planung abgeglichen werden.

### 8.2 Bootstrap-Prozess

Beim Start von vrs-core:

```python
# Umgebungsvariablen (von Coolify gesetzt)
VRS_PROJECT_ID=<uuid>
VRS_MARKETPLACE_URL=https://marketplace.vrs.gmbh
VRS_MARKETPLACE_KEY=<api_key>

# Bootstrap-Ablauf
1. vrs-core startet
2. Prüft: Sind alle lizenzierten Plugins installiert?
3. Für jedes fehlende Plugin:
   a. GET /api/v1/projects/<id>/plugins → Liste lizenzierter Plugins
   b. POST /api/v1/plugins/<name>/download → Plugin-Archiv
   c. Plugin installieren (entpacken, Dependencies)
4. Datenbank-Migrationen ausführen
5. Health-Check Endpoint aktivieren
```

### 8.3 Plugin-Download-Format

Plugins werden als ZIP-Archiv ausgeliefert:

```
plugin-crm-1.2.0.zip
├── crm/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── templates/
│   └── static/
├── migrations/
│   └── versions/
└── manifest.json
```

---

## 9. Abrechnung

### 9.1 Zahlungsmodelle

| Modell | Anwendung | Implementierung |
|--------|-----------|-----------------|
| **Prepaid (Stripe)** | Self-Service Projekte | Zahlung vor Deployment |
| **Rechnung** | Unternehmenskunden | Zahlung nach Vereinbarung |
| **Stripe-Abo** | Einzelne Plugin-Käufe | Monatliche Abrechnung |

### 9.2 Konfiguration pro Projekt

Im `Project`-Model:

```python
payment_method = Column(Enum(PaymentMethod))  # STRIPE, INVOICE, PREPAID
stripe_customer_id = Column(String(100), nullable=True)
stripe_subscription_id = Column(String(100), nullable=True)
billing_email = Column(String(255))
```

### 9.3 Lizenz-Erstellung bei Kauf

```python
# Bei Bundle-Kauf: Lizenzen für alle enthaltenen Plugins erstellen
for plugin in bundle.plugins:
    license = License(
        project_id=project.id,
        plugin_name=plugin.name,
        status=LICENSE_STATUS_ACTIVE,
        billing_cycle=bundle.billing_cycle,
        plugin_price_id=get_price_for_project_type(plugin, project.project_type),
        purchased_at=now,
        expires_at=calculate_expiry(bundle.billing_cycle),
    )
    db.session.add(license)
```

---

## 10. E-Mail-Benachrichtigungen

### 10.1 Trigger

| Event | Empfänger | Inhalt |
|-------|-----------|--------|
| Projekt erstellt | Kunde | Bestätigung, erwartete Dauer |
| Provisioning gestartet | Kunde | Status-Update |
| Projekt bereit | Kunde | Login-URL, temporäres Passwort |
| Provisioning fehlgeschlagen | Sachbearbeiter | Fehlerdetails |
| Trial endet in X Tagen | Kunde | Erinnerung, Upgrade-Link |
| Domain-Transfer abgeschlossen | Kunde | Bestätigung |

### 10.2 E-Mail-Adressen

Für automatisch generierte Projekte ohne Kunden-E-Mail:
- Pool-Adresse: `admin@projekt-<id>.vrs.gmbh`
- Später: Brevo-Integration für eigene Domains

---

## 11. Server-Infrastruktur

### 11.1 Architektur

```
┌─────────────────────────────────────────────────┐
│           Coolify Management Server             │
│  - Verwaltet alle Deployments                   │
│  - API für Orchestrator                         │
│  - UI für manuelle Eingriffe (Notfall)          │
└─────────────────────────────────────────────────┘
                        │
                        │ SSH / Docker API
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Hetzner VPS 1│ │ Hetzner VPS 2│ │ Hetzner VPS N│
│              │ │              │ │              │
│ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │
│ │ Projekt A│ │ │ │ Projekt D│ │ │ │ Projekt X│ │
│ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │
│ ┌──────────┐ │ │ ┌──────────┐ │ │              │
│ │ Projekt B│ │ │ │ Projekt E│ │ │              │
│ └──────────┘ │ │ └──────────┘ │ │              │
│ ┌──────────┐ │ │              │ │              │
│ │ Projekt C│ │ │              │ │              │
│ └──────────┘ │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 11.2 Server-Provisionierung

**Manuell (Standard):**
1. Hetzner VPS über Hetzner Cloud Console erstellen
2. In Coolify als Server hinzufügen
3. Server-UUID in Konfiguration eintragen

**Automatisch (Optional, via Coolify Hetzner-Integration):**
1. Hetzner API Token in Coolify hinterlegen
2. Orchestrator ruft Coolify API auf
3. Coolify erstellt VPS bei Hetzner
4. Server wird automatisch eingerichtet

### 11.3 Server-Auswahl bei Deployment

Der Orchestrator wählt den Ziel-Server nach Strategie:

```python
class ServerSelectionStrategy:
    """
    Strategien für Server-Auswahl bei neuem Deployment.
    """
    
    @staticmethod
    def least_loaded(servers: list[Server]) -> Server:
        """Wählt Server mit wenigsten Projekten."""
        return min(servers, key=lambda s: s.project_count)
    
    @staticmethod
    def round_robin(servers: list[Server]) -> Server:
        """Rotiert durch alle Server."""
        # Implementation mit persistentem Counter
        pass
    
    @staticmethod
    def specific(server_uuid: str) -> Server:
        """Wählt spezifischen Server (für manuelle Zuweisung)."""
        return Server.query.filter_by(uuid=server_uuid).first()
```

---

## 12. Verwaltungsoberfläche (Admin UI)

### 12.1 Funktionen für Sachbearbeiter

| Bereich | Funktionen |
|---------|------------|
| **Projekte** | Liste, Details, Status ändern, Preview-Protection |
| **Domains** | Verfügbarkeit prüfen, Registrieren, Transfer Status |
| **Provisionierung** | Manuell auslösen, Retry bei Fehler, Logs einsehen |
| **Lizenzen** | Aktivieren, Suspendieren, Verlängern |
| **Server** | Status, Auslastung, neuen Server hinzufügen |

### 12.2 Keine Coolify-Kenntnisse erforderlich

Alle Aktionen werden über die Marketplace-Admin-UI ausgeführt. Der Sachbearbeiter interagiert nie direkt mit:
- Coolify UI
- Hetzner Console
- INWX Webinterface
- SSH / Terminal

---

## 13. Glossar

| Begriff | Bedeutung |
|---------|-----------|
| **Satellit** | Ein Kundenprojekt, das vrs-core + Plugins ausführt |
| **Marketplace** | Zentraler Server für Verwaltung und Plugin-Distribution |
| **Orchestrator** | Service im Marketplace für automatische Provisionierung |
| **Bundle** | Vordefinierte Plugin-Kombination für einen Projekttyp |
| **Preview-Protection** | Login-Schutz für nicht-freigegebene Projekte |
| **Bootstrap** | Automatischer Start-Prozess von vrs-core |

---

## 14. Nächste Schritte

Siehe begleitende Dokumente:

1. **VRS_MODELS_SPEC.md** – Detaillierte Model-Definitionen
2. **VRS_ORCHESTRATOR_SPEC.md** – Implementierung des Orchestrators
3. **VRS_API_INTEGRATIONS.md** – INWX, Coolify, Hetzner API Details

---

## 15. Versionierung

| Version | Datum | Änderungen |
|---------|-------|------------|
| 1.0 | Jan 2026 | Initiale Version |
