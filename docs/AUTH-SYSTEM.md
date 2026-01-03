# V-Flask Auth-System

## Permission-basierte Decorators

Das System nutzt granulare Permission-Codes statt hardcodierter Rollen-Checks.

### permission_required Decorator

```python
from v_flask.auth import permission_required

@blueprint.route('/projekte')
@permission_required('projekt.read')
def list_projekte():
    projekte = Projekt.query.all()
    return render_template('projekte/list.html', projekte=projekte)

@blueprint.route('/projekt/<int:id>/delete', methods=['POST'])
@permission_required('projekt.delete')
def delete_projekt(id):
    projekt = Projekt.query.get_or_404(id)
    db.session.delete(projekt)
    db.session.commit()
    flash('Projekt gelöscht.', 'success')
    return redirect(url_for('.list_projekte'))
```

### Convenience-Decorators

```python
from v_flask.auth import admin_required, login_required_with_message

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/profile')
@login_required_with_message
def profile():
    return render_template('profile.html')
```

---

## Decorator-Implementierung

```python
# v_flask/auth/decorators.py
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def permission_required(permission_code: str):
    """Decorator für granulare Berechtigungsprüfung."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bitte melde dich an.', 'warning')
                return redirect(url_for('auth.login'))
            if not current_user.has_permission(permission_code):
                flash('Keine Berechtigung für diese Aktion.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Shortcut für Admin-Berechtigung (admin.*)"""
    return permission_required('admin.*')(f)

def login_required_with_message(f):
    """Login mit deutscher Fehlermeldung."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bitte melde dich an.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
```

---

## Permission-Codes

### Format

```
<modul>.<aktion>
```

Beispiele:
- `projekt.read` - Projekte lesen
- `projekt.create` - Projekte erstellen
- `projekt.update` - Projekte bearbeiten
- `projekt.delete` - Projekte löschen
- `task.comment` - Tasks kommentieren

### Wildcards

Mit `.*` können alle Aktionen eines Moduls erlaubt werden:

- `projekt.*` - Alle Projekt-Aktionen
- `admin.*` - Alle Admin-Aktionen

```python
rolle = Rolle(name='projektleiter')
perm = Permission(code='projekt.*')
rolle.permissions.append(perm)

# Jetzt erlaubt:
rolle.has_permission('projekt.read')    # True
rolle.has_permission('projekt.delete')  # True
rolle.has_permission('user.delete')     # False
```

---

## User-Methoden

### has_permission()

Prüft ob der User (über seine Rolle) eine Berechtigung hat:

```python
user = User.query.get(1)

if user.has_permission('projekt.delete'):
    # User darf Projekte löschen
    pass
```

### Convenience-Properties

Bleiben für Backward-Kompatibilität:

```python
user.is_admin        # True wenn rolle.name == 'admin'
user.is_mitarbeiter  # True wenn rolle.name in ('admin', 'mitarbeiter')
user.is_kunde        # True wenn rolle.name == 'kunde'
user.is_internal     # True wenn is_admin oder is_mitarbeiter
```

---

## VFlask Integration

```python
from flask import Flask
from v_flask import VFlask

app = Flask(__name__)
v_flask = VFlask(app)

# Login-Manager ist automatisch konfiguriert
# user_loader ist registriert
# Context-Processor für Betreiber ist aktiv
```
