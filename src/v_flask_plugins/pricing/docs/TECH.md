# Pricing Plugin - Technische Architektur

## Übersicht

Dieses Dokument beschreibt die technische Implementierung des Pricing-Plugins für V-Flask.

**Plugin-Name:** `pricing`  
**Python-Package:** `v_flask_pricing`  
**Tabellen-Prefix:** `pricing_`  

---

## Verzeichnisstruktur

```
v_flask_pricing/
├── __init__.py              # Plugin-Registrierung
├── plugin.py                # Plugin-Klasse mit Hooks
├── models/
│   ├── __init__.py
│   ├── rule.py              # PricingRule Model
│   ├── tier.py              # PricingTier Model (Staffelpreise)
│   └── settings.py          # PricingSettings Model
├── services/
│   ├── __init__.py
│   ├── price_service.py     # Hauptservice für Preisfindung
│   ├── rule_service.py      # Regelverwaltung
│   └── margin_service.py    # Margen-Berechnung
├── repositories/
│   ├── __init__.py
│   └── rule_repository.py   # Datenbankabfragen für Regeln
├── routes/
│   ├── __init__.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── rules.py         # /admin/pricing/rules
│   │   ├── tiers.py         # /admin/pricing/tiers
│   │   └── settings.py      # /admin/pricing/settings
│   └── api/
│       ├── __init__.py
│       └── prices.py        # API für Shop-Plugin
├── templates/
│   └── pricing/
│       └── admin/
│           ├── rules/
│           │   ├── list.html
│           │   ├── form.html
│           │   └── customer_search.html
│           ├── dashboard.html
│           └── settings.html
├── forms/
│   ├── __init__.py
│   ├── rule_form.py
│   └── tier_form.py
└── migrations/
    └── versions/
        └── 001_initial.py
```

---

## Datenmodell

### pricing_rule

```python
from sqlalchemy import Column, String, Enum, UUID, ForeignKey, Numeric, Date, Boolean, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import enum

class RuleType(enum.Enum):
    CUSTOMER_PRODUCT = 'customer_product'
    CUSTOMER_SERIES = 'customer_series'
    CUSTOMER_BRAND = 'customer_brand'
    CUSTOMER_MANUFACTURER = 'customer_manufacturer'
    CUSTOMER_PRODUCT_GROUP = 'customer_product_group'
    CUSTOMER_PRICE_TAG = 'customer_price_tag'
    GROUP_GLOBAL = 'group_global'

class TargetType(enum.Enum):
    PRODUCT = 'product'
    SERIES = 'series'
    BRAND = 'brand'
    MANUFACTURER = 'manufacturer'
    PRODUCT_GROUP = 'product_group'
    PRICE_TAG = 'price_tag'
    GLOBAL = 'global'

class PriceType(enum.Enum):
    FIXED = 'fixed'
    DISCOUNT_PERCENT = 'discount_percent'

class PricingRule(Base):
    __tablename__ = 'pricing_rule'
    
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    
    rule_type = Column(Enum(RuleType), nullable=False)
    
    # Geltungsbereich: Kunde ODER Gruppe
    customer_id = Column(UUID, ForeignKey('crm_customer.id'), nullable=True)
    customer_group_id = Column(UUID, ForeignKey('crm_customer_group.id'), nullable=True)
    
    # Ziel der Regel
    target_type = Column(Enum(TargetType), nullable=False)
    target_id = Column(UUID, nullable=True)  # NULL bei target_type = GLOBAL
    
    # Preiskonditionen
    price_type = Column(Enum(PriceType), nullable=False)
    price_value = Column(Numeric(10, 2), nullable=False)
    
    # Gültigkeit
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    
    # Steuerung
    priority = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    note = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tiers = relationship('PricingTier', back_populates='rule', cascade='all, delete-orphan')
    customer = relationship('Customer', foreign_keys=[customer_id])
    customer_group = relationship('CustomerGroup', foreign_keys=[customer_group_id])
```

### pricing_tier

```python
class PricingTier(Base):
    __tablename__ = 'pricing_tier'
    
    id = Column(UUID, primary_key=True, default=uuid4)
    rule_id = Column(UUID, ForeignKey('pricing_rule.id'), nullable=False)
    
    min_quantity = Column(Integer, nullable=False)
    price_value = Column(Numeric(10, 2), nullable=False)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    rule = relationship('PricingRule', back_populates='tiers')
    
    __table_args__ = (
        UniqueConstraint('rule_id', 'min_quantity', name='uq_tier_rule_quantity'),
    )
```

---

## Services

### PriceService (Hauptservice)

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from datetime import date
from uuid import UUID

@dataclass
class PriceResult:
    """Ergebnis der Preisfindung"""
    final_price: Decimal
    list_price: Decimal
    discount_percent: Decimal
    rule_applied: Optional[str]
    rule_id: Optional[UUID]
    is_discounted: bool
    margin_warning: bool
    margin_percent: Optional[Decimal]  # Aktuelle Marge

class PriceService:
    """
    Zentraler Service für Preisfindung.
    Wird vom Shop-Plugin verwendet.
    
    Abhängigkeiten:
    - PIM ProductService (für Produktdaten)
    - CRM CustomerService (für Kundendaten)
    - RuleRepository (für Preisregeln)
    - MarginService (für Margenprüfung)
    """
    
    def __init__(
        self,
        pim_product_service,
        crm_customer_service,
        rule_repository,
        margin_service,
        settings
    ):
        self.pim = pim_product_service
        self.crm = crm_customer_service
        self.rules = rule_repository
        self.margin = margin_service
        self.settings = settings
    
    def get_price(
        self, 
        product_id: UUID, 
        customer_id: UUID,
        quantity: int = 1,
        reference_date: date = None
    ) -> PriceResult:
        """
        Ermittelt den Preis für einen Artikel und Kunden.
        
        Args:
            product_id: ID des Produkts
            customer_id: ID des Kunden
            quantity: Bestellmenge (für Staffelpreise)
            reference_date: Datum für Gültigkeitsprüfung (Default: heute)
        
        Returns:
            PriceResult mit allen Preisdetails
        """
        if reference_date is None:
            reference_date = date.today()
        
        # Basisdaten laden
        product = self.pim.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        list_price = product.price_net
        
        customer = self.crm.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        customer_group = self.crm.get_group(customer_id)
        
        # Anwendbare Regel finden
        rule = self._find_best_rule(product, customer, customer_group, reference_date)
        
        # Kein Rabatt? Listenpreis zurückgeben
        if not rule:
            return PriceResult(
                final_price=list_price,
                list_price=list_price,
                discount_percent=Decimal('0'),
                rule_applied=None,
                rule_id=None,
                is_discounted=False,
                margin_warning=False,
                margin_percent=self.margin.calculate(product, list_price)
            )
        
        # Preis berechnen
        final_price = self._calculate_price_from_rule(rule, list_price, quantity)
        
        # Ersparnis berechnen
        if list_price > 0:
            discount_percent = ((list_price - final_price) / list_price * 100).quantize(Decimal('0.01'))
        else:
            discount_percent = Decimal('0')
        
        # Marge prüfen
        margin_result = self.margin.check(product, final_price)
        
        return PriceResult(
            final_price=final_price,
            list_price=list_price,
            discount_percent=discount_percent,
            rule_applied=rule.name,
            rule_id=rule.id,
            is_discounted=final_price < list_price,
            margin_warning=margin_result.is_below_minimum,
            margin_percent=margin_result.margin_percent
        )
    
    def get_prices_bulk(
        self,
        product_ids: list[UUID],
        customer_id: UUID,
        quantity: int = 1
    ) -> dict[UUID, PriceResult]:
        """
        Ermittelt Preise für mehrere Artikel (Performance-optimiert).
        Für Katalogansichten im Shop.
        """
        results = {}
        
        # Kunde einmal laden
        customer = self.crm.get_by_id(customer_id)
        customer_group = self.crm.get_group(customer_id)
        
        # Produkte laden
        products = self.pim.get_by_ids(product_ids)
        
        # Alle potentiell relevanten Regeln vorladen
        self.rules.preload_rules_for_customer(customer_id)
        if customer_group:
            self.rules.preload_rules_for_group(customer_group.id)
        
        for product in products:
            results[product.id] = self._get_price_internal(
                product, customer, customer_group, quantity
            )
        
        return results
    
    def _find_best_rule(self, product, customer, customer_group, reference_date) -> Optional[PricingRule]:
        """
        Findet die beste Preisregel nach Priorität.
        
        Reihenfolge (wird durch rule_type + priority bestimmt):
        1. customer_product (Prio 600+)
        2. customer_series (Prio 500+)
        3. customer_brand (Prio 400+)
        4. customer_manufacturer (Prio 300+)
        5. customer_product_group (Prio 200+)
        6. customer_price_tag (Prio 100+)
        7. group_global (Prio 0+)
        """
        rules = []
        
        # 1. Kundenspezifischer Artikelpreis
        r = self.rules.find_rule(
            customer_id=customer.id,
            target_type=TargetType.PRODUCT,
            target_id=product.id,
            date=reference_date
        )
        if r:
            rules.append((600 + r.priority, r))
        
        # 2. Kundenspezifischer Serienrabatt
        if product.series_id:
            r = self.rules.find_rule(
                customer_id=customer.id,
                target_type=TargetType.SERIES,
                target_id=product.series_id,
                date=reference_date
            )
            if r:
                rules.append((500 + r.priority, r))
        
        # 3. Kundenspezifischer Markenrabatt
        if product.brand_id:
            r = self.rules.find_rule(
                customer_id=customer.id,
                target_type=TargetType.BRAND,
                target_id=product.brand_id,
                date=reference_date
            )
            if r:
                rules.append((400 + r.priority, r))
        
        # 4. Kundenspezifischer Herstellerrabatt
        if product.manufacturer_id:
            r = self.rules.find_rule(
                customer_id=customer.id,
                target_type=TargetType.MANUFACTURER,
                target_id=product.manufacturer_id,
                date=reference_date
            )
            if r:
                rules.append((300 + r.priority, r))
        
        # 5. Kundenspezifischer Warengruppenrabatt
        if product.product_group_id:
            r = self.rules.find_rule(
                customer_id=customer.id,
                target_type=TargetType.PRODUCT_GROUP,
                target_id=product.product_group_id,
                date=reference_date
            )
            if r:
                rules.append((200 + r.priority, r))
        
        # 6. Kundenspezifischer Preis-Tag-Rabatt
        if product.price_tags:
            for tag in product.price_tags:
                r = self.rules.find_rule(
                    customer_id=customer.id,
                    target_type=TargetType.PRICE_TAG,
                    target_id=tag.id,
                    date=reference_date
                )
                if r:
                    rules.append((100 + r.priority, r))
        
        # 7. Kundengruppen-Rabatt
        if customer_group:
            r = self.rules.find_rule(
                customer_group_id=customer_group.id,
                target_type=TargetType.GLOBAL,
                target_id=None,
                date=reference_date
            )
            if r:
                rules.append((0 + r.priority, r))
        
        if not rules:
            return None
        
        # Nach kombinierter Priorität sortieren (höher = wichtiger)
        rules.sort(key=lambda x: x[0], reverse=True)
        return rules[0][1]
    
    def _calculate_price_from_rule(
        self, 
        rule: PricingRule, 
        list_price: Decimal, 
        quantity: int
    ) -> Decimal:
        """Berechnet den Endpreis aus Regel und ggf. Staffel"""
        
        # Passende Staffel finden
        tiers = sorted(rule.tiers, key=lambda t: t.min_quantity, reverse=True)
        applicable_value = rule.price_value
        
        for tier in tiers:
            if quantity >= tier.min_quantity:
                applicable_value = tier.price_value
                break
        
        # Preis berechnen
        if rule.price_type == PriceType.FIXED:
            return applicable_value
        else:  # DISCOUNT_PERCENT
            discount = list_price * (applicable_value / 100)
            return (list_price - discount).quantize(Decimal('0.01'))
```

### MarginService

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class MarginResult:
    margin_percent: Decimal
    is_below_minimum: bool
    minimum_margin: Decimal
    recommended_min_price: Decimal

class MarginService:
    """Service für Margenprüfung"""
    
    def __init__(self, settings):
        self.settings = settings
    
    def calculate(self, product, selling_price: Decimal) -> Decimal:
        """Berechnet die Marge in Prozent"""
        if not product.cost_price or product.cost_price == 0:
            return Decimal('100')  # Keine Kosten = 100% Marge
        
        if selling_price == 0:
            return Decimal('0')
        
        margin = ((selling_price - product.cost_price) / selling_price * 100)
        return margin.quantize(Decimal('0.01'))
    
    def check(self, product, selling_price: Decimal) -> MarginResult:
        """Prüft ob Mindestmarge eingehalten wird"""
        min_margin_enabled = self.settings.get('min_margin_enabled', True)
        min_margin_percent = Decimal(str(self.settings.get('min_margin_percent', 10)))
        
        margin = self.calculate(product, selling_price)
        
        # Empfohlener Mindestpreis berechnen
        if product.cost_price:
            # Formel: min_price = cost_price / (1 - min_margin/100)
            recommended_min = (product.cost_price / (1 - min_margin_percent / 100)).quantize(Decimal('0.01'))
        else:
            recommended_min = Decimal('0')
        
        return MarginResult(
            margin_percent=margin,
            is_below_minimum=min_margin_enabled and margin < min_margin_percent,
            minimum_margin=min_margin_percent,
            recommended_min_price=recommended_min
        )
```

### RuleService (Verwaltung)

```python
class RuleService:
    """Service für Regelverwaltung (Admin)"""
    
    def __init__(self, repository, pim_service, crm_service):
        self.repo = repository
        self.pim = pim_service
        self.crm = crm_service
    
    def create_rule(self, data: RuleCreate) -> PricingRule:
        """Neue Preisregel erstellen"""
        # Validierung
        self._validate_rule_data(data)
        
        # Erstellen
        rule = self.repo.create(data)
        
        # Staffelpreise erstellen falls vorhanden
        if data.tiers:
            for tier_data in data.tiers:
                self.repo.create_tier(rule.id, tier_data)
        
        return rule
    
    def update_rule(self, rule_id: UUID, data: RuleUpdate) -> PricingRule:
        """Preisregel aktualisieren"""
        self._validate_rule_data(data)
        return self.repo.update(rule_id, data)
    
    def delete_rule(self, rule_id: UUID) -> bool:
        """Preisregel löschen (inkl. Staffeln durch CASCADE)"""
        return self.repo.delete(rule_id)
    
    def get_rules_for_customer(self, customer_id: UUID) -> list[PricingRule]:
        """Alle Regeln für einen Kunden"""
        return self.repo.find_by_customer(customer_id)
    
    def get_rules_for_group(self, group_id: UUID) -> list[PricingRule]:
        """Alle Regeln für eine Kundengruppe"""
        return self.repo.find_by_group(group_id)
    
    def get_expiring_rules(self, days: int = 30) -> list[PricingRule]:
        """Regeln die in X Tagen ablaufen"""
        return self.repo.find_expiring(days)
    
    def get_rules_with_margin_warning(self) -> list[dict]:
        """Regeln mit Margen-Unterschreitung"""
        # Komplexe Abfrage: Alle Festpreis-Regeln prüfen
        pass
    
    def _validate_rule_data(self, data):
        """Validiert Regel-Daten"""
        # Entweder Kunde oder Gruppe muss gesetzt sein
        if not data.customer_id and not data.customer_group_id:
            raise ValueError("Either customer_id or customer_group_id required")
        
        # Nicht beides
        if data.customer_id and data.customer_group_id:
            raise ValueError("Cannot set both customer_id and customer_group_id")
        
        # Gruppe nur mit target_type = GLOBAL
        if data.customer_group_id and data.target_type != TargetType.GLOBAL:
            raise ValueError("Group rules must have target_type GLOBAL")
        
        # target_id bei GLOBAL nicht erlaubt
        if data.target_type == TargetType.GLOBAL and data.target_id:
            raise ValueError("GLOBAL rules cannot have target_id")
        
        # target_id bei anderen Typen erforderlich
        if data.target_type != TargetType.GLOBAL and not data.target_id:
            raise ValueError("Non-GLOBAL rules require target_id")
        
        # Gültigkeitszeitraum prüfen
        if data.valid_from and data.valid_to:
            if data.valid_from > data.valid_to:
                raise ValueError("valid_from must be before valid_to")
```

---

## Repository

### RuleRepository

```python
class RuleRepository:
    """Datenbankabfragen für Preisregeln"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def find_rule(
        self,
        customer_id: UUID = None,
        customer_group_id: UUID = None,
        target_type: TargetType = None,
        target_id: UUID = None,
        date: date = None
    ) -> Optional[PricingRule]:
        """
        Findet eine aktive Regel nach Kriterien.
        Prüft Gültigkeit automatisch.
        """
        query = self.db.query(PricingRule).filter(
            PricingRule.is_active == True
        )
        
        if customer_id:
            query = query.filter(PricingRule.customer_id == customer_id)
        
        if customer_group_id:
            query = query.filter(PricingRule.customer_group_id == customer_group_id)
        
        if target_type:
            query = query.filter(PricingRule.target_type == target_type)
        
        if target_id:
            query = query.filter(PricingRule.target_id == target_id)
        elif target_type == TargetType.GLOBAL:
            query = query.filter(PricingRule.target_id.is_(None))
        
        # Gültigkeitsprüfung
        if date:
            query = query.filter(
                or_(PricingRule.valid_from.is_(None), PricingRule.valid_from <= date)
            ).filter(
                or_(PricingRule.valid_to.is_(None), PricingRule.valid_to >= date)
            )
        
        return query.first()
    
    def preload_rules_for_customer(self, customer_id: UUID):
        """Lädt alle Regeln für einen Kunden in den Session-Cache"""
        # Optimierung für Bulk-Preisabfragen
        pass
    
    def find_expiring(self, days: int) -> list[PricingRule]:
        """Findet Regeln die in X Tagen ablaufen"""
        cutoff = date.today() + timedelta(days=days)
        return self.db.query(PricingRule).filter(
            PricingRule.is_active == True,
            PricingRule.valid_to.isnot(None),
            PricingRule.valid_to <= cutoff,
            PricingRule.valid_to >= date.today()
        ).all()
```

---

## API-Routen

### Für Shop-Plugin

| Methode | Route | Beschreibung |
|---------|-------|--------------|
| GET | `/api/pricing/price/<product_id>/<customer_id>` | Einzelpreis |
| POST | `/api/pricing/prices` | Bulk-Preise |

```python
# routes/api/prices.py

@api_bp.route('/price/<product_id>/<customer_id>')
def get_price(product_id, customer_id):
    """Einzelpreis für Produkt und Kunde"""
    quantity = request.args.get('quantity', 1, type=int)
    
    result = price_service.get_price(
        UUID(product_id),
        UUID(customer_id),
        quantity=quantity
    )
    
    return jsonify({
        'final_price': str(result.final_price),
        'list_price': str(result.list_price),
        'discount_percent': str(result.discount_percent),
        'is_discounted': result.is_discounted,
        'rule_applied': result.rule_applied
    })

@api_bp.route('/prices', methods=['POST'])
def get_prices_bulk():
    """Bulk-Preise für mehrere Produkte"""
    data = request.json
    product_ids = [UUID(pid) for pid in data['product_ids']]
    customer_id = UUID(data['customer_id'])
    quantity = data.get('quantity', 1)
    
    results = price_service.get_prices_bulk(product_ids, customer_id, quantity)
    
    return jsonify({
        str(pid): {
            'final_price': str(r.final_price),
            'list_price': str(r.list_price),
            'discount_percent': str(r.discount_percent),
            'is_discounted': r.is_discounted
        }
        for pid, r in results.items()
    })
```

---

## Plugin-Registrierung

```python
# plugin.py

class PricingPlugin:
    name = 'pricing'
    version = '1.0.0'
    
    dependencies = ['pim', 'crm']  # Beide erforderlich
    
    provides_services = [
        'PriceService',
        'RuleService',
        'MarginService'
    ]
    
    def init_app(self, app):
        """Plugin initialisieren"""
        # Services registrieren
        pim_service = app.get_service('pim.ProductService')
        crm_service = app.get_service('crm.CustomerService')
        
        # Eigene Services erstellen
        self.rule_repo = RuleRepository(app.db.session)
        self.margin_service = MarginService(self.get_settings())
        self.price_service = PriceService(
            pim_service,
            crm_service,
            self.rule_repo,
            self.margin_service,
            self.get_settings()
        )
        self.rule_service = RuleService(
            self.rule_repo,
            pim_service,
            crm_service
        )
        
        # Services registrieren
        app.register_service('pricing.PriceService', self.price_service)
        app.register_service('pricing.RuleService', self.rule_service)
        app.register_service('pricing.MarginService', self.margin_service)
        
        # Routen registrieren
        from .routes.admin import admin_bp
        from .routes.api import api_bp
        app.register_blueprint(admin_bp, url_prefix='/admin/pricing')
        app.register_blueprint(api_bp, url_prefix='/api/pricing')
```

---

## Hinweise für AI-Code-Agenten

### Toast-Messages bei Margen-Warnung

Bei der Implementierung der Admin-Oberfläche (Preisregel-Formular) soll bei Margen-Unterschreitung eine Toast-Message angezeigt werden.

**Suchstrategie:**
1. Im V-Flask Framework nach Toast-Service suchen:
   - `v_flask/services/toast_service.py`
   - `v_flask/utils/flash_messages.py`
   - In bestehenden Plugins nach `toast` oder `flash` suchen

2. Falls vorhanden: Service verwenden
3. Falls nicht vorhanden: Einfachen Toast-Service implementieren (kann von mehreren Plugins genutzt werden)

### Kaskadierende Dropdowns

Im Preisregel-Formular müssen die Dropdowns kaskadierend sein:
- Bei Auswahl von "Marke" → Dropdown zeigt nur Marken des ausgewählten Herstellers
- Bei Auswahl von "Serie" → Dropdown zeigt nur Serien der ausgewählten Marke

Dies erfordert JavaScript für dynamisches Nachladen oder Alpine.js falls im Projekt verwendet.

### Performance-Optimierung

Bei Bulk-Preisabfragen (Katalogansicht) sollte:
1. Alle Produkte in einem Query laden
2. Alle potentiell relevanten Regeln vorladen
3. In-Memory Preisberechnung durchführen

Nicht: Für jedes Produkt einzelne DB-Abfragen machen.
