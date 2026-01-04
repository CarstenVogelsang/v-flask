# Logging-Service

Der v-flask Logging-Service bietet strukturiertes Audit-Logging für alle Aktionen in der Anwendung.

## Übersicht

- **4 Wichtigkeitsstufen**: niedrig, mittel, hoch, kritisch
- **Automatische Context-Erfassung**: User-ID, IP-Adresse
- **Entity-Tracking**: Verknüpfung mit betroffenen Objekten
- **Optional async**: Hintergrund-Worker für hohe Last (via Threading)

---

## Basis-Verwendung

```python
from v_flask.services import log_event

# Einfaches Event loggen
log_event('projekt', 'erstellt', 'Projekt "Website Relaunch" erstellt')

# Mit Entity-Referenz
log_event(
    modul='projekt',
    aktion='gelöscht',
    details='Projekt wurde gelöscht',
    wichtigkeit='hoch',
    entity_type='Projekt',
    entity_id=42
)
```

---

## Convenience-Funktionen

Für bessere Lesbarkeit gibt es Wrapper mit vordefinierten Wichtigkeitsstufen:

```python
from v_flask.services import log_niedrig, log_mittel, log_hoch, log_kritisch

# Routine-Aktion (Views, Listen)
log_niedrig('projekt', 'angezeigt', 'Projektliste aufgerufen')

# Standard-Änderung (Create, Update)
log_mittel('projekt', 'aktualisiert', 'Titel geändert')

# Signifikante Änderung (Delete, Bulk-Operationen)
log_hoch('projekt', 'gelöscht', 'Projekt #42 entfernt')

# Sicherheitsrelevant (Login-Fehler, Permission Denied)
log_kritisch('auth', 'login_failed', f'Fehlgeschlagener Login für: {email}')
```

---

## Wichtigkeitsstufen

| Level | Funktion | Typische Verwendung |
|-------|----------|---------------------|
| `niedrig` | `log_niedrig()` | View-Actions, Read-Operationen, Listen |
| `mittel` | `log_mittel()` | Create, Update, Form-Submissions |
| `hoch` | `log_hoch()` | Delete, Bulk-Änderungen, Berechtigungsänderungen |
| `kritisch` | `log_kritisch()` | Login-Fehler, Security-Events, Exceptions |

---

## Exception-Decorator

Für automatisches Logging von Exceptions in Routes:

```python
from v_flask.services import log_exceptions

@app.route('/api/projekt/<int:id>', methods=['DELETE'])
@log_exceptions('projekt')
def delete_projekt(id):
    projekt = Projekt.query.get_or_404(id)
    db.session.delete(projekt)
    db.session.commit()
    return jsonify({'status': 'deleted'})
```

Bei einer Exception wird automatisch ein kritisches Event geloggt:
```
modul: 'projekt'
aktion: 'exception'
details: 'ValueError: Ungültige ID'
wichtigkeit: 'kritisch'
```

Die Exception wird anschließend re-raised, sodass normale Error-Handler greifen.

---

## Logs abfragen

```python
from v_flask.services import get_logs_for_entity, get_logs_for_user

# Logs für ein bestimmtes Entity
projekt_logs = get_logs_for_entity('Projekt', 42, limit=20)

# Logs für einen User
user_logs = get_logs_for_user(user_id=5, limit=50)
```

---

## Async-Logging (Optional)

Für hohe Last kann das Logging in einen Hintergrund-Worker ausgelagert werden:

```python
from v_flask import VFlask
from v_flask.services import init_async_logging, shutdown_async_logging
import atexit

def create_app():
    app = Flask(__name__)
    v_flask = VFlask(app)

    # Async-Logging aktivieren
    init_async_logging()

    # Sauberes Shutdown bei App-Ende
    atexit.register(shutdown_async_logging)

    return app
```

**Wie es funktioniert:**
- Log-Events werden in eine Queue gestellt
- Ein Daemon-Thread arbeitet die Queue ab
- Die Anwendung wartet nicht auf Datenbank-Commits

**Wann verwenden:**
- Hohe Request-Last
- Logging darf Response-Zeit nicht beeinflussen
- POC/Entwicklung: Sync ist völlig ausreichend

---

## AuditLog-Model

Die Logs werden in der `audit_log`-Tabelle gespeichert:

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
    ip_address = db.Column(db.String(45))  # IPv6-kompatibel
```

---

## Best Practices

### 1. Konsistente Modul-Namen
```python
# Gut: Gleicher Modul-Name überall
log_mittel('projekt', 'erstellt', ...)
log_mittel('projekt', 'aktualisiert', ...)
log_hoch('projekt', 'gelöscht', ...)

# Schlecht: Inkonsistente Namen
log_mittel('projects', 'created', ...)
log_mittel('Projekt', 'update', ...)
```

### 2. Deutsche Aktionsnamen
```python
# Konsistent: erstellt, aktualisiert, gelöscht, angezeigt
log_mittel('user', 'erstellt', f'Benutzer {email} angelegt')
log_hoch('user', 'gelöscht', f'Benutzer {email} entfernt')
```

### 3. Entity-Referenzen nutzen
```python
# Ermöglicht spätere Filterung nach Entity
log_hoch(
    'projekt',
    'status_geändert',
    f'Status von {old_status} auf {new_status} geändert',
    entity_type='Projekt',
    entity_id=projekt.id
)
```

### 4. Sicherheitsrelevantes immer kritisch loggen
```python
log_kritisch('auth', 'login_failed', f'IP: {request.remote_addr}')
log_kritisch('auth', 'permission_denied', f'User {user.id} wollte {action}')
log_kritisch('admin', 'rolle_geändert', f'User {user.id} ist jetzt {new_role}')
```
