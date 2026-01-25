# CRM Plugin - Fortschritt & Phasenplan

## Status-Übersicht

| Phase | Status | Fortschritt |
|-------|--------|-------------|
| Phase 1: POC | 🟢 Abgeschlossen | 100% |
| Phase 2: MVP | ⚪ Nicht begonnen | 0% |
| Phase 3: V1 | ⚪ Nicht begonnen | 0% |

**Legende:** ⚪ Nicht begonnen | 🔵 In Arbeit | 🟢 Abgeschlossen

---

## Phase 1: POC (Proof of Concept)

**Ziel:** Grundlegende Kundenverwaltung mit Login-Fähigkeit

### Aufgaben

- [x] **1.1 Plugin-Grundstruktur**
  - [x] `__init__.py` mit Plugin-Manifest
  - [x] Verzeichnisstruktur anlegen
  - [x] Plugin in Marketplace-JSON registriert

- [x] **1.2 Datenbank-Models**
  - [x] `crm_customer` (Basis-Felder)
  - [x] `crm_address` (eine Adresse pro Kunde)
  - [x] `crm_customer_auth` (Login-Daten)
  - [x] `crm_contact` (vorbereitet für MVP)
  - [x] `crm_customer_group` (vorbereitet für MVP)
  - [ ] Migration erstellen und testen (bei Installation)

- [x] **1.3 Customer-Service**
  - [x] `create()` mit Kundennummer-Generierung
  - [x] `get_by_id()`, `get_by_email()`, `get_by_number()`
  - [x] `update()`, `delete()`
  - [x] `search()` mit Paginierung
  - [x] USt-IdNr. Validierung (DE-Format)

- [x] **1.4 Auth-Service**
  - [x] `authenticate()` - Login prüfen
  - [x] `enable_shop_access()` - Zugang aktivieren
  - [x] `set_password()` - Passwort setzen (Admin)
  - [x] `change_password()` - Passwort ändern (User)
  - [x] `unlock_account()` - Gesperrten Account entsperren
  - [x] Passwort-Hashing mit werkzeug.security (pbkdf2:sha256)
  - [x] Brute-Force-Schutz (vorgezogen aus MVP)

- [x] **1.5 Admin-Oberfläche**
  - [x] Kundenliste mit Suche und Filter
  - [x] Kunde anlegen/bearbeiten
  - [x] Shop-Zugang aktivieren + Passwort setzen
  - [x] Passwort zurücksetzen (Admin)
  - [x] Account entsperren
  - [x] Adressen hinzufügen/löschen

- [x] **1.6 API für Shop**
  - [x] `POST /api/crm/auth/login`
  - [x] `GET /api/crm/customers/<id>` (noch ohne JWT-Auth)

**Akzeptanzkriterien POC:**
- [x] Admin kann Kunden anlegen
- [x] Admin kann Shop-Zugang aktivieren und Passwort setzen
- [x] Shop-Plugin kann Login durchführen (API-Route implementiert)
- [x] Shop-Plugin kann Kundendaten abrufen (API-Route implementiert)

**Status:** 🟢 Abgeschlossen (2026-01-21)

---

## Phase 2: MVP (Minimum Viable Product)

**Ziel:** Vollständige B2B-Kundenverwaltung mit Ansprechpartnern

### Aufgaben

- [ ] **2.1 Ansprechpartner-Verwaltung**
  - [x] `crm_contact` Model (bereits erstellt)
  - [ ] `ContactService` implementieren
  - [ ] Admin-UI: Ansprechpartner pro Kunde
  - [ ] Haupt-Ansprechpartner markieren

- [ ] **2.2 Erweiterte Adressverwaltung**
  - [x] Getrennte Rechnungs-/Lieferadressen (Model bereit)
  - [x] Standard-Adressen markieren
  - [ ] Admin-UI: Adressen bearbeiten (nur hinzufügen/löschen implementiert)

- [ ] **2.3 Kundengruppen**
  - [x] `crm_customer_group` Model (bereits erstellt)
  - [ ] `GroupService` implementieren
  - [ ] Admin-UI: Gruppen verwalten
  - [ ] Kunden zu Gruppen zuordnen

- [ ] **2.4 Passwort-Reset**
  - [ ] Reset-Token generieren
  - [ ] `request_password_reset()` implementieren
  - [ ] `reset_password()` implementieren
  - [ ] E-Mail-Integration (Mail-Service suchen/erstellen)

- [x] **2.5 Brute-Force-Schutz** (vorgezogen in POC)
  - [x] Fehlversuche zählen
  - [x] Account temporär sperren
  - [x] Settings für Schwellwerte

- [ ] **2.6 Admin-UI Erweiterungen**
  - [ ] Kunden-Detailansicht mit Tabs
  - [ ] Filter nach Gruppe
  - [x] Passwort zurücksetzen (Admin)

- [ ] **2.7 API-Routen**
  - [ ] `POST /api/crm/auth/login`
  - [ ] `GET /api/crm/customers/<id>` (geschützt)
  - [ ] `POST /api/crm/auth/request-reset`
  - [ ] `POST /api/crm/auth/reset-password`
  - [ ] `GET /api/crm/customers/<id>/addresses`

**Akzeptanzkriterien MVP:**
- [ ] Mehrere Ansprechpartner pro Kunde möglich
- [x] Getrennte Rechnungs-/Lieferadressen
- [ ] Kundengruppen funktionieren
- [ ] Passwort-Reset per E-Mail funktioniert
- [x] Brute-Force-Schutz aktiv

**Status:** ⚪ Nicht begonnen

---

## Phase 3: V1 (Vollversion)

**Ziel:** Produktionsreife mit Import/Export und DSGVO

### Aufgaben

- [ ] **3.1 CSV-Import**
  - [ ] Import-Formular mit Spalten-Mapping
  - [ ] Validierung vor Import
  - [ ] Fehlerprotokoll
  - [ ] Duplikat-Erkennung

- [ ] **3.2 CSV-Export**
  - [ ] Kunden exportieren
  - [ ] Filter anwendbar
  - [ ] Spaltenauswahl

- [ ] **3.3 Volltext-Suche**
  - [x] Suche über wichtige Felder (Firma, KdNr, E-Mail, USt-IdNr.)
  - [ ] Performante Implementierung (Index)

- [ ] **3.4 DSGVO-Funktionen**
  - [ ] Datenauskunft (JSON/PDF-Export)
  - [ ] Datenlöschung/Anonymisierung
  - [ ] Lösch-Protokoll

- [ ] **3.5 Änderungsprotokoll**
  - [ ] Wer hat wann was geändert
  - [ ] In Kunden-Detailansicht anzeigen

- [ ] **3.6 Plugin-Einstellungen UI**
  - [x] Settings-Schema definiert
  - [ ] Kundennummer-Format konfigurierbar machen
  - [ ] Passwort-Richtlinien anwenden
  - [ ] Brute-Force-Schwellwerte anwenden

**Akzeptanzkriterien V1:**
- [ ] CSV-Import funktioniert fehlerfrei
- [ ] CSV-Export mit Filtern
- [ ] DSGVO-Auskunft generierbar
- [ ] DSGVO-Löschung anonymisiert korrekt
- [ ] Änderungsprotokoll vollständig

**Status:** ⚪ Nicht begonnen

---

## Abhängigkeiten

### CRM benötigt

| Abhängigkeit | Status | Anmerkung |
|--------------|--------|-----------|
| V-Flask Core | ✅ Vorhanden | Plugin-System, DB, Auth |
| werkzeug.security | ✅ Vorhanden | Passwort-Hashing |
| Mail-Service | ❓ Prüfen | Für Passwort-Reset E-Mails (MVP) |

### CRM wird benötigt von

| Plugin | Nutzt | Priorität |
|--------|-------|-----------|
| Shop | Kunden, Auth, Adressen | Hoch |
| Pricing | Kundengruppen | Hoch |
| Go POS | Kunden (später) | Niedrig |

---

## Offene Entscheidungen

| # | Frage | Optionen | Entscheidung |
|---|-------|----------|--------------|
| 1 | Session-Management | JWT / Server-Session | Empfehlung: JWT |
| 2 | Passwort-Hashing | bcrypt / werkzeug.security | ✅ werkzeug.security (konsistent mit User-Model) |
| 3 | Mail-Service | Bestehend / Neu | Prüfen ob vorhanden (MVP) |

---

## Changelog

### 2026-01-21 - POC Phase 1 abgeschlossen

#### Added
- ✅ Plugin-Manifest (`__init__.py`) mit UI-Slots und Settings-Schema
- ✅ Models: Customer, Address, CustomerAuth (in separaten Dateien)
- ✅ VatIdValidator für USt-IdNr. Validierung (DE-Format)
- ✅ Services: CustomerService, AddressService, CustomerAuthService
- ✅ Admin-Routes für Kunden, Adressen, Shop-Zugang
- ✅ API-Routes: Login und Kundendaten-Abruf
- ✅ Admin-Templates (DaisyUI): Kundenliste, Formular, Detail, Shop-Zugang
- ✅ Plugin in plugins_marketplace.json eingetragen
- ✅ Brute-Force-Schutz implementiert (vorgezogen aus MVP)

#### Architektur-Entscheidungen
- Passwort-Hashing: werkzeug.security (pbkdf2:sha256) statt bcrypt
  - Konsistent mit v-flask User-Model
  - Keine zusätzliche Dependency (bcrypt)
- Models für MVP vorbereitet (Contact, CustomerGroup)
- Kundennummer-Format: K-{YYYY}-{NNNNN} (z.B. K-2026-00001)
- UUID als Primary Keys
- Soft-Delete via Status-Enum (active/inactive/blocked)

#### Offene Punkte
- [ ] Datenbank-Migrationen erstellen (bei Projekt-Installation)
- [ ] API-Routen für Shop-Plugin (MVP)
- [ ] Ansprechpartner-Verwaltung (MVP)
- [ ] Kundengruppen-Verwaltung (MVP)
- [ ] Passwort-Reset mit E-Mail (MVP)

### 2025-01-20 - Konzeption abgeschlossen

- ✅ CRM-Plugin Konzept erarbeitet
- ✅ Entscheidung: CRM bleibt schlank (keine Preislogik)
- ✅ Entscheidung: Pricing wird eigenes Plugin
- ✅ Ansprechpartner kommen ins MVP
- ✅ SPEC.md erstellt
- ✅ TECH.md erstellt
- ✅ PROGRESS.md erstellt

---

## Hinweise für AI-Code-Agenten

### POC ist implementiert

Die POC-Phase ist abgeschlossen. Bei der Weiterentwicklung:

1. **Für MVP**: ContactService und GroupService implementieren
2. **API-Routen**: Blueprint unter `/api/crm/` erstellen
3. **Mail-Service**: Für Passwort-Reset benötigt

### Implementierte Dateien

```
v_flask_plugins/crm/
├── __init__.py                    # Plugin-Manifest
├── models/
│   ├── __init__.py                # Model-Exports
│   ├── customer.py                # Customer + CustomerStatus
│   ├── address.py                 # Address + AddressType
│   └── customer_auth.py           # CustomerAuth
├── validators/
│   ├── __init__.py
│   └── vat_id.py                  # VatIdValidator
├── services/
│   └── __init__.py                # CustomerService, AddressService, CustomerAuthService
├── routes/
│   ├── __init__.py                # Blueprint-Exports
│   ├── admin.py                   # Admin-Routes (/admin/crm/...)
│   └── api.py                     # API-Routes (/api/crm/...)
├── templates/
│   └── crm/
│       └── admin/
│           └── customers/
│               ├── list.html          # Kundenliste mit Suche
│               ├── form.html          # Kunde anlegen/bearbeiten
│               ├── detail.html        # Kundendetails
│               ├── enable_access.html # Shop-Zugang aktivieren
│               └── reset_password.html # Passwort zurücksetzen
└── docs/
    ├── SPEC.md
    ├── TECH.md
    └── PROGRESS.md
```

### Code-Qualität

- Services nutzen DTOs (CustomerCreate, CustomerUpdate, etc.)
- Validatoren: VatIdValidator, PasswordValidator
- CRMService Facade für einfachen Zugriff
- Singleton-Pattern: `crm_service` importieren
