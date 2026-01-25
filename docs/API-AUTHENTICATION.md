# API-Authentifizierung mit JWT

v-flask bietet ein optionales JWT-basiertes Authentifizierungssystem für REST APIs.

## Installation

JWT-Support ist als optionale Dependency verfügbar:

```bash
# Mit uv
uv add v-flask[api]

# Mit pip
pip install v-flask[api]
```

## Konzept

### Wann API vs. Inter-Plugin-Kommunikation?

| Szenario | Lösung |
|----------|--------|
| Shop-Frontend → Backend | REST API mit JWT |
| Mobile App → Backend | REST API mit JWT |
| Plugin A → Plugin B (Server-Side) | Direkter Service-Import |

**API-Endpunkte sind für externe Clients**, nicht für Plugin-zu-Plugin-Kommunikation innerhalb des Systems.

```python
# Inter-Plugin-Kommunikation (Server-Side)
# Shop-Plugin importiert CRM-Service direkt
from v_flask_plugins.crm.services import crm_service

customer = crm_service.customers.get_by_id(customer_id)
```

```python
# Externe Clients (Frontend, Mobile)
# POST /api/crm/auth/login → Token
# GET /api/crm/customers/{id} (mit Bearer Token)
```

## Verwendung

### Token generieren (Login)

```python
from v_flask.api import generate_token

@app.route('/api/auth/login', methods=['POST'])
def login():
    # ... Credentials validieren ...

    token = generate_token({
        'user_id': str(user.id),    # UUID als String
        'user_type': 'customer',    # 'admin', 'customer', 'user', etc.
        'email': user.email,        # Optionale Zusatzdaten
    })

    return jsonify({
        'success': True,
        'token': token,
    })
```

### Endpoint schützen

```python
from v_flask.api import jwt_required, get_current_api_user

@app.route('/api/protected')
@jwt_required
def protected_endpoint():
    user = get_current_api_user()

    return jsonify({
        'user_id': user['user_id'],
        'user_type': user['user_type'],
    })
```

### Autorisierung (Zugriffskontrolle)

```python
@app.route('/api/customers/<customer_id>')
@jwt_required
def get_customer(customer_id: str):
    user = get_current_api_user()

    # Kunden dürfen nur eigene Daten abrufen
    if user['user_type'] == 'customer' and user['user_id'] != customer_id:
        return jsonify({'error': 'forbidden'}), 403

    # Admins haben vollen Zugriff
    # ... Kundendaten zurückgeben ...
```

### Optionale Authentifizierung

Für Endpoints, die auch ohne Token funktionieren sollen:

```python
from v_flask.api import optional_jwt, get_current_api_user

@app.route('/api/products')
@optional_jwt
def list_products():
    user = get_current_api_user()

    if user and user['user_type'] == 'customer':
        # Kundenspezifische Preise
        return get_customer_prices(user['user_id'])
    else:
        # Öffentliche Preise
        return get_public_prices()
```

## Token-Format

JWT-Tokens werden mit dem `SECRET_KEY` der Flask-App signiert:

```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_type": "customer",
    "email": "kunde@example.com",
    "iat": 1705826400,
    "exp": 1705912800
}
```

- `iat`: Issued at (Erstellungszeitpunkt)
- `exp`: Expiration (Ablaufzeitpunkt)
- Standard-Gültigkeit: 24 Stunden

### Token-Gültigkeit anpassen

```python
# Token mit 1 Woche Gültigkeit
token = generate_token(payload, expires_hours=168)

# Token mit 1 Stunde Gültigkeit
token = generate_token(payload, expires_hours=1)
```

## HTTP-Header

Clients senden den Token im Authorization-Header:

```http
GET /api/customers/123 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Fehler-Responses

### 401 Unauthorized

```json
{
    "error": "missing_token",
    "message": "Authorization header required"
}
```

```json
{
    "error": "invalid_token",
    "message": "Token invalid or expired"
}
```

### 403 Forbidden

```json
{
    "error": "forbidden",
    "message": "Zugriff verweigert"
}
```

## Plugin-Integration

### CRM-Plugin API-Endpoints

Das CRM-Plugin stellt folgende JWT-geschützte Endpoints bereit:

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/api/crm/auth/login` | POST | Nein | Login, gibt JWT-Token zurück |
| `/api/crm/me` | GET | JWT | Eigene Kundendaten |
| `/api/crm/customers/<id>` | GET | JWT | Kundendaten (nur eigene oder Admin) |
| `/api/crm/customers/<id>/addresses` | GET | JWT | Kundenadresse (nur eigene oder Admin) |

### Beispiel: Shop-Frontend Login

```javascript
// Login
const response = await fetch('/api/crm/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'kunde@example.com',
        password: 'geheim123'
    })
});

const { token, customer } = await response.json();

// Token speichern
localStorage.setItem('auth_token', token);

// Geschützten Endpoint aufrufen
const meResponse = await fetch('/api/crm/me', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

## Sicherheitshinweise

1. **SECRET_KEY**: Muss in Production ein starker, zufälliger Wert sein
2. **HTTPS**: Tokens nur über verschlüsselte Verbindungen übertragen
3. **Token-Speicherung**: Im Frontend `localStorage` oder `sessionStorage` verwenden
4. **Sensitive Daten**: Keine Passwörter oder kritische Daten im Token-Payload
5. **Token-Ablauf**: Kurze Gültigkeiten für sensible Anwendungen

## API-Funktionsreferenz

### `generate_token(payload, expires_hours=24)`

Generiert einen JWT-Token.

**Parameter:**
- `payload`: Dict mit Benutzerinformationen (user_id, user_type, ...)
- `expires_hours`: Token-Gültigkeit in Stunden

**Rückgabe:** JWT-Token als String

### `decode_token(token)`

Dekodiert und validiert einen Token.

**Parameter:**
- `token`: Der JWT-Token-String

**Rückgabe:** Payload-Dict oder `None` bei ungültigem Token

### `jwt_required`

Decorator für Endpoints, die einen gültigen Token erfordern.

### `optional_jwt`

Decorator für Endpoints, die optional einen Token akzeptieren.

### `get_current_api_user()`

Gibt den aktuellen API-User aus dem JWT-Payload zurück.

**Rückgabe:** Dict mit Token-Payload oder `None`

### `JWT_AVAILABLE`

Boolean, der anzeigt, ob PyJWT installiert ist.

```python
from v_flask.api import JWT_AVAILABLE

if not JWT_AVAILABLE:
    print("PyJWT nicht installiert - API-Auth deaktiviert")
```
