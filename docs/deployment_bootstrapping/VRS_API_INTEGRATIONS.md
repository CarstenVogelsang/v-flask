# VRS API Integrationen

> **Version:** 1.0  
> **Datum:** Januar 2026  
> **Bezug:** VRS_DEPLOYMENT_SPEC.md, VRS_ORCHESTRATOR_SPEC.md

---

## 1. Übersicht

Dieses Dokument beschreibt die Integration mit externen APIs:

1. **INWX** - Domain-Registrierung und DNS-Management
2. **Coolify** - Container-Orchestrierung und Deployment
3. **Hetzner** - Server-Provisionierung (optional)
4. **Brevo** - E-Mail-Versand (out of scope für v1)

---

## 2. INWX API

### 2.1 Allgemein

| Eigenschaft | Wert |
|-------------|------|
| Protokoll | JSON-RPC / XML-RPC |
| Live-URL | `https://api.domrobot.com/jsonrpc/` |
| Test-URL | `https://api.ote.domrobot.com/jsonrpc/` |
| Authentifizierung | Username + Password + optional 2FA |
| Dokumentation | https://www.inwx.de/de/help/apidoc |
| Python Client | `pip install inwx-domrobot` |

### 2.2 Authentifizierung

```python
from INWX.Domrobot import ApiClient

# Live
client = ApiClient(api_url=ApiClient.API_LIVE_URL)

# Test (OT&E)
client = ApiClient(api_url=ApiClient.API_OTE_URL)

# Login
result = client.login(username, password, shared_secret)  # shared_secret für 2FA
if result['code'] != 1000:
    raise Exception(f"Login failed: {result['msg']}")
```

### 2.3 Benötigte API-Methoden

#### Domain-Verfügbarkeit prüfen

```python
# domain.check
result = client.call_api('domain.check', {
    'domain': 'example.com'
})

# Response
{
    'code': 1000,
    'resData': {
        'domain': [{
            'domain': 'example.com',
            'avail': True,  # oder False
            'price': 12.50,
            'currency': 'EUR',
            'premium': False
        }]
    }
}
```

#### Domain registrieren

```python
# domain.create
result = client.call_api('domain.create', {
    'domain': 'example.com',
    'registrant': 12345,  # Contact-ID
    'admin': 12345,
    'tech': 12345,
    'billing': 12345,
    'ns1': 'ns.inwx.de',  # Optional, default: INWX NS
    'ns2': 'ns2.inwx.de',
})

# Response
{
    'code': 1000,
    'resData': {
        'id': 987654  # Domain-ID
    }
}
```

#### Domain transferieren

```python
# domain.transfer
result = client.call_api('domain.transfer', {
    'domain': 'example.com',
    'authCode': 'ABC123XYZ',
    'registrant': 12345,
})

# Response
{
    'code': 1000,
    'resData': {
        'id': 987654
    }
}
```

#### DNS Record erstellen

```python
# nameserver.createRecord
result = client.call_api('nameserver.createRecord', {
    'domain': 'example.com',
    'type': 'A',          # A, AAAA, CNAME, MX, TXT, etc.
    'content': '1.2.3.4',
    'name': '',           # Leer = Root, oder Subdomain
    'ttl': 300,
})

# Response
{
    'code': 1000,
    'resData': {
        'id': 123456  # Record-ID
    }
}
```

#### DNS Record aktualisieren

```python
# nameserver.updateRecord
result = client.call_api('nameserver.updateRecord', {
    'id': 123456,
    'content': '5.6.7.8',  # Neue IP
    'ttl': 600,            # Neuer TTL
})
```

#### DNS Record löschen

```python
# nameserver.deleteRecord
result = client.call_api('nameserver.deleteRecord', {
    'id': 123456
})
```

#### DNS Records auflisten

```python
# nameserver.info
result = client.call_api('nameserver.info', {
    'domain': 'example.com'
})

# Response
{
    'code': 1000,
    'resData': {
        'record': [
            {'id': 123, 'type': 'A', 'name': '', 'content': '1.2.3.4', 'ttl': 300},
            {'id': 124, 'type': 'CNAME', 'name': 'www', 'content': 'example.com', 'ttl': 300},
        ]
    }
}
```

### 2.4 Error Codes

| Code | Bedeutung |
|------|-----------|
| 1000 | Erfolg |
| 2001 | Authentifizierung fehlgeschlagen |
| 2002 | Account gesperrt |
| 2100 | Object nicht gefunden |
| 2302 | Object existiert bereits |
| 2303 | Parameter fehlt |
| 2304 | Ungültiger Parameter |

### 2.5 Kontakte (Contact-IDs)

Für Domain-Registrierung werden Contact-IDs benötigt:

```python
# contact.create
result = client.call_api('contact.create', {
    'type': 'PERSON',  # oder 'ORG'
    'name': 'Max Mustermann',
    'org': 'Firma GmbH',
    'street': 'Musterstraße 1',
    'city': 'Musterstadt',
    'pc': '12345',
    'cc': 'DE',
    'voice': '+49.123456789',
    'email': 'admin@example.com',
})

# Response
{
    'code': 1000,
    'resData': {
        'id': 12345  # Contact-ID
    }
}
```

**Empfehlung:** Einen Standard-Kontakt für alle VRS-Domains anlegen und ID speichern.

---

## 3. Coolify API

### 3.1 Allgemein

| Eigenschaft | Wert |
|-------------|------|
| Protokoll | REST (JSON) |
| Basis-URL | `https://<coolify-host>/api/v1` |
| Authentifizierung | Bearer Token |
| Dokumentation | https://coolify.io/docs/api-reference/ |

### 3.2 Authentifizierung

```bash
# Token erstellen:
# Coolify UI → Keys & Tokens → API Tokens → Create

# Request Header
Authorization: Bearer <token>
Content-Type: application/json
```

### 3.3 Benötigte Endpoints

#### Projekt erstellen

```http
POST /projects
Content-Type: application/json
Authorization: Bearer <token>

{
    "name": "vrs-projekt-name",
    "description": "VRS Projekt: Beschreibung"
}
```

**Response:**
```json
{
    "uuid": "abc123...",
    "name": "vrs-projekt-name"
}
```

#### Application erstellen (Public Git)

```http
POST /applications/public
Content-Type: application/json
Authorization: Bearer <token>

{
    "project_uuid": "abc123...",
    "server_uuid": "xyz789...",
    "environment_name": "production",
    
    "git_repository": "https://github.com/vrs/vrs-core.git",
    "git_branch": "main",
    
    "build_pack": "nixpacks",
    "ports_exposes": "8000",
    
    "domains": "https://projekt.vrs.gmbh",
    "is_force_https_enabled": true,
    "is_auto_deploy_enabled": false,
    
    "health_check_enabled": true,
    "health_check_path": "/health",
    "health_check_interval": 30,
    
    "name": "vrs-projekt",
    "instant_deploy": false
}
```

**Response:**
```json
{
    "uuid": "app-uuid-123..."
}
```

#### Environment Variable erstellen

```http
POST /applications/{uuid}/envs
Content-Type: application/json
Authorization: Bearer <token>

{
    "key": "VRS_PROJECT_ID",
    "value": "123",
    "is_build_time": true,
    "is_preview": false
}
```

#### Bulk Environment Variables

```http
PATCH /applications/{uuid}/envs/bulk
Content-Type: application/json
Authorization: Bearer <token>

{
    "data": [
        {"key": "VAR1", "value": "value1"},
        {"key": "VAR2", "value": "value2"}
    ]
}
```

#### Deployment starten

```http
GET /applications/{uuid}/start
Authorization: Bearer <token>
```

**Response:**
```json
{
    "deployment_uuid": "deploy-123...",
    "message": "Deployment started"
}
```

#### Application-Status abfragen

```http
GET /applications/{uuid}
Authorization: Bearer <token>
```

**Response:**
```json
{
    "uuid": "app-uuid...",
    "name": "vrs-projekt",
    "fqdn": "https://projekt.vrs.gmbh",
    "status": "running",
    "created_at": "2026-01-15T10:00:00Z"
}
```

**Status-Werte:**
- `running` - Läuft
- `stopped` - Gestoppt
- `restarting` - Neustart
- `deploying` - Deployment läuft
- `failed` - Fehler

#### Application stoppen/neustarten

```http
GET /applications/{uuid}/stop
GET /applications/{uuid}/restart
Authorization: Bearer <token>
```

#### Server auflisten

```http
GET /servers
Authorization: Bearer <token>
```

**Response:**
```json
[
    {
        "uuid": "server-uuid...",
        "name": "hetzner-1",
        "ip": "1.2.3.4",
        "status": "active"
    }
]
```

### 3.4 Error Handling

```json
// 400 Bad Request
{
    "message": "Validation failed",
    "errors": {
        "domain": ["Domain is already in use"]
    }
}

// 401 Unauthorized
{
    "message": "Unauthenticated."
}

// 404 Not Found
{
    "message": "Application not found"
}
```

### 3.5 Wichtige Hinweise

1. **SSL/HTTPS:** Coolify kümmert sich automatisch um Let's Encrypt Zertifikate wenn `is_force_https_enabled: true`.

2. **Nixpacks:** Für Python-Projekte erkennt Nixpacks automatisch `pyproject.toml` oder `requirements.txt`.

3. **Health Checks:** Unbedingt konfigurieren, sonst keine Rolling Updates.

4. **Domains:** Format: `https://domain.com` oder `https://domain.com,https://www.domain.com` für mehrere.

---

## 4. Hetzner Cloud API (Optional)

### 4.1 Allgemein

| Eigenschaft | Wert |
|-------------|------|
| Protokoll | REST (JSON) |
| Basis-URL | `https://api.hetzner.cloud/v1` |
| Authentifizierung | Bearer Token |
| Dokumentation | https://docs.hetzner.cloud/ |

### 4.2 Via Coolify

Coolify hat eine eingebaute Hetzner-Integration:

```http
# Hetzner Locations abrufen
GET /hetzner/locations?token={hetzner_token}

# Server erstellen
POST /hetzner/servers
{
    "token": "hetzner-api-token",
    "name": "vrs-server-3",
    "server_type": "cx31",
    "location": "fsn1",
    "image": "ubuntu-22.04"
}
```

### 4.3 Direkte Hetzner API (falls benötigt)

```python
import httpx

HETZNER_TOKEN = "..."
BASE_URL = "https://api.hetzner.cloud/v1"

headers = {
    "Authorization": f"Bearer {HETZNER_TOKEN}",
    "Content-Type": "application/json"
}

# Server erstellen
response = httpx.post(
    f"{BASE_URL}/servers",
    headers=headers,
    json={
        "name": "vrs-server-3",
        "server_type": "cx31",
        "image": "ubuntu-22.04",
        "location": "fsn1",
        "ssh_keys": [12345],  # SSH Key ID
        "start_after_create": True
    }
)

server = response.json()["server"]
server_id = server["id"]
server_ip = server["public_net"]["ipv4"]["ip"]
```

### 4.4 Server-Typen

| Typ | vCPU | RAM | SSD | Preis/Monat |
|-----|------|-----|-----|-------------|
| cx11 | 1 | 2GB | 20GB | ~€4 |
| cx21 | 2 | 4GB | 40GB | ~€6 |
| cx31 | 2 | 8GB | 80GB | ~€12 |
| cx41 | 4 | 16GB | 160GB | ~€23 |

**Empfehlung für VRS:** `cx31` als Standard, skalierbar je nach Bedarf.

---

## 5. Umgebungsvariablen

### 5.1 Marketplace Server

```bash
# .env für vrs-marketplace

# INWX
INWX_USERNAME=your_username
INWX_PASSWORD=your_password
INWX_2FA_SECRET=your_2fa_secret  # Optional
INWX_USE_TEST=false  # true für OT&E

# Coolify
COOLIFY_API_URL=https://coolify.vrs.gmbh/api/v1
COOLIFY_API_TOKEN=your_coolify_token
COOLIFY_DEFAULT_SERVER_UUID=server-uuid-here

# vrs-core Repository
VRS_CORE_REPO=https://github.com/vrs/vrs-core.git
VRS_CORE_BRANCH=main

# Hetzner (Optional)
HETZNER_API_TOKEN=your_hetzner_token

# E-Mail
SMTP_HOST=smtp.brevo.com
SMTP_PORT=587
SMTP_USER=your_user
SMTP_PASSWORD=your_password
SMTP_FROM=noreply@vrs.gmbh

# Marketplace
MARKETPLACE_URL=https://marketplace.vrs.gmbh
MARKETPLACE_API_KEY=internal_api_key
```

### 5.2 Satelliten-Projekte (vrs-core)

Diese werden automatisch von Coolify gesetzt:

```bash
# Automatisch gesetzt vom Orchestrator
VRS_PROJECT_ID=123
VRS_MARKETPLACE_URL=https://marketplace.vrs.gmbh
VRS_MARKETPLACE_KEY=project_specific_key
VRS_PLUGINS=core,directory,kontakt,crm

# Projekt-spezifisch (aus Coolify Secrets)
DATABASE_URL=postgresql://...
SECRET_KEY=random_secret
```

---

## 6. Rate Limits & Best Practices

### 6.1 INWX

- Keine dokumentierten Rate Limits
- Empfehlung: Max 10 Requests/Sekunde
- Session nach ~30 Minuten Inaktivität beendet

### 6.2 Coolify

- Keine dokumentierten Rate Limits
- Empfehlung: Deployments sequentiell (nicht parallel)
- Timeout für API-Calls: 60 Sekunden

### 6.3 Hetzner

- 3600 Requests/Stunde
- Server-Erstellung: ~30 Sekunden

### 6.4 Allgemeine Empfehlungen

1. **Retry-Logik:** Exponential Backoff bei transienten Fehlern
2. **Logging:** Alle API-Calls loggen für Debugging
3. **Timeouts:** Angemessene Timeouts setzen (10-60s je nach Operation)
4. **Credentials:** Nie in Code, immer aus Environment

---

## 7. Beispiel: Kompletter Flow

```python
# Vereinfachtes Beispiel eines kompletten Provisioning-Flows

async def provision_complete_project(
    project_name: str,
    domain: str,
    plugins: list[str],
) -> dict:
    """
    Provisioniert ein komplettes Projekt.
    """
    
    # 1. INWX: DNS anlegen
    inwx = INWXClient()
    dns_records = inwx.setup_project_dns(
        domain=domain,
        server_ip="1.2.3.4",
    )
    print(f"DNS Records angelegt: {dns_records}")
    
    # 2. Coolify: Projekt erstellen
    coolify = CoolifyClient()
    
    project = await coolify.create_project(
        name=f"vrs-{project_name}"
    )
    print(f"Coolify Projekt: {project.uuid}")
    
    # 3. Coolify: Application erstellen
    app = await coolify.create_application(
        project_uuid=project.uuid,
        server_uuid="default-server-uuid",
        domain=domain,
        vrs_project_id="123",
        vrs_plugins=plugins,
    )
    print(f"Application: {app.uuid}")
    
    # 4. Coolify: Deployment starten
    deployment = await coolify.deploy_application(app.uuid)
    print(f"Deployment gestartet: {deployment.uuid}")
    
    # 5. Warten auf Deployment
    while True:
        status = await coolify.get_deployment_status(app.uuid)
        if status == "running":
            break
        elif status in ("failed", "error"):
            raise Exception("Deployment failed")
        await asyncio.sleep(10)
    
    print(f"Projekt live unter: https://{domain}")
    
    return {
        "domain": domain,
        "dns_records": dns_records,
        "coolify_project": project.uuid,
        "coolify_app": app.uuid,
    }
```

---

## 8. Troubleshooting

### 8.1 INWX

| Problem | Lösung |
|---------|--------|
| Login fehlgeschlagen | Credentials prüfen, 2FA-Secret korrekt? |
| Domain nicht verfügbar | Ist Domain wirklich frei? Premium-Domain? |
| DNS-Record existiert | Record ID merken und updaten statt neu anlegen |

### 8.2 Coolify

| Problem | Lösung |
|---------|--------|
| 401 Unauthorized | Token abgelaufen? Neu generieren |
| Deployment failed | Logs in Coolify UI prüfen |
| Health Check failed | Endpoint `/health` implementiert? Ports korrekt? |
| SSL-Fehler | Domain korrekt konfiguriert? DNS propagiert? |

### 8.3 Generell

```python
# Debug-Modus für API-Calls
import logging
logging.basicConfig(level=logging.DEBUG)

# httpx Debugging
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)
```
