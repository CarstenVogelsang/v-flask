# Pricing Plugin - Spezifikation

## Übersicht

Das Pricing-Plugin ist ein **Bridge-Plugin**, das PIM (Produkte) und CRM (Kunden) verbindet, um kundenspezifische Preise zu berechnen. Es verwaltet Preisregeln, Staffelpreise, Rabatte und zeitlich begrenzte Konditionen.

**Plugin-Name:** `pricing`  
**Tabellen-Prefix:** `pricing_`  
**URL-Prefix Admin:** `/admin/pricing/`  
**Abhängigkeiten:** `pim` (required), `crm` (required)

---

## Kernprinzipien

1. **Bridge-Funktion:** Verbindet PIM-Produkte mit CRM-Kunden für Preisfindung
2. **Regelbasiert:** Flexible Preisregeln auf verschiedenen Ebenen
3. **Priorisiert:** Klare Hierarchie welche Regel "gewinnt"
4. **Zeitgesteuert:** Preise können zeitlich begrenzt sein
5. **Transparent:** Streichpreis-Anzeige mit Ersparnis

---

## Preisfindungs-Hierarchie

Die Preisfindung prüft von **spezifisch zu allgemein** - der erste Treffer gewinnt:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PREISFINDUNGS-HIERARCHIE                     │
│                (Erste Treffer-Regel gewinnt)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. KUNDENSPEZIFISCHER ARTIKELPREIS                            │
│     → Kunde X, Artikel Y = 15,00 € (Festpreis)                 │
│     → Höchste Priorität, überschreibt alles                    │
│                                                                 │
│  2. KUNDENSPEZIFISCHER SERIENRABATT                            │
│     → Kunde X, Serie "ProLine" = 12% Rabatt auf Listenpreis    │
│                                                                 │
│  3. KUNDENSPEZIFISCHER MARKENRABATT                            │
│     → Kunde X, Marke "Bosch" = 10% Rabatt auf Listenpreis      │
│                                                                 │
│  4. KUNDENSPEZIFISCHER HERSTELLERRABATT                        │
│     → Kunde X, Hersteller "Bosch GmbH" = 8% Rabatt             │
│                                                                 │
│  5. KUNDENSPEZIFISCHER WARENGRUPPENRABATT                      │
│     → Kunde X, Warengruppe "Profi-Tools" = 7% Rabatt           │
│                                                                 │
│  6. KUNDENSPEZIFISCHER PREIS-TAG-RABATT                        │
│     → Kunde X, Tag "Auslaufmodell" = 15% Rabatt                │
│                                                                 │
│  7. KUNDENGRUPPEN-RABATT (auf Gesamtsortiment)                 │
│     → Kunde in Gruppe "Gold" = 5% auf alles                    │
│                                                                 │
│  8. LISTENPREIS (aus PIM)                                      │
│     → Standard-VK-Preis, keine Rabatte                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

+ STAFFELPREISE können auf jeder Ebene (1-7) definiert werden
+ ZEITLICHE BEGRENZUNG kann auf jeder Ebene (1-7) definiert werden
```

---

## Datenmodell

### Entity-Relationship-Diagramm

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PIM Plugin    │     │  Pricing Plugin │     │   CRM Plugin    │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│                 │     │                 │     │                 │
│ pim_product     │◄────┤ pricing_rule    │────►│ crm_customer    │
│ pim_brand       │◄────┤                 │────►│ crm_customer_   │
│ pim_series      │◄────┤ pricing_tier    │     │ group           │
│ pim_manufacturer│◄────┤ (Staffelpreise) │     │                 │
│ pim_product_    │◄────┤                 │     │                 │
│ group           │     │                 │     │                 │
│ pim_price_tag   │◄────┤                 │     │                 │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### pricing_rule (Preisregeln)

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| name | VARCHAR(255) | NOT NULL | Bezeichnung der Regel |
| rule_type | ENUM | NOT NULL | Typ der Regel (siehe unten) |
| customer_id | UUID | FK → crm_customer | Spezifischer Kunde (NULL = Gruppe) |
| customer_group_id | UUID | FK → crm_customer_group | Kundengruppe (NULL = spez. Kunde) |
| target_type | ENUM | NOT NULL | Worauf bezieht sich die Regel |
| target_id | UUID | NULL | ID des Ziels (Artikel, Marke, etc.) |
| price_type | ENUM | NOT NULL | Festpreis oder Rabatt |
| price_value | DECIMAL(10,2) | NOT NULL | Festpreis in € oder Rabatt in % |
| valid_from | DATE | NULL | Gültig ab (NULL = sofort) |
| valid_to | DATE | NULL | Gültig bis (NULL = unbegrenzt) |
| priority | INT | NOT NULL | Manuelle Priorität (höher = wichtiger) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv |
| note | TEXT | NULL | Interne Notiz |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**ENUM rule_type:**
- `customer_product` - Kundenspezifischer Artikelpreis
- `customer_series` - Kundenspezifischer Serienrabatt
- `customer_brand` - Kundenspezifischer Markenrabatt
- `customer_manufacturer` - Kundenspezifischer Herstellerrabatt
- `customer_product_group` - Kundenspezifischer Warengruppenrabatt
- `customer_price_tag` - Kundenspezifischer Preis-Tag-Rabatt
- `group_global` - Kundengruppen-Rabatt auf Gesamtsortiment

**ENUM target_type:**
- `product` - Einzelner Artikel
- `series` - Produktserie
- `brand` - Marke
- `manufacturer` - Hersteller
- `product_group` - Warengruppe
- `price_tag` - Preis-Tag
- `global` - Gesamtsortiment

**ENUM price_type:**
- `fixed` - Festpreis in €
- `discount_percent` - Rabatt in %

**Indizes:**
- `idx_pricing_rule_customer` auf `customer_id`
- `idx_pricing_rule_group` auf `customer_group_id`
- `idx_pricing_rule_target` auf `target_type, target_id`
- `idx_pricing_rule_validity` auf `valid_from, valid_to`

### pricing_tier (Staffelpreise)

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| rule_id | UUID | FK → pricing_rule | Zugehörige Preisregel |
| min_quantity | INT | NOT NULL | Ab Menge |
| price_value | DECIMAL(10,2) | NOT NULL | Preis/Rabatt für diese Staffel |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |

**Unique Constraint:** `(rule_id, min_quantity)` - Pro Regel nur eine Staffel pro Menge

**Beispiel:**
```
Regel: Kunde X, Artikel Y, Festpreis
├── Staffel 1: ab 1 Stück = 10,00 €
├── Staffel 2: ab 10 Stück = 9,00 €
└── Staffel 3: ab 50 Stück = 8,00 €
```

### pricing_settings (Einstellungen)

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| key | VARCHAR(100) | UNIQUE, NOT NULL | Einstellungsschlüssel |
| value | TEXT | NOT NULL | Wert (JSON-encoded) |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Standard-Einstellungen:**
- `min_margin_enabled` = `true` - Mindestmarge aktiv
- `min_margin_percent` = `10` - Mindestmarge in %
- `show_strikethrough_price` = `true` - Streichpreis anzeigen
- `show_savings_percent` = `true` - Ersparnis in % anzeigen

---

## Preisfindungs-Algorithmus

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from datetime import date

@dataclass
class PriceResult:
    """Ergebnis der Preisfindung"""
    final_price: Decimal          # Endpreis für den Kunden
    list_price: Decimal           # Listenpreis aus PIM
    discount_percent: Decimal     # Ersparnis in %
    rule_applied: Optional[str]   # Name der angewandten Regel
    rule_id: Optional[str]        # ID der angewandten Regel
    is_discounted: bool           # Wurde rabattiert?
    margin_warning: bool          # Unter Mindestmarge?

class PriceService:
    """
    Zentraler Service für Preisfindung.
    Wird vom Shop-Plugin verwendet.
    """
    
    def __init__(self, pim_service, crm_service, rule_repository, settings):
        self.pim = pim_service
        self.crm = crm_service
        self.rules = rule_repository
        self.settings = settings
    
    def get_price(
        self, 
        product_id: str, 
        customer_id: str,
        quantity: int = 1,
        date: date = None
    ) -> PriceResult:
        """
        Ermittelt den Preis für einen Artikel und Kunden.
        
        Ablauf:
        1. Listenpreis aus PIM holen
        2. Kunde und Kundengruppe aus CRM holen
        3. Produktdetails aus PIM holen (Marke, Serie, etc.)
        4. Anwendbare Regeln finden (nach Priorität sortiert)
        5. Erste passende Regel anwenden
        6. Staffelpreis prüfen falls vorhanden
        7. Mindestmarge prüfen
        8. PriceResult zurückgeben
        """
        if date is None:
            date = date.today()
        
        # 1. Basisdaten holen
        product = self.pim.get_product(product_id)
        list_price = product.price_net
        customer = self.crm.get_customer(customer_id)
        customer_group = self.crm.get_customer_group(customer_id)
        
        # 2. Anwendbare Regeln suchen (priorisiert)
        rules = self._find_applicable_rules(
            product=product,
            customer=customer,
            customer_group=customer_group,
            date=date
        )
        
        # 3. Erste passende Regel anwenden
        if not rules:
            return PriceResult(
                final_price=list_price,
                list_price=list_price,
                discount_percent=Decimal('0'),
                rule_applied=None,
                rule_id=None,
                is_discounted=False,
                margin_warning=False
            )
        
        rule = rules[0]  # Höchste Priorität
        
        # 4. Preis/Rabatt berechnen (mit Staffel)
        final_price = self._calculate_price(rule, list_price, quantity)
        
        # 5. Ersparnis berechnen
        discount_percent = ((list_price - final_price) / list_price * 100).quantize(Decimal('0.01'))
        
        # 6. Mindestmarge prüfen
        margin_warning = self._check_margin(product, final_price)
        
        return PriceResult(
            final_price=final_price,
            list_price=list_price,
            discount_percent=discount_percent,
            rule_applied=rule.name,
            rule_id=str(rule.id),
            is_discounted=final_price < list_price,
            margin_warning=margin_warning
        )
    
    def _find_applicable_rules(self, product, customer, customer_group, date):
        """
        Findet alle anwendbaren Regeln, sortiert nach Priorität.
        
        Reihenfolge (höhere Priorität zuerst):
        1. Kundenspezifischer Artikelpreis
        2. Kundenspezifischer Serienrabatt
        3. Kundenspezifischer Markenrabatt
        4. Kundenspezifischer Herstellerrabatt
        5. Kundenspezifischer Warengruppenrabatt
        6. Kundenspezifischer Preis-Tag-Rabatt
        7. Kundengruppen-Rabatt
        """
        rules = []
        
        # 1. Kundenspezifischer Artikelpreis
        rule = self.rules.find_customer_product_rule(customer.id, product.id, date)
        if rule:
            rules.append(rule)
        
        # 2. Kundenspezifischer Serienrabatt
        if product.series_id:
            rule = self.rules.find_customer_series_rule(customer.id, product.series_id, date)
            if rule:
                rules.append(rule)
        
        # 3. Kundenspezifischer Markenrabatt
        if product.brand_id:
            rule = self.rules.find_customer_brand_rule(customer.id, product.brand_id, date)
            if rule:
                rules.append(rule)
        
        # 4. Kundenspezifischer Herstellerrabatt
        if product.manufacturer_id:
            rule = self.rules.find_customer_manufacturer_rule(customer.id, product.manufacturer_id, date)
            if rule:
                rules.append(rule)
        
        # 5. Kundenspezifischer Warengruppenrabatt
        if product.product_group_id:
            rule = self.rules.find_customer_product_group_rule(customer.id, product.product_group_id, date)
            if rule:
                rules.append(rule)
        
        # 6. Kundenspezifischer Preis-Tag-Rabatt
        for tag in product.price_tags:
            rule = self.rules.find_customer_price_tag_rule(customer.id, tag.id, date)
            if rule:
                rules.append(rule)
        
        # 7. Kundengruppen-Rabatt
        if customer_group:
            rule = self.rules.find_group_global_rule(customer_group.id, date)
            if rule:
                rules.append(rule)
        
        # Nach Priorität sortieren (höher = wichtiger)
        rules.sort(key=lambda r: r.priority, reverse=True)
        
        return rules
    
    def _calculate_price(self, rule, list_price: Decimal, quantity: int) -> Decimal:
        """Berechnet den Preis basierend auf Regel und Staffel"""
        
        # Staffelpreis suchen
        tiers = self.rules.get_tiers(rule.id)
        applicable_tier = None
        for tier in sorted(tiers, key=lambda t: t.min_quantity, reverse=True):
            if quantity >= tier.min_quantity:
                applicable_tier = tier
                break
        
        # Wert aus Staffel oder Regel
        value = applicable_tier.price_value if applicable_tier else rule.price_value
        
        # Festpreis oder Rabatt anwenden
        if rule.price_type == 'fixed':
            return value
        else:  # discount_percent
            discount = list_price * (value / 100)
            return (list_price - discount).quantize(Decimal('0.01'))
    
    def _check_margin(self, product, final_price: Decimal) -> bool:
        """Prüft ob Mindestmarge unterschritten wird"""
        if not self.settings.get('min_margin_enabled', True):
            return False
        
        if not product.cost_price or product.cost_price == 0:
            return False
        
        min_margin = Decimal(str(self.settings.get('min_margin_percent', 10)))
        actual_margin = ((final_price - product.cost_price) / final_price * 100)
        
        return actual_margin < min_margin
```

---

## Admin-Oberfläche

### Navigationsstruktur

```
Pricing (Hauptmenü)
├── Übersicht (Dashboard)
│   ├── Aktive Regeln
│   ├── Regeln mit Margen-Warnung
│   └── Ablaufende Regeln (nächste 30 Tage)
├── Kundenpreise
│   ├── Nach Kunde suchen
│   └── Neue Regel für Kunde
├── Gruppenrabatte
│   ├── Übersicht
│   └── Neuer Gruppenrabatt
├── Staffelpreise
│   └── Übersicht aller Staffeln
└── Einstellungen
    ├── Mindestmarge
    └── Anzeige-Optionen
```

### Preisregel-Formular

```
┌─────────────────────────────────────────────────────────────────┐
│ Neue Preisregel erstellen                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Bezeichnung: [Sonderpreis Bosch für Müller GmbH___________]    │
│                                                                 │
│ ┌─ Geltungsbereich ──────────────────────────────────────────┐ │
│ │                                                             │ │
│ │ Gilt für:  ○ Spezifischen Kunden  ○ Kundengruppe           │ │
│ │                                                             │ │
│ │ Kunde: [Müller GmbH (K-2025-00042)_______________] [Suche] │ │
│ │                                                             │ │
│ │ Bezogen auf:  ○ Artikel  ○ Serie  ○ Marke  ○ Hersteller   │ │
│ │               ○ Warengruppe  ○ Preis-Tag  ○ Alles          │ │
│ │                                                             │ │
│ │ Marke: [Bosch Professional_______________________] [Suche] │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ Preiskonditionen ─────────────────────────────────────────┐ │
│ │                                                             │ │
│ │ Preistyp:  ○ Festpreis (€)  ● Rabatt (%)                   │ │
│ │                                                             │ │
│ │ Rabatt: [12,00] %                                          │ │
│ │                                                             │ │
│ │ ☑ Staffelpreise aktivieren                                 │ │
│ │   ┌──────────────────────────────────────────────────┐     │ │
│ │   │ Ab Menge │ Rabatt % │                      [+]   │     │ │
│ │   ├──────────┼──────────┤                            │     │ │
│ │   │ 1        │ 12,00    │                      [-]   │     │ │
│ │   │ 10       │ 15,00    │                      [-]   │     │ │
│ │   │ 50       │ 18,00    │                      [-]   │     │ │
│ │   └──────────────────────────────────────────────────┘     │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ Gültigkeit ───────────────────────────────────────────────┐ │
│ │                                                             │ │
│ │ Von: [01.01.2025] bis: [31.12.2025]  ☐ Unbegrenzt          │ │
│ │                                                             │ │
│ │ ☑ Aktiv                                                    │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Notiz: [Vereinbarung lt. Rahmenvertrag vom 01.01.2025_______]  │
│                                                                 │
│                              [Abbrechen]  [Speichern]           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Margen-Warnung bei Preiseingabe

Bei der Eingabe von Festpreisen oder hohen Rabatten soll eine Warnung erscheinen, wenn die Mindestmarge unterschritten wird:

```
┌─────────────────────────────────────────────────────────────────┐
│ Preistyp:  ● Festpreis (€)  ○ Rabatt (%)                       │
│                                                                 │
│ Festpreis: [8,50] €                                            │
│            ─────                                                │
│            ⚠️ (rot markiertes Feld)                            │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ⚠️ Margen-Warnung                                           ││
│ │                                                              ││
│ │ Der eingegebene Preis von 8,50 € liegt unter der           ││
│ │ konfigurierten Mindestmarge von 10%.                        ││
│ │                                                              ││
│ │ Listenpreis: 12,00 €                                        ││
│ │ Einkaufspreis: 8,00 €                                       ││
│ │ Aktuelle Marge: 5,9%                                        ││
│ │ Mindestmarge: 10%                                           ││
│ │                                                              ││
│ │ Empfohlener Mindestpreis: 8,89 €                            ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Hinweis für AI-Code-Agenten:** Für die Toast-Meldung bei Margen-Unterschreitung soll im V-Flask Framework nach einem bestehenden Toast-Message-Service gesucht werden. Falls nicht vorhanden, muss ein einfacher Toast-Service implementiert werden.

---

## Shop-Integration (Preisanzeige)

Das Shop-Plugin zeigt Preise mit Streichpreis und Ersparnis an:

```html
<!-- Produktkarte im Shop -->
<div class="product-price">
    {% if price_result.is_discounted %}
        <span class="list-price strikethrough">{{ price_result.list_price|currency }}</span>
        <span class="final-price highlight">{{ price_result.final_price|currency }}</span>
        <span class="savings">Sie sparen {{ price_result.discount_percent }}%</span>
    {% else %}
        <span class="final-price">{{ price_result.final_price|currency }}</span>
    {% endif %}
</div>
```

**Darstellung:**
```
┌────────────────────────────────┐
│  Bosch GSR 18V-60 FC          │
│                                │
│  UVP: 299,00 €  (durchgestr.) │
│  Ihr Preis: 263,12 €          │
│  Sie sparen 12%               │
│                                │
│  [In den Warenkorb]           │
└────────────────────────────────┘
```

---

## API für Shop-Plugin

```python
# Shop verwendet den PriceService

class ShopCatalogService:
    def __init__(self, price_service: PriceService):
        self.pricing = price_service
    
    def get_product_for_customer(self, product_id: str, customer_id: str) -> ProductWithPrice:
        """Produkt mit kundenspezifischem Preis laden"""
        product = self.pim.get_product(product_id)
        price = self.pricing.get_price(product_id, customer_id)
        
        return ProductWithPrice(
            product=product,
            price=price
        )
    
    def get_catalog_for_customer(
        self, 
        customer_id: str, 
        category_id: str = None
    ) -> list[ProductWithPrice]:
        """Produktliste mit kundenspezifischen Preisen"""
        products = self.pim.get_products(category_id=category_id)
        
        return [
            ProductWithPrice(
                product=p,
                price=self.pricing.get_price(p.id, customer_id)
            )
            for p in products
        ]
```

---

## Plugin-Einstellungen

| Einstellung | Typ | Default | Beschreibung |
|-------------|-----|---------|--------------|
| `min_margin_enabled` | bool | `true` | Mindestmarge aktiv |
| `min_margin_percent` | decimal | `10.0` | Mindestmarge in % |
| `show_strikethrough_price` | bool | `true` | Streichpreis im Shop anzeigen |
| `show_savings_percent` | bool | `true` | "Sie sparen X%" anzeigen |
| `default_rule_priority` | int | `100` | Standard-Priorität für neue Regeln |

---

## Versionierung

### POC
- Nur kundenspezifische Artikelpreise
- Keine Staffelpreise
- Keine zeitliche Begrenzung

### MVP
- Alle Regel-Typen (Artikel, Serie, Marke, etc.)
- Staffelpreise
- Zeitliche Begrenzung
- Mindestmarge-Warnung
- Admin-UI vollständig

### V1
- Preishistorie / Änderungsprotokoll
- Massenimport von Preisregeln (CSV)
- Preisreport / Auswertungen
- API für externe Systeme
