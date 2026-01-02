# PRD: Migration von ev247 zu v-flask

## Übersicht

Dieses Dokument beschreibt die schrittweise Migration der Core-Komponenten aus dem ev247-Projekt (ev_pricat_converter) in das wiederverwendbare v-flask Package.

## Ziel

Extraktion der folgenden Komponenten als eigenständiges, installierbares Python-Package:
- User-System (User, Rolle, Flask-Login Integration)
- Config-System (Key-Value Store)
- LookupWert-System (Dynamische Typen)
- Modul-Registry (Dashboard)
- Audit-Logging
- Auth-Decorators

---

## Quell-Projekt

**Pfad:** `/Users/cvogelsang/projekte_ev/ev_pricat_converter/`

**WICHTIG:** Das Quell-Projekt wird NIEMALS geändert! Nur LESEN!

---

## Migrations-Schritte

### Phase 1: Models extrahieren

#### 1.1 User Model

**Quelle:** `app/models/user.py`

**Anpassungen:**
- Import von `db` ändern zu relativem Import
- Flask-Login `UserMixin` beibehalten
- Password-Hashing Methoden übernehmen
- Properties (is_admin, is_mitarbeiter, is_kunde) übernehmen

**Abhängigkeiten:**
- Rolle Model (FK)
- Kein Import von anderen ev247-spezifischen Models!

```python
# Beispiel-Struktur
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    vorname = db.Column(db.String(50))
    nachname = db.Column(db.String(50))
    rolle_id = db.Column(db.Integer, db.ForeignKey('rolle.id'))
    aktiv = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    rolle = db.relationship('Rolle', back_populates='users')

    # Properties
    @property
    def is_admin(self):
        return self.rolle and self.rolle.name == 'admin'

    @property
    def is_mitarbeiter(self):
        return self.rolle and self.rolle.name in ['admin', 'mitarbeiter']
```

#### 1.2 Rolle Model

**Quelle:** `app/models/rolle.py`

**Struktur:**
```python
class Rolle(db.Model):
    __tablename__ = 'rolle'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    beschreibung = db.Column(db.String(200))

    users = db.relationship('User', back_populates='rolle')
```

#### 1.3 Config Model

**Quelle:** `app/models/config.py`

**Struktur:**
```python
class Config(db.Model):
    __tablename__ = 'config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    beschreibung = db.Column(db.String(200))

    @classmethod
    def get_value(cls, key, default=''):
        config = cls.query.filter_by(key=key).first()
        return config.value if config else default

    @classmethod
    def set_value(cls, key, value, beschreibung=None):
        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = cls(key=key, value=value, beschreibung=beschreibung)
            db.session.add(config)
        db.session.commit()
```

#### 1.4 LookupWert Model

**Quelle:** `app/models/lookup_wert.py`

**Anpassungen:**
- Generisch halten
- Keine ev247-spezifischen Kategorien hardcoden

#### 1.5 Modul Model

**Quelle:** `app/models/modul.py`

**Anpassungen:**
- ModulTyp Enum übernehmen
- Dashboard-Integration beibehalten
- ModulZugriff Relationship übernehmen

#### 1.6 AuditLog Model

**Quelle:** `app/models/audit_log.py`

**Struktur bleibt gleich.**

---

### Phase 2: Services extrahieren

#### 2.1 Logging Service

**Quelle:** `app/services/logging_service.py`

**Funktionen:**
- `log_event(modul, aktion, details, wichtigkeit='niedrig', entity_type=None, entity_id=None)`
- `log_kritisch(...)` - Wrapper für kritische Events
- `log_hoch(...)` - Wrapper für wichtige Events
- `log_mittel(...)` - Wrapper für normale Events

**Anpassungen:**
- Import von AuditLog aus v_flask.models
- Import von current_user aus flask_login
- Kein Modul-Lookup mehr (modul als String Parameter)

---

### Phase 3: Auth-Decorators

#### 3.1 Decorators

**Quelle:** `app/routes/auth.py` (nur die Decorator-Funktionen)

**Funktionen:**
```python
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Zugriff verweigert. Admin-Rechte erforderlich.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def mitarbeiter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_mitarbeiter:
            flash('Zugriff verweigert. Mitarbeiter-Rechte erforderlich.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
```

---

### Phase 4: Extension-Klasse

#### 4.1 VFlask Extension

**Datei:** `src/v_flask/__init__.py`

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

class VFlask:
    def __init__(self, app: Flask = None, db: SQLAlchemy = None):
        self.app = app
        self.db = db
        self.login_manager = LoginManager()

        if app is not None:
            self.init_app(app, db)

    def init_app(self, app: Flask, db: SQLAlchemy):
        self.app = app
        self.db = db

        # Login Manager konfigurieren
        self.login_manager.init_app(app)
        self.login_manager.login_view = 'auth.login'
        self.login_manager.login_message = 'Bitte melde dich an.'

        # User Loader registrieren
        @self.login_manager.user_loader
        def load_user(user_id):
            from v_flask.models import User
            return User.query.get(int(user_id))

        # Extension in app speichern
        app.extensions['v_flask'] = self

        # Template-Ordner registrieren
        # (für base.html und macros)
```

---

### Phase 5: Templates

#### 5.1 Basis-Template

**Quelle:** `app/templates/base.html`

**Anpassungen:**
- Generischer machen
- Keine ev247-spezifischen Branding-Elemente
- Bootstrap 5 + Tabler Icons beibehalten

#### 5.2 Macros

**Quelle:** `app/templates/macros/`

- `breadcrumb.html` - Breadcrumb-Navigation
- `help.html` - Hilfe-Icons
- `admin_tile.html` - Admin Dashboard Kacheln

---

## Test-Strategie

### Unit Tests

```python
# tests/test_models.py
def test_user_password_hashing():
    user = User(email='test@example.com')
    user.set_password('secret')
    assert user.check_password('secret')
    assert not user.check_password('wrong')

def test_config_get_set():
    Config.set_value('test_key', 'test_value')
    assert Config.get_value('test_key') == 'test_value'
    assert Config.get_value('missing', 'default') == 'default'
```

### Integration Tests

Mit Test-App (vz_fruehstueckenclick):
1. v-flask als editable install
2. Flask-App mit VFlask initialisieren
3. Tabellen erstellen
4. CRUD-Operationen testen

---

## Abhängigkeits-Graph

```
v-flask (Core)
├── User ─────────────────┐
│   └── Rolle             │
├── Config                │
├── LookupWert            ├── Alle nutzen: db (SQLAlchemy)
├── Modul                 │
│   └── ModulZugriff      │
├── AuditLog ─────────────┘
│
├── Services
│   └── logging_service ──── nutzt: AuditLog, current_user
│
└── Auth
    └── decorators ───────── nutzt: current_user, User.is_admin/is_mitarbeiter
```

---

## Checkliste

- [ ] Models extrahiert und angepasst
  - [ ] User
  - [ ] Rolle
  - [ ] Config
  - [ ] LookupWert
  - [ ] Modul
  - [ ] ModulZugriff
  - [ ] AuditLog
- [ ] Services implementiert
  - [ ] logging_service
- [ ] Auth-Decorators implementiert
  - [ ] admin_required
  - [ ] mitarbeiter_required
- [ ] VFlask Extension-Klasse erstellt
- [ ] Templates kopiert
  - [ ] base.html
  - [ ] macros/breadcrumb.html
  - [ ] macros/help.html
  - [ ] macros/admin_tile.html
- [ ] Tests geschrieben
- [ ] In Test-App verifiziert

---

## Bekannte Einschränkungen

1. **Migrations:** Das Package liefert keine Alembic-Migrations mit. Die Host-App muss `flask db migrate` ausführen.

2. **Template-Overrides:** Host-Apps können die Templates überschreiben, indem sie eigene Versionen im `templates/` Ordner anlegen.

3. **URL-Endpoints:** Decorators erwarten `main.index` als Fallback. Host-App muss diesen Endpoint bereitstellen oder Decorators anpassen.

---

## Nächste Schritte nach v-flask

Nach erfolgreicher Migration von v-flask wird **v-flask-projektverwaltung** erstellt:
- Projekt, Komponente, Task Models
- Admin-Routes (/admin/projekte/*)
- REST-API (/api/projekte/*, /api/tasks/*)
- Kanban-Board, PRD-Editor Templates
