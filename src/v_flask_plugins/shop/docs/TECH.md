# Shop Plugin - Technische Dokumentation

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                         SHOP PLUGIN                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Routes     │  │   Services   │  │      Models          │  │
│  │              │  │              │  │                      │  │
│  │ public_bp    │  │ CartService  │  │ shop_customer_product│  │
│  │ admin_bp     │  │ OrderService │  │ shop_customer_price  │  │
│  │ api_bp       │  │ PriceService │  │ shop_cart            │  │
│  │              │  │ SearchService│  │ shop_cart_item       │  │
│  └──────────────┘  └──────────────┘  │ shop_order           │  │
│         │                 │          │ shop_order_item      │  │
│         │                 │          │ shop_order_history   │  │
│         ▼                 ▼          │ shop_settings        │  │
│  ┌─────────────────────────────┐    └──────────────────────┘  │
│  │       Templates             │              │                │
│  │                             │              │                │
│  │ shop/public/               │              │                │
│  │   home.html                │              │                │
│  │   catalog/                 │              │                │
│  │   cart.html                │              │                │
│  │   checkout.html            │              │                │
│  │   orders/                  │              │                │
│  │                             │              │                │
│  │ shop/admin/                │              │                │
│  │   dashboard.html           │              │                │
│  │   orders/                  │              │                │
│  │   pricing/                 │              │                │
│  │   curation/                │              │                │
│  └─────────────────────────────┘              │                │
│                                               │                │
└───────────────────────────────────────────────┼────────────────┘
                                                │
                    ┌───────────────────────────┼───────────────┐
                    │                           │               │
                    ▼                           ▼               ▼
            ┌─────────────┐            ┌─────────────┐  ┌─────────────┐
            │ PIM Plugin  │            │ CRM Plugin  │  │ Fragebogen  │
            │             │            │             │  │ (optional)  │
            │ - Product   │            │ - Kunde     │  │             │
            │ - Category  │            │ - Adresse   │  │ - Formular  │
            │ - Image     │            │ - Kontakt   │  │ - Antworten │
            └─────────────┘            └─────────────┘  └─────────────┘
```

## Komponenten

### Models

| Model | Tabelle | Beschreibung |
|-------|---------|--------------|
| CustomerProduct | `shop_customer_product` | Kuratierte + Favoriten-Produkte pro Kunde |
| CustomerPrice | `shop_customer_price` | Kundenspezifische Preise |
| Cart | `shop_cart` | Warenkorb-Header pro Kunde |
| CartItem | `shop_cart_item` | Warenkorb-Positionen |
| Order | `shop_order` | Bestellungen |
| OrderItem | `shop_order_item` | Bestellpositionen (mit Snapshot) |
| OrderStatusHistory | `shop_order_status_history` | Status-Änderungen |
| ShopSettings | `shop_settings` | Key-Value Plugin-Einstellungen |

### Model-Details

```python
# shop_customer_product
class CustomerProduct(db.Model):
    __tablename__ = 'shop_customer_product'
    
    id = Column(Integer, primary_key=True)
    kunde_id = Column(Integer, ForeignKey('crm_kunde.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('pim_product.id'), nullable=False)
    added_by = Column(String(20))  # 'admin' oder 'customer'
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint: Ein Produkt pro Kunde nur einmal
    __table_args__ = (UniqueConstraint('kunde_id', 'product_id'),)


# shop_customer_price
class CustomerPrice(db.Model):
    __tablename__ = 'shop_customer_price'
    
    id = Column(Integer, primary_key=True)
    kunde_id = Column(Integer, ForeignKey('crm_kunde.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('pim_product.id'), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# shop_order
class Order(db.Model):
    __tablename__ = 'shop_order'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    kunde_id = Column(Integer, ForeignKey('crm_kunde.id'), nullable=False)
    status = Column(String(20), default='new')  # new, confirmed, processing, shipped, completed, cancelled
    
    # Snapshot der Lieferadresse (JSON)
    shipping_address = Column(JSON)
    
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# shop_order_item (mit Snapshot für Historisierung)
class OrderItem(db.Model):
    __tablename__ = 'shop_order_item'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('shop_order.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('pim_product.id'), nullable=True)  # Nullable für gelöschte Produkte
    
    # Snapshots zum Bestellzeitpunkt
    sku = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
```

### Routes

#### Public Routes (Frontend)

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/shop/` | GET | Kunde | Startseite mit "Meine Produkte" |
| `/shop/login` | GET/POST | - | Login-Formular |
| `/shop/logout` | GET | Kunde | Logout |
| `/shop/kategorie/<slug>` | GET | Kunde | Kategorie mit Produkten |
| `/shop/produkt/<slug>` | GET | Kunde | Produktdetail |
| `/shop/suche` | GET | Kunde | Suchseite |
| `/shop/warenkorb` | GET | Kunde | Warenkorb anzeigen |
| `/shop/warenkorb/add` | POST | Kunde | Produkt hinzufügen |
| `/shop/warenkorb/update` | POST | Kunde | Menge ändern |
| `/shop/warenkorb/remove` | POST | Kunde | Position entfernen |
| `/shop/checkout` | GET/POST | Kunde | Bestellung aufgeben |
| `/shop/bestellungen` | GET | Kunde | Bestellhistorie |
| `/shop/bestellung/<nr>` | GET | Kunde | Bestelldetail |
| `/shop/meine-produkte/add` | POST | Kunde | Produkt zu Favoriten |
| `/shop/meine-produkte/remove` | POST | Kunde | Produkt aus Favoriten |
| `/shop/schnellbestellung` | GET/POST | Kunde | SKU + Menge Eingabe |

#### Admin Routes (Backend)

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/admin/shop/` | GET | Admin | Dashboard |
| `/admin/shop/bestellungen` | GET | Admin | Bestellübersicht |
| `/admin/shop/bestellung/<id>` | GET | Admin | Bestelldetail |
| `/admin/shop/bestellung/<id>/status` | POST | Admin | Status ändern |
| `/admin/shop/preise` | GET | Admin | Kundenpreise Übersicht |
| `/admin/shop/preise/kunde/<id>` | GET | Admin | Preise für Kunde |
| `/admin/shop/preise/edit` | POST | Admin | Preis speichern |
| `/admin/shop/kuratierung` | GET | Admin | Kuratierung Übersicht |
| `/admin/shop/kuratierung/kunde/<id>` | GET | Admin | Produkte für Kunde |
| `/admin/shop/kuratierung/add` | POST | Admin | Produkt zuweisen |
| `/admin/shop/kuratierung/remove` | POST | Admin | Zuweisung entfernen |
| `/admin/shop/einstellungen` | GET/POST | Admin | Shop-Einstellungen |

### Templates

| Template | Zweck |
|----------|-------|
| `shop/public/home.html` | Startseite mit "Meine Produkte" |
| `shop/public/login.html` | Login-Formular |
| `shop/public/catalog/category.html` | Kategorieansicht |
| `shop/public/catalog/product.html` | Produktdetail |
| `shop/public/catalog/search.html` | Suchergebnisse |
| `shop/public/cart.html` | Warenkorb |
| `shop/public/checkout.html` | Checkout |
| `shop/public/orders/list.html` | Bestellhistorie |
| `shop/public/orders/detail.html` | Bestelldetail |
| `shop/admin/dashboard.html` | Admin-Dashboard |
| `shop/admin/orders/list.html` | Bestellübersicht |
| `shop/admin/orders/detail.html` | Bestelldetail |
| `shop/admin/pricing/list.html` | Kundenpreise |
| `shop/admin/pricing/customer.html` | Preise pro Kunde |
| `shop/admin/curation/list.html` | Kuratierung Übersicht |
| `shop/admin/curation/customer.html` | Produkte pro Kunde |
| `shop/admin/settings.html` | Einstellungen |

## UI-Slots

| Slot | Konfiguration |
|------|---------------|
| `admin_menu` | `{name: 'Shop', icon: 'shopping-cart', url: '/admin/shop/', children: [...]}` |
| `admin_dashboard_widgets` | Neue Bestellungen, Umsatz heute/Monat |

## Services

### PriceService

```python
class PriceService:
    def get_price_for_customer(self, product_id: int, kunde_id: int) -> Decimal:
        """
        Ermittelt den Preis für einen Kunden.
        1. Prüft kundenspezifischen Preis (mit Gültigkeitszeitraum)
        2. Fallback auf Listenpreis aus PIM
        """
        
    def get_customer_prices(self, kunde_id: int) -> list[CustomerPrice]:
        """Alle kundenspez. Preise für einen Kunden."""
        
    def set_customer_price(self, kunde_id: int, product_id: int, price: Decimal, 
                           valid_from: date = None, valid_until: date = None):
        """Kundenspez. Preis setzen/aktualisieren."""
```

### CartService

```python
class CartService:
    def get_or_create_cart(self, kunde_id: int) -> Cart:
        """Warenkorb für Kunde holen oder erstellen."""
        
    def add_item(self, cart: Cart, product_id: int, quantity: int):
        """Produkt hinzufügen (oder Menge erhöhen)."""
        
    def update_quantity(self, cart: Cart, item_id: int, quantity: int):
        """Menge ändern (0 = entfernen)."""
        
    def get_cart_total(self, cart: Cart, kunde_id: int) -> dict:
        """Berechnet Summen mit kundenspez. Preisen."""
```

### OrderService

```python
class OrderService:
    def create_order(self, cart: Cart, kunde_id: int, shipping_address: dict, 
                     notes: str = None) -> Order:
        """
        Erstellt Bestellung aus Warenkorb.
        - Generiert Bestellnummer
        - Erstellt Snapshots der Produkte und Preise
        - Leert Warenkorb
        """
        
    def change_status(self, order: Order, new_status: str, 
                      changed_by: str, comment: str = None):
        """Status ändern mit History-Eintrag."""
        
    def generate_order_number(self) -> str:
        """Generiert eindeutige Bestellnummer (z.B. 'ORD-2025-00001')."""
```

## Abhängigkeiten

### Von PIM Plugin benötigt

```python
# Models
from pim.models import Product, Category, ProductImage

# Services (falls vorhanden)
from pim.services import ProductService, CategoryService
```

### Von CRM Plugin benötigt

```python
# Models
from crm.models import Kunde, Adresse

# Auth-Integration
# Kunde muss sich einloggen können - wie ist Auth im CRM gelöst?
```

### Von Fragebogen Plugin (optional)

```python
# Für Selbstregistrierung
from fragebogen.models import Fragebogen, Antwort
from fragebogen.services import FragebogenService
```

## Technische Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Snapshots in OrderItem | Bestellhistorie bleibt korrekt auch wenn Produkte geändert/gelöscht werden |
| JSON für shipping_address | Flexibel, Adresse kann sich nach Bestellung ändern |
| Separate CustomerProduct Tabelle | Ermöglicht `added_by` Unterscheidung (admin vs customer) |
| Status als String statt Enum | Einfacher erweiterbar, DB-Migration-freundlicher |
| Warenkorb in DB statt Session | Persistent über Sessions, später auch API-fähig |

## Offene Punkte / Klärungsbedarf

1. **Auth-Integration:** Wie loggt sich ein CRM-Kunde ein? Hat CRM bereits Auth?
2. **PIM-Interface:** Welche Methoden stellt PIM bereit? Gibt es Services?
3. **E-Mail-Versand:** Bestellbestätigung, Status-Updates - gibt es ein Mail-Plugin?
4. **Bestellnummer-Format:** Konfigurierbar oder fest?
5. **Mehrwertsteuer:** Pro Produkt oder global? Netto/Brutto-Eingabe?
