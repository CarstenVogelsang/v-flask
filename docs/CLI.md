# CLI-Befehle

v-flask stellt Flask CLI-Befehle für Datenbank-Setup und Initialisierung bereit.

## Übersicht

| Befehl | Beschreibung |
|--------|--------------|
| `flask init-db` | Erstellt alle Datenbank-Tabellen |
| `flask seed` | Seeded Core-Daten (Rollen, Permissions) |
| `flask create-admin` | Erstellt einen Admin-Benutzer |

## Setup-Workflow

```bash
# 1. Datenbank initialisieren
flask init-db

# 2. Core-Daten seeden
flask seed

# 3. Admin-Benutzer erstellen
flask create-admin
```

---

## flask init-db

Erstellt alle SQLAlchemy-Tabellen.

```bash
flask init-db
```

**Ausgabe:**
```
Database initialized!
```

**Wann verwenden:**
- Bei initialem Setup
- Wenn kein Flask-Migrate verwendet wird
- Nach `flask reset-db` (falls implementiert)

**Hinweis:** Der Befehl ist idempotent - existierende Tabellen werden nicht verändert.

---

## flask seed

Seeded grundlegende Daten für das Rollen- und Berechtigungssystem.

```bash
flask seed
```

**Erstellte Rollen:**

| Rolle | Beschreibung |
|-------|--------------|
| `admin` | Administrator mit Vollzugriff |
| `mitarbeiter` | Mitarbeiter mit eingeschränkten Rechten |
| `kunde` | Kunde mit Lesezugriff |

**Erstellte Permissions:**

| Code | Beschreibung | Modul |
|------|--------------|-------|
| `admin.*` | Vollzugriff auf alle Funktionen | core |
| `user.read` | Benutzer anzeigen | core |
| `user.create` | Benutzer erstellen | core |
| `user.update` | Benutzer bearbeiten | core |
| `user.delete` | Benutzer löschen | core |
| `config.read` | Konfiguration lesen | core |
| `config.update` | Konfiguration ändern | core |

**Rollen-Zuordnung:**
- `admin`: admin.* (Vollzugriff)
- `mitarbeiter`: user.read, config.read
- `kunde`: (keine Core-Permissions)

**Default Betreiber:**
Falls kein Betreiber existiert, wird ein Default erstellt:
- Name: "Default"
- Primary Color: #3b82f6
- Secondary Color: #64748b

**Hinweis:** Der Befehl ist idempotent - existierende Daten werden nicht dupliziert.

---

## flask create-admin

Erstellt einen neuen Admin-Benutzer.

### Interaktiv (mit Prompts)

```bash
flask create-admin
```

**Ausgabe:**
```
E-Mail: admin@example.com
Vorname: Max
Nachname: Mustermann
Passwort: ****
Passwort (wiederholen): ****

Admin user 'admin@example.com' created successfully!
```

### Mit Optionen

```bash
flask create-admin \
    --email admin@example.com \
    --vorname Max \
    --nachname Mustermann \
    --password geheim123
```

**Optionen:**

| Option | Beschreibung |
|--------|--------------|
| `--email` | E-Mail-Adresse (muss @ und . enthalten) |
| `--vorname` | Vorname des Benutzers |
| `--nachname` | Nachname des Benutzers |
| `--password` | Passwort (wird bei Prompt versteckt) |

**Voraussetzungen:**
- `flask seed` muss zuerst ausgeführt werden (admin-Rolle muss existieren)

**Fehlerbehandlung:**
- Fehlermeldung bei ungültigem E-Mail-Format
- Fehlermeldung bei bereits existierender E-Mail
- Fehlermeldung wenn admin-Rolle nicht existiert

---

## Beispiel: Komplettes Setup

```bash
# Virtuelle Umgebung aktivieren
source .venv/bin/activate

# Datenbank initialisieren
flask init-db
# Output: Database initialized!

# Core-Daten seeden
flask seed
# Output:
# Seeding core data...
# Creating roles...
#   Created role: admin
#   Created role: mitarbeiter
#   Created role: kunde
# ...
# Seeding complete!

# Admin-Benutzer erstellen
flask create-admin --email admin@firma.de --vorname Admin --nachname User
# Output: Admin user 'admin@firma.de' created successfully!
```

---

## Host-App Integration

Die CLI-Befehle werden automatisch registriert, wenn VFlask initialisiert wird:

```python
from flask import Flask
from v_flask import VFlask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SECRET_KEY'] = 'secret'

v_flask = VFlask(app)

# CLI-Befehle sind jetzt verfügbar:
# flask init-db
# flask seed
# flask create-admin
```

### Eigene CLI-Befehle hinzufügen

Host-Apps können eigene Befehle ergänzen:

```python
import click
from flask import Flask
from v_flask import VFlask, db

app = Flask(__name__)
v_flask = VFlask(app)

@app.cli.command('seed-demo')
def seed_demo_command():
    """Seed demo data for testing."""
    from myapp.models import Projekt

    projekt = Projekt(name='Demo-Projekt')
    db.session.add(projekt)
    db.session.commit()
    click.echo('Demo data seeded!')
```

---

## Troubleshooting

### "Admin role not found"

```
Error: Admin role not found. Run 'flask seed' first.
```

**Lösung:** `flask seed` vor `flask create-admin` ausführen.

### "User already exists"

```
Error: User with email 'admin@example.com' already exists.
```

**Lösung:** Andere E-Mail-Adresse verwenden oder existierenden Benutzer bearbeiten.

### "Invalid email format"

```
Error: Invalid email format.
```

**Lösung:** E-Mail muss @ und . enthalten (z.B. `user@domain.com`).
