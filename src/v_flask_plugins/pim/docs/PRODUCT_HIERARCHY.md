# PIM Plugin - Erweiterung für Produkthierarchie

## Übersicht

Diese Erweiterung des PIM-Plugins fügt die Produkthierarchie hinzu, die für das Pricing-Plugin benötigt wird:

- **Hersteller** (Manufacturer)
- **Marken** (Brands) - gehören zu Hersteller
- **Serien** (Series) - gehören zu Marke (optional)
- **Warengruppen** (Product Groups) - für Preisregeln
- **Preis-Tags** (Price Tags) - für flexible Preisregeln

---

## Produkthierarchie

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRODUKTHIERARCHIE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Hersteller (pim_manufacturer)                                  │
│  └── Marke (pim_brand)                                         │
│      └── Serie (pim_series) [optional]                         │
│          └── Artikel (pim_product)                             │
│                                                                 │
│  Parallel dazu:                                                 │
│  ├── Kategorie (pim_category) - Navigationsstruktur            │
│  ├── Warengruppe (pim_product_group) - für Preisregeln         │
│  └── Preis-Tags (pim_price_tag) - flexible Kennzeichnung       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Beispiel

```
Hersteller: Bosch
├── Marke: Bosch Professional (blau)
│   ├── Serie: 18V-System
│   │   ├── Artikel: GSR 18V-60 FC
│   │   └── Artikel: GBH 18V-26
│   └── Serie: 12V-System
│       └── Artikel: GSR 12V-35
└── Marke: Bosch Home & Garden (grün)
    └── Artikel: PSR 1800 (keine Serie)

Artikel: GSR 18V-60 FC
├── Hersteller: Bosch
├── Marke: Bosch Professional
├── Serie: 18V-System
├── Kategorie: Elektrowerkzeuge > Akkuschrauber
├── Warengruppe: Profi-Werkzeuge
└── Preis-Tags: [Neuheit, Bestseller]
```

---

## Neue Tabellen

### pim_manufacturer (Hersteller)

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| name | VARCHAR(255) | UNIQUE, NOT NULL | Herstellername |
| slug | VARCHAR(255) | UNIQUE, NOT NULL | URL-freundlicher Name |
| description | TEXT | NULL | Beschreibung |
| logo_url | VARCHAR(500) | NULL | Logo-URL (S3) |
| website | VARCHAR(255) | NULL | Hersteller-Website |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv |
| sort_order | INT | NOT NULL, DEFAULT 0 | Sortierung |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

### pim_brand (Marke)

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| manufacturer_id | UUID | FK, NOT NULL | Zugehöriger Hersteller |
| name | VARCHAR(255) | NOT NULL | Markenname |
| slug | VARCHAR(255) | UNIQUE, NOT NULL | URL-freundlicher Name |
| description | TEXT | NULL | Beschreibung |
| logo_url | VARCHAR(500) | NULL | Marken-Logo (S3) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv |
| sort_order | INT | NOT NULL, DEFAULT 0 | Sortierung |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Unique Constraint:** `(manufacturer_id, name)` - Markenname eindeutig pro Hersteller

### pim_series (Serie)

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| brand_id | UUID | FK, NOT NULL | Zugehörige Marke |
| name | VARCHAR(255) | NOT NULL | Serienname |
| slug | VARCHAR(255) | UNIQUE, NOT NULL | URL-freundlicher Name |
| description | TEXT | NULL | Beschreibung |
| image_url | VARCHAR(500) | NULL | Serien-Bild (S3) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv |
| sort_order | INT | NOT NULL, DEFAULT 0 | Sortierung |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Unique Constraint:** `(brand_id, name)` - Serienname eindeutig pro Marke

### pim_product_group (Warengruppe)

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| name | VARCHAR(255) | UNIQUE, NOT NULL | Gruppenname |
| slug | VARCHAR(255) | UNIQUE, NOT NULL | URL-freundlicher Name |
| description | TEXT | NULL | Beschreibung |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv |
| sort_order | INT | NOT NULL, DEFAULT 0 | Sortierung |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Verwendung:** Für Preisregeln im Pricing-Plugin (z.B. "Alle Artikel der Warengruppe 'Profi-Werkzeuge' bekommen 5% Rabatt")

### pim_price_tag (Preis-Tag)

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| id | UUID | PK | Primärschlüssel |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Tag-Name |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-freundlicher Name |
| color | VARCHAR(7) | NULL | Hex-Farbe (#FF0000) |
| description | TEXT | NULL | Beschreibung |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv |
| sort_order | INT | NOT NULL, DEFAULT 0 | Sortierung |
| created_at | TIMESTAMP | NOT NULL | Erstellzeitpunkt |
| updated_at | TIMESTAMP | NOT NULL | Letzte Änderung |

**Beispiele:** "Neuheit", "Auslaufmodell", "Bestseller", "Sale", "Sonderposten"

### pim_product_price_tag (n:m Verknüpfung)

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|--------------|
| product_id | UUID | FK, PK | Produkt |
| price_tag_id | UUID | FK, PK | Preis-Tag |
| created_at | TIMESTAMP | NOT NULL | Zuordnungszeitpunkt |

---

## Erweiterung pim_product

Die bestehende `pim_product` Tabelle wird erweitert:

```sql
ALTER TABLE pim_product ADD COLUMN manufacturer_id UUID REFERENCES pim_manufacturer(id);
ALTER TABLE pim_product ADD COLUMN brand_id UUID REFERENCES pim_brand(id);
ALTER TABLE pim_product ADD COLUMN series_id UUID REFERENCES pim_series(id);
ALTER TABLE pim_product ADD COLUMN product_group_id UUID REFERENCES pim_product_group(id);
```

| Neue Spalte | Typ | Constraints | Beschreibung |
|-------------|-----|-------------|--------------|
| manufacturer_id | UUID | FK, NULL | Hersteller |
| brand_id | UUID | FK, NULL | Marke |
| series_id | UUID | FK, NULL | Serie (optional) |
| product_group_id | UUID | FK, NULL | Warengruppe |

**Hinweis:** Alle neuen Felder sind optional (NULL erlaubt), um Abwärtskompatibilität zu gewährleisten.

---

## Entity-Relationship-Diagramm

```
┌─────────────────┐
│ pim_manufacturer│
│                 │
│ id (PK)         │
│ name            │
│ slug            │
└────────┬────────┘
         │ 1:N
         ▼
┌─────────────────┐
│ pim_brand       │
│                 │
│ id (PK)         │
│ manufacturer_id │──┐
│ name            │  │
│ slug            │  │
└────────┬────────┘  │
         │ 1:N       │
         ▼           │
┌─────────────────┐  │
│ pim_series      │  │
│                 │  │
│ id (PK)         │  │
│ brand_id        │──┼─┐
│ name            │  │ │
└────────┬────────┘  │ │
         │ 1:N       │ │
         ▼           │ │
┌─────────────────┐  │ │
│ pim_product     │  │ │
│                 │  │ │
│ id (PK)         │  │ │
│ manufacturer_id │◄─┘ │
│ brand_id        │◄───┘
│ series_id       │◄────┘
│ product_group_id│◄──────┐
│ category_id     │       │
└────────┬────────┘       │
         │                │
         │ N:M            │
         ▼                │
┌─────────────────┐       │
│pim_product_     │       │
│price_tag        │       │
│                 │       │
│ product_id (FK) │       │
│ price_tag_id(FK)│       │
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│ pim_price_tag   │       │
└─────────────────┘       │
                          │
┌─────────────────┐       │
│pim_product_group│───────┘
└─────────────────┘
```

---

## Services

### ManufacturerService

```python
class ManufacturerService:
    def get_all(self, active_only: bool = True) -> list[Manufacturer]
    def get_by_id(self, id: UUID) -> Manufacturer | None
    def get_by_slug(self, slug: str) -> Manufacturer | None
    def create(self, data: ManufacturerCreate) -> Manufacturer
    def update(self, id: UUID, data: ManufacturerUpdate) -> Manufacturer
    def delete(self, id: UUID) -> bool
    def get_brands(self, manufacturer_id: UUID) -> list[Brand]
```

### BrandService

```python
class BrandService:
    def get_all(self, active_only: bool = True) -> list[Brand]
    def get_by_manufacturer(self, manufacturer_id: UUID) -> list[Brand]
    def get_by_id(self, id: UUID) -> Brand | None
    def get_by_slug(self, slug: str) -> Brand | None
    def create(self, data: BrandCreate) -> Brand
    def update(self, id: UUID, data: BrandUpdate) -> Brand
    def delete(self, id: UUID) -> bool
    def get_series(self, brand_id: UUID) -> list[Series]
```

### SeriesService

```python
class SeriesService:
    def get_all(self, active_only: bool = True) -> list[Series]
    def get_by_brand(self, brand_id: UUID) -> list[Series]
    def get_by_id(self, id: UUID) -> Series | None
    def get_by_slug(self, slug: str) -> Series | None
    def create(self, data: SeriesCreate) -> Series
    def update(self, id: UUID, data: SeriesUpdate) -> Series
    def delete(self, id: UUID) -> bool
    def get_products(self, series_id: UUID) -> list[Product]
```

### ProductGroupService

```python
class ProductGroupService:
    def get_all(self, active_only: bool = True) -> list[ProductGroup]
    def get_by_id(self, id: UUID) -> ProductGroup | None
    def get_by_slug(self, slug: str) -> ProductGroup | None
    def create(self, data: ProductGroupCreate) -> ProductGroup
    def update(self, id: UUID, data: ProductGroupUpdate) -> ProductGroup
    def delete(self, id: UUID) -> bool
    def get_products(self, group_id: UUID) -> list[Product]
```

### PriceTagService

```python
class PriceTagService:
    def get_all(self, active_only: bool = True) -> list[PriceTag]
    def get_by_id(self, id: UUID) -> PriceTag | None
    def get_by_slug(self, slug: str) -> PriceTag | None
    def create(self, data: PriceTagCreate) -> PriceTag
    def update(self, id: UUID, data: PriceTagUpdate) -> PriceTag
    def delete(self, id: UUID) -> bool
    def get_products(self, tag_id: UUID) -> list[Product]
    def add_to_product(self, product_id: UUID, tag_id: UUID) -> bool
    def remove_from_product(self, product_id: UUID, tag_id: UUID) -> bool
```

---

## Admin-Oberfläche Erweiterungen

### Neue Menüpunkte

```
PIM (Hauptmenü)
├── Produkte (bestehend)
├── Kategorien (bestehend)
├── Hersteller [NEU]
│   ├── Übersicht
│   └── Neuer Hersteller
├── Marken [NEU]
│   ├── Übersicht
│   └── Neue Marke
├── Serien [NEU]
│   ├── Übersicht
│   └── Neue Serie
├── Warengruppen [NEU]
│   ├── Übersicht
│   └── Neue Warengruppe
├── Preis-Tags [NEU]
│   ├── Übersicht
│   └── Neuer Tag
└── Bilder (bestehend)
```

### Produkt-Formular Erweiterung

Im Produkt-Formular werden neue Felder hinzugefügt:

```
┌─────────────────────────────────────────────────────────────┐
│ Produkt bearbeiten: GSR 18V-60 FC                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Stammdaten                 │ Zuordnungen                   │
│ ─────────────────────────  │ ───────────────────────────── │
│ SKU: [BOsch-GSR18V60]      │ Kategorie: [Akkuschrauber ▼]  │
│ Name: [GSR 18V-60 FC]      │ Hersteller: [Bosch        ▼]  │
│ Preis: [299,00 €]          │ Marke: [Professional      ▼]  │ ← Gefiltert nach Hersteller
│                            │ Serie: [18V-System        ▼]  │ ← Gefiltert nach Marke
│                            │ Warengruppe: [Profi-Tools ▼]  │
│                            │                               │
│                            │ Preis-Tags:                   │
│                            │ ☑ Neuheit                     │
│                            │ ☐ Auslaufmodell               │
│                            │ ☑ Bestseller                  │
│                            │                               │
└─────────────────────────────────────────────────────────────┘
```

**Wichtig:** Die Dropdowns für Marke und Serie sind **kaskadierend**:
- Marken-Dropdown zeigt nur Marken des gewählten Herstellers
- Serien-Dropdown zeigt nur Serien der gewählten Marke
- Bei Änderung des Herstellers wird Marke zurückgesetzt
- Bei Änderung der Marke wird Serie zurückgesetzt

---

## API für Pricing-Plugin

Das PIM stellt APIs bereit, die das Pricing-Plugin nutzt:

```python
# Pricing-Plugin fragt: "Welche Produkte gehören zur Marke X?"
products = pim_product_service.get_by_brand(brand_id)

# Pricing-Plugin fragt: "Welche Produkte haben den Tag 'Sale'?"
products = pim_price_tag_service.get_products(sale_tag_id)

# Pricing-Plugin fragt: "Zu welchem Hersteller/Marke/Serie gehört Produkt X?"
product = pim_product_service.get_by_id(product_id)
manufacturer = product.manufacturer  # Eager loaded
brand = product.brand
series = product.series
```

---

## Migration

```python
# migrations/versions/002_product_hierarchy.py

def upgrade():
    # Hersteller
    op.create_table('pim_manufacturer',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Marke
    op.create_table('pim_brand',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('manufacturer_id', sa.UUID(), sa.ForeignKey('pim_manufacturer.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False),
        # ... weitere Spalten
    )
    op.create_unique_constraint('uq_brand_manufacturer_name', 'pim_brand', ['manufacturer_id', 'name'])
    
    # Serie
    op.create_table('pim_series',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('brand_id', sa.UUID(), sa.ForeignKey('pim_brand.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False),
        # ... weitere Spalten
    )
    op.create_unique_constraint('uq_series_brand_name', 'pim_series', ['brand_id', 'name'])
    
    # Warengruppe
    op.create_table('pim_product_group', ...)
    
    # Preis-Tags
    op.create_table('pim_price_tag', ...)
    op.create_table('pim_product_price_tag', ...)
    
    # Produkt erweitern
    op.add_column('pim_product', sa.Column('manufacturer_id', sa.UUID(), sa.ForeignKey('pim_manufacturer.id')))
    op.add_column('pim_product', sa.Column('brand_id', sa.UUID(), sa.ForeignKey('pim_brand.id')))
    op.add_column('pim_product', sa.Column('series_id', sa.UUID(), sa.ForeignKey('pim_series.id')))
    op.add_column('pim_product', sa.Column('product_group_id', sa.UUID(), sa.ForeignKey('pim_product_group.id')))

def downgrade():
    # Rückgängig machen in umgekehrter Reihenfolge
    pass
```

---

## Phasen-Zuordnung

Diese Erweiterungen sollten **vor dem Pricing-Plugin** implementiert werden, idealerweise als Teil von **PIM MVP**:

| Feature | Phase |
|---------|-------|
| Hersteller-Verwaltung | PIM MVP |
| Marken-Verwaltung | PIM MVP |
| Serien-Verwaltung | PIM MVP |
| Warengruppen | PIM MVP |
| Preis-Tags | PIM MVP |
| Kaskadierende Dropdowns | PIM MVP |
| Logo/Bild-Upload | PIM V1 |
