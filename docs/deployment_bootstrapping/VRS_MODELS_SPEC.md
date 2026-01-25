# VRS Models Spezifikation

> **Version:** 1.0  
> **Datum:** Januar 2026  
> **Bezug:** VRS_DEPLOYMENT_SPEC.md

---

## 1. Übersicht der Models

### 1.1 Bestehende Models (anzupassen)

| Model | Datei | Änderungen |
|-------|-------|------------|
| `Project` | `project.py` | Erweitern um Provisioning-Felder |
| `ProjectType` | `project_type.py` | Unverändert |
| `License` | `license.py` | Unverändert |
| `PluginPrice` | `plugin_price.py` | Unverändert |
| `LicenseHistory` | `license_history.py` | Unverändert |

### 1.2 Neue Models

| Model | Datei | Zweck |
|-------|-------|-------|
| `BaseDomain` | `base_domain.py` | Verwaltung von Basis-Domains für Subdomains |
| `ProjectDomain` | `project_domain.py` | Domain(s) eines Projekts |
| `Server` | `server.py` | Hetzner VPS / Coolify Server |
| `ProvisioningLog` | `provisioning_log.py` | Audit-Trail für Provisionierung |
| `Bundle` | `bundle.py` | Plugin-Bundles (Vorschlag) |
| `PreviewAccess` | `preview_access.py` | Preview-Protection Tokens |

---

## 2. Enum-Definitionen

### 2.1 ProvisioningStatus

```python
# enums.py

import enum

class ProvisioningStatus(enum.Enum):
    """Status des Provisionierungs-Prozesses."""
    
    DRAFT = 'draft'
    """Projekt angelegt, Fragebogen nicht abgeschlossen."""
    
    PENDING_PAYMENT = 'pending_payment'
    """Wartet auf Zahlungsbestätigung."""
    
    PENDING_DOMAIN = 'pending_domain'
    """Domain-Registrierung oder Transfer läuft."""
    
    PROVISIONING = 'provisioning'
    """Coolify-Deployment wird erstellt."""
    
    BOOTSTRAPPING = 'bootstrapping'
    """vrs-core startet und lädt Plugins."""
    
    ACTIVE = 'active'
    """Projekt ist live und erreichbar."""
    
    SUSPENDED = 'suspended'
    """Temporär deaktiviert (z.B. Zahlungsproblem)."""
    
    ARCHIVED = 'archived'
    """Projekt wurde beendet/archiviert."""
    
    ERROR = 'error'
    """Fehler bei Provisionierung."""


class DomainType(enum.Enum):
    """Art der Domain-Zuweisung."""
    
    SUBDOMAIN = 'subdomain'
    """Subdomain unter einer Basis-Domain (z.B. projekt.vrs.gmbh)."""
    
    OWNED = 'owned'
    """Bereits bei uns registrierte Domain."""
    
    REGISTERED = 'registered'
    """Neu über INWX registrierte Domain."""
    
    TRANSFERRED = 'transferred'
    """Von anderem Registrar zu INWX transferiert."""


class DomainStatus(enum.Enum):
    """Status einer Domain."""
    
    PENDING_REGISTRATION = 'pending_registration'
    """Domain-Registrierung läuft."""
    
    PENDING_TRANSFER = 'pending_transfer'
    """Domain-Transfer läuft."""
    
    PENDING_DNS = 'pending_dns'
    """DNS-Records werden angelegt."""
    
    ACTIVE = 'active'
    """Domain ist aktiv und konfiguriert."""
    
    EXPIRED = 'expired'
    """Domain ist abgelaufen."""
    
    SUSPENDED = 'suspended'
    """Domain ist suspendiert."""


class PaymentMethod(enum.Enum):
    """Zahlungsmethode für ein Projekt."""
    
    STRIPE_PREPAID = 'stripe_prepaid'
    """Vorauszahlung via Stripe."""
    
    STRIPE_SUBSCRIPTION = 'stripe_subscription'
    """Stripe-Abo (monatlich/jährlich)."""
    
    INVOICE = 'invoice'
    """Zahlung per Rechnung."""
    
    FREE = 'free'
    """Kostenloses Projekt (intern)."""


class ServerStatus(enum.Enum):
    """Status eines Servers."""
    
    PROVISIONING = 'provisioning'
    """Server wird erstellt."""
    
    ACTIVE = 'active'
    """Server ist aktiv und erreichbar."""
    
    MAINTENANCE = 'maintenance'
    """Server ist in Wartung."""
    
    OFFLINE = 'offline'
    """Server ist nicht erreichbar."""
```

---

## 3. Model: Project (Erweiterung)

```python
# project.py - Erweiterte Version

"""Project model for satellite projects."""
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from v_flask import db
from .enums import ProvisioningStatus, PaymentMethod

if TYPE_CHECKING:
    from .project_domain import ProjectDomain
    from .server import Server


class Project(db.Model):
    """Satellite project that can purchase and download plugins.

    Each project has a unique API key for authentication.
    """

    __tablename__ = 'marketplace_project'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    owner_email = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Superadmin projects can see alpha/beta plugins (V-Flask internal projects)
    is_superadmin = db.Column(db.Boolean, default=False, nullable=False)

    # Project type (for pricing tiers)
    project_type_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project_type.id'),
        nullable=True,
        index=True
    )

    # Trial period tracking
    trial_start_date = db.Column(db.DateTime, nullable=True)
    trial_end_date = db.Column(db.DateTime, nullable=True)

    # ============================================================
    # NEU: Provisioning-Felder
    # ============================================================
    
    provisioning_status = db.Column(
        db.Enum(ProvisioningStatus),
        default=ProvisioningStatus.DRAFT,
        nullable=False,
        index=True
    )
    provisioning_started_at = db.Column(db.DateTime, nullable=True)
    provisioning_completed_at = db.Column(db.DateTime, nullable=True)
    provisioning_error = db.Column(db.Text, nullable=True)
    provisioning_retry_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Coolify-Referenzen
    coolify_project_uuid = db.Column(db.String(100), nullable=True, index=True)
    coolify_app_uuid = db.Column(db.String(100), nullable=True, index=True)
    coolify_environment_uuid = db.Column(db.String(100), nullable=True)
    
    # Server-Zuweisung
    server_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_server.id'),
        nullable=True,
        index=True
    )
    
    # Demo/Preview
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    cloned_from_project_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project.id'),
        nullable=True
    )
    preview_protection_enabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Billing
    payment_method = db.Column(
        db.Enum(PaymentMethod),
        default=PaymentMethod.INVOICE,
        nullable=False
    )
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    billing_email = db.Column(db.String(255), nullable=True)
    
    # Bundle (wenn über Bundle gekauft)
    bundle_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_bundle.id'),
        nullable=True
    )

    # ============================================================
    # Ende NEU
    # ============================================================

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships (bestehend)
    licenses = db.relationship('License', back_populates='project', lazy='dynamic')
    orders = db.relationship('Order', back_populates='project', lazy='dynamic')
    project_type = db.relationship('ProjectType', back_populates='projects')
    
    # Relationships (neu)
    domains = db.relationship(
        'ProjectDomain',
        back_populates='project',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    server = db.relationship('Server', back_populates='projects')
    cloned_from = db.relationship(
        'Project',
        remote_side=[id],
        backref='clones'
    )
    bundle = db.relationship('Bundle', back_populates='projects')
    provisioning_logs = db.relationship(
        'ProvisioningLog',
        back_populates='project',
        lazy='dynamic',
        order_by='desc(ProvisioningLog.created_at)'
    )
    preview_accesses = db.relationship(
        'PreviewAccess',
        back_populates='project',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<Project {self.name}>'

    # ============================================================
    # NEU: Properties und Methoden
    # ============================================================

    @property
    def primary_domain(self) -> 'ProjectDomain | None':
        """Get the primary domain for this project."""
        return self.domains.filter_by(is_primary=True).first()
    
    @property
    def primary_domain_name(self) -> str | None:
        """Get the primary domain name as string."""
        domain = self.primary_domain
        return domain.full_domain if domain else None
    
    @property
    def is_provisioning(self) -> bool:
        """Check if project is currently being provisioned."""
        return self.provisioning_status in (
            ProvisioningStatus.PENDING_DOMAIN,
            ProvisioningStatus.PROVISIONING,
            ProvisioningStatus.BOOTSTRAPPING,
        )
    
    @property
    def is_live(self) -> bool:
        """Check if project is live and accessible."""
        return self.provisioning_status == ProvisioningStatus.ACTIVE
    
    @property
    def can_retry_provisioning(self) -> bool:
        """Check if provisioning can be retried."""
        return (
            self.provisioning_status == ProvisioningStatus.ERROR
            and self.provisioning_retry_count < 3
        )
    
    def set_provisioning_error(self, error: str) -> None:
        """Set provisioning error and increment retry count."""
        self.provisioning_status = ProvisioningStatus.ERROR
        self.provisioning_error = error
        self.provisioning_retry_count += 1
        db.session.commit()
    
    def clear_provisioning_error(self) -> None:
        """Clear provisioning error for retry."""
        self.provisioning_error = None
        db.session.commit()

    # ============================================================
    # Bestehende Properties (unverändert)
    # ============================================================

    @property
    def can_see_dev_plugins(self) -> bool:
        """Check if project can see alpha/beta plugins."""
        return self.is_superadmin

    @property
    def active_licenses(self):
        """Get all active (non-expired) licenses."""
        from .license import License
        now = datetime.now(timezone.utc)
        return self.licenses.filter(
            (License.expires_at.is_(None)) | (License.expires_at > now)
        ).all()

    def has_license_for(self, plugin_name: str) -> bool:
        """Check if project has an active license for a plugin."""
        from .license import License, LICENSE_STATUS_ACTIVE, LICENSE_STATUS_TRIAL
        now = datetime.now(timezone.utc)
        return self.licenses.filter(
            License.plugin_name == plugin_name,
            License.status.in_([LICENSE_STATUS_ACTIVE, LICENSE_STATUS_TRIAL]),
            (License.expires_at.is_(None)) | (License.expires_at > now)
        ).count() > 0

    @property
    def is_in_trial(self) -> bool:
        """Check if project is currently in trial period."""
        if not self.trial_start_date or not self.trial_end_date:
            return False
        now = datetime.now(timezone.utc)
        return self.trial_start_date <= now <= self.trial_end_date

    @property
    def is_trial_expired(self) -> bool:
        """Check if trial period has expired."""
        if not self.trial_end_date:
            return False
        return datetime.now(timezone.utc) > self.trial_end_date

    @property
    def trial_days_remaining(self) -> int | None:
        """Get remaining trial days, or None if not in trial."""
        if not self.trial_end_date:
            return None
        now = datetime.now(timezone.utc)
        if now > self.trial_end_date:
            return 0
        delta = self.trial_end_date - now
        return max(0, delta.days)

    def start_trial(self, days: int | None = None) -> bool:
        """Start trial period for this project."""
        from datetime import timedelta

        if days is None:
            if not self.project_type or not self.project_type.has_trial:
                return False
            days = self.project_type.trial_days

        if days <= 0:
            return False

        now = datetime.now(timezone.utc)
        self.trial_start_date = now
        self.trial_end_date = now + timedelta(days=days)
        db.session.commit()
        return True
```

---

## 4. Model: BaseDomain (Neu)

```python
# base_domain.py

"""BaseDomain model for managing base domains for subdomains."""
from datetime import datetime, timezone

from v_flask import db


class BaseDomain(db.Model):
    """Base domain that can be used for project subdomains.
    
    Example: If vrs.gmbh is a base domain, projects can use
    subdomains like projekt.vrs.gmbh.
    """

    __tablename__ = 'marketplace_base_domain'

    id = db.Column(db.Integer, primary_key=True)
    
    # Domain name (e.g., "vrs.gmbh")
    domain = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Display name for UI
    display_name = db.Column(db.String(100), nullable=False)
    
    # INWX reference (for the base domain itself)
    inwx_domain_id = db.Column(db.Integer, nullable=True)
    
    # Whether this base domain is available for new projects
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Whether this is the default base domain
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    
    # Sort order for display
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    # Wildcard SSL certificate (if available)
    has_wildcard_ssl = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    project_domains = db.relationship(
        'ProjectDomain',
        back_populates='base_domain',
        lazy='dynamic'
    )

    def __repr__(self) -> str:
        return f'<BaseDomain {self.domain}>'

    @classmethod
    def get_default(cls) -> 'BaseDomain | None':
        """Get the default base domain."""
        return cls.query.filter_by(is_default=True, is_active=True).first()
    
    @classmethod
    def get_active(cls) -> list['BaseDomain']:
        """Get all active base domains ordered by sort_order."""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()
    
    @classmethod
    def seed_defaults(cls) -> list['BaseDomain']:
        """Create default base domains if they don't exist."""
        defaults = [
            {
                'domain': 'vrs.gmbh',
                'display_name': 'VRS GmbH',
                'is_active': True,
                'is_default': True,
                'sort_order': 1,
            },
        ]

        created = []
        for data in defaults:
            existing = cls.query.filter_by(domain=data['domain']).first()
            if not existing:
                base_domain = cls(**data)
                db.session.add(base_domain)
                created.append(base_domain)

        if created:
            db.session.commit()

        return created
```

---

## 5. Model: ProjectDomain (Neu)

```python
# project_domain.py

"""ProjectDomain model for project domain management."""
from datetime import datetime, timezone

from v_flask import db
from .enums import DomainType, DomainStatus


class ProjectDomain(db.Model):
    """Domain(s) assigned to a project.
    
    A project can have multiple domains, but only one primary.
    """

    __tablename__ = 'marketplace_project_domain'

    id = db.Column(db.Integer, primary_key=True)
    
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project.id'),
        nullable=False,
        index=True
    )
    
    # Full domain name (e.g., "projekt.vrs.gmbh" or "example.com")
    domain = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Domain type
    domain_type = db.Column(
        db.Enum(DomainType),
        nullable=False
    )
    
    # Domain status
    status = db.Column(
        db.Enum(DomainStatus),
        default=DomainStatus.PENDING_DNS,
        nullable=False,
        index=True
    )
    
    # Whether this is the primary domain
    is_primary = db.Column(db.Boolean, default=True, nullable=False)
    
    # ============================================================
    # Subdomain-specific fields
    # ============================================================
    
    # Reference to base domain (for subdomains)
    base_domain_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_base_domain.id'),
        nullable=True,
        index=True
    )
    
    # Subdomain part (e.g., "projekt" for "projekt.vrs.gmbh")
    subdomain = db.Column(db.String(100), nullable=True)
    
    # ============================================================
    # INWX references
    # ============================================================
    
    # INWX domain object ID (for registered/transferred domains)
    inwx_domain_id = db.Column(db.Integer, nullable=True)
    
    # INWX DNS record IDs (stored as JSON for multiple records)
    # Format: {"a": 123, "www": 456, "aaaa": 789}
    inwx_record_ids = db.Column(db.JSON, nullable=True)
    
    # ============================================================
    # Registration/Transfer fields
    # ============================================================
    
    # Auth code for transfers (encrypted in production!)
    transfer_auth_code = db.Column(db.String(255), nullable=True)
    
    # Registration/renewal costs (in cents)
    registration_cost_cents = db.Column(db.Integer, nullable=True)
    renewal_cost_cents = db.Column(db.Integer, nullable=True)
    
    # Domain expiration
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # ============================================================
    # SSL fields
    # ============================================================
    
    ssl_provisioned = db.Column(db.Boolean, default=False, nullable=False)
    ssl_expires_at = db.Column(db.DateTime, nullable=True)
    
    # ============================================================
    # Timestamps
    # ============================================================
    
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    project = db.relationship('Project', back_populates='domains')
    base_domain = db.relationship('BaseDomain', back_populates='project_domains')

    # Constraints
    __table_args__ = (
        # Unique subdomain per base domain
        db.UniqueConstraint(
            'base_domain_id', 'subdomain',
            name='uq_base_domain_subdomain'
        ),
    )

    def __repr__(self) -> str:
        return f'<ProjectDomain {self.domain}>'

    @property
    def full_domain(self) -> str:
        """Get the full domain name."""
        if self.domain_type == DomainType.SUBDOMAIN and self.base_domain:
            return f'{self.subdomain}.{self.base_domain.domain}'
        return self.domain
    
    @property
    def is_subdomain(self) -> bool:
        """Check if this is a subdomain."""
        return self.domain_type == DomainType.SUBDOMAIN
    
    @property
    def is_active(self) -> bool:
        """Check if domain is active."""
        return self.status == DomainStatus.ACTIVE
    
    @property
    def is_pending(self) -> bool:
        """Check if domain is in any pending state."""
        return self.status in (
            DomainStatus.PENDING_REGISTRATION,
            DomainStatus.PENDING_TRANSFER,
            DomainStatus.PENDING_DNS,
        )
    
    def get_inwx_record_id(self, record_type: str) -> int | None:
        """Get INWX record ID for a specific record type."""
        if not self.inwx_record_ids:
            return None
        return self.inwx_record_ids.get(record_type.lower())
    
    def set_inwx_record_id(self, record_type: str, record_id: int) -> None:
        """Set INWX record ID for a specific record type."""
        if self.inwx_record_ids is None:
            self.inwx_record_ids = {}
        self.inwx_record_ids[record_type.lower()] = record_id
    
    @classmethod
    def create_subdomain(
        cls,
        project_id: int,
        subdomain: str,
        base_domain_id: int | None = None
    ) -> 'ProjectDomain':
        """Create a subdomain entry.
        
        Args:
            project_id: ID of the project
            subdomain: Subdomain part (e.g., "mein-projekt")
            base_domain_id: ID of base domain, or None for default
        
        Returns:
            Created ProjectDomain instance
        """
        if base_domain_id is None:
            from .base_domain import BaseDomain
            default = BaseDomain.get_default()
            if not default:
                raise ValueError("No default base domain configured")
            base_domain_id = default.id
        
        from .base_domain import BaseDomain
        base = BaseDomain.query.get(base_domain_id)
        
        domain = cls(
            project_id=project_id,
            domain=f'{subdomain}.{base.domain}',
            domain_type=DomainType.SUBDOMAIN,
            status=DomainStatus.PENDING_DNS,
            is_primary=True,
            base_domain_id=base_domain_id,
            subdomain=subdomain,
        )
        
        db.session.add(domain)
        db.session.commit()
        return domain
```

---

## 6. Model: Server (Neu)

```python
# server.py

"""Server model for Hetzner VPS / Coolify server management."""
from datetime import datetime, timezone

from v_flask import db
from .enums import ServerStatus


class Server(db.Model):
    """Hetzner VPS server managed by Coolify.
    
    Each server can host multiple projects.
    """

    __tablename__ = 'marketplace_server'

    id = db.Column(db.Integer, primary_key=True)
    
    # Display name
    name = db.Column(db.String(100), nullable=False)
    
    # Coolify server UUID
    coolify_uuid = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Hetzner server ID (if created via Hetzner API)
    hetzner_server_id = db.Column(db.Integer, nullable=True)
    
    # Server status
    status = db.Column(
        db.Enum(ServerStatus),
        default=ServerStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Connection details
    ip_address = db.Column(db.String(45), nullable=False)  # IPv4 or IPv6
    ssh_port = db.Column(db.Integer, default=22, nullable=False)
    
    # Capacity
    max_projects = db.Column(db.Integer, default=20, nullable=False)
    
    # Hetzner details
    hetzner_server_type = db.Column(db.String(50), nullable=True)  # e.g., "cx31"
    hetzner_location = db.Column(db.String(50), nullable=True)  # e.g., "fsn1"
    
    # Whether new projects can be deployed to this server
    is_accepting_new = db.Column(db.Boolean, default=True, nullable=False)
    
    # Notes
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    projects = db.relationship('Project', back_populates='server', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Server {self.name} ({self.ip_address})>'

    @property
    def project_count(self) -> int:
        """Get number of projects on this server."""
        return self.projects.count()
    
    @property
    def available_slots(self) -> int:
        """Get number of available project slots."""
        return max(0, self.max_projects - self.project_count)
    
    @property
    def is_available(self) -> bool:
        """Check if server can accept new projects."""
        return (
            self.status == ServerStatus.ACTIVE
            and self.is_accepting_new
            and self.available_slots > 0
        )
    
    @classmethod
    def get_available(cls) -> list['Server']:
        """Get all servers that can accept new projects."""
        servers = cls.query.filter_by(
            status=ServerStatus.ACTIVE,
            is_accepting_new=True
        ).all()
        return [s for s in servers if s.available_slots > 0]
    
    @classmethod
    def get_least_loaded(cls) -> 'Server | None':
        """Get the server with the most available slots."""
        available = cls.get_available()
        if not available:
            return None
        return max(available, key=lambda s: s.available_slots)
```

---

## 7. Model: ProvisioningLog (Neu)

```python
# provisioning_log.py

"""ProvisioningLog model for audit trail of provisioning actions."""
from datetime import datetime, timezone

from v_flask import db


class ProvisioningLog(db.Model):
    """Audit trail for provisioning actions.
    
    Records all steps during project provisioning for debugging
    and support purposes.
    """

    __tablename__ = 'marketplace_provisioning_log'

    id = db.Column(db.Integer, primary_key=True)
    
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project.id'),
        nullable=False,
        index=True
    )
    
    # Action type
    action = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )
    # Actions: dns_created, dns_failed, coolify_project_created, 
    # coolify_app_created, deployment_started, deployment_completed,
    # bootstrap_started, bootstrap_completed, health_check_passed,
    # health_check_failed, error, retry, status_changed, etc.
    
    # Status before/after
    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=True)
    
    # Details
    message = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.Text, nullable=True)
    
    # External references (for debugging)
    external_id = db.Column(db.String(255), nullable=True)  # e.g., Coolify deployment ID
    external_service = db.Column(db.String(50), nullable=True)  # e.g., "coolify", "inwx"
    
    # Metadata
    metadata_json = db.Column(db.JSON, nullable=True)
    
    # Who/what triggered this
    triggered_by = db.Column(db.String(255), nullable=True)  # email or "system"
    
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    project = db.relationship('Project', back_populates='provisioning_logs')

    __table_args__ = (
        db.Index('idx_prov_log_project_created', 'project_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f'<ProvisioningLog {self.project_id}: {self.action}>'

    @classmethod
    def log(
        cls,
        project_id: int,
        action: str,
        message: str | None = None,
        old_status: str | None = None,
        new_status: str | None = None,
        error_details: str | None = None,
        external_id: str | None = None,
        external_service: str | None = None,
        triggered_by: str | None = None,
        metadata: dict | None = None,
    ) -> 'ProvisioningLog':
        """Create a new log entry.
        
        Args:
            project_id: ID of the project
            action: Action type
            message: Human-readable message
            old_status: Previous status
            new_status: New status
            error_details: Error details if applicable
            external_id: External service ID
            external_service: Name of external service
            triggered_by: Who triggered this action
            metadata: Additional metadata as dict
        
        Returns:
            Created ProvisioningLog entry
        """
        entry = cls(
            project_id=project_id,
            action=action,
            message=message,
            old_status=old_status,
            new_status=new_status,
            error_details=error_details,
            external_id=external_id,
            external_service=external_service,
            triggered_by=triggered_by or 'system',
            metadata_json=metadata,
        )
        
        db.session.add(entry)
        db.session.commit()
        return entry

    @classmethod
    def get_for_project(
        cls,
        project_id: int,
        limit: int = 100
    ) -> list['ProvisioningLog']:
        """Get log entries for a project, newest first."""
        return cls.query.filter_by(
            project_id=project_id
        ).order_by(
            cls.created_at.desc()
        ).limit(limit).all()
```

---

## 8. Model: PreviewAccess (Neu)

```python
# preview_access.py

"""PreviewAccess model for demo project access control."""
from datetime import datetime, timezone, timedelta
import secrets

from v_flask import db


class PreviewAccess(db.Model):
    """Access token for preview-protected projects.
    
    Allows temporary access to demo projects via magic link or code.
    """

    __tablename__ = 'marketplace_preview_access'

    id = db.Column(db.Integer, primary_key=True)
    
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project.id'),
        nullable=False,
        index=True
    )
    
    # Access token (for magic links)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # Short code (for manual entry)
    code = db.Column(db.String(6), nullable=True, index=True)
    
    # Who this access was created for
    email = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    
    # Validity
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Usage tracking
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    used_ip = db.Column(db.String(45), nullable=True)
    
    # Whether this token allows multiple uses
    is_reusable = db.Column(db.Boolean, default=True, nullable=False)
    use_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Notes
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    created_by = db.Column(db.String(255), nullable=True)  # email of admin

    # Relationships
    project = db.relationship('Project', back_populates='preview_accesses')

    def __repr__(self) -> str:
        return f'<PreviewAccess {self.project_id}: {self.email or self.code}>'

    @property
    def is_valid(self) -> bool:
        """Check if this access token is still valid."""
        if datetime.now(timezone.utc) > self.expires_at:
            return False
        if not self.is_reusable and self.is_used:
            return False
        return True
    
    @property
    def magic_link(self) -> str:
        """Generate magic link URL."""
        # This would use the project's domain
        project_domain = self.project.primary_domain_name
        return f'https://{project_domain}/preview-access?token={self.token}'
    
    def mark_used(self, ip: str | None = None) -> None:
        """Mark this access as used."""
        self.is_used = True
        self.use_count += 1
        self.used_at = datetime.now(timezone.utc)
        self.used_ip = ip
        db.session.commit()
    
    @classmethod
    def create(
        cls,
        project_id: int,
        email: str | None = None,
        name: str | None = None,
        hours_valid: int = 48,
        is_reusable: bool = True,
        created_by: str | None = None,
    ) -> 'PreviewAccess':
        """Create a new preview access token.
        
        Args:
            project_id: ID of the project
            email: Email of the recipient (optional)
            name: Name of the recipient (optional)
            hours_valid: How many hours the token is valid
            is_reusable: Whether token can be used multiple times
            created_by: Email of admin who created this
        
        Returns:
            Created PreviewAccess instance
        """
        access = cls(
            project_id=project_id,
            token=secrets.token_urlsafe(48),
            code=cls._generate_code(),
            email=email,
            name=name,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=hours_valid),
            is_reusable=is_reusable,
            created_by=created_by,
        )
        
        db.session.add(access)
        db.session.commit()
        return access
    
    @staticmethod
    def _generate_code() -> str:
        """Generate a 6-digit access code."""
        return ''.join(secrets.choice('0123456789') for _ in range(6))
    
    @classmethod
    def validate_token(cls, token: str) -> 'PreviewAccess | None':
        """Validate a token and return the access if valid."""
        access = cls.query.filter_by(token=token).first()
        if access and access.is_valid:
            return access
        return None
    
    @classmethod
    def validate_code(cls, project_id: int, code: str) -> 'PreviewAccess | None':
        """Validate a code for a specific project."""
        access = cls.query.filter_by(
            project_id=project_id,
            code=code
        ).first()
        if access and access.is_valid:
            return access
        return None
```

---

## 9. Model: Bundle (Vorschlag)

> **Hinweis:** Dieses Model ist ein Vorschlag und muss mit bereits existierender Planung abgeglichen werden.

```python
# bundle.py

"""Bundle model for plugin bundles (VORSCHLAG).

WICHTIG: Dieses Model ist ein Vorschlag. Es muss geprüft werden,
inwieweit bereits Planung oder Code für Bundles existiert.
Diese Definition soll als Ausgangspunkt dienen.
"""
from datetime import datetime, timezone

from v_flask import db


# Association table for Bundle <-> Plugin
bundle_plugins = db.Table(
    'marketplace_bundle_plugins',
    db.Column('bundle_id', db.Integer, db.ForeignKey('marketplace_bundle.id'), primary_key=True),
    db.Column('plugin_id', db.Integer, db.ForeignKey('marketplace_plugin_meta.id'), primary_key=True),
)


class Bundle(db.Model):
    """Plugin bundle for a project type.
    
    A bundle is a predefined combination of plugins offered
    at a combined price for a specific project type.
    
    VORSCHLAG - mit existierender Planung abgleichen!
    """

    __tablename__ = 'marketplace_bundle'

    id = db.Column(db.Integer, primary_key=True)
    
    # Bundle identifier
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Associated project type
    project_type_id = db.Column(
        db.Integer,
        db.ForeignKey('marketplace_project_type.id'),
        nullable=False,
        index=True
    )
    
    # Whether this is the default bundle for the project type
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    
    # Billing
    billing_cycle = db.Column(
        db.String(20),
        default='monthly',
        nullable=False
    )  # once, monthly, yearly
    
    # Discount (optional - price is sum of plugin prices minus discount)
    discount_percent = db.Column(db.Integer, default=0, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Display
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    project_type = db.relationship('ProjectType', backref='bundles')
    plugins = db.relationship(
        'PluginMeta',
        secondary=bundle_plugins,
        backref='bundles'
    )
    projects = db.relationship('Project', back_populates='bundle', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Bundle {self.code}: {self.name}>'

    @property
    def plugin_names(self) -> list[str]:
        """Get list of plugin names in this bundle."""
        return [p.name for p in self.plugins]
    
    @property
    def total_price_cents(self) -> int:
        """Calculate total price (sum of plugin prices minus discount).
        
        Uses PluginPrice for the associated project type.
        """
        from .plugin_price import PluginPrice
        
        total = 0
        for plugin in self.plugins:
            price = PluginPrice.get_for_plugin_and_type(
                plugin_id=plugin.id,
                project_type_id=self.project_type_id,
                billing_cycle=self.billing_cycle
            )
            if price:
                total += price.price_cents
        
        # Apply discount
        if self.discount_percent > 0:
            total = int(total * (100 - self.discount_percent) / 100)
        
        return total
    
    @property
    def price_display(self) -> str:
        """Get formatted price for display."""
        cents = self.total_price_cents
        if cents == 0:
            return 'Kostenlos'
        
        euros = cents / 100
        formatted = f'{euros:.2f} €'.replace('.', ',')
        
        suffix_map = {
            'once': '',
            'monthly': '/Monat',
            'yearly': '/Jahr',
        }
        return formatted + suffix_map.get(self.billing_cycle, '')
    
    @classmethod
    def get_for_project_type(cls, project_type_id: int) -> list['Bundle']:
        """Get all active bundles for a project type."""
        return cls.query.filter_by(
            project_type_id=project_type_id,
            is_active=True
        ).order_by(cls.sort_order).all()
    
    @classmethod
    def get_default_for_project_type(cls, project_type_id: int) -> 'Bundle | None':
        """Get the default bundle for a project type."""
        return cls.query.filter_by(
            project_type_id=project_type_id,
            is_default=True,
            is_active=True
        ).first()
```

---

## 10. Migration Notes

### 10.1 Neue Tabellen

```sql
-- In dieser Reihenfolge erstellen (wegen Foreign Keys):
1. marketplace_base_domain
2. marketplace_server
3. marketplace_bundle  (falls verwendet)
4. marketplace_project_domain
5. marketplace_provisioning_log
6. marketplace_preview_access
7. marketplace_bundle_plugins  (falls verwendet)
```

### 10.2 Änderungen an marketplace_project

```sql
-- Neue Spalten hinzufügen
ALTER TABLE marketplace_project ADD COLUMN provisioning_status VARCHAR(30) DEFAULT 'draft';
ALTER TABLE marketplace_project ADD COLUMN provisioning_started_at TIMESTAMP;
ALTER TABLE marketplace_project ADD COLUMN provisioning_completed_at TIMESTAMP;
ALTER TABLE marketplace_project ADD COLUMN provisioning_error TEXT;
ALTER TABLE marketplace_project ADD COLUMN provisioning_retry_count INTEGER DEFAULT 0;
ALTER TABLE marketplace_project ADD COLUMN coolify_project_uuid VARCHAR(100);
ALTER TABLE marketplace_project ADD COLUMN coolify_app_uuid VARCHAR(100);
ALTER TABLE marketplace_project ADD COLUMN coolify_environment_uuid VARCHAR(100);
ALTER TABLE marketplace_project ADD COLUMN server_id INTEGER REFERENCES marketplace_server(id);
ALTER TABLE marketplace_project ADD COLUMN is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE marketplace_project ADD COLUMN cloned_from_project_id INTEGER REFERENCES marketplace_project(id);
ALTER TABLE marketplace_project ADD COLUMN preview_protection_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE marketplace_project ADD COLUMN payment_method VARCHAR(30) DEFAULT 'invoice';
ALTER TABLE marketplace_project ADD COLUMN stripe_customer_id VARCHAR(100);
ALTER TABLE marketplace_project ADD COLUMN stripe_subscription_id VARCHAR(100);
ALTER TABLE marketplace_project ADD COLUMN billing_email VARCHAR(255);
ALTER TABLE marketplace_project ADD COLUMN bundle_id INTEGER REFERENCES marketplace_bundle(id);

-- Indizes
CREATE INDEX idx_project_provisioning_status ON marketplace_project(provisioning_status);
CREATE INDEX idx_project_coolify_app ON marketplace_project(coolify_app_uuid);
CREATE INDEX idx_project_server ON marketplace_project(server_id);
```

### 10.3 Alembic Migration Template

```python
"""Add provisioning and deployment fields to Project.

Revision ID: xxxx
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'xxxx'
down_revision = 'yyyy'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("""
        CREATE TYPE provisioningstatus AS ENUM (
            'draft', 'pending_payment', 'pending_domain', 
            'provisioning', 'bootstrapping', 'active', 
            'suspended', 'archived', 'error'
        )
    """)
    
    # ... rest of migration


def downgrade():
    # ... reverse operations
    op.execute("DROP TYPE provisioningstatus")
```

---

## 11. Beziehungsdiagramm

```
                    ┌─────────────┐
                    │ ProjectType │
                    └──────┬──────┘
                           │ 1:N
                           ▼
┌──────────┐        ┌─────────────┐        ┌────────────┐
│  Bundle  │◄───────│   Project   │───────▶│   Server   │
└──────────┘  N:1   └──────┬──────┘  N:1   └────────────┘
     │                     │
     │ N:M                 │ 1:N
     ▼                     ▼
┌──────────┐        ┌─────────────────┐
│PluginMeta│        │  ProjectDomain  │
└──────────┘        └────────┬────────┘
                             │ N:1
                             ▼
                    ┌─────────────────┐
                    │   BaseDomain    │
                    └─────────────────┘

┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   License   │     │ProvisioningLog │     │  PreviewAccess  │
└──────┬──────┘     └────────┬────────┘     └────────┬────────┘
       │ N:1                 │ N:1                   │ N:1
       └─────────────────────┼───────────────────────┘
                             ▼
                    ┌─────────────┐
                    │   Project   │
                    └─────────────┘
```
