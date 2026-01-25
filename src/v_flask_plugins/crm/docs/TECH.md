# CRM Plugin - Technische Architektur

## Übersicht

Dieses Dokument beschreibt die technische Implementierung des CRM-Plugins für V-Flask.

**Plugin-Name:** `crm`  
**Python-Package:** `v_flask_crm`  
**Tabellen-Prefix:** `crm_`  

---

## Verzeichnisstruktur

```
v_flask_crm/
├── __init__.py              # Plugin-Registrierung
├── plugin.py                # Plugin-Klasse mit Hooks
├── models/
│   ├── __init__.py
│   ├── customer.py          # Customer Model
│   ├── contact.py           # Contact Model
│   ├── address.py           # Address Model
│   ├── customer_group.py    # CustomerGroup Model
│   └── customer_auth.py     # CustomerAuth Model
├── services/
│   ├── __init__.py
│   ├── customer_service.py
│   ├── contact_service.py
│   ├── address_service.py
│   ├── group_service.py
│   ├── auth_service.py
│   └── import_export_service.py
├── routes/
│   ├── __init__.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── customers.py     # /admin/crm/customers
│   │   ├── groups.py        # /admin/crm/groups
│   │   └── import_export.py # /admin/crm/import
│   └── api/
│       ├── __init__.py
│       └── customers.py     # API für Shop-Plugin
├── templates/
│   └── crm/
│       └── admin/
│           ├── customers/
│           │   ├── list.html
│           │   ├── detail.html
│           │   └── form.html
│           ├── groups/
│           │   ├── list.html
│           │   └── form.html
│           └── import/
│               └── upload.html
├── forms/
│   ├── __init__.py
│   ├── customer_form.py
│   ├── contact_form.py
│   ├── address_form.py
│   └── group_form.py
├── validators/
│   ├── __init__.py
│   ├── vat_id.py            # USt-IdNr. Validierung
│   └── password.py          # Passwort-Stärke
└── migrations/
    └── versions/
        └── 001_initial.py
```

---

## Datenmodell

### Entity-Relationship-Diagramm

```
┌─────────────────┐     ┌─────────────────┐
│ crm_customer    │     │ crm_customer_   │
│                 │     │ group           │
│ id (PK)         │     │                 │
│ customer_number │  ┌──│ id (PK)         │
│ company_name    │  │  │ name            │
│ legal_form      │  │  │ description     │
│ vat_id          │  │  │ sort_order      │
│ tax_number      │  │  └─────────────────┘
│ email           │  │
│ phone           │  │
│ website         │  │
│ notes           │  │
│ tags            │  │
│ status          │  │
│ group_id (FK)───┼──┘
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────┴────┬─────────────┐
    │         │             │
    ▼         ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐
│ crm_    │ │ crm_    │ │ crm_        │
│ contact │ │ address │ │ customer_   │
│         │ │         │ │ auth        │
│ id (PK) │ │ id (PK) │ │             │
│ cust_id │ │ cust_id │ │ id (PK)     │
│ salut.  │ │ type    │ │ customer_id │
│ first   │ │ company │ │ email       │
│ last    │ │ contact │ │ pw_hash     │
│ position│ │ street  │ │ is_active   │
│ dept    │ │ street2 │ │ last_login  │
│ email   │ │ zip     │ │ login_count │
│ phone   │ │ city    │ │ failed_att. │
│ mobile  │ │ country │ │ locked_until│
│ is_prim.│ │ is_def_ │ │ reset_token │
│ is_act. │ │ billing │ │ token_exp.  │
└─────────┘ │ is_def_ │ └─────────────┘
            │ shipping│
            └─────────┘
```

### Tabellen-Definitionen

#### crm_customer

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| customer_number | VARCHAR(50) | UNIQUE, NOT NULL | Kundennummer |
| company_name | VARCHAR(255) | NOT NULL | Firmenname |
| legal_form | VARCHAR(50) | NULL | Rechtsform (GmbH, AG, etc.) |
| vat_id | VARCHAR(20) | NULL | USt-IdNr. (DE123456789) |
| tax_number | VARCHAR(50) | NULL | Steuernummer |
| email | VARCHAR(255) | NOT NULL | Haupt-E-Mail |
| phone | VARCHAR(50) | NULL | Telefon |
| website | VARCHAR(255) | NULL | Website-URL |
| notes | TEXT | NULL | Interne Notizen |
| tags | JSON | NULL | Array von Tags |
| status | ENUM | NOT NULL, DEFAULT 'active' | active, inactive, blocked |
| group_id | UUID | FK → crm_customer_group | Kundengruppe |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Indizes:**
- `idx_crm_customer_number` auf `customer_number`
- `idx_crm_customer_email` auf `email`
- `idx_crm_customer_status` auf `status`
- `idx_crm_customer_group` auf `group_id`

#### crm_contact

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| customer_id | UUID | FK, NOT NULL | Zugehöriger Kunde |
| salutation | ENUM | NULL | mr, mrs, diverse, none |
| first_name | VARCHAR(100) | NOT NULL | Vorname |
| last_name | VARCHAR(100) | NOT NULL | Nachname |
| position | VARCHAR(100) | NULL | Position im Unternehmen |
| department | VARCHAR(100) | NULL | Abteilung |
| email | VARCHAR(255) | NULL | Direkte E-Mail |
| phone_direct | VARCHAR(50) | NULL | Durchwahl |
| phone_mobile | VARCHAR(50) | NULL | Mobilnummer |
| is_primary | BOOLEAN | NOT NULL, DEFAULT FALSE | Haupt-Ansprechpartner |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Indizes:**
- `idx_crm_contact_customer` auf `customer_id`
- `idx_crm_contact_primary` auf `customer_id, is_primary`

**Constraints:**
- Pro Kunde maximal ein Kontakt mit `is_primary = TRUE` (per Trigger oder Application-Logic)

#### crm_address

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| customer_id | UUID | FK, NOT NULL | Zugehöriger Kunde |
| address_type | ENUM | NOT NULL | billing, shipping, both |
| company_name | VARCHAR(255) | NULL | Abweichender Firmenname |
| contact_name | VARCHAR(200) | NULL | Ansprechpartner für Lieferung |
| street | VARCHAR(255) | NOT NULL | Straße + Hausnummer |
| street2 | VARCHAR(255) | NULL | Adresszusatz |
| zip_code | VARCHAR(20) | NOT NULL | PLZ |
| city | VARCHAR(100) | NOT NULL | Ort |
| country | CHAR(2) | NOT NULL, DEFAULT 'DE' | ISO-Ländercode |
| is_default_billing | BOOLEAN | NOT NULL, DEFAULT FALSE | Standard-Rechnungsadresse |
| is_default_shipping | BOOLEAN | NOT NULL, DEFAULT FALSE | Standard-Lieferadresse |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Indizes:**
- `idx_crm_address_customer` auf `customer_id`
- `idx_crm_address_defaults` auf `customer_id, is_default_billing, is_default_shipping`

#### crm_customer_group

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Gruppenname |
| description | TEXT | NULL | Beschreibung |
| sort_order | INT | NOT NULL, DEFAULT 0 | Sortierung |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Hinweis:** Rabatte/Preiskonditionen werden im Pricing-Plugin verwaltet, hier nur die Gruppe selbst.

#### crm_customer_auth

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| customer_id | UUID | FK, UNIQUE, NOT NULL | 1:1 zum Kunden |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login-E-Mail |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt-Hash |
| is_active | BOOLEAN | NOT NULL, DEFAULT FALSE | Shop-Zugang aktiv |
| last_login | TIMESTAMP | NULL | Letzter erfolgreicher Login |
| login_count | INT | NOT NULL, DEFAULT 0 | Anzahl Logins |
| failed_attempts | INT | NOT NULL, DEFAULT 0 | Fehlversuche |
| locked_until | TIMESTAMP | NULL | Gesperrt bis (Brute-Force) |
| password_reset_token | VARCHAR(100) | NULL | Reset-Token |
| password_reset_expires | TIMESTAMP | NULL | Token-Ablauf |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Indizes:**
- `idx_crm_auth_email` auf `email`
- `idx_crm_auth_customer` auf `customer_id`
- `idx_crm_auth_reset_token` auf `password_reset_token`

---

## Services

### CustomerService

```python
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass
class CustomerCreate:
    company_name: str
    email: str
    legal_form: Optional[str] = None
    vat_id: Optional[str] = None
    tax_number: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    group_id: Optional[UUID] = None

@dataclass
class CustomerUpdate:
    company_name: Optional[str] = None
    email: Optional[str] = None
    legal_form: Optional[str] = None
    vat_id: Optional[str] = None
    tax_number: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None
    group_id: Optional[UUID] = None

class CustomerService:
    def __init__(self, db_session, settings):
        self.db = db_session
        self.settings = settings
    
    def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Kunde anhand ID laden"""
        pass
    
    def get_by_number(self, customer_number: str) -> Optional[Customer]:
        """Kunde anhand Kundennummer laden"""
        pass
    
    def get_by_email(self, email: str) -> Optional[Customer]:
        """Kunde anhand E-Mail laden"""
        pass
    
    def search(
        self, 
        query: Optional[str] = None,
        status: Optional[str] = None,
        group_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        page: int = 1,
        per_page: int = 20
    ) -> tuple[list[Customer], int]:
        """
        Kunden suchen mit Filterung und Paginierung.
        Gibt (Ergebnisse, Gesamtanzahl) zurück.
        """
        pass
    
    def create(self, data: CustomerCreate) -> Customer:
        """
        Neuen Kunden anlegen.
        - Generiert Kundennummer automatisch
        - Validiert USt-IdNr. falls angegeben
        """
        pass
    
    def update(self, customer_id: UUID, data: CustomerUpdate) -> Customer:
        """Kundendaten aktualisieren"""
        pass
    
    def delete(self, customer_id: UUID) -> bool:
        """
        Kunde löschen.
        - Prüft ob Bestellungen existieren (Shop-Plugin)
        - Falls ja: nur deaktivieren, nicht löschen
        """
        pass
    
    def generate_customer_number(self) -> str:
        """
        Kundennummer nach konfiguriertem Format generieren.
        Format aus Settings: 'K-{YYYY}-{NNNNN}'
        """
        pass
    
    def get_group(self, customer_id: UUID) -> Optional[CustomerGroup]:
        """Kundengruppe laden"""
        pass
    
    def set_group(self, customer_id: UUID, group_id: Optional[UUID]) -> bool:
        """Kunde einer Gruppe zuordnen (oder entfernen mit None)"""
        pass
```

### CustomerAuthService

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import bcrypt
import secrets

@dataclass
class AuthResult:
    success: bool
    customer: Optional[Customer] = None
    error: Optional[str] = None  # 'invalid_credentials', 'account_locked', 'access_disabled'

@dataclass
class SessionToken:
    token: str
    customer_id: UUID
    expires_at: datetime

class CustomerAuthService:
    def __init__(self, db_session, settings):
        self.db = db_session
        self.settings = settings
    
    def authenticate(self, email: str, password: str) -> AuthResult:
        """
        Login-Versuch prüfen.
        
        Ablauf:
        1. Auth-Eintrag per E-Mail suchen
        2. Prüfen ob locked_until in Zukunft
        3. Prüfen ob is_active = True
        4. Passwort verifizieren
        5. Bei Erfolg: failed_attempts zurücksetzen, last_login setzen
        6. Bei Fehler: failed_attempts erhöhen, ggf. locked_until setzen
        """
        pass
    
    def create_session(self, customer: Customer) -> SessionToken:
        """
        Session für eingeloggten Kunden erstellen.
        
        Hinweis: Session-Management kann über:
        - Eigene crm_session Tabelle
        - Flask-Session mit Redis
        - JWT-Token (stateless)
        
        Empfehlung: JWT für Shop, da stateless und skalierbar.
        """
        pass
    
    def validate_session(self, token: str) -> Optional[Customer]:
        """Session-Token validieren, Kunde zurückgeben"""
        pass
    
    def invalidate_session(self, token: str) -> bool:
        """Session beenden (Logout)"""
        pass
    
    def request_password_reset(self, email: str) -> bool:
        """
        Passwort-Reset anfordern.
        
        Ablauf:
        1. Auth-Eintrag per E-Mail suchen
        2. Zufälligen Token generieren (secrets.token_urlsafe)
        3. Token und Ablaufzeit speichern
        4. E-Mail mit Reset-Link senden (über Mail-Service)
        
        Gibt immer True zurück (auch wenn E-Mail nicht existiert)
        um Enumeration zu verhindern.
        """
        pass
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Passwort mit Token zurücksetzen.
        
        Ablauf:
        1. Token in DB suchen
        2. Prüfen ob nicht abgelaufen
        3. Passwort validieren (Länge, etc.)
        4. Neuen Hash speichern
        5. Token invalidieren
        """
        pass
    
    def change_password(
        self, 
        customer_id: UUID, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """Passwort ändern (eingeloggt)"""
        pass
    
    def enable_shop_access(self, customer_id: UUID) -> bool:
        """
        Shop-Zugang aktivieren.
        Erstellt Auth-Eintrag falls nicht vorhanden.
        """
        pass
    
    def disable_shop_access(self, customer_id: UUID) -> bool:
        """Shop-Zugang deaktivieren"""
        pass
    
    def set_initial_password(self, customer_id: UUID, password: str) -> bool:
        """Initiales Passwort setzen (durch Admin)"""
        pass
    
    def _hash_password(self, password: str) -> str:
        """Passwort hashen mit bcrypt"""
        return bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def _verify_password(self, password: str, hash: str) -> bool:
        """Passwort gegen Hash prüfen"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            hash.encode('utf-8')
        )
    
    def _generate_reset_token(self) -> str:
        """Sicheren Reset-Token generieren"""
        return secrets.token_urlsafe(32)
    
    def _is_locked(self, auth: CustomerAuth) -> bool:
        """Prüfen ob Account gesperrt"""
        if auth.locked_until is None:
            return False
        return auth.locked_until > datetime.utcnow()
```

---

## Routen

### Admin-Routen

| Methode | Route | Handler | Beschreibung |
|---------|-------|---------|--------------|
| GET | `/admin/crm/customers` | `list_customers` | Kundenliste |
| GET | `/admin/crm/customers/new` | `new_customer` | Formular: Neuer Kunde |
| POST | `/admin/crm/customers` | `create_customer` | Kunde anlegen |
| GET | `/admin/crm/customers/<id>` | `show_customer` | Kundendetails |
| GET | `/admin/crm/customers/<id>/edit` | `edit_customer` | Formular: Bearbeiten |
| PUT | `/admin/crm/customers/<id>` | `update_customer` | Kunde aktualisieren |
| DELETE | `/admin/crm/customers/<id>` | `delete_customer` | Kunde löschen |
| POST | `/admin/crm/customers/<id>/contacts` | `add_contact` | Ansprechpartner hinzufügen |
| PUT | `/admin/crm/contacts/<id>` | `update_contact` | Ansprechpartner bearbeiten |
| DELETE | `/admin/crm/contacts/<id>` | `delete_contact` | Ansprechpartner löschen |
| POST | `/admin/crm/customers/<id>/addresses` | `add_address` | Adresse hinzufügen |
| PUT | `/admin/crm/addresses/<id>` | `update_address` | Adresse bearbeiten |
| DELETE | `/admin/crm/addresses/<id>` | `delete_address` | Adresse löschen |
| POST | `/admin/crm/customers/<id>/enable-access` | `enable_shop_access` | Shop-Zugang aktivieren |
| POST | `/admin/crm/customers/<id>/disable-access` | `disable_shop_access` | Shop-Zugang deaktivieren |
| POST | `/admin/crm/customers/<id>/reset-password` | `reset_password` | Passwort zurücksetzen |
| GET | `/admin/crm/groups` | `list_groups` | Gruppenliste |
| POST | `/admin/crm/groups` | `create_group` | Gruppe anlegen |
| PUT | `/admin/crm/groups/<id>` | `update_group` | Gruppe bearbeiten |
| DELETE | `/admin/crm/groups/<id>` | `delete_group` | Gruppe löschen |
| GET | `/admin/crm/import` | `import_form` | Import-Formular |
| POST | `/admin/crm/import` | `import_csv` | CSV importieren |
| GET | `/admin/crm/export` | `export_csv` | CSV exportieren |

### API-Routen (für Shop-Plugin)

| Methode | Route | Beschreibung |
|---------|-------|--------------|
| POST | `/api/crm/auth/login` | Shop-Login |
| POST | `/api/crm/auth/logout` | Shop-Logout |
| POST | `/api/crm/auth/request-reset` | Reset anfordern |
| POST | `/api/crm/auth/reset-password` | Passwort zurücksetzen |
| GET | `/api/crm/customers/<id>` | Kundendaten (geschützt) |
| GET | `/api/crm/customers/<id>/addresses` | Adressen (geschützt) |

---

## Validierung

### USt-IdNr. Validierung

```python
import re

class VatIdValidator:
    """
    Validiert deutsche USt-IdNr.
    Format: DE + 9 Ziffern (DE123456789)
    """
    
    PATTERN = re.compile(r'^DE[0-9]{9}$')
    
    def validate(self, vat_id: str) -> tuple[bool, str]:
        """
        Validiert USt-IdNr.
        Gibt (is_valid, error_message) zurück.
        """
        if not vat_id:
            return True, ""  # Optional
        
        vat_id = vat_id.strip().upper().replace(' ', '')
        
        if not self.PATTERN.match(vat_id):
            return False, "USt-IdNr. muss Format DE123456789 haben"
        
        # Optional: Prüfziffer validieren
        # Optional: EU-VIES-Service anfragen
        
        return True, ""
```

### Passwort-Validierung

```python
class PasswordValidator:
    """Validiert Passwort-Stärke basierend auf Settings"""
    
    def __init__(self, settings):
        self.min_length = settings.get('password_min_length', 8)
        self.require_special = settings.get('password_require_special', False)
    
    def validate(self, password: str) -> tuple[bool, str]:
        if len(password) < self.min_length:
            return False, f"Mindestens {self.min_length} Zeichen"
        
        if self.require_special:
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return False, "Mindestens ein Sonderzeichen"
        
        return True, ""
```

---

## Integration mit anderen Plugins

### Shop-Plugin nutzt CRM

```python
# In shop/services/checkout_service.py

class CheckoutService:
    def __init__(self, crm_customer_service, crm_address_service):
        self.customers = crm_customer_service
        self.addresses = crm_address_service
    
    def get_checkout_data(self, customer_id: str) -> CheckoutData:
        customer = self.customers.get_by_id(customer_id)
        billing = self.addresses.get_default_billing(customer_id)
        shipping = self.addresses.get_default_shipping(customer_id)
        
        return CheckoutData(
            customer=customer,
            billing_address=billing,
            shipping_address=shipping
        )
```

### Pricing-Plugin nutzt CRM

```python
# In pricing/services/price_service.py

class PriceService:
    def __init__(self, crm_customer_service):
        self.customers = crm_customer_service
    
    def get_customer_group(self, customer_id: str) -> CustomerGroup | None:
        return self.customers.get_group(customer_id)
```

---

## Sicherheit

### Passwort-Hashing

- **Algorithmus:** bcrypt
- **Work Factor:** 12 (Default)
- **Niemals:** Plaintext speichern

### Session-Management

Empfehlung für Shop: **JWT-Token**

```python
import jwt
from datetime import datetime, timedelta

class JWTService:
    def __init__(self, secret_key: str, expiry_hours: int = 24):
        self.secret = secret_key
        self.expiry = expiry_hours
    
    def create_token(self, customer_id: str) -> str:
        payload = {
            'sub': customer_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.expiry)
        }
        return jwt.encode(payload, self.secret, algorithm='HS256')
    
    def verify_token(self, token: str) -> str | None:
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

### Brute-Force-Schutz

```python
def handle_failed_login(auth: CustomerAuth):
    auth.failed_attempts += 1
    
    max_attempts = settings.get('brute_force_attempts', 5)
    lockout_minutes = settings.get('brute_force_lockout_minutes', 15)
    
    if auth.failed_attempts >= max_attempts:
        auth.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
        # Optional: E-Mail senden
    
    db.commit()
```

---

## Hinweise für AI-Code-Agenten (Claude Code)

### Toast-Messages

Bei der Implementierung von Admin-Formularen soll nach einem existierenden Toast-Message-Service im V-Flask Framework gesucht werden. Falls dieser nicht vorhanden ist, muss ein einfacher Toast-Service implementiert werden, der von mehreren Plugins genutzt werden kann.

Mögliche Orte zum Suchen:
- `v_flask/services/toast_service.py`
- `v_flask/utils/flash_messages.py`
- Bestehende Plugins, die bereits Toast-Messages verwenden

### Plugin-Abhängigkeiten

Das CRM-Plugin hat keine harten Abhängigkeiten, stellt aber Services bereit, die von anderen Plugins genutzt werden:

```python
# In plugin.py
class CRMPlugin:
    name = 'crm'
    dependencies = []  # Keine Abhängigkeiten
    
    provides_services = [
        'CustomerService',
        'ContactService', 
        'AddressService',
        'CustomerAuthService'
    ]
```
