# VRS Orchestrator Spezifikation

> **Version:** 1.0  
> **Datum:** Januar 2026  
> **Bezug:** VRS_DEPLOYMENT_SPEC.md, VRS_MODELS_SPEC.md

---

## 1. Übersicht

Der **Orchestrator** ist der zentrale Service für die automatische Provisionierung von VRS-Projekten. Er koordiniert:

1. INWX API (DNS, Domain-Registrierung, Transfer)
2. Coolify API (Projekte, Applications, Deployments)
3. Hetzner API (Server-Provisionierung, optional)
4. E-Mail-Benachrichtigungen

---

## 2. Verzeichnisstruktur

```
vrs-marketplace/
└── server/
    └── app/
        ├── orchestrator/
        │   ├── __init__.py
        │   ├── provisioner.py          # Haupt-Orchestrierungslogik
        │   ├── clients/
        │   │   ├── __init__.py
        │   │   ├── inwx_client.py      # INWX API Client
        │   │   ├── coolify_client.py   # Coolify API Client
        │   │   └── hetzner_client.py   # Hetzner API Client (optional)
        │   ├── tasks/
        │   │   ├── __init__.py
        │   │   ├── dns_tasks.py        # DNS-spezifische Tasks
        │   │   ├── deployment_tasks.py # Coolify Deployment Tasks
        │   │   └── notification_tasks.py
        │   ├── strategies/
        │   │   ├── __init__.py
        │   │   └── server_selection.py # Server-Auswahl-Strategien
        │   └── exceptions.py           # Custom Exceptions
        └── ...
```

---

## 3. INWX Client

### 3.1 Konfiguration

```python
# config.py

class INWXConfig:
    """INWX API Konfiguration."""
    
    # API URLs
    API_LIVE_URL = 'https://api.domrobot.com/jsonrpc/'
    API_TEST_URL = 'https://api.ote.domrobot.com/jsonrpc/'
    
    # Credentials (aus Environment)
    USERNAME = os.getenv('INWX_USERNAME')
    PASSWORD = os.getenv('INWX_PASSWORD')
    SHARED_SECRET = os.getenv('INWX_2FA_SECRET')  # Für 2FA (optional)
    
    # Test-Modus
    USE_TEST_API = os.getenv('INWX_USE_TEST', 'false').lower() == 'true'
```

### 3.2 Client Implementation

```python
# orchestrator/clients/inwx_client.py

"""INWX API Client für DNS und Domain-Management."""
from typing import Any
from dataclasses import dataclass

from INWX.Domrobot import ApiClient

from app.orchestrator.exceptions import (
    INWXError,
    DomainNotAvailableError,
    DNSRecordError,
)
from app.config import INWXConfig


@dataclass
class DomainCheckResult:
    """Ergebnis einer Domain-Verfügbarkeitsprüfung."""
    domain: str
    available: bool
    price_cents: int | None = None
    currency: str = 'EUR'
    premium: bool = False


@dataclass
class DNSRecord:
    """DNS Record Daten."""
    record_id: int
    record_type: str
    name: str
    content: str
    ttl: int


class INWXClient:
    """Client für INWX API (JSON-RPC).
    
    Verwendet den offiziellen INWX Python Client (inwx-domrobot).
    
    Beispiel:
        client = INWXClient()
        
        # Domain prüfen
        result = client.check_domain_availability('example.com')
        if result.available:
            domain_id = client.register_domain('example.com', contact_id)
        
        # DNS Record anlegen
        record_id = client.create_dns_record(
            domain='example.com',
            record_type='A',
            name='@',
            content='1.2.3.4'
        )
    """
    
    def __init__(self):
        api_url = INWXConfig.API_TEST_URL if INWXConfig.USE_TEST_API else INWXConfig.API_LIVE_URL
        self._client = ApiClient(api_url=api_url, debug_mode=False)
        self._logged_in = False
    
    def _ensure_login(self) -> None:
        """Stellt sicher, dass wir eingeloggt sind."""
        if self._logged_in:
            return
        
        result = self._client.login(
            INWXConfig.USERNAME,
            INWXConfig.PASSWORD,
            INWXConfig.SHARED_SECRET
        )
        
        if result.get('code') != 1000:
            raise INWXError(f"Login failed: {result.get('msg')}")
        
        self._logged_in = True
    
    def _call(self, method: str, params: dict | None = None) -> dict:
        """Führt einen API-Call aus.
        
        Args:
            method: API-Methode (z.B. 'domain.check')
            params: Parameter für den Call
        
        Returns:
            API Response
        
        Raises:
            INWXError: Bei API-Fehlern
        """
        self._ensure_login()
        
        result = self._client.call_api(
            api_method=method,
            method_params=params or {}
        )
        
        if result.get('code') != 1000:
            raise INWXError(
                f"API error in {method}: {result.get('code')} - {result.get('msg')}"
            )
        
        return result
    
    # =========================================================
    # Domain-Verfügbarkeit
    # =========================================================
    
    def check_domain_availability(self, domain: str) -> DomainCheckResult:
        """Prüft ob eine Domain verfügbar ist.
        
        Args:
            domain: Domain zu prüfen (z.B. 'example.com')
        
        Returns:
            DomainCheckResult mit Verfügbarkeit und Preis
        """
        result = self._call('domain.check', {'domain': domain})
        
        domain_data = result['resData']['domain'][0]
        
        return DomainCheckResult(
            domain=domain,
            available=domain_data.get('avail', False),
            price_cents=self._price_to_cents(domain_data.get('price')),
            currency=domain_data.get('currency', 'EUR'),
            premium=domain_data.get('premium', False),
        )
    
    def _price_to_cents(self, price: Any) -> int | None:
        """Konvertiert Preis zu Cents."""
        if price is None:
            return None
        try:
            return int(float(price) * 100)
        except (ValueError, TypeError):
            return None
    
    # =========================================================
    # Domain-Registrierung
    # =========================================================
    
    def register_domain(
        self,
        domain: str,
        registrant_id: int,
        admin_id: int | None = None,
        tech_id: int | None = None,
        billing_id: int | None = None,
        nameservers: list[str] | None = None,
    ) -> int:
        """Registriert eine neue Domain.
        
        Args:
            domain: Domain zu registrieren
            registrant_id: INWX Contact-ID für Registrant
            admin_id: Contact-ID für Admin-C (optional, default: registrant)
            tech_id: Contact-ID für Tech-C (optional, default: registrant)
            billing_id: Contact-ID für Billing-C (optional, default: registrant)
            nameservers: Liste von Nameservern (optional, default: INWX NS)
        
        Returns:
            INWX Domain-ID
        
        Raises:
            DomainNotAvailableError: Wenn Domain nicht verfügbar
            INWXError: Bei anderen Fehlern
        """
        # Erst Verfügbarkeit prüfen
        check = self.check_domain_availability(domain)
        if not check.available:
            raise DomainNotAvailableError(f"Domain {domain} is not available")
        
        params = {
            'domain': domain,
            'registrant': registrant_id,
            'admin': admin_id or registrant_id,
            'tech': tech_id or registrant_id,
            'billing': billing_id or registrant_id,
        }
        
        if nameservers:
            for i, ns in enumerate(nameservers[:5], 1):
                params[f'ns{i}'] = ns
        
        result = self._call('domain.create', params)
        
        return result['resData']['id']
    
    # =========================================================
    # Domain-Transfer
    # =========================================================
    
    def initiate_transfer(
        self,
        domain: str,
        auth_code: str,
        registrant_id: int,
    ) -> int:
        """Initiiert einen Domain-Transfer.
        
        Args:
            domain: Domain zu transferieren
            auth_code: Auth-Code vom aktuellen Registrar
            registrant_id: INWX Contact-ID
        
        Returns:
            Transfer-ID (für Status-Abfragen)
        """
        result = self._call('domain.transfer', {
            'domain': domain,
            'authCode': auth_code,
            'registrant': registrant_id,
        })
        
        return result['resData']['id']
    
    def get_transfer_status(self, domain: str) -> str:
        """Prüft den Status eines Domain-Transfers.
        
        Args:
            domain: Domain
        
        Returns:
            Status: 'pending', 'completed', 'failed', 'cancelled'
        """
        result = self._call('domain.info', {'domain': domain})
        
        # INWX liefert verschiedene Status-Informationen
        status = result['resData'].get('status', '')
        
        if 'transfer' in status.lower():
            return 'pending'
        elif status == 'OK':
            return 'completed'
        else:
            return 'pending'  # Konservativ
    
    # =========================================================
    # DNS Records
    # =========================================================
    
    def create_dns_record(
        self,
        domain: str,
        record_type: str,
        content: str,
        name: str = '',
        ttl: int = 300,
    ) -> int:
        """Erstellt einen DNS Record.
        
        Args:
            domain: Domain (z.B. 'example.com')
            record_type: Record-Typ ('A', 'AAAA', 'CNAME', 'TXT', 'MX')
            content: Record-Inhalt (IP, Hostname, Text)
            name: Subdomain oder '@' für Root (leer = Root)
            ttl: Time-to-Live in Sekunden
        
        Returns:
            Record-ID
        
        Raises:
            DNSRecordError: Bei Fehlern
        """
        try:
            result = self._call('nameserver.createRecord', {
                'domain': domain,
                'type': record_type.upper(),
                'content': content,
                'name': name,
                'ttl': ttl,
            })
            
            return result['resData']['id']
        except INWXError as e:
            raise DNSRecordError(f"Failed to create {record_type} record: {e}")
    
    def update_dns_record(
        self,
        record_id: int,
        content: str | None = None,
        ttl: int | None = None,
    ) -> None:
        """Aktualisiert einen DNS Record.
        
        Args:
            record_id: ID des Records
            content: Neuer Inhalt (optional)
            ttl: Neuer TTL (optional)
        """
        params = {'id': record_id}
        if content is not None:
            params['content'] = content
        if ttl is not None:
            params['ttl'] = ttl
        
        self._call('nameserver.updateRecord', params)
    
    def delete_dns_record(self, record_id: int) -> None:
        """Löscht einen DNS Record.
        
        Args:
            record_id: ID des Records
        """
        self._call('nameserver.deleteRecord', {'id': record_id})
    
    def list_dns_records(self, domain: str) -> list[DNSRecord]:
        """Listet alle DNS Records einer Domain.
        
        Args:
            domain: Domain
        
        Returns:
            Liste von DNSRecord
        """
        result = self._call('nameserver.info', {'domain': domain})
        
        records = []
        for r in result.get('resData', {}).get('record', []):
            records.append(DNSRecord(
                record_id=r['id'],
                record_type=r['type'],
                name=r['name'],
                content=r['content'],
                ttl=r['ttl'],
            ))
        
        return records
    
    # =========================================================
    # Convenience Methods
    # =========================================================
    
    def setup_project_dns(
        self,
        domain: str,
        server_ip: str,
        is_subdomain: bool = False,
        base_domain: str | None = None,
    ) -> dict[str, int]:
        """Richtet DNS für ein Projekt ein.
        
        Erstellt:
        - A-Record für die Domain
        - CNAME für www (nur bei Haupt-Domains)
        
        Args:
            domain: Vollständige Domain (z.B. 'projekt.vrs.gmbh')
            server_ip: IP-Adresse des Servers
            is_subdomain: Ob es eine Subdomain ist
            base_domain: Basis-Domain (für Subdomains)
        
        Returns:
            Dict mit Record-IDs: {'a': 123, 'www': 456}
        """
        record_ids = {}
        
        if is_subdomain and base_domain:
            # Subdomain: A-Record auf Basis-Domain anlegen
            subdomain_part = domain.replace(f'.{base_domain}', '')
            
            a_id = self.create_dns_record(
                domain=base_domain,
                record_type='A',
                name=subdomain_part,
                content=server_ip,
            )
            record_ids['a'] = a_id
            
            # www CNAME für Subdomain
            www_id = self.create_dns_record(
                domain=base_domain,
                record_type='CNAME',
                name=f'www.{subdomain_part}',
                content=f'{subdomain_part}.{base_domain}',
            )
            record_ids['www'] = www_id
        else:
            # Eigene Domain: A-Record für Root
            a_id = self.create_dns_record(
                domain=domain,
                record_type='A',
                name='',  # Root
                content=server_ip,
            )
            record_ids['a'] = a_id
            
            # www CNAME
            www_id = self.create_dns_record(
                domain=domain,
                record_type='CNAME',
                name='www',
                content=domain,
            )
            record_ids['www'] = www_id
        
        return record_ids
    
    def cleanup_project_dns(self, record_ids: dict[str, int]) -> None:
        """Entfernt alle DNS Records eines Projekts.
        
        Args:
            record_ids: Dict mit Record-IDs (von setup_project_dns)
        """
        for record_type, record_id in record_ids.items():
            try:
                self.delete_dns_record(record_id)
            except INWXError:
                # Ignoriere Fehler beim Löschen (Record existiert vielleicht nicht mehr)
                pass
    
    def __del__(self):
        """Logout beim Beenden."""
        if self._logged_in:
            try:
                self._client.logout()
            except:
                pass
```

---

## 4. Coolify Client

### 4.1 Konfiguration

```python
# config.py

class CoolifyConfig:
    """Coolify API Konfiguration."""
    
    # API URL (z.B. 'https://coolify.vrs.gmbh/api/v1')
    API_URL = os.getenv('COOLIFY_API_URL')
    
    # API Token (erstellt unter Keys & Tokens → API Tokens)
    API_TOKEN = os.getenv('COOLIFY_API_TOKEN')
    
    # Default Server UUID (für neue Projekte)
    DEFAULT_SERVER_UUID = os.getenv('COOLIFY_DEFAULT_SERVER_UUID')
    
    # vrs-core Git Repository
    VRS_CORE_REPO = os.getenv('VRS_CORE_REPO', 'https://github.com/vrs/vrs-core.git')
    VRS_CORE_BRANCH = os.getenv('VRS_CORE_BRANCH', 'main')
```

### 4.2 Client Implementation

```python
# orchestrator/clients/coolify_client.py

"""Coolify API Client für Deployments."""
import httpx
from typing import Any
from dataclasses import dataclass

from app.orchestrator.exceptions import CoolifyError
from app.config import CoolifyConfig


@dataclass
class CoolifyProject:
    """Coolify Projekt."""
    uuid: str
    name: str


@dataclass
class CoolifyApplication:
    """Coolify Application."""
    uuid: str
    name: str
    fqdn: str | None
    status: str


@dataclass
class DeploymentInfo:
    """Deployment-Informationen."""
    uuid: str
    status: str
    created_at: str


class CoolifyClient:
    """Client für Coolify API (REST).
    
    Beispiel:
        client = CoolifyClient()
        
        # Projekt erstellen
        project = client.create_project('Mein Projekt')
        
        # Application erstellen
        app = client.create_application(
            project_uuid=project.uuid,
            server_uuid='xxx',
            domain='example.com'
        )
        
        # Deployment starten
        client.deploy_application(app.uuid)
    """
    
    def __init__(self, api_url: str | None = None, api_token: str | None = None):
        self.api_url = (api_url or CoolifyConfig.API_URL).rstrip('/')
        self.api_token = api_token or CoolifyConfig.API_TOKEN
        
        if not self.api_url or not self.api_token:
            raise ValueError("Coolify API URL and Token are required")
        
        self._headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Führt einen API-Request aus.
        
        Args:
            method: HTTP-Methode ('GET', 'POST', 'PATCH', 'DELETE')
            endpoint: API-Endpoint (z.B. '/projects')
            data: Request-Body (für POST/PATCH)
            params: Query-Parameter
        
        Returns:
            Response JSON
        
        Raises:
            CoolifyError: Bei API-Fehlern
        """
        url = f'{self.api_url}{endpoint}'
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._headers,
                    json=data,
                    params=params,
                )
                
                if response.status_code >= 400:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', error_msg)
                    except:
                        pass
                    raise CoolifyError(
                        f"API error ({response.status_code}): {error_msg}"
                    )
                
                if response.status_code == 204:
                    return {}
                
                return response.json()
            
            except httpx.RequestError as e:
                raise CoolifyError(f"Request failed: {e}")
    
    # =========================================================
    # Projects
    # =========================================================
    
    async def create_project(
        self,
        name: str,
        description: str | None = None,
    ) -> CoolifyProject:
        """Erstellt ein neues Coolify-Projekt.
        
        Args:
            name: Projektname
            description: Beschreibung (optional)
        
        Returns:
            CoolifyProject
        """
        data = await self._request('POST', '/projects', {
            'name': name,
            'description': description or '',
        })
        
        return CoolifyProject(
            uuid=data['uuid'],
            name=name,
        )
    
    async def get_project(self, uuid: str) -> CoolifyProject:
        """Holt ein Projekt nach UUID."""
        data = await self._request('GET', f'/projects/{uuid}')
        
        return CoolifyProject(
            uuid=data['uuid'],
            name=data['name'],
        )
    
    async def delete_project(self, uuid: str) -> None:
        """Löscht ein Projekt."""
        await self._request('DELETE', f'/projects/{uuid}')
    
    # =========================================================
    # Environments
    # =========================================================
    
    async def create_environment(
        self,
        project_uuid: str,
        name: str = 'production',
    ) -> str:
        """Erstellt ein Environment in einem Projekt.
        
        Args:
            project_uuid: UUID des Projekts
            name: Environment-Name
        
        Returns:
            Environment-UUID
        """
        data = await self._request(
            'POST',
            f'/projects/{project_uuid}/environments',
            {'name': name}
        )
        
        return data.get('uuid') or data.get('id')
    
    # =========================================================
    # Applications
    # =========================================================
    
    async def create_application(
        self,
        project_uuid: str,
        server_uuid: str,
        domain: str,
        vrs_project_id: str,
        vrs_plugins: list[str],
        name: str | None = None,
        environment_name: str = 'production',
    ) -> CoolifyApplication:
        """Erstellt eine vrs-core Application.
        
        Args:
            project_uuid: Coolify Projekt-UUID
            server_uuid: Server-UUID für Deployment
            domain: Domain (ohne https://)
            vrs_project_id: VRS Projekt-ID
            vrs_plugins: Liste der Plugin-Namen
            name: Application-Name (optional)
            environment_name: Environment-Name
        
        Returns:
            CoolifyApplication
        """
        app_name = name or f'vrs-{vrs_project_id[:8]}'
        
        # Application erstellen
        data = await self._request('POST', '/applications/public', {
            'project_uuid': project_uuid,
            'server_uuid': server_uuid,
            'environment_name': environment_name,
            
            # Git Repository
            'git_repository': CoolifyConfig.VRS_CORE_REPO,
            'git_branch': CoolifyConfig.VRS_CORE_BRANCH,
            
            # Build
            'build_pack': 'nixpacks',
            'ports_exposes': '8000',
            
            # Domain & HTTPS
            'domains': f'https://{domain}',
            'is_force_https_enabled': True,
            'is_auto_deploy_enabled': False,
            
            # Health Check
            'health_check_enabled': True,
            'health_check_path': '/health',
            'health_check_interval': 30,
            
            # Name
            'name': app_name,
            
            # Kein Auto-Deploy bei Erstellung
            'instant_deploy': False,
        })
        
        app_uuid = data['uuid']
        
        # Environment Variables setzen
        env_vars = {
            'VRS_PROJECT_ID': vrs_project_id,
            'VRS_MARKETPLACE_URL': 'https://marketplace.vrs.gmbh',
            'VRS_PLUGINS': ','.join(vrs_plugins),
            # Secret-Variablen werden separat gesetzt
        }
        
        for key, value in env_vars.items():
            await self.create_env_variable(
                app_uuid=app_uuid,
                key=key,
                value=value,
                is_build_time=key.startswith('VRS_'),
            )
        
        return CoolifyApplication(
            uuid=app_uuid,
            name=app_name,
            fqdn=f'https://{domain}',
            status='created',
        )
    
    async def get_application(self, uuid: str) -> CoolifyApplication:
        """Holt eine Application nach UUID."""
        data = await self._request('GET', f'/applications/{uuid}')
        
        return CoolifyApplication(
            uuid=data['uuid'],
            name=data.get('name', ''),
            fqdn=data.get('fqdn'),
            status=data.get('status', 'unknown'),
        )
    
    async def update_application(
        self,
        uuid: str,
        **updates: Any,
    ) -> None:
        """Aktualisiert eine Application.
        
        Args:
            uuid: Application-UUID
            **updates: Felder zum Aktualisieren
        """
        await self._request('PATCH', f'/applications/{uuid}', updates)
    
    async def delete_application(self, uuid: str) -> None:
        """Löscht eine Application."""
        await self._request('DELETE', f'/applications/{uuid}')
    
    # =========================================================
    # Environment Variables
    # =========================================================
    
    async def create_env_variable(
        self,
        app_uuid: str,
        key: str,
        value: str,
        is_build_time: bool = False,
        is_secret: bool = False,
    ) -> None:
        """Erstellt eine Umgebungsvariable.
        
        Args:
            app_uuid: Application-UUID
            key: Variable-Name
            value: Variable-Wert
            is_build_time: Verfügbar während Build?
            is_secret: Als Secret behandeln?
        """
        await self._request('POST', f'/applications/{app_uuid}/envs', {
            'key': key,
            'value': value,
            'is_build_time': is_build_time,
            'is_preview': False,
            # is_secret wird automatisch erkannt wenn key mit SECRET/KEY/PASSWORD endet
        })
    
    async def bulk_create_env_variables(
        self,
        app_uuid: str,
        variables: dict[str, str],
    ) -> None:
        """Erstellt mehrere Umgebungsvariablen.
        
        Args:
            app_uuid: Application-UUID
            variables: Dict von Key -> Value
        """
        await self._request(
            'PATCH',
            f'/applications/{app_uuid}/envs/bulk',
            {'data': [{'key': k, 'value': v} for k, v in variables.items()]}
        )
    
    # =========================================================
    # Deployments
    # =========================================================
    
    async def deploy_application(self, app_uuid: str) -> DeploymentInfo:
        """Startet ein Deployment.
        
        Args:
            app_uuid: Application-UUID
        
        Returns:
            DeploymentInfo
        """
        data = await self._request('GET', f'/applications/{app_uuid}/start')
        
        return DeploymentInfo(
            uuid=data.get('deployment_uuid', ''),
            status='queued',
            created_at=data.get('created_at', ''),
        )
    
    async def restart_application(self, app_uuid: str) -> DeploymentInfo:
        """Startet eine Application neu."""
        data = await self._request('GET', f'/applications/{app_uuid}/restart')
        
        return DeploymentInfo(
            uuid=data.get('deployment_uuid', ''),
            status='queued',
            created_at=data.get('created_at', ''),
        )
    
    async def stop_application(self, app_uuid: str) -> None:
        """Stoppt eine Application."""
        await self._request('GET', f'/applications/{app_uuid}/stop')
    
    async def get_deployment_status(self, app_uuid: str) -> str:
        """Holt den aktuellen Status einer Application.
        
        Args:
            app_uuid: Application-UUID
        
        Returns:
            Status: 'running', 'stopped', 'deploying', 'failed', etc.
        """
        app = await self.get_application(app_uuid)
        return app.status
    
    async def get_deployments(
        self,
        app_uuid: str,
        limit: int = 10,
    ) -> list[DeploymentInfo]:
        """Holt Deployment-History einer Application."""
        data = await self._request(
            'GET',
            f'/applications/{app_uuid}/deployments',
            params={'limit': limit}
        )
        
        return [
            DeploymentInfo(
                uuid=d['uuid'],
                status=d['status'],
                created_at=d['created_at'],
            )
            for d in data.get('data', [])
        ]
    
    # =========================================================
    # Servers
    # =========================================================
    
    async def list_servers(self) -> list[dict]:
        """Listet alle verfügbaren Server."""
        data = await self._request('GET', '/servers')
        return data.get('data', data) if isinstance(data, dict) else data
    
    async def get_server(self, uuid: str) -> dict:
        """Holt Server-Details."""
        return await self._request('GET', f'/servers/{uuid}')
    
    async def validate_server(self, uuid: str) -> bool:
        """Validiert Server-Konnektivität."""
        try:
            await self._request('GET', f'/servers/{uuid}/validate')
            return True
        except CoolifyError:
            return False
```

---

## 5. Haupt-Provisioner

```python
# orchestrator/provisioner.py

"""Haupt-Orchestrierungslogik für Projekt-Provisionierung."""
import asyncio
import secrets
from datetime import datetime, timezone
from typing import Callable, Any

from v_flask import db

from app.models import (
    Project, ProjectDomain, Server, ProvisioningLog,
    ProvisioningStatus, DomainType, DomainStatus,
)
from app.orchestrator.clients.inwx_client import INWXClient
from app.orchestrator.clients.coolify_client import CoolifyClient
from app.orchestrator.exceptions import ProvisioningError
from app.orchestrator.strategies.server_selection import ServerSelector


class ProjectProvisioner:
    """Orchestriert die Provisionierung eines VRS-Projekts.
    
    Ablauf:
    1. DNS konfigurieren (INWX)
    2. Coolify-Projekt erstellen
    3. Application deployen
    4. Health Check
    5. Benachrichtigung
    
    Beispiel:
        provisioner = ProjectProvisioner()
        await provisioner.provision_project(project)
    """
    
    MAX_RETRIES = 3
    HEALTH_CHECK_TIMEOUT = 600  # 10 Minuten
    HEALTH_CHECK_INTERVAL = 15  # Sekunden
    
    def __init__(self):
        self.inwx = INWXClient()
        self.coolify = CoolifyClient()
        self.server_selector = ServerSelector()
    
    async def provision_project(self, project: Project) -> None:
        """Provisioniert ein komplettes Projekt.
        
        Args:
            project: Das zu provisionierende Projekt
        
        Raises:
            ProvisioningError: Bei Fehlern
        """
        self._log(project, 'provisioning_started', message='Provisionierung gestartet')
        
        project.provisioning_started_at = datetime.now(timezone.utc)
        project.provisioning_error = None
        db.session.commit()
        
        try:
            # 1. DNS konfigurieren
            await self._configure_dns(project)
            
            # 2. Server auswählen
            server = await self._select_server(project)
            
            # 3. Coolify-Projekt erstellen
            await self._create_coolify_project(project, server)
            
            # 4. Application deployen
            await self._deploy_application(project)
            
            # 5. Auf Deployment warten
            await self._wait_for_deployment(project)
            
            # 6. Health Check
            await self._health_check(project)
            
            # 7. Abschluss
            await self._finalize(project)
            
        except Exception as e:
            await self._handle_error(project, e)
            raise
    
    # =========================================================
    # DNS
    # =========================================================
    
    async def _configure_dns(self, project: Project) -> None:
        """Konfiguriert DNS für das Projekt."""
        self._update_status(project, ProvisioningStatus.PENDING_DOMAIN)
        
        domain = project.primary_domain
        if not domain:
            raise ProvisioningError("No domain configured for project")
        
        # Prüfen ob DNS schon konfiguriert
        if domain.status == DomainStatus.ACTIVE:
            self._log(project, 'dns_skipped', message='DNS bereits konfiguriert')
            return
        
        # Warte auf Domain-Registrierung/Transfer falls nötig
        if domain.status == DomainStatus.PENDING_REGISTRATION:
            await self._wait_for_domain_registration(project, domain)
        elif domain.status == DomainStatus.PENDING_TRANSFER:
            await self._wait_for_domain_transfer(project, domain)
        
        # DNS-Records anlegen
        server = project.server or await self._select_server(project)
        
        try:
            record_ids = self.inwx.setup_project_dns(
                domain=domain.full_domain,
                server_ip=server.ip_address,
                is_subdomain=domain.is_subdomain,
                base_domain=domain.base_domain.domain if domain.base_domain else None,
            )
            
            domain.inwx_record_ids = record_ids
            domain.status = DomainStatus.ACTIVE
            db.session.commit()
            
            self._log(
                project, 'dns_configured',
                message=f'DNS Records angelegt: {record_ids}',
                external_service='inwx',
            )
            
            # Kurze Pause für DNS-Propagation
            await asyncio.sleep(5)
            
        except Exception as e:
            self._log(
                project, 'dns_failed',
                error_details=str(e),
                external_service='inwx',
            )
            raise ProvisioningError(f"DNS configuration failed: {e}")
    
    async def _wait_for_domain_registration(
        self,
        project: Project,
        domain: ProjectDomain,
        timeout: int = 300,
    ) -> None:
        """Wartet auf Domain-Registrierung."""
        # Domain-Registrierung ist normalerweise schnell (<1 Minute)
        # Hier könnte Polling implementiert werden
        self._log(project, 'domain_registration_waiting')
        await asyncio.sleep(10)  # Placeholder
    
    async def _wait_for_domain_transfer(
        self,
        project: Project,
        domain: ProjectDomain,
        timeout: int = 432000,  # 5 Tage
    ) -> None:
        """Wartet auf Domain-Transfer.
        
        HINWEIS: Domain-Transfers können mehrere Tage dauern.
        Diese Methode sollte in Produktion als separater Hintergrund-Job laufen.
        """
        self._log(project, 'domain_transfer_waiting')
        
        start_time = datetime.now(timezone.utc)
        
        while True:
            status = self.inwx.get_transfer_status(domain.domain)
            
            if status == 'completed':
                domain.status = DomainStatus.PENDING_DNS
                db.session.commit()
                self._log(project, 'domain_transfer_completed')
                return
            
            if status == 'failed':
                raise ProvisioningError("Domain transfer failed")
            
            # Timeout prüfen
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed > timeout:
                raise ProvisioningError("Domain transfer timeout")
            
            # Warte und prüfe erneut
            await asyncio.sleep(3600)  # Stündlich prüfen
    
    # =========================================================
    # Server Selection
    # =========================================================
    
    async def _select_server(self, project: Project) -> Server:
        """Wählt einen Server für das Deployment."""
        if project.server:
            return project.server
        
        server = self.server_selector.select()
        
        if not server:
            raise ProvisioningError("No available server for deployment")
        
        project.server = server
        project.server_id = server.id
        db.session.commit()
        
        self._log(
            project, 'server_selected',
            message=f'Server ausgewählt: {server.name}',
        )
        
        return server
    
    # =========================================================
    # Coolify
    # =========================================================
    
    async def _create_coolify_project(
        self,
        project: Project,
        server: Server,
    ) -> None:
        """Erstellt Coolify-Projekt und Application."""
        self._update_status(project, ProvisioningStatus.PROVISIONING)
        
        try:
            # 1. Coolify-Projekt erstellen
            coolify_project = await self.coolify.create_project(
                name=f'vrs-{project.slug}',
                description=f'VRS Projekt: {project.name}',
            )
            
            project.coolify_project_uuid = coolify_project.uuid
            db.session.commit()
            
            self._log(
                project, 'coolify_project_created',
                message=f'Coolify Projekt erstellt: {coolify_project.uuid}',
                external_id=coolify_project.uuid,
                external_service='coolify',
            )
            
            # 2. Application erstellen
            domain = project.primary_domain
            plugins = self._get_plugin_names(project)
            
            coolify_app = await self.coolify.create_application(
                project_uuid=coolify_project.uuid,
                server_uuid=server.coolify_uuid,
                domain=domain.full_domain,
                vrs_project_id=str(project.id),
                vrs_plugins=plugins,
                name=f'vrs-{project.slug}',
            )
            
            project.coolify_app_uuid = coolify_app.uuid
            db.session.commit()
            
            self._log(
                project, 'coolify_app_created',
                message=f'Application erstellt: {coolify_app.uuid}',
                external_id=coolify_app.uuid,
                external_service='coolify',
            )
            
        except Exception as e:
            self._log(
                project, 'coolify_error',
                error_details=str(e),
                external_service='coolify',
            )
            raise ProvisioningError(f"Coolify setup failed: {e}")
    
    def _get_plugin_names(self, project: Project) -> list[str]:
        """Holt Plugin-Namen für das Projekt."""
        # Aus Bundle oder Lizenzen
        if project.bundle:
            return project.bundle.plugin_names
        
        # Aus aktiven Lizenzen
        return [lic.plugin_name for lic in project.active_licenses]
    
    async def _deploy_application(self, project: Project) -> None:
        """Startet das Deployment."""
        self._update_status(project, ProvisioningStatus.BOOTSTRAPPING)
        
        try:
            deployment = await self.coolify.deploy_application(
                project.coolify_app_uuid
            )
            
            self._log(
                project, 'deployment_started',
                message='Deployment gestartet',
                external_id=deployment.uuid,
                external_service='coolify',
            )
            
        except Exception as e:
            raise ProvisioningError(f"Deployment failed: {e}")
    
    async def _wait_for_deployment(self, project: Project) -> None:
        """Wartet auf erfolgreiches Deployment."""
        start_time = datetime.now(timezone.utc)
        
        while True:
            status = await self.coolify.get_deployment_status(
                project.coolify_app_uuid
            )
            
            if status == 'running':
                self._log(project, 'deployment_completed')
                return
            
            if status in ('failed', 'error'):
                raise ProvisioningError(f"Deployment failed with status: {status}")
            
            # Timeout prüfen
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed > self.HEALTH_CHECK_TIMEOUT:
                raise ProvisioningError("Deployment timeout")
            
            await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)
    
    # =========================================================
    # Health Check
    # =========================================================
    
    async def _health_check(self, project: Project) -> None:
        """Führt Health Check durch."""
        import httpx
        
        domain = project.primary_domain
        url = f'https://{domain.full_domain}/health'
        
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(verify=False, timeout=10) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        self._log(project, 'health_check_passed')
                        return
            except Exception as e:
                self._log(
                    project, 'health_check_attempt',
                    message=f'Attempt {attempt + 1}/{max_attempts}: {e}',
                )
            
            await asyncio.sleep(10)
        
        self._log(project, 'health_check_failed')
        raise ProvisioningError("Health check failed after max attempts")
    
    # =========================================================
    # Finalize
    # =========================================================
    
    async def _finalize(self, project: Project) -> None:
        """Schließt Provisionierung ab."""
        project.provisioning_status = ProvisioningStatus.ACTIVE
        project.provisioning_completed_at = datetime.now(timezone.utc)
        project.is_active = True
        db.session.commit()
        
        self._log(project, 'provisioning_completed', message='Provisionierung abgeschlossen')
        
        # Benachrichtigung senden
        await self._send_notification(project)
    
    async def _send_notification(self, project: Project) -> None:
        """Sendet Benachrichtigung an Kunden."""
        from app.orchestrator.tasks.notification_tasks import send_welcome_email
        
        # Temporäres Passwort generieren
        temp_password = secrets.token_urlsafe(12)
        
        # TODO: Passwort in vrs-core setzen via API
        
        await send_welcome_email(
            project=project,
            temp_password=temp_password,
        )
        
        self._log(project, 'notification_sent')
    
    # =========================================================
    # Error Handling
    # =========================================================
    
    async def _handle_error(self, project: Project, error: Exception) -> None:
        """Behandelt Fehler während Provisionierung."""
        project.provisioning_status = ProvisioningStatus.ERROR
        project.provisioning_error = str(error)
        project.provisioning_retry_count += 1
        db.session.commit()
        
        self._log(
            project, 'provisioning_failed',
            error_details=str(error),
        )
        
        # Admin benachrichtigen
        from app.orchestrator.tasks.notification_tasks import send_admin_alert
        await send_admin_alert(project, error)
    
    # =========================================================
    # Helpers
    # =========================================================
    
    def _update_status(
        self,
        project: Project,
        status: ProvisioningStatus,
    ) -> None:
        """Aktualisiert Provisioning-Status."""
        old_status = project.provisioning_status
        project.provisioning_status = status
        db.session.commit()
        
        self._log(
            project, 'status_changed',
            old_status=old_status.value if old_status else None,
            new_status=status.value,
        )
    
    def _log(
        self,
        project: Project,
        action: str,
        **kwargs,
    ) -> None:
        """Erstellt Log-Eintrag."""
        ProvisioningLog.log(
            project_id=project.id,
            action=action,
            triggered_by='system',
            **kwargs,
        )
```

---

## 6. Server Selection Strategies

```python
# orchestrator/strategies/server_selection.py

"""Server-Auswahl-Strategien."""
from abc import ABC, abstractmethod

from app.models import Server


class ServerSelectionStrategy(ABC):
    """Basis-Klasse für Server-Auswahl."""
    
    @abstractmethod
    def select(self, servers: list[Server]) -> Server | None:
        """Wählt einen Server aus der Liste."""
        pass


class LeastLoadedStrategy(ServerSelectionStrategy):
    """Wählt den Server mit der geringsten Last."""
    
    def select(self, servers: list[Server]) -> Server | None:
        if not servers:
            return None
        return max(servers, key=lambda s: s.available_slots)


class RoundRobinStrategy(ServerSelectionStrategy):
    """Rotiert durch alle Server."""
    
    _counter = 0
    
    def select(self, servers: list[Server]) -> Server | None:
        if not servers:
            return None
        
        server = servers[self._counter % len(servers)]
        RoundRobinStrategy._counter += 1
        return server


class ServerSelector:
    """Server-Selector mit konfigurierbarer Strategie."""
    
    def __init__(self, strategy: ServerSelectionStrategy | None = None):
        self.strategy = strategy or LeastLoadedStrategy()
    
    def select(self) -> Server | None:
        """Wählt einen verfügbaren Server."""
        available = Server.get_available()
        return self.strategy.select(available)
```

---

## 7. Exceptions

```python
# orchestrator/exceptions.py

"""Custom Exceptions für Orchestrator."""


class OrchestratorError(Exception):
    """Basis-Exception für Orchestrator."""
    pass


class ProvisioningError(OrchestratorError):
    """Fehler während Provisionierung."""
    pass


class INWXError(OrchestratorError):
    """Fehler bei INWX API."""
    pass


class DomainNotAvailableError(INWXError):
    """Domain ist nicht verfügbar."""
    pass


class DNSRecordError(INWXError):
    """Fehler bei DNS Record Operation."""
    pass


class CoolifyError(OrchestratorError):
    """Fehler bei Coolify API."""
    pass
```

---

## 8. Async Task Queue

Für lang laufende Tasks (Domain-Transfer, etc.) sollte eine Task Queue verwendet werden:

```python
# orchestrator/tasks/__init__.py

"""Async Tasks für Orchestrator.

Empfehlung: Celery oder Dramatiq für Production.
Für einfache Fälle: asyncio.create_task()
"""

import asyncio
from functools import wraps


def background_task(func):
    """Decorator für Hintergrund-Tasks."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.create_task(func(*args, **kwargs))
    return wrapper


# Beispiel Celery-Setup (falls verwendet):
#
# from celery import Celery
# celery_app = Celery('vrs-marketplace')
#
# @celery_app.task
# def provision_project_task(project_id: int):
#     from app.orchestrator.provisioner import ProjectProvisioner
#     from app.models import Project
#     
#     project = Project.query.get(project_id)
#     provisioner = ProjectProvisioner()
#     asyncio.run(provisioner.provision_project(project))
```

---

## 9. Verwendung

### 9.1 In Routes

```python
# routes/api.py

from flask import Blueprint, request, jsonify
from app.orchestrator.provisioner import ProjectProvisioner
from app.models import Project, ProvisioningStatus

api = Blueprint('api', __name__)


@api.route('/projects', methods=['POST'])
async def create_project():
    """Erstellt und provisioniert ein neues Projekt."""
    data = request.json
    
    # Projekt anlegen
    project = Project(
        name=data['name'],
        slug=data['slug'],
        owner_email=data['email'],
        project_type_id=data['project_type_id'],
        provisioning_status=ProvisioningStatus.DRAFT,
    )
    db.session.add(project)
    db.session.commit()
    
    # Domain anlegen
    # ... (siehe Models)
    
    # Provisionierung starten (async)
    provisioner = ProjectProvisioner()
    asyncio.create_task(provisioner.provision_project(project))
    
    return jsonify({
        'project_id': project.id,
        'status': 'provisioning',
    }), 202
```

### 9.2 Manueller Retry

```python
@api.route('/projects/<int:project_id>/retry', methods=['POST'])
async def retry_provisioning(project_id: int):
    """Wiederholt fehlgeschlagene Provisionierung."""
    project = Project.query.get_or_404(project_id)
    
    if not project.can_retry_provisioning:
        return jsonify({'error': 'Cannot retry'}), 400
    
    project.clear_provisioning_error()
    
    provisioner = ProjectProvisioner()
    asyncio.create_task(provisioner.provision_project(project))
    
    return jsonify({'status': 'retrying'}), 202
```
