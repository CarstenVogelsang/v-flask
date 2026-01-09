# V-Flask Architektur

## Package-Struktur

```
v-flask/
├── src/v_flask/
│   ├── __init__.py          # VFlask Extension
│   ├── extensions.py         # SQLAlchemy db instance
│   ├── models/
│   │   ├── user.py           # User + UserTyp
│   │   ├── rolle.py          # Rolle
│   │   ├── permission.py     # Permission + rolle_permission
│   │   ├── betreiber.py      # CI/Theming
│   │   ├── config.py         # Key-Value Store
│   │   ├── lookup_wert.py    # Dynamische Typen
│   │   ├── modul.py          # Dashboard Registry
│   │   └── audit_log.py      # Logging
│   ├── services/
│   │   └── logging_service.py
│   └── auth/
│       └── decorators.py     # permission_required()
├── tests/
├── docs/
└── pyproject.toml
```

## Abhängigkeits-Graph

```
User ──────────────────┐
│   └── Rolle          │
│       └── Permission │
├── Betreiber          ├── Alle nutzen: db (SQLAlchemy)
├── Config             │
├── LookupWert         │
├── Modul              │
│   └── ModulZugriff   │
├── AuditLog ──────────┘
│
├── Services
│   └── logging_service ──── nutzt: AuditLog, current_user
│
└── Auth
    └── decorators ───────── nutzt: Permission, Rolle
```

---

## Models

### User Model

```python
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

    rolle = db.relationship('Rolle', back_populates='users')

    def has_permission(self, code: str) -> bool:
        """Prüft ob User eine bestimmte Berechtigung hat."""
        if not self.rolle:
            return False
        return self.rolle.has_permission(code)

    # Convenience-Properties (bleiben für Kompatibilität)
    @property
    def is_admin(self) -> bool:
        return self.rolle and self.rolle.name == 'admin'

    @property
    def is_mitarbeiter(self) -> bool:
        return self.rolle and self.rolle.name in ('admin', 'mitarbeiter')
```

### Rolle Model

```python
class Rolle(db.Model):
    __tablename__ = 'rolle'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    beschreibung = db.Column(db.String(200))

    users = db.relationship('User', back_populates='rolle')
    permissions = db.relationship('Permission',
                                   secondary='rolle_permission',
                                   backref='rollen')

    def has_permission(self, code: str) -> bool:
        """Prüft ob Rolle eine Permission hat (inkl. Wildcards)."""
        for p in self.permissions:
            if p.code == code:
                return True
            # Wildcard-Support: 'projekt.*' erlaubt 'projekt.delete'
            if p.code.endswith('.*'):
                prefix = p.code[:-1]
                if code.startswith(prefix):
                    return True
        return False
```

### Permission Model

```python
class Permission(db.Model):
    __tablename__ = 'permission'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    beschreibung = db.Column(db.String(200))
    modul = db.Column(db.String(50))  # z.B. 'projektverwaltung'

# Zuordnungstabelle
rolle_permission = db.Table('rolle_permission',
    db.Column('rolle_id', db.Integer, db.ForeignKey('rolle.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)
```

### Betreiber Model

```python
class Betreiber(db.Model):
    __tablename__ = 'betreiber'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(500))
    impressum = db.Column(db.Text)
    datenschutz = db.Column(db.Text)

    # CI-Einstellungen
    primary_color = db.Column(db.String(7), default='#3b82f6')
    secondary_color = db.Column(db.String(7), default='#64748b')
    font_family = db.Column(db.String(100), default='Inter')
```

### Config Model

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

### AuditLog Model

```python
class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    modul = db.Column(db.String(50))
    aktion = db.Column(db.String(100))
    details = db.Column(db.Text)
    wichtigkeit = db.Column(db.String(20), default='niedrig')
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)

    user = db.relationship('User')
```

### LookupWert Model

Dynamische Lookup-Werte für Kategorien wie Status, Priorität, etc.
Unterstützt hybrides Multi-Tenancy:
- **Global**: `betreiber_id = NULL` (geteilt über alle Betreiber)
- **Betreiber-spezifisch**: `betreiber_id = X` (nur für diesen Betreiber)

Betreiber können nur **zusätzliche** Werte anlegen, globale nicht überschreiben.

```python
class LookupWert(db.Model):
    __tablename__ = 'lookup_wert'

    id = db.Column(db.Integer, primary_key=True)
    kategorie = db.Column(db.String(50), nullable=False, index=True)
    code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    farbe = db.Column(db.String(7))        # HEX color, z.B. '#3b82f6'
    icon = db.Column(db.String(50))        # Tabler icon name
    sort_order = db.Column(db.Integer, default=0)
    aktiv = db.Column(db.Boolean, default=True)
    betreiber_id = db.Column(db.Integer, db.ForeignKey('betreiber.id'), nullable=True)

    # Unique constraint: (kategorie, code, betreiber_id)
    __table_args__ = (
        db.UniqueConstraint('kategorie', 'code', 'betreiber_id'),
    )

    @classmethod
    def get_for_kategorie(cls, kategorie, betreiber_id=None):
        """Get all values for a category (global + betreiber)."""
        query = cls.query.filter_by(kategorie=kategorie, aktiv=True)
        if betreiber_id:
            query = query.filter(
                db.or_(cls.betreiber_id.is_(None), cls.betreiber_id == betreiber_id)
            )
        else:
            query = query.filter(cls.betreiber_id.is_(None))
        return query.order_by(cls.sort_order).all()
```

**Verwendung:**
```python
from v_flask.models import LookupWert

# Globalen Status erstellen
status_open = LookupWert(
    kategorie='status',
    code='open',
    name='Offen',
    farbe='#3b82f6',
    icon='circle'
)

# Betreiber-spezifischen Status erstellen
status_custom = LookupWert(
    kategorie='status',
    code='in_review',
    name='In Prüfung',
    farbe='#f59e0b',
    betreiber_id=1
)

# Alle Werte für eine Kategorie abfragen
statuses = LookupWert.get_for_kategorie('status', betreiber_id=1)
# Ergebnis: Globale + betreiberspezifische Werte
```

### Modul Model

Dashboard-Registry für Navigation und Modul-Tiles.
Sichtbarkeit wird über `min_permission` gesteuert.

```python
class Modul(db.Model):
    __tablename__ = 'modul'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    beschreibung = db.Column(db.String(200))
    icon = db.Column(db.String(50))           # Tabler icon name
    endpoint = db.Column(db.String(100))      # Flask endpoint name
    min_permission = db.Column(db.String(100), nullable=False)  # Mindest-Berechtigung
    sort_order = db.Column(db.Integer, default=0)
    aktiv = db.Column(db.Boolean, default=True)

    @classmethod
    def get_for_user(cls, user):
        """Get modules visible to user based on permissions."""
        if not user.is_authenticated:
            return []
        modules = cls.query.filter_by(aktiv=True).order_by(cls.sort_order).all()
        return [m for m in modules if user.has_permission(m.min_permission)]
```

**Verwendung:**
```python
from v_flask.models import Modul

# Modul registrieren
projekt_modul = Modul(
    code='projektverwaltung',
    name='Projektverwaltung',
    beschreibung='Projekte und Tasks verwalten',
    icon='folder',
    endpoint='admin.projekte',
    min_permission='projekt.read',
    sort_order=1
)

# Module für User abrufen
visible_modules = Modul.get_for_user(current_user)

# In Template
{% for modul in get_modules() %}
    <a href="{{ url_for(modul.endpoint) }}">
        <i class="ti ti-{{ modul.icon }}"></i>
        {{ modul.name }}
    </a>
{% endfor %}
```

---

## Rollen-Beispiele

| Rolle | Typische Berechtigungen |
|-------|------------------------|
| Admin | `admin.*` (Vollzugriff) |
| Projektkoordinator | `projekt.create`, `projekt.read`, `projekt.update`, `task.*` |
| Buchhaltung | `projekt.read`, `task.read`, `rechnung.*` |
| Kunde | `projekt.read`, `task.read`, `task.comment` |

---

## Model-Erweiterung (1:1 Pattern)

Host-Apps können Core-Models über separate Tabellen erweitern:

```python
# In der Host-App: app/models/user_profile.py
class UserProfile(db.Model):
    __tablename__ = 'user_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

    # App-spezifische Felder
    firma_id = db.Column(db.Integer, db.ForeignKey('firma.id'))
    abteilung = db.Column(db.String(100))

    user = db.relationship('User', backref=db.backref('profile', uselist=False))
```

Zugriff:
```python
user = User.query.get(1)
print(user.profile.abteilung)
```

---

## Templates & Static Assets

v-flask stellt wiederverwendbare Templates und Static Assets bereit:

```
src/v_flask/
├── templates/
│   └── v_flask/
│       ├── base.html              # Haupt-Basistemplate
│       ├── base_minimal.html      # Minimales Layout
│       └── macros/                # Wiederverwendbare Macros
└── static/
    ├── css/v-flask.css           # Core Styles
    ├── js/                        # JavaScript
    └── tabler-icons/              # Icon Font
```

**Verwendung:**
```jinja2
{% extends "v_flask/base.html" %}

{% block content %}
    {% from "v_flask/macros/breadcrumb.html" import breadcrumb %}
    {{ breadcrumb([...]) }}
{% endblock %}
```

Siehe [TEMPLATES.md](TEMPLATES.md) für die vollständige Dokumentation.
