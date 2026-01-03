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
