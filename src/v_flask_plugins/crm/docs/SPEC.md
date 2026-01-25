# CRM Plugin - Spezifikation

## Übersicht

Modulares Customer Relationship Management System für V-Flask mit Fokus auf B2B-Geschäftskunden. Verwaltet Kundenstammdaten, Ansprechpartner, Adressen und Shop-Authentifizierung.

**Plugin-Name:** `crm`  
**Tabellen-Prefix:** `crm_`  
**URL-Prefix Admin:** `/admin/crm/`  
**Abhängigkeiten:** Keine (Core-Plugin)  
**Optionale Abhängigkeiten:** `fragebogen` (für Selbstregistrierung)

---

## Kernprinzipien

1. **Schlank bleiben:** CRM verwaltet nur Kundenstammdaten, keine Preislogik
2. **B2B-Fokus:** Firmenkunden mit Ansprechpartnern, USt-IdNr., etc.
3. **Shop-Auth:** Stellt Login-Infrastruktur für den Shop bereit
4. **Wiederverwendbar:** Kann von Shop, Go POS, Rechnungsstellung, etc. genutzt werden

---

## Abgrenzung zu anderen Plugins

| Aspekt | CRM | Pricing | Shop |
|--------|-----|---------|------|
| Kundenstammdaten | ✅ | ❌ | ❌ |
| Adressen | ✅ | ❌ | ❌ |
| Ansprechpartner | ✅ | ❌ | ❌ |
| Kundengruppen | ✅ | Liest | ❌ |
| Shop-Login | ✅ | ❌ | Nutzt |
| Kundenspezifische Preise | ❌ | ✅ | ❌ |
| Staffelpreise | ❌ | ✅ | ❌ |
| Preisanzeige | ❌ | ❌ | ✅ |

---

## Funktionale Anforderungen

### FR-1: Kundenverwaltung

#### FR-1.1: Kunden anlegen/bearbeiten
- Kundennummer (automatisch generiert, Format konfigurierbar)
- Firmenname (Pflicht bei B2B)
- Rechtsform (GmbH, AG, KG, etc.)
- USt-IdNr. (mit Validierung DE-Format)
- Steuernummer (optional)
- E-Mail (Pflicht, für Korrespondenz)
- Telefon, Website
- Notizen (Freitext)
- Tags (für Filterung/Segmentierung)
- Status: Aktiv / Inaktiv / Gesperrt

#### FR-1.2: Kundensuche und -filterung
- Volltextsuche über alle Felder
- Filter nach Status, Tags, Erstelldatum
- Sortierung nach Name, Kundennummer, Erstelldatum
- Paginierung mit konfigurierbarer Seitengröße

#### FR-1.3: Kundennummern-Generierung
- Konfigurierbares Format in Plugin-Settings
- Vorschlag: `K-YYYY-NNNNN` (z.B. K-2025-00001)
- Alternativ: Nur numerisch, mit Präfix, etc.

### FR-2: Ansprechpartner-Verwaltung

#### FR-2.1: Ansprechpartner anlegen/bearbeiten
- Zuordnung zu genau einem Kunden
- Anrede (Herr/Frau/Divers/Keine Angabe)
- Vorname, Nachname (Pflicht)
- Position (z.B. "Einkaufsleiter")
- Abteilung (z.B. "Einkauf")
- E-Mail (optional, für direkten Kontakt)
- Telefon direkt, Mobiltelefon
- Kennzeichnung als Haupt-Ansprechpartner
- Status: Aktiv / Inaktiv

#### FR-2.2: Haupt-Ansprechpartner
- Pro Kunde genau ein Haupt-Ansprechpartner möglich
- Wird bei Korrespondenz bevorzugt verwendet
- Kann gewechselt werden

### FR-3: Adressverwaltung

#### FR-3.1: Adressen anlegen/bearbeiten
- Zuordnung zu genau einem Kunden
- Adresstyp: Rechnung / Lieferung / Beides
- Firmenname (kann von Kundenfirma abweichen, z.B. Niederlassung)
- Ansprechpartner-Name (für Lieferadressen)
- Straße, Hausnummer
- Adresszusatz (z.B. "Gebäude C, 3. OG")
- PLZ, Ort
- Land (ISO-Code, Default: DE)
- Kennzeichnung als Standard-Rechnungsadresse
- Kennzeichnung als Standard-Lieferadresse

#### FR-3.2: Standard-Adressen
- Pro Kunde genau eine Standard-Rechnungsadresse
- Pro Kunde genau eine Standard-Lieferadresse
- Können identisch sein (Adresstyp "Beides")
- Werden im Shop-Checkout vorausgewählt

### FR-4: Kundengruppen

#### FR-4.1: Gruppen verwalten
- Name (eindeutig)
- Beschreibung
- Sortierung/Priorität

**Hinweis:** Rabatte und Preiskonditionen werden im Pricing-Plugin verwaltet, nicht hier. Die Kundengruppe ist nur die Zuordnung.

#### FR-4.2: Kundenzuordnung
- Ein Kunde kann nur einer Gruppe zugeordnet sein
- Gruppe kann leer sein (Kunde ohne Gruppe = Listenpreis)
- Beim Löschen einer Gruppe: Kunden werden auf "keine Gruppe" gesetzt

### FR-5: Shop-Authentifizierung

#### FR-5.1: Login-Daten verwalten
- Benutzername = E-Mail-Adresse des Kunden
- Passwort (gehasht, bcrypt)
- Shop-Zugang aktivieren/deaktivieren
- Letzter Login (Zeitstempel)
- Login-Zähler
- Fehlgeschlagene Login-Versuche (für Brute-Force-Schutz)

#### FR-5.2: Passwort-Reset
- Passwort-Reset anfordern (generiert Token)
- Token-Gültigkeit (konfigurierbar, Default: 24h)
- Neues Passwort setzen mit gültigem Token
- Token wird nach Verwendung invalidiert

#### FR-5.3: Login-Prozess (für Shop-Plugin)
- E-Mail + Passwort prüfen
- Prüfen ob Shop-Zugang aktiv
- Prüfen ob Kunde nicht gesperrt
- Session erstellen und Token zurückgeben
- Fehlgeschlagene Versuche zählen

#### FR-5.4: Brute-Force-Schutz
- Nach X fehlgeschlagenen Versuchen: Account temporär sperren
- Sperrzeit konfigurierbar (Default: 15 Minuten)
- Optional: E-Mail-Benachrichtigung bei Sperrung

### FR-6: Import/Export

#### FR-6.1: CSV-Import
- Kunden mit Adressen importieren
- Spalten-Mapping konfigurierbar
- Validierung vor Import
- Fehlerprotokoll bei Problemen
- Duplikat-Erkennung (nach E-Mail oder Kundennummer)

#### FR-6.2: CSV-Export
- Kunden exportieren (mit/ohne Adressen)
- Filter auf Export anwendbar
- Spaltenauswahl möglich

### FR-7: DSGVO-Funktionen (V1)

#### FR-7.1: Datenauskunft
- Alle Daten eines Kunden exportieren (JSON/PDF)
- Inkl. Bestellhistorie (aus Shop), Ansprechpartner, Adressen

#### FR-7.2: Datenlöschung/Anonymisierung
- Personenbezogene Daten anonymisieren
- Referenzen in Bestellungen bleiben erhalten (anonymisiert)
- Lösch-Protokoll führen

---

## Admin-Oberfläche

### Navigationsstruktur

```
CRM (Hauptmenü)
├── Kunden
│   ├── Übersicht (Liste mit Suche/Filter)
│   ├── Neuer Kunde
│   └── [Kunde bearbeiten]
│       ├── Stammdaten
│       ├── Ansprechpartner
│       ├── Adressen
│       └── Shop-Zugang
├── Kundengruppen
│   ├── Übersicht
│   └── Neue Gruppe
├── Import/Export
│   ├── CSV-Import
│   └── CSV-Export
└── Einstellungen
    ├── Kundennummer-Format
    ├── Passwort-Richtlinien
    └── Brute-Force-Schutz
```

### Kunden-Detailansicht (Tabs)

| Tab | Inhalt |
|-----|--------|
| Stammdaten | Firma, USt-IdNr., Kontaktdaten, Tags, Status |
| Ansprechpartner | Liste der Kontakte, Haupt-AP markiert |
| Adressen | Rechnungs-/Lieferadressen, Standards markiert |
| Shop-Zugang | Login aktivieren, Passwort zurücksetzen, Letzte Logins |
| Historie | Letzte Bestellungen (aus Shop), Änderungsprotokoll |

---

## Plugin-Einstellungen

| Einstellung | Typ | Default | Beschreibung |
|-------------|-----|---------|--------------|
| `customer_number_format` | string | `K-{YYYY}-{NNNNN}` | Format für Kundennummern |
| `customer_number_start` | int | 1 | Startwert für Nummerierung |
| `password_min_length` | int | 8 | Minimale Passwortlänge |
| `password_require_special` | bool | false | Sonderzeichen erforderlich |
| `password_reset_hours` | int | 24 | Gültigkeit Reset-Token |
| `brute_force_attempts` | int | 5 | Max. fehlgeschlagene Logins |
| `brute_force_lockout_minutes` | int | 15 | Sperrzeit in Minuten |
| `default_country` | string | `DE` | Standard-Land für Adressen |

---

## API für andere Plugins

Das CRM-Plugin stellt Services bereit, die andere Plugins nutzen können:

### CustomerService

```python
class CustomerService:
    def get_by_id(self, customer_id: str) -> Customer | None
    def get_by_number(self, customer_number: str) -> Customer | None
    def get_by_email(self, email: str) -> Customer | None
    def search(self, query: str, filters: dict) -> list[Customer]
    def create(self, data: CustomerCreate) -> Customer
    def update(self, customer_id: str, data: CustomerUpdate) -> Customer
    def delete(self, customer_id: str) -> bool
    def get_group(self, customer_id: str) -> CustomerGroup | None
```

### ContactService

```python
class ContactService:
    def get_by_customer(self, customer_id: str) -> list[Contact]
    def get_primary(self, customer_id: str) -> Contact | None
    def create(self, customer_id: str, data: ContactCreate) -> Contact
    def update(self, contact_id: str, data: ContactUpdate) -> Contact
    def set_primary(self, contact_id: str) -> bool
```

### AddressService

```python
class AddressService:
    def get_by_customer(self, customer_id: str) -> list[Address]
    def get_default_billing(self, customer_id: str) -> Address | None
    def get_default_shipping(self, customer_id: str) -> Address | None
    def create(self, customer_id: str, data: AddressCreate) -> Address
    def update(self, address_id: str, data: AddressUpdate) -> Address
    def set_default_billing(self, address_id: str) -> bool
    def set_default_shipping(self, address_id: str) -> bool
```

### CustomerAuthService

```python
class CustomerAuthService:
    def authenticate(self, email: str, password: str) -> AuthResult
    def create_session(self, customer: Customer) -> SessionToken
    def validate_session(self, token: str) -> Customer | None
    def invalidate_session(self, token: str) -> bool
    def request_password_reset(self, email: str) -> bool
    def reset_password(self, token: str, new_password: str) -> bool
    def change_password(self, customer_id: str, old_pw: str, new_pw: str) -> bool
    def enable_shop_access(self, customer_id: str) -> bool
    def disable_shop_access(self, customer_id: str) -> bool
```

---

## User Stories

### Betreiber (Admin)

| ID | User Story | Priorität |
|----|------------|-----------|
| US-A01 | Als Admin möchte ich neue Geschäftskunden anlegen können | Must |
| US-A02 | Als Admin möchte ich Kundendaten bearbeiten können | Must |
| US-A03 | Als Admin möchte ich Kunden suchen und filtern können | Must |
| US-A04 | Als Admin möchte ich Ansprechpartner zu Kunden hinzufügen | Must |
| US-A05 | Als Admin möchte ich Rechnungs- und Lieferadressen verwalten | Must |
| US-A06 | Als Admin möchte ich Shop-Zugänge aktivieren/deaktivieren | Must |
| US-A07 | Als Admin möchte ich Passwörter zurücksetzen können | Must |
| US-A08 | Als Admin möchte ich Kundengruppen verwalten | Must |
| US-A09 | Als Admin möchte ich Kunden per CSV importieren | Should |
| US-A10 | Als Admin möchte ich Kunden exportieren können | Should |
| US-A11 | Als Admin möchte ich Kundendaten anonymisieren können (DSGVO) | Should |

### Shop-Kunde (B2B)

| ID | User Story | Priorität |
|----|------------|-----------|
| US-K01 | Als Kunde möchte ich mich im Shop einloggen können | Must |
| US-K02 | Als Kunde möchte ich mein Passwort zurücksetzen können | Must |
| US-K03 | Als Kunde möchte ich meine Lieferadressen verwalten | Should |
| US-K04 | Als Kunde möchte ich mein Passwort ändern können | Should |

---

## Versionierung

### POC (Proof of Concept)
- Kunden CRUD (Basisdaten)
- Eine Adresse pro Kunde (kombiniert)
- Login-Tabelle (ohne Reset)
- Keine Gruppen

### MVP (Minimum Viable Product)
- Ansprechpartner-Verwaltung
- Getrennte Rechnungs-/Lieferadressen
- Kundengruppen
- Passwort-Reset
- Brute-Force-Schutz

### V1 (Vollversion)
- CSV-Import/Export
- Volltext-Suche
- DSGVO-Funktionen
- Änderungsprotokoll

### V2 (Erweiterungen)
- B2C-Kundenmodus (optional)
- API für externe Systeme
- Erweiterte Segmentierung
